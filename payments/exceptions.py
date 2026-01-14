"""
Excepciones personalizadas para la integración con Flow.
"""


class FlowException(Exception):
    """Excepción base para errores de Flow."""
    pass


class FlowAPIError(FlowException):
    """Error de comunicación con la API de Flow."""

    def __init__(self, message, code=None, response=None):
        self.code = code
        self.response = response
        super().__init__(message)


class FlowAuthenticationError(FlowException):
    """Error de autenticación con Flow."""
    pass


class FlowPaymentError(FlowException):
    """Error al procesar un pago."""
    pass


class FlowCustomerError(FlowException):
    """Error relacionado con clientes de Flow."""
    pass


class FlowSubscriptionError(FlowException):
    """Error relacionado con suscripciones."""
    pass


class FlowRefundError(FlowException):
    """Error al procesar un reembolso."""
    pass


class FlowValidationError(FlowException):
    """Error de validación de parámetros."""
    pass
