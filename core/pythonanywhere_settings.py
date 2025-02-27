"""
Configuraciones específicas para el despliegue en PythonAnywhere.
Este archivo debe ser importado al final de settings.py en producción.

Ejemplo de uso:
    # Al final de settings.py
    try:
        from core.pythonanywhere_settings import *
    except ImportError:
        pass
"""

import os
import environ
from pathlib import Path

# Definir BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de variables de entorno
env = environ.Env()
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Configuración de seguridad
SECRET_KEY = env('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = ['forgeapp.cl', 'www.forgeapp.cl', 'webapp-2482854.pythonanywhere.com']  # Reemplaza con tu dominio real

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

# Configuración de aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_tailwind',
    'django_apscheduler',
    'forgeapp',
    'finance',
    'checkout_counters',
    'pdf_generator',
]

# Configuración de middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MercadoPagoCSPMiddleware',
]

# Configuración de plantillas
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de autenticación
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'

# Duración de la sesión
SESSION_COOKIE_AGE = 24 * 60 * 60  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Configuración de seguridad adicional
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de caché
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuración de correo electrónico
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Configuración de Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Configuración de Django APScheduler
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
SCHEDULER_DEFAULT = True

# Configuración de Mercado Pago
MP_PUBLIC_KEY = env('MP_PUBLIC_KEY')
MP_ACCESS_TOKEN = env('MP_ACCESS_TOKEN')
MP_CLIENT_ID = env('MP_CLIENT_ID')
MP_CLIENT_SECRET = env('MP_CLIENT_SECRET')
MP_SANDBOX_MODE = env.bool('MP_SANDBOX_MODE', default=False)
MP_WEBHOOK_ENABLED = env.bool('MP_WEBHOOK_ENABLED', default=True)

# Configuración de URL del sitio
SITE_URL = env('SITE_URL', default='https://forgeapp.cl')
MP_WEBHOOK_URL = f"{SITE_URL}/checkout_counters/webhook/mercadopago/"

# Configuración de encriptación
ENCRYPTION_KEY = env('ENCRYPTION_KEY').encode()

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'forgeapp_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'forgeapp.log'),
            'formatter': 'verbose',
        },
        'checkout_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'checkout.log'),
            'formatter': 'verbose',
        },
        'pdf_generator_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'pdf_generator.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'forgeapp': {
            'handlers': ['forgeapp_file'],
            'level': 'INFO',  # Cambiado de ERROR a INFO
            'propagate': True,
        },
        'checkout_counters': {
            'handlers': ['checkout_file'],
            'level': 'INFO',  # Cambiado de ERROR a INFO
            'propagate': True,
        },
        'pdf_generator': {
            'handlers': ['pdf_generator_file'],
            'level': 'INFO',  # Cambiado de ERROR a INFO
            'propagate': True,
        },
    },
}

# Asegurarse de que el directorio de logs exista
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Configuración adicional
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WSGI_APPLICATION = 'core.wsgi.application'
ROOT_URLCONF = 'core.urls'
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True
