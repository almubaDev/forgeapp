# forgeapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from datetime import datetime
import logging
import os
import re
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig
from .forms import (
    ApplicationForm, ClientForm, SubscriptionForm, 
    CalculadoraForm, ItemCalculoForm, ApplicationConfigForm
)
from .markdown_processor import process_markdown_section

logger = logging.getLogger('forgeapp')

# Application views
@login_required
def application_list(request):
    applications = Application.objects.all()
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'forgeapp/application_detail.html', {'application': application})

@login_required
def application_create(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Aplicación creada exitosamente.')
            return redirect('forgeapp:application_detail', pk=application.pk)
    else:
        form = ApplicationForm()
    return render(request, 'forgeapp/application_form.html', {'form': form, 'is_create': True})

@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada exitosamente.')
            return redirect('forgeapp:application_detail', pk=pk)
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'forgeapp/application_form.html', {'form': form, 'application': application, 'is_create': False})

@login_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Aplicación eliminada exitosamente.')
        return redirect('forgeapp:application_list')
    return render(request, 'forgeapp/application_confirm_delete.html', {'application': application})

@login_required
def application_configs(request, pk):
    application = get_object_or_404(Application, pk=pk)
    configs = application.configs.all()
    return render(request, 'forgeapp/application_configs.html', {'application': application, 'configs': configs})

@login_required
def application_config_add(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.application = application
            config.save()
            messages.success(request, 'Configuración agregada exitosamente.')
            return redirect('forgeapp:application_configs', pk=pk)
    else:
        form = ApplicationConfigForm()
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application})

@login_required
def application_config_edit(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('forgeapp:application_configs', pk=application.pk)
    else:
        form = ApplicationConfigForm(instance=config)
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application, 'config': config})

@login_required
def application_config_delete(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuración eliminada exitosamente.')
        return redirect('forgeapp:application_configs', pk=application.pk)
    return render(request, 'forgeapp/application_config_confirm_delete.html', {'config': config, 'application': application})

# Client views
@login_required
def client_list(request):
    clients = Client.objects.all()
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Obtener las suscripciones del cliente
    subscriptions = client.subscriptions.all()
    
    # Calcular valores para el resumen
    client.active_subscriptions = subscriptions.filter(status='active').count()
    client.total_subscriptions = subscriptions.count()
    client.total_value = subscriptions.filter(status='active').aggregate(Sum('price'))['price__sum'] or 0
    
    return render(request, 'forgeapp/client_detail.html', {
        'client': client,
        'subscriptions': subscriptions
    })

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('forgeapp:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'forgeapp/client_form.html', {'form': form, 'is_create': True})

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('forgeapp:client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'forgeapp/client_form.html', {'form': form, 'client': client, 'is_create': False})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('forgeapp:client_list')
    return render(request, 'forgeapp/client_confirm_delete.html', {'client': client})

# Subscription views
@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.all()
    return render(request, 'forgeapp/subscription_list.html', {'subscriptions': subscriptions})

@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    return render(request, 'forgeapp/subscription_detail.html', {'subscription': subscription})

@login_required
def subscription_create(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Suscripción creada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionForm()
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'is_create': True})

@login_required
def subscription_update(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suscripción actualizada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=pk)
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'subscription': subscription, 'is_create': False})

