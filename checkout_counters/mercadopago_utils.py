import mercadopago
import json
from django.conf import settings
import logging

# Configurar logging para depuración
logger = logging.getLogger(__name__)

def create_preference(form_instance, client, payment_return_url):
    """
    Crea una preferencia de pago en Mercado Pago con depuración mejorada.
    
    Args:
        form_instance: Instancia del formulario o modelo con los datos del pago
        client: Instancia del modelo Client
        payment_return_url: URL de retorno después del pago
        
    Returns:
        dict: Respuesta de Mercado Pago
    """
    # Inicializar el SDK de Mercado Pago
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    
    # Depurar los datos del cliente
    logger.debug(f"Client data: first_name='{client.first_name}', last_name='{client.last_name}', email='{client.email}'")
    
    # Asegurar que los campos del comprador no sean nulos
    first_name = client.first_name if client.first_name else "Cliente"
    last_name = client.last_name if client.last_name else "Apellido"
    
    # Obtener datos del formulario o modelo
    if hasattr(form_instance, 'instance'):
        # Es un formulario
        instance = form_instance.instance
    else:
        # Es un modelo
        instance = form_instance
    
    # Versión simplificada del JSON para probar si el problema está en la estructura
    preference_data = {
        "items": [
            {
                "title": instance.description if hasattr(instance, 'description') else f"Pago de suscripción {instance.reference_id}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": float(instance.amount if hasattr(instance, 'amount') else instance.price),
                "description": f"Pago de suscripción {instance.reference_id if hasattr(instance, 'reference_id') else instance.subscription.reference_id}",
                "category_id": "subscriptions",
                "id": instance.reference_id if hasattr(instance, 'reference_id') else instance.subscription.reference_id
            }
        ],
        "payer": {
            "email": client.email,
            "first_name": first_name,
            "last_name": last_name
        },
        "back_urls": {
            "success": payment_return_url,
            "failure": payment_return_url,
            "pending": payment_return_url
        },
        "notification_url": settings.MP_WEBHOOK_URL,
        "external_reference": instance.reference_id if hasattr(instance, 'reference_id') else instance.subscription.reference_id,
        "expires": True,
        "expiration_date_to": instance.expires_at.isoformat() if hasattr(instance, 'expires_at') else None,
        "auto_return": "approved"
    }
    
    # Imprimir como JSON formateado para depuración
    logger.debug(f"Preference data being sent to Mercado Pago:\n{json.dumps(preference_data, indent=2)}")
    
    # También intentemos con una versión mínima para prueba
    minimal_test = {
        "items": [{"title": "Test Product", "quantity": 1, "unit_price": 100, "currency_id": "CLP"}],
        "payer": {"email": client.email, "first_name": "Test", "last_name": "User"}
    }
    
    try:
        # Crear la preferencia en Mercado Pago
        preference_response = sdk.preference().create(preference_data)
        
        # Verificar respuesta
        logger.debug(f"Mercado Pago response status: {preference_response.get('status')}")
        logger.debug(f"Mercado Pago response: {json.dumps(preference_response, indent=2)}")
        
        if preference_response.get("status") == 201:
            logger.info(f"Preference created successfully: {preference_response['response']['id']}")
            return preference_response
        else:
            logger.error(f"Error creating preference: {preference_response}")
            # Intenta con el JSON mínimo como fallback
            logger.info("Trying with minimal JSON as fallback...")
            fallback_response = sdk.preference().create(minimal_test)
            logger.debug(f"Fallback response: {json.dumps(fallback_response, indent=2)}")
            return preference_response
            
    except Exception as e:
        logger.error(f"Exception when creating preference: {str(e)}")
        return {"status": "error", "message": str(e)}
