# Guía de Despliegue en PythonAnywhere

Esta guía te ayudará a desplegar la aplicación ForgeApp en PythonAnywhere.

## 1. Crear una cuenta en PythonAnywhere

Si aún no tienes una cuenta, regístrate en [PythonAnywhere](https://www.pythonanywhere.com/).

## 2. Configurar un entorno virtual

Una vez que hayas iniciado sesión en PythonAnywhere, abre una consola Bash y ejecuta los siguientes comandos:

```bash
# Crear un entorno virtual con Python 3.10 (o la versión que prefieras)
mkvirtualenv --python=/usr/bin/python3.10 forgeapp-env

# Activar el entorno virtual
workon forgeapp-env
```

## 3. Clonar el repositorio

```bash
# Navegar a la carpeta donde quieres clonar el repositorio
cd ~

# Clonar el repositorio (reemplaza con tu URL de Git)
git clone https://github.com/tu-usuario/forgeapp.git

# Navegar al directorio del proyecto
cd forgeapp
```

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5. Configurar el archivo .env

Crea un archivo `.env` en el directorio raíz del proyecto con las siguientes variables:

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

Asegúrate de reemplazar `tu-usuario.pythonanywhere.com` con tu dominio real de PythonAnywhere.

## 6. Configurar la aplicación web en PythonAnywhere

1. Ve a la pestaña "Web" en el dashboard de PythonAnywhere.
2. Haz clic en "Add a new web app".
3. Selecciona tu dominio.
4. Selecciona "Manual configuration".
5. Selecciona la versión de Python que coincida con tu entorno virtual.

### Configurar la sección "Code"

- **Source code**: `/home/tu-usuario/forgeapp`
- **Working directory**: `/home/tu-usuario/forgeapp`
- **WSGI configuration file**: Haz clic en el enlace para editar el archivo WSGI.

Reemplaza el contenido del archivo WSGI con lo siguiente:

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

### Configurar la sección "Virtualenv"

- Ingresa la ruta a tu entorno virtual: `/home/tu-usuario/.virtualenvs/forgeapp-env`

## 7. Configurar archivos estáticos

En la sección "Static files" de la configuración de la aplicación web:

- **URL**: `/static/`
- **Directory**: `/home/tu-usuario/forgeapp/staticfiles`

- **URL**: `/media/`
- **Directory**: `/home/tu-usuario/forgeapp/media`

## 8. Recolectar archivos estáticos

Ejecuta el siguiente comando en la consola Bash:

```bash
cd ~/forgeapp
python manage.py collectstatic
```

## 9. Aplicar migraciones

```bash
python manage.py migrate
```

## 10. Crear un superusuario (opcional)

```bash
python manage.py createsuperuser
```

## 11. Reiniciar la aplicación web

Haz clic en el botón "Reload" en la pestaña "Web" para reiniciar tu aplicación.

## 12. Configurar HTTPS (recomendado)

PythonAnywhere proporciona HTTPS de forma gratuita para todos los dominios. Asegúrate de que la opción "Force HTTPS" esté activada en la configuración de tu aplicación web.

## 13. Configurar el webhook de Mercado Pago

Una vez que tu aplicación esté desplegada, asegúrate de actualizar la URL del webhook en tu cuenta de Mercado Pago para que apunte a:

```
https://tu-usuario.pythonanywhere.com/checkout_counters/webhook/mercadopago/
```

## Solución de problemas

### Logs

Si encuentras problemas, revisa los logs en la pestaña "Web" de PythonAnywhere:

- **Error log**: Muestra errores del servidor.
- **Server log**: Muestra la salida del servidor.
- **Access log**: Muestra las solicitudes HTTP recibidas.

### Permisos de archivos

Si encuentras problemas con permisos de archivos, ejecuta:

```bash
chmod -R 755 ~/forgeapp
```

### Problemas con Mercado Pago

Si sigues teniendo problemas con Mercado Pago después del despliegue, asegúrate de que:

1. La URL del webhook esté correctamente configurada en tu cuenta de Mercado Pago.
2. El middleware CSP esté correctamente configurado para permitir recursos de Mercado Pago.
3. Las credenciales de Mercado Pago sean correctas y estén actualizadas.
4. El modo sandbox esté desactivado si estás en producción.

### Actualizar la aplicación

Para actualizar la aplicación después de hacer cambios:

```bash
cd ~/forgeapp
git pull
workon forgeapp-env
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Luego, haz clic en "Reload" en la pestaña "Web" de PythonAnywhere.
