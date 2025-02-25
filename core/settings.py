from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de variables de entorno
env = environ.Env()
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    print(f"Leyendo archivo .env desde: {env_file}")
    environ.Env.read_env(env_file)
else:
    raise Exception(f"Archivo .env no encontrado en: {env_file}")

SECRET_KEY = env('SECRET_KEY', default='your-secret-key-here')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = ['*']  # Permitir todos los hosts en desarrollo
BASE_URL = 'http://localhost:8000'  # URL base para desarrollo

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    #'tailwind',
    # 'theme',
    'crispy_forms',
    'crispy_tailwind',
    'django_apscheduler',  # Agregado
    'forgeapp',
    'finance',
    'checkout_counters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application' 

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TAILWIND_APP_NAME = 'theme'
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'

# Duración de la sesión en segundos (24 horas)
SESSION_COOKIE_AGE = 24 * 60 * 60  # 24 horas

# Mantener la renovación automática
SESSION_SAVE_EVERY_REQUEST = True

# No cerrar sesión al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Encryption settings
ENCRYPTION_KEY = env('ENCRYPTION_KEY').encode()

# Email settings
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Finance settings
ENABLE_SUBSCRIPTION_CHECK = True

# Django APScheduler settings
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
SCHEDULER_DEFAULT = True

# Logging configuration
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'finance.log'),
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
    },
    'loggers': {
        'finance': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django_apscheduler': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'forgeapp': {
            'handlers': ['console', 'forgeapp_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'checkout_counters': {
            'handlers': ['console', 'checkout_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Mercado Pago Settings
MP_PUBLIC_KEY = env('MP_PUBLIC_KEY')
MP_ACCESS_TOKEN = env('MP_ACCESS_TOKEN')
MP_CLIENT_ID = env('MP_CLIENT_ID')
MP_CLIENT_SECRET = env('MP_CLIENT_SECRET')

# Site URL for webhooks
SITE_URL = env('SITE_URL', default='http://localhost:8000')
MP_WEBHOOK_URL = f"{SITE_URL}/checkout_counters/webhook/mercadopago/"

# Asegurar que la URL del webhook sea accesible desde Internet
if DEBUG:
    import socket
    try:
        # Intentar obtener la IP pública
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Si estamos en desarrollo, usar ngrok o similar para exponer el webhook
        if SITE_URL == 'http://localhost:8000':
            logger.warning(
                "Usando localhost para webhooks. En desarrollo, considera usar ngrok "
                "para exponer el webhook a Internet: ngrok http 8000"
            )
    except Exception as e:
        logger.warning(f"No se pudo determinar la IP local: {e}")

# Mercado Pago settings
MP_WEBHOOK_ENABLED = env.bool('MP_WEBHOOK_ENABLED', default=True)

# Mercado Pago sandbox mode
MP_SANDBOX_MODE = env.bool('MP_SANDBOX_MODE', default=True)
