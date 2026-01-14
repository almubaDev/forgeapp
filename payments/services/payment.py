"""
Servicio de pagos únicos de Flow.
"""

from ..client import FlowClient
from ..exceptions import FlowPaymentError, FlowValidationError


class PaymentService:
    """
    Servicio para gestionar pagos únicos en Flow.

    Los tokens de pago son de un solo uso.
    """

    # Estados de pago
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
        """
        Inicializa el servicio.

        Args:
            client: Cliente Flow. Si no se proporciona, crea uno nuevo.
        """
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
        """
        Crea una orden de pago.

        Args:
            commerce_order: ID único de la orden en tu sistema
            subject: Descripción del pago
            amount: Monto a cobrar
            email: Correo del cliente
            url_confirmation: URL webhook para confirmación
            url_return: URL de retorno del cliente
            currency: Moneda (default: CLP)
            optional: Parámetros opcionales adicionales

        Returns:
            dict con 'url', 'token' y 'flow_order'

        Raises:
            FlowPaymentError: Si hay error al crear el pago
        """
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
        """
        Obtiene el estado de un pago por token.

        Args:
            token: Token del pago

        Returns:
            Datos del pago incluyendo estado
        """
        try:
            return self.client.get('/payment/getStatus', {'token': token})
        except Exception as e:
            raise FlowPaymentError(f"Error al obtener estado: {str(e)}")

    def get_status_by_flow_order(self, flow_order: int) -> dict:
        """
        Obtiene el estado de un pago por flowOrder.

        Args:
            flow_order: Número de orden de Flow

        Returns:
            Datos del pago incluyendo estado
        """
        try:
            return self.client.get('/payment/getStatusByFlowOrder', {'flowOrder': flow_order})
        except Exception as e:
            raise FlowPaymentError(f"Error al obtener estado: {str(e)}")

    def get_status_by_commerce_order(self, commerce_order: str) -> dict:
        """
        Obtiene el estado de un pago por commerceOrder.

        Args:
            commerce_order: ID de la orden en tu sistema

        Returns:
            Datos del pago incluyendo estado
        """
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
        """
        Crea un pago y envía el link por email al cliente.

        Args:
            commerce_order: ID único de la orden
            subject: Descripción del pago
            amount: Monto a cobrar
            email: Correo del cliente
            url_confirmation: URL webhook
            currency: Moneda (default: CLP)
            forward: 1 para redirigir automáticamente tras pago

        Returns:
            Datos del pago creado
        """
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
        """Retorna la etiqueta legible del estado."""
        return cls.STATUS_CHOICES.get(status_code, 'Desconocido')

    @classmethod
    def is_paid(cls, status_code: int) -> bool:
        """Verifica si el estado indica pago completado."""
        return status_code == cls.STATUS_PAID
