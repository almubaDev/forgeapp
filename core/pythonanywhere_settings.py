"""
Configuraciones específicas para el despliegue en PythonAnywhere.
Este archivo debe ser importado al final de settings.py en producción.

Ejemplo de uso:
    # Al final de settings.py
    try:
        from pythonanywhere_settings import *
    except ImportError:
        pass
"""

import os
import environ

# Configuración de variables de entorno
env = environ.Env()
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Configuración de base de datos MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Configuración de seguridad
DEBUG = False
ALLOWED_HOSTS = ['tu-usuario.pythonanywhere.com']  # Reemplaza con tu dominio real

# Configuración de archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de seguridad adicional
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de caché (opcional)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'checkout_counters': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'forgeapp': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Asegurarse de que el directorio de logs exista
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Configuración específica para Mercado Pago
MP_SANDBOX_MODE = False
SITE_URL = 'https://tu-usuario.pythonanywhere.com'  # Reemplaza con tu dominio real
MP_WEBHOOK_URL = f"{SITE_URL}/checkout_counters/webhook/mercadopago/"