@login_required
def subscription_delete(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Suscripción eliminada exitosamente.')
        return redirect('forgeapp:subscription_list')
    return render(request, 'forgeapp/subscription_confirm_delete.html', {'subscription': subscription})

# Calculadora views
@login_required
def calculadora_list(request):
    calculadoras = Calculadora.objects.all()
    return render(request, 'forgeapp/calculadora_list.html', {'calculadoras': calculadoras})

@login_required
def calculadora_detail(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    items = calculadora.items.all()
    
    if request.method == 'POST':
        item_form = ItemCalculoForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.calculadora = calculadora
            item.save()
            messages.success(request, 'Item agregado exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        item_form = ItemCalculoForm()
    
    return render(request, 'forgeapp/calculadora_detail.html', {
        'calculadora': calculadora,
        'items': items,
        'item_form': item_form
    })

@login_required
def calculadora_create(request):
    if request.method == 'POST':
        form = CalculadoraForm(request.POST)
        if form.is_valid():
            calculadora = form.save()
            messages.success(request, 'Calculadora creada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=calculadora.pk)
    else:
        form = CalculadoraForm()
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'is_create': True})

@login_required
def calculadora_update(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        form = CalculadoraForm(request.POST, instance=calculadora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calculadora actualizada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        form = CalculadoraForm(instance=calculadora)
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'calculadora': calculadora, 'is_create': False})

@login_required
def calculadora_delete(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        calculadora.delete()
        messages.success(request, 'Calculadora eliminada exitosamente.')
        return redirect('forgeapp:calculadora_list')
    return render(request, 'forgeapp/calculadora_confirm_delete.html', {'calculadora': calculadora})

@login_required
def calculadora_pdf(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    # Configurar el buffer y el documento
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="propuesta_{calculadora.client.name}_{calculadora.pk}.pdf"'
    
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
    
    # Crear el documento
    doc = SimpleDocTemplate(response, pagesize=letter)
    
    # Iniciar lista de elementos
    elements = []
    
    # Agregar logotipo
    logo_path = os.path.join('static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=1*inch)
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
        Paragraph(f"Cliente: {calculadora.client.name}", normal_style),
    ]
    
    # Agregar aplicación si existe
    if hasattr(calculadora, 'application') and calculadora.application:
        cliente_info.append(Paragraph(f"Aplicación: {calculadora.application.name}", normal_style))
    
    for info in cliente_info:
        elements.append(info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de costos - Desglose de items
    data = [
        ["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]
    ]
    
    # Agregar items de la calculadora
    for item in calculadora.items.all():
        data.append([
            item.descripcion,
            f"{item.cantidad:.2f}".rstrip('0').rstrip('.') if item.cantidad == int(item.cantidad) else f"{item.cantidad:.2f}",
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])
    
    # Agregar fila para "Logística de desarrollo" si hay margen
    if calculadora.margen > 0:
        logistica_valor = calculadora.subtotal * (calculadora.margen / 100)
        data.append([
            "Logística de desarrollo",
            "1",
            f"{calculadora.margen}%",
            f"${logistica_valor:,.0f}"
        ])
    
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
        [Paragraph(f"${calculadora.cuota_mensual:,.0f}", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))],
        [Paragraph(f"Total: ${calculadora.cuota_mensual * 12:,.0f}", normal_style)]
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
    descuento_texto = f"({calculadora.descuento}% descuento)" if calculadora.descuento > 0 else ""
    data_opcion2 = [
        [Paragraph(f"Opción 2: Pago Anual Anticipado {descuento_texto}", ParagraphStyle('OpcionStyle', parent=normal_style, alignment=TA_CENTER, fontSize=16, textColor=turquoise_color))],
        [Paragraph(f"${calculadora.total_anual:,.0f}", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))]
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
        from .markdown_processor import process_markdown_section
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
# forgeapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Count, Sum, Q
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from datetime import datetime
import logging
import os
import re
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig
from .forms import (
    ApplicationForm, ClientForm, SubscriptionForm, 
    CalculadoraForm, ItemCalculoForm, ApplicationConfigForm
)
from .markdown_processor import process_markdown_section

logger = logging.getLogger('forgeapp')

# Application views
@login_required
def application_list(request):
    applications = Application.objects.all()
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    return render(request, 'forgeapp/application_detail.html', {'application': application})

@login_required
def application_create(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Aplicación creada exitosamente.')
            return redirect('forgeapp:application_detail', pk=application.pk)
    else:
        form = ApplicationForm()
    return render(request, 'forgeapp/application_form.html', {'form': form, 'is_create': True})

@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada exitosamente.')
            return redirect('forgeapp:application_detail', pk=pk)
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'forgeapp/application_form.html', {'form': form, 'application': application, 'is_create': False})

@login_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Aplicación eliminada exitosamente.')
        return redirect('forgeapp:application_list')
    return render(request, 'forgeapp/application_confirm_delete.html', {'application': application})

@login_required
def application_configs(request, pk):
    application = get_object_or_404(Application, pk=pk)
    configs = application.configs.all()
    return render(request, 'forgeapp/application_configs.html', {'application': application, 'configs': configs})

@login_required
def application_config_add(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.application = application
            config.save()
            messages.success(request, 'Configuración agregada exitosamente.')
            return redirect('forgeapp:application_configs', pk=pk)
    else:
        form = ApplicationConfigForm()
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application})

@login_required
def application_config_edit(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('forgeapp:application_configs', pk=application.pk)
    else:
        form = ApplicationConfigForm(instance=config)
    return render(request, 'forgeapp/application_config_form.html', {'form': form, 'application': application, 'config': config})

@login_required
def application_config_delete(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application = config.application
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuración eliminada exitosamente.')
        return redirect('forgeapp:application_configs', pk=application.pk)
    return render(request, 'forgeapp/application_config_confirm_delete.html', {'config': config, 'application': application})

# Client views
@login_required
def client_list(request):
    clients = Client.objects.all()
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    # Obtener las suscripciones del cliente
    subscriptions = client.subscriptions.all()
    
    # Calcular valores para el resumen
    client.active_subscriptions = subscriptions.filter(status='active').count()
    client.total_subscriptions = subscriptions.count()
    client.total_value = subscriptions.filter(status='active').aggregate(Sum('price'))['price__sum'] or 0
    
    return render(request, 'forgeapp/client_detail.html', {
        'client': client,
        'subscriptions': subscriptions
    })

@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, 'Cliente creado exitosamente.')
            return redirect('forgeapp:client_detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'forgeapp/client_form.html', {'form': form, 'is_create': True})

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('forgeapp:client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'forgeapp/client_form.html', {'form': form, 'client': client, 'is_create': False})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect('forgeapp:client_list')
    return render(request, 'forgeapp/client_confirm_delete.html', {'client': client})

# Subscription views
@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.all()
    return render(request, 'forgeapp/subscription_list.html', {'subscriptions': subscriptions})

@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    return render(request, 'forgeapp/subscription_detail.html', {'subscription': subscription})

@login_required
def subscription_create(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Suscripción creada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionForm()
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'is_create': True})

@login_required
def subscription_update(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suscripción actualizada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=pk)
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'forgeapp/subscription_form.html', {'form': form, 'subscription': subscription, 'is_create': False})

@login_required
def subscription_delete(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Suscripción eliminada exitosamente.')
        return redirect('forgeapp:subscription_list')
    return render(request, 'forgeapp/subscription_confirm_delete.html', {'subscription': subscription})

# Calculadora views
@login_required
def calculadora_list(request):
    calculadoras = Calculadora.objects.all()
    return render(request, 'forgeapp/calculadora_list.html', {'calculadoras': calculadoras})

@login_required
def calculadora_detail(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    items = calculadora.items.all()
    
    if request.method == 'POST':
        item_form = ItemCalculoForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.calculadora = calculadora
            item.save()
            messages.success(request, 'Item agregado exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        item_form = ItemCalculoForm()
    
    return render(request, 'forgeapp/calculadora_detail.html', {
        'calculadora': calculadora,
        'items': items,
        'item_form': item_form
    })

@login_required
def calculadora_create(request):
    if request.method == 'POST':
        form = CalculadoraForm(request.POST)
        if form.is_valid():
            calculadora = form.save()
            messages.success(request, 'Calculadora creada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=calculadora.pk)
    else:
        form = CalculadoraForm()
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'is_create': True})

@login_required
def calculadora_update(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        form = CalculadoraForm(request.POST, instance=calculadora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calculadora actualizada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        form = CalculadoraForm(instance=calculadora)
    return render(request, 'forgeapp/calculadora_form.html', {'form': form, 'calculadora': calculadora, 'is_create': False})

@login_required
def calculadora_delete(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    if request.method == 'POST':
        calculadora.delete()
        messages.success(request, 'Calculadora eliminada exitosamente.')
        return redirect('forgeapp:calculadora_list')
    return render(request, 'forgeapp/calculadora_confirm_delete.html', {'calculadora': calculadora})

@login_required
def calculadora_pdf(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    # Configurar el buffer y el documento
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="propuesta_{calculadora.client.name}_{calculadora.pk}.pdf"'
    
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
    
    # Crear el documento
    doc = SimpleDocTemplate(response, pagesize=letter)
    
    # Iniciar lista de elementos
    elements = []
    
    # Agregar logotipo
    logo_path = os.path.join('static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=1*inch)
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
        data.append([
            item.descripcion,
            f"{item.cantidad:.2f}".rstrip('0').rstrip('.') if item.cantidad == int(item.cantidad) else f"{item.cantidad:.2f}",
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])
    
    # Agregar fila para "Logística de desarrollo" si hay margen
    if calculadora.margen > 0:
        logistica_valor = calculadora.subtotal * (calculadora.margen / 100)
        data.append([
            "Logística de desarrollo",
            "1",
            f"{calculadora.margen}%",
            f"${logistica_valor:,.0f}"
        ])
    
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
        [Paragraph(f"${calculadora.cuota_mensual:,.0f}", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))],
        [Paragraph(f"Total: ${calculadora.cuota_mensual * 12:,.0f}", normal_style)]
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
    descuento_texto = f"({calculadora.descuento}% descuento)" if calculadora.descuento > 0 else ""
    data_opcion2 = [
        [Paragraph(f"Opción 2: Pago Anual Anticipado {descuento_texto}", ParagraphStyle('OpcionStyle', parent=normal_style, alignment=TA_CENTER, fontSize=16, textColor=turquoise_color))],
        [Paragraph(f"${calculadora.total_anual:,.0f}", ParagraphStyle('PrecioStyle', parent=normal_style, fontSize=22, alignment=TA_CENTER))]
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
        from .markdown_processor import process_markdown_section
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
                
    # Agregar página de comparación con el mercado
    elements.append(PageBreak())
    
    # Comparación con el mercado
    if calculadora.costo_mercado or calculadora.tiempo_mercado:
        elements.append(Paragraph("Comparación con el Mercado", subtitle_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Comparación de costos
        if calculadora.costo_mercado:
            ahorro = calculadora.costo_mercado - calculadora.total_anual
            if ahorro > 0:
                porcentaje_ahorro = (ahorro / calculadora.costo_mercado) * 100
                
                cost_data = [
                    [Paragraph("<b>Ahorro en Costos</b>", ParagraphStyle(
                        'ComparisonTitle',
                        parent=normal_style,
                        alignment=TA_CENTER,
                        textColor=turquoise_color,
                        fontSize=14
                    ))],
                    [Paragraph(f"Costo promedio en el mercado: ${calculadora.costo_mercado:,.0f}", normal_style)],
                    [Paragraph(f"Nuestro costo: ${calculadora.total_anual:,.0f}", normal_style)],
                    [Spacer(1, 0.1*inch)],
                    [Paragraph("<b>Ahorro Total:</b>", ParagraphStyle(
                        'AhorroTotalStyle',
                        parent=normal_style,
                        fontSize=16,
                        textColor=turquoise_color
                    ))],
                    [Paragraph(f"${ahorro:,.0f} ({porcentaje_ahorro:.1f}%)", ParagraphStyle(
                        'AhorroTotalStyle',
                        parent=normal_style,
                        fontSize=16,
                        textColor=turquoise_color
                    ))]
                ]
                
                cost_table = Table(cost_data, colWidths=[12*cm])
                cost_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0a2845')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (0, -1), 8),
                    ('TOPPADDING', (0, 0), (0, -1), 8),
                    ('LEFTPADDING', (0, 0), (0, -1), 15),
                    ('RIGHTPADDING', (0, 0), (0, -1), 15),
                    ('ROUNDED', (0, 0), (0, -1), 10),
                    ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#0a2845'), radius=10),
                ]))
                
                elements.append(cost_table)
                elements.append(Spacer(1, 0.3*inch))
        
        # Comparación de tiempo
        if calculadora.tiempo_mercado:
            tiempo_forgeapp = 3  # Tiempo de entrega en semanas
            ahorro_tiempo = calculadora.tiempo_mercado - tiempo_forgeapp
            if ahorro_tiempo > 0:
                porcentaje_ahorro_tiempo = (ahorro_tiempo / calculadora.tiempo_mercado) * 100
                
                time_data = [
                    [Paragraph("<b>Ahorro en Tiempo</b>", ParagraphStyle(
                        'ComparacionStyle',
                        parent=normal_style,
                        fontSize=16,
                        textColor=turquoise_color
                    ))],
                    [Paragraph(f"Tiempo promedio en el mercado: {calculadora.tiempo_mercado} semanas", normal_style)],
                    [Paragraph(f"Nuestro tiempo de entrega: {tiempo_forgeapp} semanas", normal_style)],
                    [Spacer(1, 0.1*inch)],
                    [Paragraph("<b>Ahorro de Tiempo:</b>", ParagraphStyle(
                        'AhorroTotalStyle',
                        parent=normal_style,
                        fontSize=16,
                        textColor=turquoise_color
                    ))],
                    [Paragraph(f"{ahorro_tiempo} semanas ({porcentaje_ahorro_tiempo:.1f}%)", ParagraphStyle(
                        'AhorroTotalStyle',
                        parent=normal_style,
                        fontSize=16,
                        textColor=turquoise_color
                    ))]
                ]
                
                time_table = Table(time_data, colWidths=[12*cm])
                time_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#0a2845')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (0, -1), 8),
                    ('TOPPADDING', (0, 0), (0, -1), 8),
                    ('LEFTPADDING', (0, 0), (0, -1), 15),
                    ('RIGHTPADDING', (0, 0), (0, -1), 15),
                    ('ROUNDED', (0, 0), (0, -1), 10),
                    ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#0a2845'), radius=10),
                ]))
                
                elements.append(time_table)
    
    # Construir el PDF
    doc.build(elements, onFirstPage=page_background, onLaterPages=page_background)
    
    # Devolver la respuesta HTTP con el PDF
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
