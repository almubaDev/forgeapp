from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os

def generar_pdf_simple(request):
    # Configurar el buffer y el documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
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
    
    # Título principal
    title = Paragraph("Propuesta de Costo por servicios ForgeApp", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de costos - Desglose de items
    data = [
        ["Descripción", "Cantidad", "Precio Unit.", "Subtotal"],
        ["Servidor mensual", "12.00", "$12.000", "$144.000"],
        ["Herramienta de desarrollo rápido", "1.00", "$217.777", "$217.777"],
        ["Logística de desarrollo", "1", "$0", "$0"]
    ]
    
    tabla_costos = Table(data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm])
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
    ]))
    
    elements.append(tabla_costos)
    elements.append(Spacer(1, 0.5*inch))
    
    # Construir el PDF
    doc.build(elements)
    
    # Obtener el valor del PDF del buffer y limpiarlo
    pdf_value = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta HTTP con PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="propuesta_simple.pdf"'
    response.write(pdf_value)
    return response
