# forgeapp/forms.py
from django import forms
from .models import Application, Client, Subscription, Calculadora, ItemCalculo, ApplicationConfig

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['name', 'description', 'url', 'documentation_url', 'git_repository', 'owner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'description': forms.Textarea(attrs={
                'class': 'win98-input w-full',
                'rows': 10,
                'style': 'white-space: pre-wrap;',
                'placeholder': 'Ingrese la descripción...\nUse saltos de línea para formatear el texto'
            }),
            'url': forms.URLInput(attrs={'class': 'win98-input w-full'}),
            'documentation_url': forms.URLInput(attrs={'class': 'win98-input w-full'}),
            'git_repository': forms.URLInput(attrs={'class': 'win98-input w-full'}),
            'owner': forms.Select(attrs={'class': 'win98-input w-full'}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['rut', 'name', 'email', 'phone', 'company', 'company_rut', 'position', 'nationality', 'status', 'notes']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'win98-input w-full', 'placeholder': 'Ej: 16819925-2'}),
            'name': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'email': forms.EmailInput(attrs={'class': 'win98-input w-full'}),
            'phone': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'company': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'company_rut': forms.TextInput(attrs={'class': 'win98-input w-full', 'placeholder': 'Ej: 16819925-2'}),
            'position': forms.TextInput(attrs={'class': 'win98-input w-full', 'placeholder': 'Ej: Gerente General'}),
            'nationality': forms.Select(attrs={'class': 'win98-input w-full'}),
            'status': forms.Select(attrs={'class': 'win98-input w-full'}),
            'notes': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 4}),
        }

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['client', 'application', 'status', 'payment_type', 'price', 
                 'start_date', 'end_date', 'auto_renewal', 'renewal_notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'win98-input w-full'}),
            'application': forms.Select(attrs={'class': 'win98-input w-full'}),
            'status': forms.Select(attrs={'class': 'win98-input w-full'}),
            'payment_type': forms.Select(attrs={'class': 'win98-input w-full'}),
            'price': forms.NumberInput(attrs={'class': 'win98-input w-full'}),
            'start_date': forms.DateInput(attrs={'class': 'win98-input w-full', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'win98-input w-full', 'type': 'date'}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'win98-input'}),
            'renewal_notes': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 4}),
        }
        help_texts = {
            'payment_type': 'Tipo de pago (mensual o anual)',
            'auto_renewal': 'Habilitar renovación automática al vencimiento',
        }
        


# forgeapp/forms.py (modificar el CalculadoraForm)
class CalculadoraForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es una instancia existente (edición), incluir campos de margen y descuento
        if self.instance.pk:
            self.fields['margen'] = forms.DecimalField(
                label='Margen (%)',
                max_digits=5,
                decimal_places=2,
                min_value=0,
                initial=self.instance.margen,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                    'step': '0.01'
                })
            )
            self.fields['descuento'] = forms.DecimalField(
                label='Descuento para pago anual (%)',
                max_digits=5,
                decimal_places=2,
                min_value=0,
                initial=self.instance.descuento,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                    'step': '0.01'
                }),
                help_text='Este descuento solo se aplica al pago anual por adelantado'
            )

    class Meta:
        model = Calculadora
        fields = ['nombre', 'client', 'application', 'margen', 'descuento', 'notas', 'costo_mercado', 'tiempo_mercado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'placeholder': 'Ej: Presupuesto Proyecto Web'
            }),
            'client': forms.Select(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md'
            }),
            'application': forms.Select(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md'
            }),
            'margen': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.01',
                'min': '0'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.01',
                'min': '0'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'rows': 4,
                'placeholder': 'Notas adicionales sobre el cálculo...'
            }),
            'costo_mercado': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 5000000'
            }),
            'tiempo_mercado': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Ej: 12'
            }),
        }
        help_texts = {
            'application': 'Aplicación asociada a este cálculo (opcional)',
            'margen': 'Porcentaje de margen que se aplica al subtotal',
            'descuento': 'Porcentaje de descuento que se aplica solo al pago anual por adelantado',
        }

class ItemCalculoForm(forms.ModelForm):
    class Meta:
        model = ItemCalculo
        fields = ['descripcion', 'cantidad', 'precio_unitario']

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
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'placeholder': 'Descripción del item'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cantidad'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'w-full bg-opacity-30 focus:bg-opacity-40 backdrop-blur-md',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Precio por unidad'
            }),
        }
