"""
Servicio de suscripciones de Flow.
"""

from ..client import FlowClient
from ....exceptions import FlowSubscriptionError, FlowValidationError


class SubscriptionService:
    """
    Servicio para gestionar planes y suscripciones en Flow.

    Permite crear planes y suscribir clientes para cobros periódicos automáticos.
    """

    # Intervalos de cobro
    INTERVAL_DAILY = 1
    INTERVAL_WEEKLY = 2
    INTERVAL_MONTHLY = 3
    INTERVAL_YEARLY = 4

    INTERVAL_CHOICES = {
        INTERVAL_DAILY: 'Diario',
        INTERVAL_WEEKLY: 'Semanal',
        INTERVAL_MONTHLY: 'Mensual',
        INTERVAL_YEARLY: 'Anual',
    }

    # Estados de suscripción
    STATUS_ACTIVE = 1
    STATUS_CANCELLED = 2
    STATUS_SUSPENDED = 3

    def __init__(self, client: FlowClient = None):
        """
        Inicializa el servicio.

        Args:
            client: Cliente Flow. Si no se proporciona, crea uno nuevo.
        """
        self.client = client or FlowClient()

    # =====================
    # GESTIÓN DE PLANES
    # =====================

    def create_plan(
        self,
        plan_id: str,
        name: str,
        amount: int,
        interval: int,
        currency: str = 'CLP',
        interval_count: int = 1,
        trial_period_days: int = 0
    ) -> dict:
        """
        Crea un plan de suscripción.

        Args:
            plan_id: ID único del plan
            name: Nombre del plan
            amount: Monto del plan
            interval: Intervalo (1=diario, 2=semanal, 3=mensual, 4=anual)
            currency: Moneda (default: CLP)
            interval_count: Cantidad de intervalos entre cobros
            trial_period_days: Días de prueba gratuita

        Returns:
            Datos del plan creado
        """
        if amount <= 0:
            raise FlowValidationError("El monto debe ser mayor a 0")

        if interval not in self.INTERVAL_CHOICES:
            raise FlowValidationError("Intervalo inválido")

        params = {
            'planId': plan_id,
            'name': name,
            'currency': currency,
            'amount': amount,
            'interval': interval,
            'interval_count': interval_count,
            'trial_period_days': trial_period_days,
        }

        try:
            return self.client.post('/plans/create', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al crear plan: {str(e)}")

    def get_plan(self, plan_id: str) -> dict:
        """
        Obtiene los datos de un plan.

        Args:
            plan_id: ID del plan

        Returns:
            Datos del plan
        """
        try:
            return self.client.get('/plans/get', {'planId': plan_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al obtener plan: {str(e)}")

    def edit_plan(
        self,
        plan_id: str,
        name: str = None,
        amount: int = None,
        interval: int = None,
        interval_count: int = None,
        trial_period_days: int = None
    ) -> dict:
        """
        Edita un plan existente.

        NOTA: Si el plan tiene suscriptores activos, solo se puede
        modificar trial_period_days.

        Args:
            plan_id: ID del plan
            name: Nuevo nombre (opcional)
            amount: Nuevo monto (opcional)
            interval: Nuevo intervalo (opcional)
            interval_count: Nueva cantidad de intervalos (opcional)
            trial_period_days: Nuevos días de prueba (opcional)

        Returns:
            Datos actualizados del plan
        """
        params = {'planId': plan_id}

        if name is not None:
            params['name'] = name
        if amount is not None:
            if amount <= 0:
                raise FlowValidationError("El monto debe ser mayor a 0")
            params['amount'] = amount
        if interval is not None:
            params['interval'] = interval
        if interval_count is not None:
            params['interval_count'] = interval_count
        if trial_period_days is not None:
            params['trial_period_days'] = trial_period_days

        try:
            return self.client.post('/plans/edit', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al editar plan: {str(e)}")

    def delete_plan(self, plan_id: str) -> dict:
        """
        Elimina un plan de suscripción.

        Args:
            plan_id: ID del plan

        Returns:
            Confirmación de eliminación
        """
        try:
            return self.client.post('/plans/delete', {'planId': plan_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al eliminar plan: {str(e)}")

    def list_plans(self, start: int = 0, limit: int = 10, filter_param: str = None) -> dict:
        """
        Lista los planes del comercio.

        Args:
            start: Índice de inicio
            limit: Cantidad máxima de resultados
            filter_param: Filtro por nombre

        Returns:
            Lista de planes
        """
        params = {
            'start': start,
            'limit': limit,
        }

        if filter_param:
            params['filter'] = filter_param

        try:
            return self.client.get('/plans/list', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al listar planes: {str(e)}")

    # =====================
    # GESTIÓN DE SUSCRIPCIONES
    # =====================

    def create(
        self,
        plan_id: str,
        customer_id: str,
        url_return: str,
        subscription_start: str = None,
        coupon_id: str = None,
        trial_period_days: int = None
    ) -> dict:
        """
        Suscribe un cliente a un plan.

        Args:
            plan_id: ID del plan
            customer_id: ID del cliente en Flow
            url_return: URL de retorno tras suscripción
            subscription_start: Fecha inicio (formato YYYY-MM-DD, opcional)
            coupon_id: ID del cupón de descuento (opcional)
            trial_period_days: Días de prueba (sobreescribe plan, opcional)

        Returns:
            dict con 'url' y 'token' para completar suscripción
        """
        params = {
            'planId': plan_id,
            'customerId': customer_id,
            'url_return': url_return,
        }

        if subscription_start:
            params['subscription_start'] = subscription_start
        if coupon_id:
            params['couponId'] = coupon_id
        if trial_period_days is not None:
            params['trial_period_days'] = trial_period_days

        try:
            result = self.client.post('/subscription/create', params)
            return {
                'url': f"{result['url']}?token={result['token']}",
                'token': result['token'],
                'subscription_id': result.get('subscriptionId'),
            }
        except Exception as e:
            raise FlowSubscriptionError(f"Error al crear suscripción: {str(e)}")

    def get(self, subscription_id: str) -> dict:
        """
        Obtiene los datos de una suscripción.

        Args:
            subscription_id: ID de la suscripción

        Returns:
            Datos de la suscripción
        """
        try:
            return self.client.get('/subscription/get', {'subscriptionId': subscription_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al obtener suscripción: {str(e)}")

    def list(
        self,
        plan_id: str = None,
        start: int = 0,
        limit: int = 10,
        filter_param: str = None,
        status: int = None
    ) -> dict:
        """
        Lista suscripciones del comercio.

        Args:
            plan_id: Filtrar por plan (opcional)
            start: Índice de inicio
            limit: Cantidad máxima
            filter_param: Filtro por nombre/email
            status: Filtrar por estado (1=activa, 2=cancelada, 3=suspendida)

        Returns:
            Lista de suscripciones
        """
        params = {
            'start': start,
            'limit': limit,
        }

        if plan_id:
            params['planId'] = plan_id
        if filter_param:
            params['filter'] = filter_param
        if status is not None:
            params['status'] = status

        try:
            return self.client.get('/subscription/list', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al listar suscripciones: {str(e)}")

    def cancel(self, subscription_id: str, at_period_end: int = 1) -> dict:
        """
        Cancela una suscripción.

        Args:
            subscription_id: ID de la suscripción
            at_period_end: 1 para cancelar al final del período actual,
                          0 para cancelar inmediatamente

        Returns:
            Confirmación de cancelación
        """
        params = {
            'subscriptionId': subscription_id,
            'at_period_end': at_period_end,
        }

        try:
            return self.client.post('/subscription/cancel', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al cancelar suscripción: {str(e)}")

    def add_coupon(self, subscription_id: str, coupon_id: str) -> dict:
        """
        Agrega un cupón a una suscripción.

        Args:
            subscription_id: ID de la suscripción
            coupon_id: ID del cupón

        Returns:
            Datos actualizados
        """
        params = {
            'subscriptionId': subscription_id,
            'couponId': coupon_id,
        }

        try:
            return self.client.post('/subscription/addCoupon', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al agregar cupón: {str(e)}")

    def delete_coupon(self, subscription_id: str) -> dict:
        """
        Elimina el cupón de una suscripción.

        Args:
            subscription_id: ID de la suscripción

        Returns:
            Confirmación
        """
        try:
            return self.client.post('/subscription/deleteCoupon', {'subscriptionId': subscription_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al eliminar cupón: {str(e)}")

    # =====================
    # GESTIÓN DE CUPONES
    # =====================

    def create_coupon(
        self,
        coupon_id: str,
        name: str,
        percent_off: int = None,
        amount_off: int = None,
        currency: str = 'CLP',
        duration: int = 1,
        times: int = None,
        max_redemptions: int = None,
        expires: str = None
    ) -> dict:
        """
        Crea un cupón de descuento.

        Args:
            coupon_id: ID único del cupón
            name: Nombre del cupón
            percent_off: Porcentaje de descuento (o usar amount_off)
            amount_off: Monto fijo de descuento (o usar percent_off)
            currency: Moneda para amount_off
            duration: 1=una vez, 2=por siempre, 3=varios meses
            times: Cantidad de meses si duration=3
            max_redemptions: Máximo de usos del cupón
            expires: Fecha expiración (YYYY-MM-DD)

        Returns:
            Datos del cupón creado
        """
        if not percent_off and not amount_off:
            raise FlowValidationError("Debe especificar percent_off o amount_off")

        params = {
            'couponId': coupon_id,
            'name': name,
            'currency': currency,
            'duration': duration,
        }

        if percent_off:
            params['percent_off'] = percent_off
        if amount_off:
            params['amount_off'] = amount_off
        if times:
            params['times'] = times
        if max_redemptions:
            params['max_redemptions'] = max_redemptions
        if expires:
            params['expires'] = expires

        try:
            return self.client.post('/coupon/create', params)
        except Exception as e:
            raise FlowSubscriptionError(f"Error al crear cupón: {str(e)}")

    def get_coupon(self, coupon_id: str) -> dict:
        """Obtiene datos de un cupón."""
        try:
            return self.client.get('/coupon/get', {'couponId': coupon_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al obtener cupón: {str(e)}")

    def delete_coupon_by_id(self, coupon_id: str) -> dict:
        """Elimina un cupón."""
        try:
            return self.client.post('/coupon/delete', {'couponId': coupon_id})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al eliminar cupón: {str(e)}")

    def list_coupons(self, start: int = 0, limit: int = 10) -> dict:
        """Lista cupones del comercio."""
        try:
            return self.client.get('/coupon/list', {'start': start, 'limit': limit})
        except Exception as e:
            raise FlowSubscriptionError(f"Error al listar cupones: {str(e)}")

    @classmethod
    def get_interval_label(cls, interval: int) -> str:
        """Retorna la etiqueta del intervalo."""
        return cls.INTERVAL_CHOICES.get(interval, 'Desconocido')
