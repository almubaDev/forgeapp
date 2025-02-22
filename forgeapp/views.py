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
from datetime import datetime
import os
import re
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.units import inch

from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig
from .forms import (
    ApplicationForm, ClientForm, SubscriptionForm, 
    CalculadoraForm, ItemCalculoForm, ApplicationConfigForm
)
from .markdown_processor import process_markdown_section

# Landingpage
def landing(request):
    return render(request, 'forgeapp/landing.html')

@csrf_exempt
def contact_form(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = request.POST
        nombre = data.get('name')
        email = data.get('email')
        telefono = data.get('phone', '')
        mensaje = data.get('message')
        
        if not all([nombre, email, mensaje]):
            return JsonResponse({'error': 'Faltan campos requeridos'}, status=400)
        
        # Crear el correo HTML
        html_content = render_to_string('forgeapp/email/contact_email.html', {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'mensaje': mensaje
        })
        
        # Crear el correo
        subject = f'Nuevo contacto desde ForgeApp - {nombre}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = settings.DEFAULT_FROM_EMAIL  # O el email donde quieras recibir los contactos
        
        msg = EmailMultiAlternatives(
            subject,
            mensaje,  # Versión texto plano
            from_email,
            [to_email],
            reply_to=[email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return JsonResponse({'message': 'Mensaje enviado exitosamente'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Dashboard
@login_required
def dashboard(request):
    context = {
        'total_clients': Client.objects.count(),
        'active_subscriptions': Subscription.objects.filter(status='active').count(),
        'total_applications': Application.objects.count(),
        'recent_clients': Client.objects.order_by('-created_at')[:5],
        'recent_subscriptions': Subscription.objects.order_by('-created_at')[:5]
    }
    return render(request, 'forgeapp/dashboard.html', context)

# Application views
@login_required
def application_list(request):
    applications = Application.objects.annotate(
        total_subscriptions=Count('subscription'),
        active_subscriptions=Count('subscription', filter=Q(subscription__status='active'))
    ).order_by('-created_at')
    return render(request, 'forgeapp/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application.objects.annotate(
        total_subscriptions=Count('subscription'),
        active_subscriptions=Count('subscription', filter=Q(subscription__status='active')),
        total_revenue=Sum('subscription__price', filter=Q(subscription__status='active'))
    ), pk=pk)
    
    subscriptions = application.subscription_set.select_related('client').order_by('-created_at')
    
    return render(request, 'forgeapp/application_detail.html', {
        'application': application,
        'subscriptions': subscriptions
    })

@login_required
def application_create(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Aplicación creada exitosamente.')
            return redirect('forgeapp:application_detail', pk=application.pk)
    else:
        initial = {}
        if owner_id := request.GET.get('owner'):
            initial['owner'] = owner_id
        form = ApplicationForm(initial=initial)
    
    return render(request, 'forgeapp/application_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:application_list')
    })

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
    
    return render(request, 'forgeapp/application_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:application_detail', args=[pk])
    })

@login_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if application.subscription_set.filter(status='active').exists():
                    messages.error(request, 'No se puede eliminar una aplicación con suscripciones activas.')
                    return redirect('forgeapp:application_detail', pk=pk)
                application.delete()
                messages.success(request, 'Aplicación eliminada exitosamente.')
                return redirect('forgeapp:application_list')
        except Exception as e:
            messages.error(request, 'Error al eliminar la aplicación.')
    return redirect('forgeapp:application_detail', pk=pk)

# Vistas de configuración de aplicación
@login_required
def application_configs(request, pk):
    application = get_object_or_404(Application, pk=pk)
    configs = application.configs.all().order_by('key')
    return render(request, 'forgeapp/application_configs.html', {
        'application': application,
        'configs': configs
    })

@login_required
def application_config_add(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.application = application
            config.save()
            messages.success(request, 'Configuración creada exitosamente.')
            return redirect('forgeapp:application_configs', pk=pk)
    else:
        form = ApplicationConfigForm()
    
    return render(request, 'forgeapp/application_config_form.html', {
        'form': form,
        'application': application
    })

@login_required
def application_config_edit(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    if request.method == 'POST':
        form = ApplicationConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('forgeapp:application_configs', pk=config.application.pk)
    else:
        form = ApplicationConfigForm(instance=config)
    
    return render(request, 'forgeapp/application_config_form.html', {
        'form': form,
        'application': config.application
    })

@login_required
def application_config_delete(request, config_pk):
    config = get_object_or_404(ApplicationConfig, pk=config_pk)
    application_pk = config.application.pk
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuración eliminada exitosamente.')
    return redirect('forgeapp:application_configs', pk=application_pk)

# Client views
@login_required
def client_list(request):
    clients = Client.objects.annotate(
        total_subscriptions=Count('subscriptions'),
        active_subscriptions=Count('subscriptions', filter=Q(subscriptions__status='active')),
        total_value=Sum('subscriptions__price', filter=Q(subscriptions__status='active'))
    ).order_by('-created_at')
    return render(request, 'forgeapp/client_list.html', {'clients': clients})

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client.objects.annotate(
        total_subscriptions=Count('subscriptions'),
        active_subscriptions=Count('subscriptions', filter=Q(subscriptions__status='active')),
        total_value=Sum('subscriptions__price', filter=Q(subscriptions__status='active'))
    ), pk=pk)
    
    subscriptions = client.subscriptions.select_related('application').order_by('-created_at')
    
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
    
    return render(request, 'forgeapp/client_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:client_list')
    })

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
    
    return render(request, 'forgeapp/client_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:client_detail', args=[pk])
    })

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if client.subscriptions.filter(status='active').exists():
                    messages.error(request, 'No se puede eliminar un cliente con suscripciones activas.')
                    return redirect('forgeapp:client_detail', pk=pk)
                client.delete()
                messages.success(request, 'Cliente eliminado exitosamente.')
                return redirect('forgeapp:client_list')
        except Exception as e:
            messages.error(request, 'Error al eliminar el cliente.')
    return redirect('forgeapp:client_detail', pk=pk)

