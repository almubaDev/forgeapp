"""
Archivo WSGI para despliegue en PythonAnywhere.

Este archivo debe ser copiado en la configuración WSGI de PythonAnywhere.
"""

import os
import sys

# Añadir el directorio del proyecto al path
# Reemplaza 'tu-usuario' con tu nombre de usuario de PythonAnywhere
path = '/home/tu-usuario/forgeapp'
if path not in sys.path:
    sys.path.append(path)

# Configurar variables de entorno
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Importar la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
