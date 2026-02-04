"""
Servicio de pagos unicos de Flow.
"""

from ..client import FlowClient
from ....exceptions import FlowPaymentError, FlowValidationError


class PaymentService:
    """
    Servicio para gestionar pagos unicos en Flow.

    Los tokens de pago son de un solo uso.
    """

    STATUS_PENDING = 1
    STATUS_PAID = 2
    STATUS_REJECTED = 3
    STATUS_CANCELLED = 4

    STATUS_CHOICES = {
        STATUS_PENDING: 'Pendiente',
        STATUS_PAID: 'Pagado',
        STATUS_REJECTED: 'Rechazado',
        STATUS_CANCELLED: 'Cancelado',
    }

    def __init__(self, client: FlowClient = None):
        self.client = client or FlowClient()

    def create(
        self,
        commerce_order: str,
        subject: str,
        amount: int,
        email: str,
        url_confirmation: str,
        url_return: str,
        currency: str = 'CLP',
        optional: dict = None
    ) -> dict:
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        params = {
            'commerceOrder': commerce_order,
            'subject': subject,
            'currency': currency,
            'amount': amount,
            'email': email,
            'urlConfirmation': url_confirmation,
            'urlReturn': url_return,
        }

        if optional:
            params.update(optional)

        try:
            result = self.client.post('/payment/create', params)
            return {
                'url': f"{result['url']}?token={result['token']}",
                'token': result['token'],
                'flow_order': result['flowOrder'],
            }
        except Exception as e:
            raise FlowPaymentError(f"Error al crear pago: {str(e)}")

    def get_status(self, token: str) -> dict:
        try:
            return self.client.get('/payment/getStatus', {'token': token})
        except Exception as e:
            raise FlowPaymentError(f"Error al obtener estado: {str(e)}")

    def get_status_by_flow_order(self, flow_order: int) -> dict:
        try:
            return self.client.get('/payment/getStatusByFlowOrder', {'flowOrder': flow_order})
        except Exception as e:
            raise FlowPaymentError(f"Error al obtener estado: {str(e)}")

    def get_status_by_commerce_order(self, commerce_order: str) -> dict:
        try:
            return self.client.get('/payment/getStatusByCommerceId', {'commerceId': commerce_order})
        except Exception as e:
            raise FlowPaymentError(f"Error al obtener estado: {str(e)}")

    def create_email(
        self,
        commerce_order: str,
        subject: str,
        amount: int,
        email: str,
        url_confirmation: str,
        currency: str = 'CLP',
        forward: int = 1
    ) -> dict:
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        params = {
            'commerceOrder': commerce_order,
            'subject': subject,
            'currency': currency,
            'amount': amount,
            'email': email,
            'urlConfirmation': url_confirmation,
            'forward': forward,
        }

        try:
            return self.client.post('/payment/createEmail', params)
        except Exception as e:
            raise FlowPaymentError(f"Error al crear pago por email: {str(e)}")

    @classmethod
    def get_status_label(cls, status_code: int) -> str:
        return cls.STATUS_CHOICES.get(status_code, 'Desconocido')

    @classmethod
    def is_paid(cls, status_code: int) -> bool:
        return status_code == cls.STATUS_PAID
