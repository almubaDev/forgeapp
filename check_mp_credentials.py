import os
import environ
from pathlib import Path

# Configuración de variables de entorno
BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()
env_file = os.path.join(BASE_DIR, '.env')

if os.path.exists(env_file):
    print(f"Leyendo archivo .env desde: {env_file}")
    environ.Env.read_env(env_file)
else:
    print(f"Archivo .env no encontrado en: {env_file}")
    exit(1)

# Verificar credenciales de Mercado Pago
mp_public_key = env('MP_PUBLIC_KEY', default='')
mp_access_token = env('MP_ACCESS_TOKEN', default='')
mp_client_id = env('MP_CLIENT_ID', default='')
mp_client_secret = env('MP_CLIENT_SECRET', default='')

# Verificar Public Key
if mp_public_key.startswith('APP_USR-'):
    print("✅ MP_PUBLIC_KEY tiene el formato correcto")
    # Mostrar solo los primeros y últimos caracteres para verificar
    masked_key = mp_public_key[:10] + '...' + mp_public_key[-5:]
    print(f"   Valor: {masked_key}")
else:
    print("❌ MP_PUBLIC_KEY no tiene el formato correcto o está vacío")
    print(f"   Valor actual: {mp_public_key}")
    print("   Debería comenzar con 'APP_USR-'")

# Verificar Access Token
if mp_access_token.startswith('APP_USR-'):
    print("✅ MP_ACCESS_TOKEN tiene el formato correcto")
    masked_token = mp_access_token[:10] + '...' + mp_access_token[-5:]
    print(f"   Valor: {masked_token}")
else:
    print("❌ MP_ACCESS_TOKEN no tiene el formato correcto o está vacío")
    print(f"   Valor actual: {mp_access_token}")
    print("   Debería comenzar con 'APP_USR-'")

# Verificar Client ID
if mp_client_id.isdigit() and len(mp_client_id) > 10:
    print("✅ MP_CLIENT_ID tiene el formato correcto")
    masked_id = mp_client_id[:4] + '...' + mp_client_id[-4:]
    print(f"   Valor: {masked_id}")
else:
    print("❌ MP_CLIENT_ID no tiene el formato correcto o está vacío")
    print(f"   Valor actual: {mp_client_id}")
    print("   Debería ser un número de más de 10 dígitos")

# Verificar Client Secret
if len(mp_client_secret) > 20:
    print("✅ MP_CLIENT_SECRET tiene el formato correcto")
    masked_secret = mp_client_secret[:4] + '...' + mp_client_secret[-4:]
    print(f"   Valor: {masked_secret}")
else:
    print("❌ MP_CLIENT_SECRET no tiene el formato correcto o está vacío")
    print(f"   Valor actual: {mp_client_secret}")
    print("   Debería ser una cadena de más de 20 caracteres")

# Verificar modo sandbox
mp_sandbox_mode = env.bool('MP_SANDBOX_MODE', default=True)
print(f"ℹ️ Modo Sandbox: {'Activado' if mp_sandbox_mode else 'Desactivado'}")

# Verificar URL del webhook
site_url = env('SITE_URL', default='http://localhost:8000')
mp_webhook_url = f"{site_url}/checkout_counters/webhook/mercadopago/"
print(f"ℹ️ URL del Webhook: {mp_webhook_url}")

print("\nSi alguna de las credenciales no coincide con las proporcionadas, actualiza tu archivo .env con los valores correctos.")
