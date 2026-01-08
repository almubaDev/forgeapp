from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def register_signals():
    """
    Registra los signals una vez que la aplicación está lista.

    NOTA: Los signals de Payment están DESACTIVADOS porque ahora usamos PaymentEvent
    en forgeapp que maneja todo automáticamente mediante signals propios.
    El modelo Payment de finance está deprecado.
    """
    return  # Signals desactivados - usar PaymentEvent en forgeapp

    # CÓDIGO DEPRECADO - NO SE EJECUTA
    Subscription = apps.get_model('forgeapp', 'Subscription')
    Payment = apps.get_model('finance', 'Payment')
    Transaction = apps.get_model('finance', 'Transaction')
    
    @receiver(post_save, sender=Payment)
    def handle_payment_changes(sender, instance, created, **kwargs):
        """Maneja cambios en pagos"""
        try:
            logger.info(f"Procesando cambios en el pago ID: {instance.id}, Estado: {instance.status}")
            
            if instance.subscription:
                subscription = instance.subscription
                logger.info(f"Suscripción asociada ID: {subscription.id}, Cliente: {subscription.client.name}")

                # Si el pago está completado
                if instance.status == 'completed':
                    logger.info(f"Pago {instance.id} marcado como completado")
                    
                    # Verificar si ya existe otro pago pendiente con la misma fecha de vencimiento
                    # y marcarlo como pagado o eliminarlo
                    due_date = instance.due_date
                    if due_date:
                        logger.info(f"Buscando pagos pendientes duplicados con fecha de vencimiento: {due_date}")
                        duplicate_payments = Payment.objects.filter(
                            subscription=subscription,
                            due_date=due_date,
                            status='pending'
                        ).exclude(id=instance.id)
                        
                        if duplicate_payments.exists():
                            duplicate_count = duplicate_payments.count()
                            logger.info(f"Encontrados {duplicate_count} pagos pendientes duplicados, eliminándolos")
                            duplicate_payments.delete()
                    
                    # Activar la suscripción si está inactiva
                    if subscription.status != 'active':
                        subscription.status = 'active'
                        logger.info(f"Activando suscripción {subscription.id}")
                    
                    # Extender la fecha de fin según el tipo de pago
                    if subscription.payment_type == 'monthly':
                        current_end = max(subscription.end_date, timezone.now().date())
                        subscription.end_date = current_end + timedelta(days=30)
                        logger.info(f"Extendiendo fecha de fin a {subscription.end_date}")
                    elif subscription.payment_type == 'annual':
                        current_end = max(subscription.end_date, timezone.now().date())
                        subscription.end_date = current_end + timedelta(days=365)
                        logger.info(f"Extendiendo fecha de fin a {subscription.end_date}")

                    subscription.save()
                    logger.info(f"Suscripción guardada exitosamente")

                    # Verificar si ya existe una transacción para este pago
                    existing_transaction = Transaction.objects.filter(payment=instance).count()
                    if existing_transaction < 1:
                        # Crear transacción de ingreso solo si no existe
                        transaction = Transaction.objects.create(
                            type='income',
                            category='Pago de Suscripción',
                            description=f'Pago recibido - {subscription.client.name} - {subscription.application.name}',
                            amount=instance.amount,
                            date=instance.payment_date.date() if instance.payment_date else timezone.now().date(),
                            payment=instance,
                            notes='Ingreso registrado automáticamente por pago completado'
                        )
                        logger.info(f'Transacción de ingreso creada: {transaction.id}')
                        
                        # Generar y enviar recibo por email
                        try:
                            from django.core.mail import EmailMessage
                            from pdf_generator.views import generar_pdf_recibo_buffer
                            from io import BytesIO
                            from django.conf import settings
                            from django.template.loader import render_to_string
                            
                            # Generar el PDF en un buffer
                            buffer = BytesIO()
                            generar_pdf_recibo_buffer(instance, buffer)
                            pdf_data = buffer.getvalue()
                            buffer.close()
                            
                            # Obtener cliente
                            client = instance.subscription.client
                            if client and client.email:
                                # Crear el asunto
                                subject = f'ForgeApp: Comprobante de Pago - {instance.subscription.application.name if instance.subscription.application else "ForgeApp"}'
                                
                                # Obtener la URL del sitio para los recursos estáticos
                                site_url = settings.SITE_URL
                                
                                # Renderizar plantilla de email
                                html_content = render_to_string('finance/email/payment_receipt.html', {
                                    'payment': instance,
                                    'client': client,
                                    'subscription': instance.subscription,
                                    'application': instance.subscription.application if instance.subscription.application else None,
                                    'site_url': site_url,
                                    'now': timezone.now()
                                })
                                
                                # Crear el email con texto plano también para mejor compatibilidad
                                text_content = f"""
                                Estimado/a {client.name},
                                
                                ¡Su pago ha sido procesado exitosamente!
                                
                                Nos complace confirmarle que hemos recibido su pago por el servicio de {instance.subscription.application.name if instance.subscription.application else "ForgeApp"}. Adjunto a este email encontrará el comprobante de pago que puede guardar para sus registros.
                                
                                Detalles de la transacción:
                                - Monto: ${instance.amount}
                                - Fecha: {instance.payment_date.strftime('%d/%m/%Y %H:%M') if instance.payment_date else timezone.now().strftime('%d/%m/%Y %H:%M')}
                                - Referencia: {instance.subscription.reference_id}
                                - Tipo: {instance.subscription.get_payment_type_display()}
                                
                                Puede verificar la autenticidad de este comprobante escaneando el código QR adjunto en el PDF.
                                
                                Agradecemos su confianza en nosotros y estamos comprometidos en brindarle el mejor servicio. ¡Su satisfacción es nuestra prioridad!
                                
                                Si tiene alguna pregunta o necesita asistencia, no dude en contactarnos.
                                
                                Saludos cordiales,
                                Equipo ForgeApp
                                www.forgeapp.cl
                                """
                                
                                from django.core.mail import EmailMultiAlternatives
                                email = EmailMultiAlternatives(
                                    subject=subject,
                                    body=text_content,
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    to=[client.email]
                                )
                                
                                # Añadir versión HTML
                                email.attach_alternative(html_content, "text/html")
                                
                                # Adjuntar el PDF
                                filename = f"comprobante_{instance.id}.pdf"
                                email.attach(filename, pdf_data, 'application/pdf')
                                
                                # Enviar el email
                                email.send(fail_silently=False)
                                logger.info(f'Email con recibo enviado a {client.email} para pago {instance.id}')
                        except Exception as e:
                            logger.error(f'Error al enviar email con recibo: {str(e)}')

                # Si el pago falló o fue cancelado
                elif instance.status in ['failed', 'cancelled']:
                    logger.info(f"Pago {instance.id} marcado como fallido o cancelado")
                    
                    # Verificar si hay otros pagos pendientes o completados
                    # Usar finance_payments en lugar de payments
                    pending_or_completed = Payment.objects.filter(
                        subscription=subscription,
                        status__in=['pending', 'completed']
                    ).exclude(id=instance.id).exists()
                    
                    if not pending_or_completed:
                        subscription.status = 'cancelled'
                        subscription.save()
                        logger.info(f"Suscripción {subscription.id} cancelada por falta de pagos")

        except Exception as e:
            logger.error(f'Error al manejar cambios en pago: {e}')