# Subscription views
@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.select_related('client', 'application').order_by('-created_at')
    return render(request, 'forgeapp/subscription_list.html', {'subscriptions': subscriptions})

@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(
        Subscription.objects.select_related('client', 'application'), 
        pk=pk
    )
    
    return render(request, 'forgeapp/subscription_detail.html', {
        'subscription': subscription
    })

@login_required
def subscription_create(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Suscripción creada exitosamente.')
            return redirect('forgeapp:subscription_detail', pk=subscription.pk)
    else:
        initial = {}
        if client_id := request.GET.get('client'):
            initial['client'] = client_id
        if app_id := request.GET.get('application'):
            initial['application'] = app_id
        form = SubscriptionForm(initial=initial)
    
    return render(request, 'forgeapp/subscription_form.html', {
        'form': form,
        'cancel_url': request.GET.get('next', reverse('forgeapp:subscription_list'))
    })

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
    
    return render(request, 'forgeapp/subscription_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:subscription_detail', args=[pk])
    })

@login_required
def subscription_delete(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                client_id = subscription.client.id
                subscription.delete()
                messages.success(request, 'Suscripción eliminada exitosamente.')
                return redirect('forgeapp:client_detail', pk=client_id)
        except Exception as e:
            messages.error(request, 'Error al eliminar la suscripción.')
    return redirect('forgeapp:subscription_detail', pk=pk)

# Calculadora views
@login_required
def calculadora_list(request):
    calculadoras = Calculadora.objects.select_related('client').prefetch_related('items').order_by('-created_at')
    for calculadora in calculadoras:
        calculadora.recalcular_totales()
    return render(request, 'forgeapp/calculadora_list.html', {
        'calculadoras': calculadoras
    })

@login_required
def calculadora_create(request):
    if request.method == 'POST':
        form = CalculadoraForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                calculadora = form.save()
                # Forzar un recálculo inicial de totales
                calculadora.recalcular_totales()
                calculadora.save()
            messages.success(request, 'Calculadora creada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=calculadora.pk)
    else:
        initial = {}
        if client_id := request.GET.get('client'):
            initial['client'] = client_id
        form = CalculadoraForm(initial=initial)
    
    return render(request, 'forgeapp/calculadora_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:calculadora_list')
    })

