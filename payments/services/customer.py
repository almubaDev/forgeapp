"""
Servicio de clientes y cargos automáticos de Flow.
"""

from ..client import FlowClient
from ..exceptions import FlowCustomerError, FlowValidationError


class CustomerService:
    """
    Servicio para gestionar clientes en Flow.

    Permite crear clientes, registrar tarjetas y realizar cargos automáticos.
    """

    # Estados de registro de tarjeta
    REGISTER_PENDING = 0
    REGISTER_COMPLETED = 1

    def __init__(self, client: FlowClient = None):
        """
        Inicializa el servicio.

        Args:
            client: Cliente Flow. Si no se proporciona, crea uno nuevo.
        """
        self.client = client or FlowClient()

    # =====================
    # GESTIÓN DE CLIENTES
    # =====================

    def create(self, name: str, email: str, external_id: str) -> dict:
        """
        Crea un cliente en Flow.

        Args:
            name: Nombre del cliente
            email: Correo del cliente
            external_id: ID del cliente en tu sistema

        Returns:
            Datos del cliente creado incluyendo customerId
        """
        params = {
            'name': name,
            'email': email,
            'externalId': external_id,
        }

        try:
            return self.client.post('/customer/create', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al crear cliente: {str(e)}")

    def get(self, customer_id: str) -> dict:
        """
        Obtiene los datos de un cliente.

        Args:
            customer_id: ID del cliente en Flow

        Returns:
            Datos del cliente
        """
        try:
            return self.client.get('/customer/get', {'customerId': customer_id})
        except Exception as e:
            raise FlowCustomerError(f"Error al obtener cliente: {str(e)}")

    def get_by_external_id(self, external_id: str) -> dict:
        """
        Obtiene un cliente por su ID externo.

        Args:
            external_id: ID del cliente en tu sistema

        Returns:
            Datos del cliente
        """
        try:
            return self.client.get('/customer/getByExternalId', {'externalId': external_id})
        except Exception as e:
            raise FlowCustomerError(f"Error al obtener cliente: {str(e)}")

    def edit(self, customer_id: str, name: str = None, email: str = None, external_id: str = None) -> dict:
        """
        Edita los datos de un cliente.

        Args:
            customer_id: ID del cliente en Flow
            name: Nuevo nombre (opcional)
            email: Nuevo email (opcional)
            external_id: Nuevo ID externo (opcional)

        Returns:
            Datos actualizados del cliente
        """
        params = {'customerId': customer_id}

        if name:
            params['name'] = name
        if email:
            params['email'] = email
        if external_id:
            params['externalId'] = external_id

        try:
            return self.client.post('/customer/edit', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al editar cliente: {str(e)}")

    def delete(self, customer_id: str) -> dict:
        """
        Elimina un cliente y su registro de tarjeta.

        Args:
            customer_id: ID del cliente en Flow

        Returns:
            Confirmación de eliminación
        """
        try:
            return self.client.post('/customer/delete', {'customerId': customer_id})
        except Exception as e:
            raise FlowCustomerError(f"Error al eliminar cliente: {str(e)}")

    def list(self, start: int = 0, limit: int = 10, filter_param: str = None, status: int = None) -> dict:
        """
        Lista clientes del comercio.

        Args:
            start: Índice de inicio
            limit: Cantidad máxima de resultados
            filter_param: Filtro por nombre o email
            status: Filtro por estado (1=con tarjeta, 0=sin tarjeta)

        Returns:
            Lista de clientes
        """
        params = {
            'start': start,
            'limit': limit,
        }

        if filter_param:
            params['filter'] = filter_param
        if status is not None:
            params['status'] = status

        try:
            return self.client.get('/customer/list', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al listar clientes: {str(e)}")

    # =====================
    # REGISTRO DE TARJETA
    # =====================

    def register(self, customer_id: str, url_return: str) -> dict:
        """
        Genera URL para que el cliente registre su tarjeta.

        Args:
            customer_id: ID del cliente en Flow
            url_return: URL de retorno tras registro

        Returns:
            dict con 'url' y 'token' para registro
        """
        params = {
            'customerId': customer_id,
            'url_return': url_return,
        }

        try:
            result = self.client.post('/customer/register', params)
            return {
                'url': f"{result['url']}?token={result['token']}",
                'token': result['token'],
            }
        except Exception as e:
            raise FlowCustomerError(f"Error al generar registro: {str(e)}")

    def get_register_status(self, token: str) -> dict:
        """
        Verifica el estado del registro de tarjeta.

        Args:
            token: Token del registro

        Returns:
            Estado del registro
        """
        try:
            return self.client.get('/customer/getRegisterStatus', {'token': token})
        except Exception as e:
            raise FlowCustomerError(f"Error al verificar registro: {str(e)}")

    def unregister(self, customer_id: str) -> dict:
        """
        Elimina el registro de tarjeta de un cliente.

        Args:
            customer_id: ID del cliente en Flow

        Returns:
            Confirmación de eliminación
        """
        try:
            return self.client.post('/customer/unRegister', {'customerId': customer_id})
        except Exception as e:
            raise FlowCustomerError(f"Error al eliminar tarjeta: {str(e)}")

    # =====================
    # CARGOS AUTOMÁTICOS
    # =====================

    def charge(
        self,
        customer_id: str,
        amount: int,
        subject: str,
        commerce_order: str,
        currency: str = 'CLP',
        optional_email: int = 0
    ) -> dict:
        """
        Realiza un cargo automático a la tarjeta del cliente.

        Requiere que el cliente tenga tarjeta registrada.

        Args:
            customer_id: ID del cliente en Flow
            amount: Monto a cobrar
            subject: Descripción del cobro
            commerce_order: ID de la orden en tu sistema
            currency: Moneda (default: CLP)
            optional_email: 1 para enviar comprobante por email

        Returns:
            Datos del cargo realizado

        Límites por defecto:
            - Máximo por transacción: 250.000 CLP
            - Máximo diario por cliente: 500.000 CLP
            - Máximo 5 cobros diarios por cliente
        """
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        params = {
            'customerId': customer_id,
            'amount': amount,
            'subject': subject,
            'commerceOrder': commerce_order,
            'currency': currency,
            'optionalEmail': optional_email,
        }

        try:
            return self.client.post('/customer/charge', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al realizar cargo: {str(e)}")

    def collect(
        self,
        customer_id: str,
        amount: int,
        subject: str,
        commerce_order: str,
        url_confirmation: str,
        currency: str = 'CLP',
        by_email: int = 0,
        forward: int = 0
    ) -> dict:
        """
        Envía un cobro a un cliente.

        Si tiene tarjeta registrada, cobra automáticamente.
        Si no tiene tarjeta, genera un link de pago.

        Args:
            customer_id: ID del cliente en Flow
            amount: Monto a cobrar
            subject: Descripción del cobro
            commerce_order: ID de la orden en tu sistema
            url_confirmation: URL webhook
            currency: Moneda (default: CLP)
            by_email: 1 para enviar cobro por email
            forward: 1 para redirigir tras pago (si genera link)

        Returns:
            Datos del cobro
        """
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        params = {
            'customerId': customer_id,
            'amount': amount,
            'subject': subject,
            'commerceOrder': commerce_order,
            'urlConfirmation': url_confirmation,
            'currency': currency,
            'byEmail': by_email,
            'forward': forward,
        }

        try:
            return self.client.post('/customer/collect', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al enviar cobro: {str(e)}")

    def batch_collect(self, url_callback: str, url_confirmation: str, collectors: list) -> dict:
        """
        Envía múltiples cobros de forma masiva.

        Args:
            url_callback: URL para notificar resultado del batch
            url_confirmation: URL webhook para cada cobro
            collectors: Lista de cobros, cada uno con:
                - customerId
                - amount
                - subject
                - commerceOrder

        Returns:
            Token del batch y cantidad de cobros procesados
        """
        import json

        params = {
            'urlCallBack': url_callback,
            'urlConfirmation': url_confirmation,
            'batchRows': json.dumps(collectors),
        }

        try:
            return self.client.post('/customer/batchCollect', params)
        except Exception as e:
            raise FlowCustomerError(f"Error en cobro masivo: {str(e)}")

    def get_batch_collect_status(self, token: str) -> dict:
        """
        Obtiene el estado de un batch de cobros.

        Args:
            token: Token del batch

        Returns:
            Estado del batch
        """
        try:
            return self.client.get('/customer/getBatchCollectStatus', {'token': token})
        except Exception as e:
            raise FlowCustomerError(f"Error al obtener estado del batch: {str(e)}")

    def reverse_charge(self, commerce_order: str) -> dict:
        """
        Reversa un cargo dentro de las 24 horas siguientes.

        Args:
            commerce_order: ID de la orden a reversar

        Returns:
            Confirmación de reversa
        """
        try:
            return self.client.post('/customer/reverseCharge', {'commerceOrder': commerce_order})
        except Exception as e:
            raise FlowCustomerError(f"Error al reversar cargo: {str(e)}")

    def get_charge_attempts(self, customer_id: str) -> dict:
        """
        Obtiene los intentos de cargo del día para un cliente.

        Args:
            customer_id: ID del cliente

        Returns:
            Cantidad de intentos y montos del día
        """
        try:
            return self.client.get('/customer/getChargeAttempts', {'customerId': customer_id})
        except Exception as e:
            raise FlowCustomerError(f"Error al obtener intentos: {str(e)}")

    def get_charges(self, customer_id: str, start: int = 0, limit: int = 10) -> dict:
        """
        Lista los cargos realizados a un cliente.

        Args:
            customer_id: ID del cliente
            start: Índice de inicio
            limit: Cantidad máxima

        Returns:
            Lista de cargos
        """
        params = {
            'customerId': customer_id,
            'start': start,
            'limit': limit,
        }

        try:
            return self.client.get('/customer/getCharges', params)
        except Exception as e:
            raise FlowCustomerError(f"Error al listar cargos: {str(e)}")
