"""
Archivo WSGI para despliegue en PythonAnywhere.

Este archivo debe ser copiado en la configuración WSGI de PythonAnywhere.
"""

import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
# Reemplaza 'tu-usuario' con tu nombre de usuario de PythonAnywhere
path = '/home/tu-usuario/forgeapp'
if path not in sys.path:
    sys.path.append(path)

# Configurar variables de entorno
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Cargar variables de entorno desde .env
import environ
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Importar la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