@login_required
def calculadora_detail(request, pk):
    calculadora = get_object_or_404(Calculadora.objects.select_related('client'), pk=pk)
    calculadora.recalcular_totales()  # Forzar recálculo de totales
    items = calculadora.items.all()
    
    if request.method == 'POST':
        item_form = ItemCalculoForm(request.POST)
        if item_form.is_valid():
            with transaction.atomic():
                # First save the calculadora to ensure it has a primary key
                calculadora.save()
                # Then create and save the item with the proper association
                item = item_form.save(commit=False)
                item.calculadora = calculadora
                item.save()
                # Recalculate totals after adding the item
                calculadora.recalcular_totales()
                calculadora.save()
            messages.success(request, 'Item agregado exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        item_form = ItemCalculoForm()

    return render(request, 'forgeapp/calculadora_detail.html', {
        'calculadora': calculadora,
        'items': items,
        'item_form': item_form
    })

def add_markdown_content(description, elements, styles):
    """Agrega contenido markdown al PDF con estilos mejorados"""
    
    # Estilos para diferentes niveles de títulos
    title_styles = {
        1: ParagraphStyle(
            'Title1',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=15,
            textColor=colors.HexColor('#64C5E8'),
            fontName='Helvetica-Bold',
            alignment=0  # Alineado a la izquierda
        ),
        2: ParagraphStyle(
            'Title2',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.HexColor('#64C5E8'),
            fontName='Helvetica-Bold',
            alignment=0,
            leftIndent=20
        ),
        3: ParagraphStyle(
            'Title3',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=10,
            textColor=colors.HexColor('#64C5E8'),
            fontName='Helvetica-Bold',
            alignment=0,
            leftIndent=40
        ),
        4: ParagraphStyle(
            'Title4',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.HexColor('#64C5E8'),
            fontName='Helvetica-Bold',
            alignment=0,
            leftIndent=60
        )
    }
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=20,
        rightIndent=20
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=11,
        leftIndent=40,
        rightIndent=20,
        spaceBefore=2,
        spaceAfter=2,
        leading=14,
        bulletIndent=20
    )
    
    sections = process_markdown_section(description)
    
    for section_type, content in sections:
        if section_type == 'title':
            level = content['level']
            text = content['text']
            style = title_styles.get(level, title_styles[1])  # Default to level 1 if not found
            
            elements.append(Spacer(1, style.spaceBefore))
            elements.append(Paragraph(
                f'<para><b>{text}</b></para>',
                style
            ))
            elements.append(Spacer(1, style.spaceAfter))
            
        elif section_type == 'list':
            for item in content:
                elements.append(Paragraph(
                    f'<para>• {item}</para>',
                    bullet_style
                ))
                
        else:  # content
            elements.append(Paragraph(
                f'<para>{content}</para>',
                content_style
            ))

