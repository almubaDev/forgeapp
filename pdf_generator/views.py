from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
import os
import logging
from django.conf import settings
from datetime import datetime
import qrcode
import secrets

from forgeapp.models import Calculadora, ServiceContractToken
from finance.models import Payment, Transaction, Receipt

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

def generar_pdf_recibo_buffer(payment, buffer=None):
    """
    Genera un PDF con el recibo de pago basado en un Payment.
    """
    if buffer is None:
        buffer = BytesIO()
    
    try:
        # Configurar el documento
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch)
        
        # Definir estilos personalizados
        styles = getSampleStyleSheet()
        
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
        
        # Buscar o crear un recibo asociado
        try:
            receipt = Receipt.objects.get(payment=payment)
        except Receipt.DoesNotExist:
            # Generar un código de verificación único
            verification_code = secrets.token_hex(8)
            
            # Crear un nuevo recibo
            receipt = Receipt.objects.create(
                payment=payment,
                receipt_number=f"REC-{payment.id}-{int(datetime.now().timestamp())}",
                verification_code=verification_code
            )
        
        # Información del recibo
        recibo_info = [
            [Paragraph("<b>Comprobante N°:</b>", label_style), Paragraph(receipt.receipt_number, normal_style)],
            [Paragraph("<b>Fecha:</b>", label_style), Paragraph(payment.payment_date.strftime("%d/%m/%Y %H:%M"), normal_style)],
        ]
        
        # Agregar información del cliente
        if payment.subscription and payment.subscription.client:
            client = payment.subscription.client
            recibo_info.extend([
                [Paragraph("<b>Cliente:</b>", label_style), Paragraph(client.name, normal_style)],
                [Paragraph("<b>RUT:</b>", label_style), Paragraph(client.rut if client.rut else "No disponible", normal_style)],
            ])
            
            if client.company:
                recibo_info.append([Paragraph("<b>Empresa:</b>", label_style), Paragraph(client.company, normal_style)])
                if client.company_rut:
                    recibo_info.append([Paragraph("<b>RUT Empresa:</b>", label_style), Paragraph(client.company_rut, normal_style)])
        
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
        elements.append(Paragraph("Detalles del Servicio", ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )))
        elements.append(Spacer(1, 0.2*inch))
        
        # Información del servicio
        servicio_info = []
        
        # Agregar información de la suscripción si está disponible
        if payment.subscription:
            subscription = payment.subscription
            
            if subscription.application:
                servicio_info.append([Paragraph("<b>Aplicación:</b>", label_style), Paragraph(subscription.application.name, normal_style)])
            
            servicio_info.append([Paragraph("<b>Referencia:</b>", label_style), Paragraph(subscription.reference_id, normal_style)])
            
            if subscription.start_date and subscription.end_date:
                periodo = f"{subscription.start_date.strftime('%d/%m/%Y')} - {subscription.end_date.strftime('%d/%m/%Y')}"
                servicio_info.append([Paragraph("<b>Período:</b>", label_style), Paragraph(periodo, normal_style)])
            
            if hasattr(subscription, 'get_payment_type_display'):
                servicio_info.append([Paragraph("<b>Tipo de Pago:</b>", label_style), Paragraph(subscription.get_payment_type_display(), normal_style)])
        
        # Agregar monto
        servicio_info.append([Paragraph("<b>Monto:</b>", label_style), Paragraph(f"${payment.amount:,.0f}", normal_style)])
        
        # Agregar estado
        servicio_info.append([Paragraph("<b>Estado:</b>", label_style), Paragraph(payment.get_status_display(), normal_style)])
        
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
        
        # Solo añadir el código de verificación al QR, no una URL completa
        qr.add_data(f"{receipt.receipt_number}|{receipt.verification_code}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        img.save(qr_buffer)
        qr_buffer.seek(0)
        
        # Agregar código QR
        qr_img = Image(qr_buffer, width=2*inch, height=2*inch)
        
        # Crear tabla para el código QR
        qr_data = [[qr_img]]
        qr_table = Table(qr_data, colWidths=[15*cm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(qr_table)
        
        # Espaciado final
        elements.append(Spacer(1, 0.2*inch))
        
        # Construir el PDF
        doc.build(elements)
        
        # Devolver el buffer posicionado al inicio
        buffer.seek(0)
        return buffer
    
    except Exception as e:
        logger.error(f"Error al generar PDF de recibo: {str(e)}")
        raise

def generar_pdf_recibo(payment):
    """
    Genera un PDF con el recibo de pago.
    """
    try:
        # Generar el PDF en un buffer
        buffer = BytesIO()
        generar_pdf_recibo_buffer(payment, buffer)
        
        # Obtener el valor del PDF del buffer
        pdf_value = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP con PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{payment.id}.pdf"'
        response.write(pdf_value)
        return response
    
    except Exception as e:
        logger.error(f"Error al generar PDF de recibo: {str(e)}")
        raise

def verificar_comprobante(request, receipt_number, verification_code):
    """
    Verifica la autenticidad de un comprobante de pago.
    """
    try:
        # Buscar el recibo
        receipt = Receipt.objects.get(receipt_number=receipt_number, verification_code=verification_code)
        payment = receipt.payment
        
        # Si existe, mostrar la información
        return render(request, 'pdf_generator/verificar_comprobante.html', {
            'is_valid': True,
            'receipt': receipt,
            'payment': payment,
            'client': payment.subscription.client if payment.subscription else None,
            'application': payment.subscription.application if payment.subscription else None,
            'now': timezone.now(),
        })
    except Receipt.DoesNotExist:
        # Si no existe, mostrar mensaje de error
        return render(request, 'pdf_generator/verificar_comprobante.html', {
            'is_valid': False,
            'error_message': 'El comprobante no existe o el código de verificación es inválido.'
        })
    except Exception as e:
        logger.error(f"Error al verificar comprobante: {str(e)}")
        return render(request, 'pdf_generator/verificar_comprobante.html', {
            'is_valid': False,
            'error_message': f'Error al verificar el comprobante: {str(e)}'
        })

def verificar_comprobante_form(request):
    """
    Muestra un formulario para verificar un comprobante o procesa el formulario.
    """
    if request.method == 'POST':
        receipt_number = request.POST.get('receipt_number')
        verification_code = request.POST.get('verification_code')
        
        if not receipt_number or not verification_code:
            return render(request, 'pdf_generator/verificar_form.html', {
                'error_message': 'Por favor complete todos los campos.'
            })
        
        # Redirigir a la vista de verificación con los datos proporcionados
        return redirect('pdf_generator:verificar_comprobante', receipt_number=receipt_number, verification_code=verification_code)
    
    # Si es GET, mostrar el formulario
    return render(request, 'pdf_generator/verificar_form.html')
