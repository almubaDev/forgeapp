from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
import os
import logging
import qrcode
from django.urls import reverse
from django.conf import settings
from datetime import datetime

from forgeapp.models import Calculadora
from checkout_counters.models import Receipt, PaymentLink

logger = logging.getLogger('pdf_generator')

def generar_pdf_propuesta_buffer(calculadora, buffer=None):
    """
    Genera un PDF con la propuesta de costos basada en una calculadora y lo escribe en un buffer.
    
    Args:
        calculadora: Instancia de Calculadora
        buffer: BytesIO buffer (opcional). Si no se proporciona, se crea uno nuevo.
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    if buffer is None:
        buffer = BytesIO()
    
    try:
        # Configurar el documento
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        
        # Definir estilos personalizados
        styles = getSampleStyleSheet()
        
        # Color azul del fondo
        bg_color = colors.HexColor('#0e3559')
        
        # Color turquesa para los títulos
        turquoise_color = colors.HexColor('#4EB8D5')
        
        # Estilo para los títulos principales
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        # Iniciar lista de elementos
        elements = []
        
        # Agregar logotipo
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
        
        # URL del sitio
        url = Paragraph("www.forgeapp.cl", ParagraphStyle(
            'URLStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=turquoise_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica'
        ))
        elements.append(url)
        elements.append(Spacer(1, 0.5*inch))
        
        # Título principal
        title = Paragraph("Propuesta de Costo por servicio", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Información del cliente
        cliente_info = [
            Paragraph(f"Cliente: {calculadora.client.name}", normal_style),
        ]
        
        # Agregar aplicación si existe
        if hasattr(calculadora, 'application') and calculadora.application:
            cliente_info.append(Paragraph(f"Aplicación: {calculadora.application.name}", normal_style))
        
        for info in cliente_info:
            elements.append(info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla de costos
        data = [
            ["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
        ]
        
        # Agregar items de la calculadora
        for item in calculadora.items.all():
            cantidad_str = f"{item.cantidad:.2f}".rstrip('0').rstrip('.') if item.cantidad == int(item.cantidad) else f"{item.cantidad:.2f}"
            data.append([
                item.descripcion,
                cantidad_str,
                f"${item.precio_unitario:,.0f}",
                f"${item.subtotal:,.0f}"
            ])
        
        # Agregar fila para "Logística de desarrollo" si hay margen
        if calculadora.margen > 0:
            logistica_valor = calculadora.subtotal * (calculadora.margen / 100)
            data.append([
                "Logística de desarrollo",
                "1",
                f"${logistica_valor:,.0f}",  # Mostrar el valor en dinero en lugar del porcentaje
                f"${logistica_valor:,.0f}"
            ])
        
        tabla_costos = Table(data, colWidths=[9*cm, 2*cm, 2.5*cm, 2.5*cm])
        tabla_costos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0e4575')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0e3559')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4EB8D5')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(tabla_costos)
        elements.append(Spacer(1, 0.5*inch))
        
        # Costo mensual
        costo_mensual = Paragraph("Costo", subtitle_style)
        elements.append(costo_mensual)
        elements.append(Spacer(1, 0.2*inch))
        
        # Mostrar solo el costo mensual
        costo_mensual_texto = Paragraph(
            f"${calculadora.cuota_mensual:,.0f} a pagar mes a mes mientras se esté suscrito.",
            ParagraphStyle(
                'CostoMensualStyle',
                parent=normal_style,
                fontSize=16,
                alignment=TA_LEFT
            )
        )
        elements.append(costo_mensual_texto)
        elements.append(Spacer(1, 0.5*inch))
        
        # Descripción de la aplicación (si existe)
        if hasattr(calculadora, 'application') and calculadora.application and calculadora.application.description:
            # Agregar página de salto
            elements.append(PageBreak())
            
            desc_app = Paragraph("Descripción de la Aplicación", subtitle_style)
            elements.append(desc_app)
            elements.append(Spacer(1, 0.2*inch))
            
            # Descripción funcional
            desc_func = Paragraph("Descripción Funcional", ParagraphStyle(
                'FuncionalStyle', 
                parent=subtitle_style, 
                fontSize=16
            ))
            elements.append(desc_func)
            elements.append(Spacer(1, 0.2*inch))
            
            # Procesar markdown
            from forgeapp.markdown_processor import process_markdown_section
            sections = process_markdown_section(calculadora.application.description)
            
            for section_type, content in sections:
                if section_type == 'title':
                    level = content['level']
                    if level == 1:
                        elements.append(Paragraph(content['text'], ParagraphStyle(
                            'SeccionStyle',
                            parent=styles['Heading1'],
                            fontSize=16,
                            textColor=turquoise_color,
                            alignment=TA_LEFT,
                            spaceAfter=10,
                            fontName='Helvetica-Bold'
                        )))
                    elif level == 2:
                        elements.append(Paragraph(content['text'], ParagraphStyle(
                            'SeccionStyle',
                            parent=styles['Heading2'],
                            fontSize=14,
                            textColor=turquoise_color,
                            alignment=TA_LEFT,
                            spaceAfter=10,
                            fontName='Helvetica-Bold'
                        )))
                    else:
                        elements.append(Paragraph(content['text'], ParagraphStyle(
                            'SeccionStyle',
                            parent=styles['Heading3'],
                            fontSize=12,
                            textColor=turquoise_color,
                            alignment=TA_LEFT,
                            spaceAfter=10,
                            fontName='Helvetica-Bold'
                        )))
                    elements.append(Spacer(1, 0.1*inch))
                elif section_type == 'content':
                    elements.append(Paragraph(content, normal_style))
                    elements.append(Spacer(1, 0.2*inch))
                elif section_type == 'list':
                    list_content = " - ".join(content)
                    elements.append(Paragraph(list_content, normal_style))
                    elements.append(Spacer(1, 0.2*inch))
        
        # Construir el PDF
        doc.build(elements, onFirstPage=page_background, onLaterPages=page_background)
        
        # Devolver el buffer posicionado al inicio
        buffer.seek(0)
        return buffer
    
    except Exception as e:
        logger.error(f"Error al generar PDF en buffer: {str(e)}")
        raise

@login_required
def generar_pdf_propuesta(request, pk):
    """
    Genera un PDF con la propuesta de costos basada en una calculadora.
    """
    try:
        # Obtener la calculadora
        calculadora = get_object_or_404(Calculadora, pk=pk)
        
        # Generar el PDF en un buffer
        buffer = BytesIO()
        generar_pdf_propuesta_buffer(calculadora, buffer)
        
        # Obtener el valor del PDF del buffer
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP con PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="propuesta_{calculadora.client.name}_{calculadora.pk}.pdf"'
        response.write(pdf_value)
        return response
    
    except Exception as e:
        logger.error(f"Error al generar PDF: {str(e)}")
        raise

def page_background(canvas, doc):
    """
    Función para agregar el fondo azul a todas las páginas
    """
    # Color de fondo azul
    canvas.setFillColor(colors.HexColor('#0e3559'))
    canvas.rect(0, 0, doc.width + 2*doc.leftMargin, doc.height + 2*doc.bottomMargin, fill=1)
    
    # Agregar un pie de página o elementos adicionales si se desea
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.5*inch, "ForgeApp - www.forgeapp.cl")

@login_required
def generar_pdf_recibo(request, pk):
    """
    Genera un PDF con el recibo de pago basado en un PaymentLink.
    """
    try:
        # Configurar el buffer y el documento
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        
        # Obtener el PaymentLink
        payment_link = get_object_or_404(PaymentLink, pk=pk)
        
        # Definir estilos personalizados
        styles = getSampleStyleSheet()
        
        # Color azul del fondo
        bg_color = colors.HexColor('#0e3559')
        
        # Color turquesa para los títulos
        turquoise_color = colors.HexColor('#4EB8D5')
        
        # Estilo para los títulos principales
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=turquoise_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        # Estilo para etiquetas
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#0e3559'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Iniciar lista de elementos
        elements = []
        
        # Agregar logotipo
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
        
        # Título principal
        title = Paragraph("Comprobante de Pago", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Generar un número de recibo si no existe
        receipt_number = f"REC-{payment_link.reference_id}"
        
        # Verificar si ya existe un recibo para este pago
        try:
            receipt = Receipt.objects.get(payment_link=payment_link)
            receipt_number = receipt.receipt_number
        except Receipt.DoesNotExist:
            pass
        
        # Información del recibo
        recibo_info = [
            [Paragraph("<b>Comprobante N°:</b>", label_style), Paragraph(receipt_number, normal_style)],
            [Paragraph("<b>Fecha:</b>", label_style), Paragraph(payment_link.created_at.strftime("%d/%m/%Y %H:%M"), normal_style)],
        ]
        
        # Agregar información del cliente si está disponible
        if payment_link.subscription and payment_link.subscription.client:
            client = payment_link.subscription.client
            recibo_info.extend([
                [Paragraph("<b>Cliente:</b>", label_style), Paragraph(client.name, normal_style)],
                [Paragraph("<b>RUT:</b>", label_style), Paragraph(client.rut if client.rut else "No disponible", normal_style)],
            ])
            
            if client.company:
                recibo_info.append([Paragraph("<b>Empresa:</b>", label_style), Paragraph(client.company, normal_style)])
                
                if client.company_rut:
                    recibo_info.append([Paragraph("<b>RUT Empresa:</b>", label_style), Paragraph(client.company_rut, normal_style)])
        
        # Agregar información del pagador si está disponible
        elif payment_link.payer_name:
            recibo_info.append([Paragraph("<b>Pagador:</b>", label_style), Paragraph(payment_link.payer_name, normal_style)])
            
            if payment_link.payer_email:
                recibo_info.append([Paragraph("<b>Email:</b>", label_style), Paragraph(payment_link.payer_email, normal_style)])
        
        # Crear tabla con la información del recibo
        tabla_info = Table(recibo_info, colWidths=[3*cm, 12*cm])
        tabla_info.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(tabla_info)
        elements.append(Spacer(1, 0.5*inch))
        
        # Detalles del servicio
        elements.append(Paragraph("Detalles del Servicio", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información del servicio
        servicio_info = []
        
        # Agregar información de la suscripción si está disponible
        if payment_link.subscription:
            subscription = payment_link.subscription
            
            if subscription.application:
                servicio_info.append([Paragraph("<b>Aplicación:</b>", label_style), Paragraph(subscription.application.name, normal_style)])
            
            servicio_info.append([Paragraph("<b>Referencia:</b>", label_style), Paragraph(subscription.reference_id, normal_style)])
            
            if subscription.start_date and subscription.end_date:
                periodo = f"{subscription.start_date.strftime('%d/%m/%Y')} - {subscription.end_date.strftime('%d/%m/%Y')}"
                servicio_info.append([Paragraph("<b>Período:</b>", label_style), Paragraph(periodo, normal_style)])
            
            if hasattr(subscription, 'get_payment_type_display'):
                servicio_info.append([Paragraph("<b>Tipo de Pago:</b>", label_style), Paragraph(subscription.get_payment_type_display(), normal_style)])
        
        # Agregar descripción del pago
        servicio_info.append([Paragraph("<b>Descripción:</b>", label_style), Paragraph(payment_link.description, normal_style)])
        
        # Agregar monto
        servicio_info.append([Paragraph("<b>Monto:</b>", label_style), Paragraph(f"${payment_link.amount:,.0f}", normal_style)])
        
        # Agregar estado
        servicio_info.append([Paragraph("<b>Estado:</b>", label_style), Paragraph(payment_link.get_status_display(), normal_style)])
        
        # Crear tabla con la información del servicio
        tabla_servicio = Table(servicio_info, colWidths=[3*cm, 12*cm])
        tabla_servicio.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(tabla_servicio)
        elements.append(Spacer(1, 0.5*inch))
        
        # Generar código QR para verificación
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # URL de verificación
        verification_url = f"{settings.SITE_URL}{reverse('checkout_counters:verify_receipt', kwargs={'secret_code': payment_link.pk})}"
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        img.save(qr_buffer)
        qr_buffer.seek(0)
        
        # Agregar código QR
        qr_img = Image(qr_buffer, width=2*inch, height=2*inch)
        
        # Crear tabla para el código QR (sin texto de verificación)
        qr_data = [
            [qr_img]
        ]
        
        qr_table = Table(qr_data, colWidths=[15*cm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(qr_table)
        
        # Crear una función de callback personalizada para el fondo de página
        def recibo_page_background_with_payment_link(canvas, doc):
            recibo_page_background(canvas, doc, payment_link)
        
        # Construir el PDF
        doc.build(elements, onFirstPage=recibo_page_background_with_payment_link, onLaterPages=recibo_page_background_with_payment_link)
        
        # Obtener el valor del PDF del buffer y limpiarlo
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP con PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{receipt_number}.pdf"'
        response.write(pdf_value)
        return response
    
    except Exception as e:
        logger.error(f"Error al generar PDF de recibo: {str(e)}")
        raise

def recibo_page_background(canvas, doc, payment_link=None):
    """
    Función para agregar el fondo y pie de página para el recibo
    """
    # Agregar un pie de página
    canvas.setFillColor(colors.HexColor('#0e3559'))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.5*inch, "ForgeApp - www.forgeapp.cl")
    canvas.drawString(doc.width - 3*inch, 0.5*inch, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Agregar marca de agua "PAGADO" si el pago está completado
    if payment_link and payment_link.is_paid:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#4EB8D5'))
        canvas.setFont("Helvetica-Bold", 72)
        canvas.translate(doc.width/2, doc.height/2)
        canvas.rotate(45)
        canvas.setFillAlpha(0.1)
        canvas.drawCentredString(0, 0, "PAGADO")
        canvas.restoreState()

def generar_pdf_contrato_buffer(token_obj, buffer=None):
    """
    Genera un PDF con el contrato de servicio y lo escribe en un buffer.
    
    Args:
        token_obj: Instancia de ServiceContractToken
        buffer: BytesIO buffer (opcional). Si no se proporciona, se crea uno nuevo.
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    if buffer is None:
        buffer = BytesIO()
    
    try:
        from forgeapp.models import Application
        
        # Obtener el cliente y la aplicación
        client = token_obj.client
        application = Application.objects.get(pk=token_obj.application_id)
        
        # Configurar el documento
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        
        # Definir estilos personalizados
        styles = getSampleStyleSheet()
        
        # Color azul del fondo
        bg_color = colors.HexColor('#0e3559')
        
        # Color turquesa para los títulos
        turquoise_color = colors.HexColor('#4EB8D5')
        
        # Estilo para los títulos principales
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=turquoise_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica'
        )
        
        # Estilo para etiquetas
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#0e3559'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para títulos de secciones
        section_title_style = ParagraphStyle(
            'SectionTitleStyle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#0e3559'),
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Iniciar lista de elementos
        elements = []
        
        # Agregar logotipo
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*inch))
        
        # Título principal
        title = Paragraph("CONTRATO DE SERVICIO", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Información del contrato
        elements.append(Paragraph("INFORMACIÓN DEL CONTRATO", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Fecha de firma
        if token_obj.used and token_obj.used_at:
            fecha_firma = token_obj.used_at.strftime("%d/%m/%Y %H:%M")
            elements.append(Paragraph(f"<b>Fecha de Firma:</b> {fecha_firma}", normal_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Información del cliente
        elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        cliente_info = [
            [Paragraph("<b>Nombre:</b>", label_style), Paragraph(client.name, normal_style)],
            [Paragraph("<b>RUT:</b>", label_style), Paragraph(client.rut, normal_style)],
            [Paragraph("<b>Email:</b>", label_style), Paragraph(client.email, normal_style)],
        ]
        
        if client.phone:
            cliente_info.append([Paragraph("<b>Teléfono:</b>", label_style), Paragraph(client.phone, normal_style)])
        
        if client.company:
            cliente_info.append([Paragraph("<b>Empresa:</b>", label_style), Paragraph(client.company, normal_style)])
            
            if client.company_rut:
                cliente_info.append([Paragraph("<b>RUT Empresa:</b>", label_style), Paragraph(client.company_rut, normal_style)])
        
        # Crear tabla con la información del cliente
        tabla_cliente = Table(cliente_info, colWidths=[3*cm, 12*cm])
        tabla_cliente.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(tabla_cliente)
        elements.append(Spacer(1, 0.5*inch))
        
        # Información de la suscripción
        elements.append(Paragraph("DETALLES DEL SERVICIO", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        servicio_info = [
            [Paragraph("<b>Aplicación:</b>", label_style), Paragraph(application.name, normal_style)],
            [Paragraph("<b>Tipo de Suscripción:</b>", label_style), Paragraph("Mensual" if token_obj.subscription_type == "monthly" else "Anual", normal_style)],
            [Paragraph("<b>Valor:</b>", label_style), Paragraph(f"${token_obj.price:,.0f}", normal_style)],
        ]
        
        # Crear tabla con la información del servicio
        tabla_servicio = Table(servicio_info, colWidths=[3*cm, 12*cm])
        tabla_servicio.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(tabla_servicio)
        elements.append(Spacer(1, 0.5*inch))
        
        # Términos y condiciones
        elements.append(Paragraph("TÉRMINOS Y CONDICIONES", subtitle_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 1. DEFINICIONES
        elements.append(Paragraph("1. DEFINICIONES", section_title_style))
        elements.append(Paragraph('"ForgeApp" se refiere a la empresa proveedora del servicio.', normal_style))
        elements.append(Paragraph('"Cliente" se refiere a la persona natural o jurídica que contrata los servicios de ForgeApp.', normal_style))
        elements.append(Paragraph('"Servicio" se refiere a la aplicación o software proporcionado bajo el modelo SaaS.', normal_style))
        elements.append(Paragraph('"SaaS" (Software as a Service) se refiere al modelo de distribución de software donde el software y los datos se alojan en servidores del proveedor y se accede a ellos a través de internet.', normal_style))
        elements.append(Paragraph('"Suscripción" se refiere al pago periódico que realiza el Cliente para acceder al Servicio.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 2. DESCRIPCIÓN DEL SERVICIO
        elements.append(Paragraph("2. DESCRIPCIÓN DEL SERVICIO", section_title_style))
        elements.append(Paragraph('ForgeApp proporcionará al Cliente acceso a la aplicación seleccionada a través de internet, bajo el modelo SaaS.', normal_style))
        elements.append(Paragraph('El servicio incluye alojamiento, mantenimiento, actualizaciones y soporte técnico básico.', normal_style))
        elements.append(Paragraph('ForgeApp se reserva el derecho de realizar mejoras y modificaciones al Servicio sin previo aviso, siempre que no afecten negativamente la funcionalidad principal.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 3. DURACIÓN DEL CONTRATO
        elements.append(Paragraph("3. DURACIÓN DEL CONTRATO", section_title_style))
        elements.append(Paragraph(f'El presente contrato tendrá una duración inicial de {"un mes" if token_obj.subscription_type == "monthly" else "un año"}, según el tipo de suscripción seleccionada.', normal_style))
        elements.append(Paragraph('El contrato se renovará automáticamente por períodos iguales, salvo que el Cliente notifique su intención de no renovar con al menos 15 días de anticipación a la fecha de renovación.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 4. PRECIO Y FORMA DE PAGO
        elements.append(Paragraph("4. PRECIO Y FORMA DE PAGO", section_title_style))
        elements.append(Paragraph('El Cliente pagará a ForgeApp el precio correspondiente al tipo de suscripción seleccionada.', normal_style))
        elements.append(Paragraph('Los pagos se realizarán por adelantado, al inicio de cada período de suscripción.', normal_style))
        elements.append(Paragraph('ForgeApp se reserva el derecho de modificar los precios, notificando al Cliente con al menos 30 días de anticipación.', normal_style))
        elements.append(Paragraph('La falta de pago dará lugar a la suspensión del Servicio hasta que se regularice la situación.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Agregar página de salto
        elements.append(PageBreak())
        
        # 5. PROPIEDAD INTELECTUAL
        elements.append(Paragraph("5. PROPIEDAD INTELECTUAL", section_title_style))
        elements.append(Paragraph('Las aplicaciones creadas y puestas a disposición bajo servicio SaaS serán propiedad de ForgeApp hasta que el Cliente cumpla 48 mensualidades de suscripción, continuas o no.', normal_style))
        elements.append(Paragraph('Después del período mencionado (48 meses), el Cliente podrá solicitar el código de su aplicación para hacer uso del mismo fuera del vínculo con ForgeApp.', normal_style))
        elements.append(Paragraph('Durante los primeros 48 meses de suscripción, la aplicación es propiedad de ForgeApp y el Cliente solo podrá hacer uso de ella mientras mantenga su suscripción al día.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 6. PROTECCIÓN DE DATOS
        elements.append(Paragraph("6. PROTECCIÓN DE DATOS", section_title_style))
        elements.append(Paragraph('La protección de los datos almacenados por el Cliente en la aplicación proporcionada por ForgeApp es de responsabilidad compartida.', normal_style))
        elements.append(Paragraph('El Cliente debe seguir las siguientes normas de seguridad estándar para la protección de los datos:', normal_style))
        elements.append(Paragraph('- Utilizar contraseñas seguras y cambiarlas periódicamente.', normal_style))
        elements.append(Paragraph('- No compartir credenciales de acceso entre usuarios.', normal_style))
        elements.append(Paragraph('- Mantener actualizado el software de los dispositivos desde los que se accede al Servicio.', normal_style))
        elements.append(Paragraph('- Utilizar conexiones seguras (HTTPS) para acceder al Servicio.', normal_style))
        elements.append(Paragraph('- Realizar copias de seguridad periódicas de los datos críticos.', normal_style))
        elements.append(Paragraph('- Notificar inmediatamente a ForgeApp cualquier brecha de seguridad detectada.', normal_style))
        elements.append(Paragraph('ForgeApp implementará medidas de seguridad razonables para proteger los datos del Cliente, incluyendo cifrado de datos, copias de seguridad periódicas y controles de acceso.', normal_style))
        elements.append(Paragraph('ForgeApp cumplirá con la legislación aplicable en materia de protección de datos personales.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 7. PROPIEDAD DE LOS DATOS
        elements.append(Paragraph("7. PROPIEDAD DE LOS DATOS", section_title_style))
        elements.append(Paragraph('Los datos almacenados en las bases de datos relacionadas a los software y/o aplicaciones web brindadas bajo sistema SaaS por ForgeApp son propiedad del Cliente que contrata los servicios.', normal_style))
        elements.append(Paragraph('El Cliente puede solicitar sus datos cuando estime conveniente para migrarse a otro proveedor de servicio.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 8. LIMITACIÓN DE RESPONSABILIDAD
        elements.append(Paragraph("8. LIMITACIÓN DE RESPONSABILIDAD", section_title_style))
        elements.append(Paragraph('ForgeApp no será responsable por daños indirectos, incidentales, especiales o consecuentes que resulten del uso o la imposibilidad de usar el Servicio.', normal_style))
        elements.append(Paragraph('La responsabilidad total de ForgeApp se limitará al monto pagado por el Cliente durante los últimos 12 meses.', normal_style))
        elements.append(Paragraph('ForgeApp no garantiza que el Servicio esté libre de errores o que su funcionamiento sea ininterrumpido.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 9. TERMINACIÓN DEL CONTRATO
        elements.append(Paragraph("9. TERMINACIÓN DEL CONTRATO", section_title_style))
        elements.append(Paragraph('Cualquiera de las partes podrá terminar el contrato en caso de incumplimiento grave de la otra parte.', normal_style))
        elements.append(Paragraph('En caso de terminación, el Cliente tendrá acceso al Servicio hasta el final del período pagado.', normal_style))
        elements.append(Paragraph('ForgeApp proporcionará al Cliente una copia de sus datos en un formato estándar, si así lo solicita, dentro de los 30 días siguientes a la terminación.', normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # 10. DISPOSICIONES GENERALES
        elements.append(Paragraph("10. DISPOSICIONES GENERALES", section_title_style))
        elements.append(Paragraph('Este contrato constituye el acuerdo completo entre las partes y reemplaza cualquier acuerdo previo.', normal_style))
        elements.append(Paragraph('Las modificaciones a este contrato deberán hacerse por escrito y ser aceptadas por ambas partes.', normal_style))
        elements.append(Paragraph('La invalidez o inaplicabilidad de cualquier disposición de este contrato no afectará la validez o aplicabilidad de las demás disposiciones.', normal_style))
        elements.append(Paragraph('Este contrato se regirá por las leyes de Chile y cualquier controversia será sometida a la jurisdicción de los tribunales de Santiago.', normal_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Firma del cliente
        if token_obj.used and token_obj.used_at:
            elements.append(Paragraph("ACEPTACIÓN DEL CLIENTE", subtitle_style))
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(f"El cliente {client.name} ha aceptado este contrato electrónicamente el {token_obj.used_at.strftime('%d/%m/%Y')} a las {token_obj.used_at.strftime('%H:%M')} horas.", normal_style))
        
        # Construir el PDF
        doc.build(elements)
        
        # Devolver el buffer posicionado al inicio
        buffer.seek(0)
        return buffer
    
    except Exception as e:
        logger.error(f"Error al generar PDF de contrato en buffer: {str(e)}")
        raise

def generar_pdf_contrato(request, token_id):
    """
    Genera un PDF con el contrato de servicio.
    """
    try:
        from forgeapp.models import ServiceContractToken
        
        # Obtener el token
        token_obj = get_object_or_404(ServiceContractToken, id=token_id)
        
        # Verificar que el token haya sido usado (contrato aceptado)
        if not token_obj.used:
            return HttpResponse("Este contrato no ha sido aceptado aún.", status=400)
        
        # Generar el PDF en un buffer
        buffer = BytesIO()
        generar_pdf_contrato_buffer(token_obj, buffer)
        
        # Obtener el valor del PDF del buffer
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP con PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrato_{token_obj.client.name}_{token_obj.token[:8]}.pdf"'
        response.write(pdf_value)
        return response
    
    except Exception as e:
        logger.error(f"Error al generar PDF de contrato: {str(e)}")
        raise