@login_required
def calculadora_pdf(request, pk):
    calculadora = get_object_or_404(Calculadora.objects.select_related('client', 'application'), pk=pk)
    calculadora.recalcular_totales()
    items = calculadora.items.all()
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="propuesta_{calculadora.nombre}.pdf"'
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos base
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        textColor=colors.HexColor('#64C5E8'),
        spaceAfter=30,
    )
    
    styles['Normal'].textColor = colors.white
    styles['Heading2'].textColor = colors.HexColor('#41A3CD')
    
    # Logo y URL
    logo_path = os.path.join('static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path)
        img.drawHeight = 1*inch
        img.drawWidth = 2*inch
        elements.append(img)
        elements.append(Spacer(1, 10))
        
        # URL centrada
        url_style = ParagraphStyle(
            'URL',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64C5E8'),
            alignment=1  # Centrado
        )
        elements.append(Paragraph(
            '<para><link href="http://www.forgeapp.net">www.forgeapp.net</link></para>',
            url_style
        ))
        elements.append(Spacer(1, 20))
    
    # Título
    elements.append(Paragraph("Propuesta de Costo por servicios ForgeApp", title_style))
    
    # Información del cliente y aplicación
    elements.append(Paragraph(f"Cliente: {calculadora.client.name}", styles['Normal']))
    if calculadora.application:
        elements.append(Paragraph(f"Aplicación: {calculadora.application.name}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Tabla de items
    data = [['Descripción', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    for item in items:
        data.append([
            item.descripcion,
            str(item.cantidad),
            f"${item.precio_unitario:,.0f}".replace(",", "."),
            f"${item.subtotal:,.0f}".replace(",", ".")
        ])
    
    # Logística de desarrollo
    logistica = calculadora.subtotal * calculadora.margen / 100
    data.append([
        "Logística de desarrollo",
        "1",
        f"${logistica:,.0f}".replace(",", "."),
        f"${logistica:,.0f}".replace(",", ".")
    ])
    
    table = Table(data, colWidths=[250, 70, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B5C8E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#41A3CD')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Formas de pago
    elements.append(Paragraph("Formas de Pago", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    # Estilo común para las opciones de pago
    pago_style = ParagraphStyle(
        'PagoStyle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=15,
        borderColor=colors.HexColor('#41A3CD'),
        borderWidth=1,
        borderPadding=15,
        borderRadius=8,
        leftIndent=20,
        rightIndent=20,
        leading=16,
        alignment=1
    )
    
    # Pago mensual
    elements.append(Paragraph(
        f'''
        <para alignment="center">
            <font size="14" color="#64C5E8"><b>Opción 1: Pago Mensual</b></font><br/><br/>
            <font size="14" color="white">12 Cuotas de:</font><br/>
            <font size="18" color="white"><b>${f"{calculadora.cuota_mensual:,.0f}".replace(",", ".")}</b></font><br/><br/>
            <font size="14" color="white">Total: ${f"{calculadora.cuota_mensual * 12:,.0f}".replace(",", ".")}</font>
        </para>
        ''',
        pago_style
    ))
    elements.append(Spacer(1, 20))

    # Pago anual
    descuento_text = f" ({calculadora.descuento}% descuento)" if calculadora.descuento > 0 else ""
    elements.append(Paragraph(
        f'''
        <para alignment="center">
            <font size="14" color="#64C5E8"><b>Opción 2: Pago Anual Anticipado{descuento_text}</b></font><br/><br/>
            <font size="18" color="white"><b>${f"{calculadora.total_anual:,.0f}".replace(",", ".")}</b></font>
        </para>
        ''',
        pago_style
    ))
    elements.append(Spacer(1, 20))
    
    # Descripción de la aplicación
    if calculadora.application and calculadora.application.description:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Descripción de la Aplicación", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Procesar el markdown de la descripción
        add_markdown_content(calculadora.application.description, elements, styles)
        
        # Forzar nueva página para la comparación con el mercado
        elements.append(PageBreak())
        
        # Comparación con el mercado
        if calculadora.costo_mercado or calculadora.tiempo_mercado:
            elements.append(Paragraph("Comparación con el Mercado", styles['Heading2']))
            elements.append(Spacer(1, 15))
            
            comparison_style = ParagraphStyle(
                'ComparisonStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=10,
                spaceBefore=10,
                borderColor=colors.HexColor('#41A3CD'),
                borderWidth=1,
                borderPadding=15,
                borderRadius=8,
                leftIndent=20,
                rightIndent=20,
                leading=16
            )

            # Ahorro en costos
            if calculadora.costo_mercado:
                ahorro_dinero = calculadora.costo_mercado - calculadora.total_anual
                ahorro_porcentaje = (ahorro_dinero / calculadora.costo_mercado) * 100
                
                elements.append(Paragraph(
                    f'''
                    <para>
                        <font color="#64C5E8" size="13"><b>Ahorro en Costos</b></font><br/>
                        <font color="white" size="12">Costo promedio en el mercado: </font>
                        <font color="white" size="12"><b>${f"{calculadora.costo_mercado:,.0f}".replace(",", ".")}</b></font><br/>
                        <font color="white" size="12">Nuestro costo: </font>
                        <font color="white" size="12"><b>${f"{calculadora.total_anual:,.0f}".replace(",", ".")}</b></font><br/><br/>
                        <font color="#64C5E8" size="14"><b>Ahorro Total:</b></font><br/>
                        <font color="#64C5E8" size="14"><b>${f"{ahorro_dinero:,.0f}".replace(",", ".")} ({ahorro_porcentaje:.1f}%)</b></font>
                    </para>
                    ''',
                    comparison_style
                ))
                elements.append(Spacer(1, 15))

            # Ahorro en tiempo
            if calculadora.tiempo_mercado:
                tiempo_nuestro = 3  # Fijo en 3 semanas
                ahorro_tiempo = calculadora.tiempo_mercado - tiempo_nuestro
                ahorro_tiempo_porcentaje = (ahorro_tiempo / calculadora.tiempo_mercado) * 100
                
                elements.append(Paragraph(
                    f'''
                    <para>
                        <font color="#64C5E8" size="13"><b>Ahorro en Tiempo</b></font><br/>
                        <font color="white" size="12">Tiempo promedio en el mercado: </font>
                        <font color="white" size="12"><b>{f"{calculadora.tiempo_mercado:,.1f}".replace(",", ".")} semanas</b></font><br/>
                        <font color="white" size="12">Nuestro tiempo de entrega: </font>
                        <font color="white" size="12"><b>{tiempo_nuestro} semanas</b></font><br/><br/>
                        <font color="#64C5E8" size="14"><b>Ahorro de Tiempo:</b></font><br/>
                        <font color="#64C5E8" size="14"><b>{f"{ahorro_tiempo:,.1f}".replace(",", ".")} semanas ({ahorro_tiempo_porcentaje:.1f}%)</b></font>
                    </para>
                    ''',
                    comparison_style
                ))
            
            elements.append(Spacer(1, 30))
    
    # Canvas personalizado para el fondo
    def myFirstPage(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#1B3A5D'))
        canvas.rect(0, 0, letter[0], letter[1], fill=True)
        canvas.restoreState()
    
    # Generar PDF
    doc.build(elements, onFirstPage=myFirstPage, onLaterPages=myFirstPage)
    
    return response

@login_required
def calculadora_update(request, pk):
    calculadora = get_object_or_404(Calculadora.objects.select_related('client'), pk=pk)
    if request.method == 'POST':
        form = CalculadoraForm(request.POST, instance=calculadora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calculadora actualizada exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
    else:
        form = CalculadoraForm(instance=calculadora)
    
    return render(request, 'forgeapp/calculadora_form.html', {
        'form': form,
        'cancel_url': reverse('forgeapp:calculadora_detail', args=[pk])
    })

@login_required
def calculadora_delete(request, pk):
    calculadora = get_object_or_404(Calculadora.objects.select_related('client'), pk=pk)
    if request.method == 'POST':
        client_id = calculadora.client.id
        calculadora.delete()
        messages.success(request, 'Calculadora eliminada exitosamente.')
        return redirect('forgeapp:client_detail', pk=client_id)
    return redirect('forgeapp:calculadora_detail', pk=pk)

@login_required
def item_delete(request, pk):
    item = get_object_or_404(ItemCalculo, pk=pk)
    calculadora_id = item.calculadora.id
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item eliminado exitosamente.')
    return redirect('forgeapp:calculadora_detail', pk=calculadora_id)

@login_required
def subscription_activate(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.status = 'active'
        subscription.save()
        messages.success(request, 'Suscripción activada exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_suspend(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.status = 'suspended'
        subscription.save()
        messages.success(request, 'Suscripción suspendida exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def subscription_cancel(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.save()
        messages.success(request, 'Suscripción cancelada exitosamente.')
    return redirect('forgeapp:subscription_detail', pk=pk)

@login_required
def generar_suscripciones(request, pk):
    calculadora = get_object_or_404(Calculadora, pk=pk)
    
    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.POST['start_date'], '%Y-%m-%d').date()
            auto_renewal = request.POST.get('auto_renewal') == 'on'
            
            # Generar suscripciones
            calculadora.generar_suscripciones(start_date, auto_renewal)
            
            messages.success(request, 'Suscripciones generadas exitosamente.')
            return redirect('forgeapp:calculadora_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Error al generar suscripciones: {str(e)}')
            
    return redirect('forgeapp:calculadora_detail', pk=pk)
