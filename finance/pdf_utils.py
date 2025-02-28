from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os
import logging
import qrcode
from django.urls import reverse
from django.conf import settings
from datetime import datetime

from .models import Payment

logger = logging.getLogger('finance')

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
        
        # Información del recibo
        recibo_info = [
            [Paragraph("<b>Comprobante N°:</b>", label_style), Paragraph(payment.transaction_id or str(payment.id), normal_style)],
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
        
        # URL de verificación
        verification_url = f"{settings.SITE_URL}/finance/verify/{payment.id}/"
        qr.add_data(verification_url)
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
