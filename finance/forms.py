from django import forms
from .models import Payment, Transaction, PaymentMethod, Receipt

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'type', 'is_active', 'config']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'type': forms.Select(attrs={'class': 'win98-input w-full'}),
            'config': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 4}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['subscription', 'amount', 'due_date', 'payment_method', 'notes']
        widgets = {
            'subscription': forms.Select(attrs={'class': 'win98-input w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'win98-input w-full', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'win98-input w-full', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'win98-input w-full'}),
            'notes': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 3}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'category', 'description', 'amount', 'date', 'payment', 'notes']
        widgets = {
            'type': forms.Select(attrs={'class': 'win98-input w-full'}),
            'category': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'description': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'win98-input w-full', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'win98-input w-full', 'type': 'date'}),
            'payment': forms.Select(attrs={'class': 'win98-input w-full'}),
            'notes': forms.Textarea(attrs={'class': 'win98-input w-full', 'rows': 3}),
        }

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['payment', 'receipt_number', 'pdf_file']
        widgets = {
            'payment': forms.Select(attrs={'class': 'win98-input w-full'}),
            'receipt_number': forms.TextInput(attrs={'class': 'win98-input w-full'}),
            'pdf_file': forms.FileInput(attrs={'class': 'win98-input w-full'}),
        }

class DateRangeForm(forms.Form):
    """Formulario para filtrar por rango de fechas"""
    start_date = forms.DateField(
        label='Fecha Inicio',
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        label='Fecha Fin',
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )

class PaymentFilterForm(forms.Form):
    """Formulario para filtrar pagos"""
    status = forms.ChoiceField(
        choices=[('', 'Todos')] + Payment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'win98-input w-full'})
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        required=False,
        empty_label="Todos los métodos",
        widget=forms.Select(attrs={'class': 'win98-input w-full'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )

class TransactionFilterForm(forms.Form):
    """Formulario para filtrar transacciones"""
    type = forms.ChoiceField(
        choices=[('', 'Todos')] + Transaction.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'win98-input w-full'})
    )
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'win98-input w-full'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'win98-input w-full',
            'type': 'date'
        })
    )
