# forgeapp/forms.py
from django import forms
from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['name', 'description', 'url', 'documentation_url', 'git_repository', 'owner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Nombre de la aplicación'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'rows': 6,
                'placeholder': 'Describe la aplicación, sus características principales y objetivos...'
            }),
            'url': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'https://ejemplo.com'}),
            'documentation_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'https://docs.ejemplo.com'}),
            'git_repository': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'https://github.com/usuario/proyecto'}),
            'owner': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
        }
        help_texts = {
            'name': 'Nombre identificativo de la aplicación o proyecto',
            'description': 'Descripción detallada de la aplicación, sus funcionalidades y propósito',
            'url': 'URL principal del proyecto o aplicación en producción',
            'documentation_url': 'URL de la documentación técnica o guía de usuario (opcional)',
            'git_repository': 'URL del repositorio de código fuente en GitHub, GitLab, etc. (opcional)',
            'owner': 'Cliente propietario de esta aplicación (opcional)',
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['rut', 'first_name', 'last_name', 'email', 'phone', 'company', 'company_rut', 'position', 'nationality', 'status', 'notes']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Ej: 12345678-9'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Nombres'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': '+56 9 1234 5678'}),
            'company': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'company_rut': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Ej: 12345678-9'}),
            'position': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'placeholder': 'Ej: Gerente General'}),
            'nationality': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'rows': 4}),
        }
        help_texts = {
            'rut': 'Formato: 12345678-9 (obligatorio)',
            'first_name': 'Nombres del cliente',
            'last_name': 'Apellidos del cliente',
            'email': 'Correo electrónico principal de contacto',
            'phone': 'Número de teléfono con código de país (opcional)',
            'company': 'Nombre de la empresa donde trabaja (opcional)',
            'company_rut': 'RUT de la empresa en formato 12345678-9 (opcional)',
            'position': 'Cargo que ocupa en la empresa (opcional)',
            'nationality': 'Nacionalidad del cliente',
            'status': 'Estado actual del cliente en el sistema',
            'notes': 'Notas adicionales o comentarios sobre el cliente',
        }

    def clean_company_rut(self):
        """Valida el RUT de la empresa solo si se proporciona"""
        company_rut = self.cleaned_data.get('company_rut', '').strip()
        if company_rut:
            # Solo valida si no está vacío
            import re
            if not re.match(r'^\d{7,8}-[\dkK]$', company_rut):
                raise forms.ValidationError('El RUT de la empresa debe tener el formato 12345678-9')
        return company_rut

class SubscriptionForm(forms.ModelForm):
    price = forms.DecimalField(
        label='Precio',
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
            'step': '0.01'
        })
    )

    class Meta:
        model = Subscription
        fields = ['client', 'application', 'status', 'payment_type', 'price',
                 'start_date', 'auto_renewal', 'renewal_notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'application': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'payment_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'}),
            'start_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'type': 'date'}, format='%Y-%m-%d'),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-400'}),
            'renewal_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all', 'rows': 4}),
        }
        help_texts = {
            'client': 'Cliente asociado a esta suscripción',
            'application': 'Aplicación o servicio a suscribir',
            'status': 'Estado actual de la suscripción',
            'payment_type': 'Mensual (vence en 1 mes) o Anual (vence en 1 año) - La fecha de fin se calculará automáticamente',
            'price': 'Precio de la suscripción (debe ser mayor a 0)',
            'start_date': 'Fecha de inicio - La fecha de fin se calculará automáticamente según el tipo de pago',
            'auto_renewal': 'Marcar para habilitar renovación automática al vencimiento',
            'renewal_notes': 'Notas adicionales sobre la renovación (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el campo start_date use el formato correcto para input type="date"
        if self.instance and self.instance.pk and self.instance.start_date:
            self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%d')
        


class CalculadoraForm(forms.ModelForm):
    class Meta:
        model = Calculadora
        fields = ['nombre', 'client', 'application', 'currency', 'margen', 'descuento', 'notas', 'costo_mercado', 'tiempo_mercado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'placeholder': 'Ej: Presupuesto App Móvil - Cliente XYZ'
            }),
            'client': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'
            }),
            'application': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all'
            }),
            'margen': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'rows': 4,
                'placeholder': 'Notas adicionales, observaciones o condiciones especiales...'
            }),
            'costo_mercado': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'tiempo_mercado': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all',
                'step': '0.1',
                'min': '0',
                'placeholder': '0.0'
            }),
        }
        help_texts = {
            'nombre': 'Nombre identificativo para esta calculadora de costos',
            'client': 'Cliente al que se dirige esta cotización',
            'application': 'Aplicación o proyecto asociado a esta cotización (opcional)',
            'currency': 'Moneda en la que se expresarán los valores de la cotización',
            'margen': 'Porcentaje de margen de ganancia que se aplica sobre el subtotal de items',
            'descuento': 'Porcentaje de descuento que se aplica únicamente al pago anual por adelantado',
            'notas': 'Observaciones adicionales, condiciones especiales o comentarios sobre esta cotización',
            'costo_mercado': 'Costo de referencia del mercado para comparación (opcional)',
            'tiempo_mercado': 'Tiempo estimado en meses que tomaría el proyecto según el mercado (opcional)',
        }

class ItemCalculoForm(forms.ModelForm):
    class Meta:
        model = ItemCalculo
        fields = ['descripcion', 'cantidad', 'precio_unitario']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all text-sm',
                'placeholder': 'Descripción del item'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all text-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all text-sm',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
        help_texts = {
            'descripcion': 'Nombre o descripción breve del item',
            'cantidad': 'Cantidad de unidades',
            'precio_unitario': 'Precio por unidad',
        }

class ApplicationConfigForm(forms.ModelForm):
    class Meta:
        model = ApplicationConfig
        fields = ['key', 'value', 'field_type', 'description']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'w-full'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.field_type == 'password' and instance.is_encrypted:
            self.fields['value'].initial = instance.get_value()
