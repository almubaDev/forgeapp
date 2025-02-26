import logging
from io import BytesIO
from django.conf import settings
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import qrcode
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_payment_receipt(payment_data, client_data, subscription_id, verification_code):
    """
    Genera un PDF con el recibo de pago.
    
    Args:
        payment_data: Diccionario con datos del pago
        client_data: Diccionario con datos del cliente
        subscription_id: ID de referencia de la suscripción
        verification_code: Código de verificación
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    try:
        # Configurar el buffer y el documento
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
        
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
            fontSize=20,
            textColor=turquoise_color,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=turquoise_color,
            alignment=TA_LEFT,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para texto normal
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8,
            fontName='Helvetica'
        )
        
        # Estilo para etiquetas
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#0e3559'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Iniciar lista de elementos
        elements = []
        
        # Agregar logotipo
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=0.75*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.3*inch))
        
        # Título principal
        title = Paragraph("Comprobante de Pago", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Generar un número de recibo
        receipt_number = f"REC-{payment_data['reference_id']}"
        
        # Información del recibo
        recibo_info = [
            [Paragraph("<b>Comprobante N°:</b>", label_style), Paragraph(receipt_number, normal_style)],
            [Paragraph("<b>Fecha:</b>", label_style), Paragraph(payment_data['created_at'].strftime("%d/%m/%Y %H:%M"), normal_style)],
        ]
        
        # Agregar información del cliente si está disponible
        if client_data:
            if client_data.get('company'):
                recibo_info.append([Paragraph("<b>Empresa:</b>", label_style), Paragraph(client_data['company'], normal_style)])
            
            if client_data.get('rut'):
                recibo_info.append([Paragraph("<b>RUT:</b>", label_style), Paragraph(client_data['rut'], normal_style)])
        
        # Crear tabla con la información del recibo
        tabla_info = Table(recibo_info, colWidths=[3*cm, 12*cm])
        tabla_info.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(tabla_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Detalles del servicio
        elements.append(Paragraph("Detalles del Servicio", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Información del servicio
        servicio_info = []
        
        # Agregar información de la suscripción
        servicio_info.append([Paragraph("<b>Referencia:</b>", label_style), Paragraph(subscription_id, normal_style)])
        
        # Agregar descripción del pago
        servicio_info.append([Paragraph("<b>Descripción:</b>", label_style), Paragraph(f"Pago de suscripción {subscription_id}", normal_style)])
        
        # Agregar monto
        servicio_info.append([Paragraph("<b>Monto:</b>", label_style), Paragraph(f"${payment_data['amount']:,.0f}", normal_style)])
        
        # Agregar estado
        servicio_info.append([Paragraph("<b>Estado:</b>", label_style), Paragraph(payment_data['get_status_display'](), normal_style)])
        
        # Crear tabla con la información del servicio
        tabla_servicio = Table(servicio_info, colWidths=[3*cm, 12*cm])
        tabla_servicio.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(tabla_servicio)
        elements.append(Spacer(1, 0.3*inch))
        
        # Generar código QR para verificación
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=2,
        )
        
        # Usar solo el código de verificación como contenido del QR
        qr.add_data(verification_code)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        img.save(qr_buffer)
        qr_buffer.seek(0)
        
        # Agregar código QR (sin texto de verificación)
        qr_img = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
        
        # Crear tabla para el código QR (sin texto de verificación)
        qr_table = Table([[qr_img]], colWidths=[15*cm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(qr_table)
        
        # Construir el PDF
        doc.build(elements, onFirstPage=recibo_page_background, onLaterPages=recibo_page_background)
        
        # Retornar el buffer
        buffer.seek(0)
        return buffer
    
    except Exception as e:
        logger.error(f"Error al generar PDF de recibo: {str(e)}")
        raise

def recibo_page_background(canvas, doc):
    """
    Función para agregar el fondo y pie de página para el recibo
    """
    # Agregar un pie de página
    canvas.setFillColor(colors.HexColor('#0e3559'))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.3*inch, "ForgeApp - www.forgeapp.cl")
    canvas.drawString(doc.width - 3*inch, 0.3*inch, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Agregar marca de agua "PAGADO"
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#4EB8D5'))
    canvas.setFont("Helvetica-Bold", 72)
    canvas.translate(doc.width/2, doc.height/2)
    canvas.rotate(45)
    canvas.setFillAlpha(0.1)
    canvas.drawCentredString(0, 0, "PAGADO")
    canvas.restoreState()
