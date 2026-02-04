"""
Cliente base para la API de Flow.
Maneja autenticacion HMAC-SHA256 y comunicacion con la API.
"""

import hashlib
import hmac
import requests
from django.conf import settings

from ...exceptions import FlowAPIError, FlowAuthenticationError


class FlowClient:
    """
    Cliente base para comunicacion con la API de Flow.

    Configuracion requerida en settings.py:
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
        Firma los parametros con HMAC-SHA256.

        Los parametros se ordenan alfabeticamente y se concatenan
        sin separador: "amount5000apiKeyXXXXcurrencyCLP..."
        """
        sorted_params = sorted(params.items())
        to_sign = ''.join([f"{k}{v}" for k, v in sorted_params])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, endpoint: str, params: dict, method: str = 'POST') -> dict:
        """
        Realiza una peticion a la API de Flow.
        """
        params['apiKey'] = self.api_key
        params['s'] = self._sign(params)

        base_url = self.api_url.strip().rstrip('/')
        url = f"{base_url}{endpoint}"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        try:
            if method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            try:
                data = response.json()
            except ValueError:
                raise FlowAPIError(
                    f"Respuesta invalida de Flow (HTTP {response.status_code}): {response.text[:500]}"
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
            raise FlowAPIError("Error de conexion con Flow")
        except requests.exceptions.RequestException as e:
            raise FlowAPIError(f"Error en la peticion: {str(e)}")

    def post(self, endpoint: str, params: dict) -> dict:
        """Realiza una peticion POST."""
        return self._request(endpoint, params, method='POST')

    def get(self, endpoint: str, params: dict) -> dict:
        """Realiza una peticion GET."""
        return self._request(endpoint, params, method='GET')
