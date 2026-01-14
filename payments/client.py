"""
Cliente base para la API de Flow.
Maneja autenticación HMAC-SHA256 y comunicación con la API.
"""

import hashlib
import hmac
import requests
from django.conf import settings

from .exceptions import FlowAPIError, FlowAuthenticationError


class FlowClient:
    """
    Cliente base para comunicación con la API de Flow.

    Configuración requerida en settings.py:
        FLOW_API_URL: URL base de la API
        FLOW_API_KEY: API Key del comercio
        FLOW_SECRET_KEY: Secret Key para firmar peticiones
    """

    def __init__(self, api_url=None, api_key=None, secret_key=None):
        """
        Inicializa el cliente Flow.

        Si no se proporcionan credenciales, las toma de settings.
        """
        self.api_url = api_url or getattr(settings, 'FLOW_API_URL', None)
        self.api_key = api_key or getattr(settings, 'FLOW_API_KEY', None)
        self.secret_key = secret_key or getattr(settings, 'FLOW_SECRET_KEY', None)

        if not all([self.api_url, self.api_key, self.secret_key]):
            raise FlowAuthenticationError(
                "Faltan credenciales de Flow. Configura FLOW_API_URL, "
                "FLOW_API_KEY y FLOW_SECRET_KEY en settings.py"
            )

    def _sign(self, params: dict) -> str:
        """
        Firma los parámetros con HMAC-SHA256.

        Los parámetros se ordenan alfabéticamente y se concatenan
        sin separador: "amount5000apiKeyXXXXcurrencyCLP..."

        Args:
            params: Diccionario de parámetros a firmar

        Returns:
            Firma hexadecimal
        """
        sorted_params = sorted(params.items())
        # Flow requiere concatenación SIN separador
        to_sign = ''.join([f"{k}{v}" for k, v in sorted_params])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, endpoint: str, params: dict, method: str = 'POST') -> dict:
        """
        Realiza una petición a la API de Flow.

        Args:
            endpoint: Ruta del endpoint (ej: '/payment/create')
            params: Parámetros de la petición
            method: Método HTTP ('POST' o 'GET')

        Returns:
            Respuesta JSON de la API

        Raises:
            FlowAPIError: Si hay error en la comunicación
        """
        params['apiKey'] = self.api_key
        params['s'] = self._sign(params)

        # Asegurar que no hay espacios en la URL
        base_url = self.api_url.strip().rstrip('/')
        url = f"{base_url}{endpoint}"

        # Debug: imprimir URL (quitar después de pruebas)
        print(f"[Flow Debug] URL: {url}")

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        try:
            if method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            # Intentar parsear JSON
            try:
                data = response.json()
            except ValueError:
                # Si no es JSON válido, mostrar respuesta raw
                raise FlowAPIError(
                    f"Respuesta inválida de Flow (HTTP {response.status_code}): {response.text[:500]}"
                )

            if response.status_code >= 400:
                raise FlowAPIError(
                    message=data.get('message', f'Error HTTP {response.status_code}'),
                    code=data.get('code'),
                    response=data
                )

            return data

        except FlowAPIError:
            raise
        except requests.exceptions.Timeout:
            raise FlowAPIError("Timeout al conectar con Flow")
        except requests.exceptions.ConnectionError:
            raise FlowAPIError("Error de conexión con Flow")
        except requests.exceptions.RequestException as e:
            raise FlowAPIError(f"Error en la petición: {str(e)}")

    def post(self, endpoint: str, params: dict) -> dict:
        """Realiza una petición POST."""
        return self._request(endpoint, params, method='POST')

    def get(self, endpoint: str, params: dict) -> dict:
        """Realiza una petición GET."""
        return self._request(endpoint, params, method='GET')
