"""
Servicio de reembolsos de Flow.
"""

from ..client import FlowClient
from ..exceptions import FlowRefundError, FlowValidationError


class RefundService:
    """
    Servicio para gestionar reembolsos en Flow.
    """

    # Estados de reembolso
    STATUS_PENDING = 1
    STATUS_ACCEPTED = 2
    STATUS_REJECTED = 3

    STATUS_CHOICES = {
        STATUS_PENDING: 'Pendiente',
        STATUS_ACCEPTED: 'Aceptado',
        STATUS_REJECTED: 'Rechazado',
    }

    def __init__(self, client: FlowClient = None):
        """
        Inicializa el servicio.

        Args:
            client: Cliente Flow. Si no se proporciona, crea uno nuevo.
        """
        self.client = client or FlowClient()

    def create(self, flow_order: int, amount: int, receiver_email: str) -> dict:
        """
        Crea un reembolso para una transacción.

        Args:
            flow_order: Número de orden de Flow
            amount: Monto a reembolsar
            receiver_email: Email del receptor del reembolso

        Returns:
            Datos del reembolso creado
        """
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        params = {
            'flowOrder': flow_order,
            'amount': amount,
            'receiverEmail': receiver_email,
        }

        try:
            return self.client.post('/refund/create', params)
        except Exception as e:
            raise FlowRefundError(f"Error al crear reembolso: {str(e)}")

    def get_status(self, token: str) -> dict:
        """
        Obtiene el estado de un reembolso.

        Args:
            token: Token del reembolso

        Returns:
            Datos del reembolso incluyendo estado
        """
        try:
            return self.client.get('/refund/getStatus', {'token': token})
        except Exception as e:
            raise FlowRefundError(f"Error al obtener estado: {str(e)}")

    def cancel(self, token: str) -> dict:
        """
        Cancela un reembolso pendiente.

        Args:
            token: Token del reembolso

        Returns:
            Confirmación de cancelación
        """
        try:
            return self.client.post('/refund/cancel', {'token': token})
        except Exception as e:
            raise FlowRefundError(f"Error al cancelar reembolso: {str(e)}")

    @classmethod
    def get_status_label(cls, status_code: int) -> str:
        """Retorna la etiqueta legible del estado."""
        return cls.STATUS_CHOICES.get(status_code, 'Desconocido')
