from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os

def generar_pdf_propuesta(request):
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
    
    # Estilo para información destacada
    destacado_style = ParagraphStyle(
        'DestacadoStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    # Iniciar lista de elementos
    elements = []
    
    # Agregar logotipo
    # Reemplazar 'ruta_a_logo' con la ruta actual de tu logo
    logo = Image('static/img/logo.png', width=2*inch, height=2*inch)
    elements.append(logo)
    elements.append(Spacer(1, 0.5*inch))
    
    # URL del sitio
    url = Paragraph("www.forgeapp.net", ParagraphStyle(
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
    title = Paragraph("Propuesta de Costo por servicios ForgeApp", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información del cliente
    cliente_info = [
        Paragraph("Cliente: Tamara Nicole Muñoz Badillo", normal_style),
        Paragraph("Aplicación: Manager Consultora Badillo", normal_style)
    ]
    for info in cliente_info:
        elements.append(info)
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
    
    # Sección de formas de pago
    formas_pago = Paragraph("Formas de Pago", subtitle_style)
    elements.append(formas_pago)
    elements.append(Spacer(1, 0.2*inch))
    
    # Opción 1: Pago Mensual
    data_opcion1 = [
        [Paragraph("Opción 1: Pago Mensual", ParagraphStyle('OpcionStyle', parent=normal_style, alignment=TA_CENTER, fontSize=16, textColor=turquoise_color))],
        [Paragraph("12 Cuotas de:", normal_style)],
        [Paragraph("$30.149", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))],
        [Paragraph("Total: $361.788", normal_style)]
    ]
    
    tabla_opcion1 = Table(data_opcion1, colWidths=[12*cm])
    tabla_opcion1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0a2845')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (0, -1), 8),
        ('TOPPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 15),
        ('RIGHTPADDING', (0, 0), (0, -1), 15),
        ('ROUNDED', (0, 0), (0, -1), 10),
        ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#0a2845'), radius=10),
    ]))
    
    elements.append(tabla_opcion1)
    elements.append(Spacer(1, 0.3*inch))
    
    # Opción 2: Pago Anual
    descuento_texto = "(16.67% descuento)"
    data_opcion2 = [
        [Paragraph("Opción 2: Pago Anual Anticipado " + descuento_texto, ParagraphStyle('OpcionStyle', parent=normal_style, alignment=TA_CENTER, fontSize=16, textColor=turquoise_color))],
        [Paragraph("$301.469", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))]
    ]
    
    tabla_opcion2 = Table(data_opcion2, colWidths=[12*cm])
    tabla_opcion2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0a2845')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (0, -1), 8),
        ('TOPPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING', (0, 0), (0, -1), 15),
        ('RIGHTPADDING', (0, 0), (0, -1), 15),
        ('ROUNDED', (0, 0), (0, -1), 10),
        ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#0a2845'), radius=10),
    ]))
    
    elements.append(tabla_opcion2)
    elements.append(Spacer(1, 0.5*inch))
    
    # Descripción de la aplicación
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
    
    # Generar las funcionalidades página 2
    # Gestión de Clientes
    gestion_clientes = Paragraph("Gestión de Clientes", ParagraphStyle(
        'SeccionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=turquoise_color,
        alignment=TA_LEFT,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    elements.append(gestion_clientes)
    elements.append(Spacer(1, 0.1*inch))
    
    features_clientes = Paragraph("- Registro completo de información de clientes - Almacenamiento seguro de credenciales y documentos - Sistema de seguimiento de interacciones - Asignación de responsables - Categorización de clientes", normal_style)
    elements.append(features_clientes)
    elements.append(Spacer(1, 0.2*inch))
    
    # Sistema de Calendario
    calendario = Paragraph("Sistema de Calendario", ParagraphStyle(
        'SeccionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=turquoise_color,
        alignment=TA_LEFT,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    elements.append(calendario)
    elements.append(Spacer(1, 0.1*inch))
    
    features_calendario = Paragraph("- Gestión de eventos y citas - Sistema de recordatorios automáticos - Manejo de participantes - Priorización de eventos - Vista de calendario compartido", normal_style)
    elements.append(features_calendario)
    elements.append(Spacer(1, 0.2*inch))
    
    # Gestión de Tareas
    tareas = Paragraph("Gestión de Tareas", ParagraphStyle(
        'SeccionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=turquoise_color,
        alignment=TA_LEFT,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    elements.append(tareas)
    elements.append(Spacer(1, 0.1*inch))
    
    features_tareas = Paragraph("- Creación y seguimiento de tareas - Sistema de notas y comentarios - Menciones y notificaciones - Estados y prioridades - Historial de cambios", normal_style)
    elements.append(features_tareas)
    
    # Construir el PDF
    doc.build(elements, onFirstPage=page_background, onLaterPages=page_background)
    
    # Obtener el valor del PDF del buffer y limpiarlo
    pdf_value = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta HTTP con PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="propuesta_forgeapp.pdf"'
    response.write(pdf_value)
    return response

# Función para agregar el fondo azul a todas las páginas
def page_background(canvas, doc):
    # Color de fondo azul
    canvas.setFillColor(colors.HexColor('#0e3559'))
    canvas.rect(0, 0, doc.width + 2*doc.leftMargin, doc.height + 2*doc.bottomMargin, fill=1)
    
    # Agregar un pie de página o elementos adicionales si se desea
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.5*inch, "ForgeApp - www.forgeapp.net")
