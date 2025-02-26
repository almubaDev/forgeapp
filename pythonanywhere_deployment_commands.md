# Comandos para Despliegue en PythonAnywhere

Este archivo contiene los comandos esenciales que necesitarás ejecutar para desplegar la aplicación ForgeApp en PythonAnywhere.

## 1. Configuración Inicial en PythonAnywhere

```bash
# Crear un entorno virtual
mkvirtualenv --python=/usr/bin/python3.10 forgeapp-env

# Activar el entorno virtual
workon forgeapp-env

# Clonar el repositorio (reemplaza con tu URL de Git)
cd ~
git clone https://github.com/tu-usuario/forgeapp.git
cd forgeapp
```

## 2. Instalación de Dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

## 3. Configuración del Archivo .env

Crea el archivo `.env` con la configuración para producción:

```bash
# Crear el archivo .env
nano .env
```

Contenido del archivo `.env`:
```
SECRET_KEY=Anada!312$Lacsap21
DEBUG=False

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=contacto@forgeapp.cl
EMAIL_HOST_PASSWORD=jnfu dumy gkki bjod
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=contacto@forgeapp.cl

# Encryption settings
ENCRYPTION_KEY=Hl6SAOdnpqCgYlqWxzX_qJbYoGkrTNGILGvK8KqVGYE=

# Mercado Pago Settings
MP_PUBLIC_KEY=APP_USR-875984f4-0bd7-4ac0-9873-e68715149a74
MP_ACCESS_TOKEN=APP_USR-3140749224688195-022120-5a5cf9d45712703a5db702c0e5f8f348-2281330215
MP_CLIENT_ID=3140749224688195
MP_CLIENT_SECRET=MtPoBdD1fVsqW8mm5zoxe7a3mpUy3fVR

# Site URL for webhooks (reemplaza con tu dominio de PythonAnywhere)
SITE_URL=https://tu-usuario.pythonanywhere.com

# Mercado Pago webhook settings
MP_WEBHOOK_ENABLED=True
MP_SANDBOX_MODE=False
```

## 4. Migraciones de Base de Datos

```bash
# Aplicar migraciones
python manage.py migrate
```

## 5. Recolección de Archivos Estáticos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

## 6. Crear Superusuario (opcional)

```bash
# Crear superusuario para el panel de administración
python manage.py createsuperuser
```

## 7. Configuración de la Aplicación Web en PythonAnywhere

1. Ve a la pestaña "Web" en el dashboard de PythonAnywhere
2. Haz clic en "Add a new web app"
3. Selecciona "Manual configuration" y la versión de Python que coincida con tu entorno virtual

### Configuración del archivo WSGI

Edita el archivo WSGI generado por PythonAnywhere y reemplaza su contenido con:

```python
import os
import sys

# Añadir el directorio del proyecto al path
path = '/home/tu-usuario/forgeapp'
if path not in sys.path:
    sys.path.append(path)

# Configurar variables de entorno
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Importar la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Configuración del Entorno Virtual

En la sección "Virtualenv", ingresa la ruta a tu entorno virtual:
```
/home/tu-usuario/.virtualenvs/forgeapp-env
```

### Configuración de Archivos Estáticos

En la sección "Static files", configura:

- URL: `/static/`
- Directory: `/home/tu-usuario/forgeapp/staticfiles`

- URL: `/media/`
- Directory: `/home/tu-usuario/forgeapp/media`

## 8. Reiniciar la Aplicación

Haz clic en el botón "Reload" en la pestaña "Web" para reiniciar tu aplicación.

## 9. Verificar el Despliegue

Visita tu sitio en `https://tu-usuario.pythonanywhere.com` para verificar que todo funcione correctamente.

## 10. Configurar el Webhook de Mercado Pago

Asegúrate de actualizar la URL del webhook en tu cuenta de Mercado Pago para que apunte a:
```
https://tu-usuario.pythonanywhere.com/checkout_counters/webhook/mercadopago/
```

## Comandos para Actualizar la Aplicación

Cuando necesites actualizar la aplicación después de hacer cambios:

```bash
# Activar el entorno virtual
workon forgeapp-env

# Ir al directorio del proyecto
cd ~/forgeapp

# Obtener los últimos cambios
git pull

# Instalar nuevas dependencias (si las hay)
pip install -r requirements.txt

# Aplicar migraciones (si las hay)
python manage.py migrate

# Recolectar archivos estáticos (si han cambiado)
python manage.py collectstatic --noinput
```

Luego, haz clic en "Reload" en la pestaña "Web" de PythonAnywhere para aplicar los cambios.
