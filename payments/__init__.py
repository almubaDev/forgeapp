"""
App de pagos con Flow.

Uso básico:
    from payments.services import PaymentService, CustomerService, SubscriptionService, RefundService

    # Pago único
    payment = PaymentService()
    result = payment.create(
        commerce_order='ORD-001',
        subject='Compra de producto',
        amount=10000,
        email='cliente@ejemplo.com',
        url_confirmation='https://tudominio.com/payments/confirm/',
        url_return='https://tudominio.com/payments/return/'
    )

    # Cargo a cliente con tarjeta registrada
    customer = CustomerService()
    customer.charge(
        customer_id='cus_xxx',
        amount=5000,
        subject='Cargo mensual',
        commerce_order='ORD-002'
    )
"""

from .providers.flow import (
    FlowClient,
    PaymentService,
    CustomerService,
    SubscriptionService,
    RefundService,
)
from .exceptions import (
    FlowException,
    FlowAPIError,
    FlowAuthenticationError,
    FlowPaymentError,
    FlowCustomerError,
    FlowSubscriptionError,
    FlowRefundError,
    FlowValidationError,
)

__all__ = [
    # Cliente
    'FlowClient',
    # Servicios
    'PaymentService',
    'CustomerService',
    'SubscriptionService',
    'RefundService',
    # Excepciones
    'FlowException',
    'FlowAPIError',
    'FlowAuthenticationError',
    'FlowPaymentError',
    'FlowCustomerError',
    'FlowSubscriptionError',
    'FlowRefundError',
    'FlowValidationError',
]
