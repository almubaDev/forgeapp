from django import forms

class VerificationCodeForm(forms.Form):
    """Formulario para verificar un código de comprobante"""
    verification_code = forms.CharField(
        label='Código de Verificación',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el código de verificación',
            'autofocus': True
        })
    )
