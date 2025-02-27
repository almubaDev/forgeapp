#!/bin/bash

# Definir rutas
VENV_PATH="/home/ForgeApp/.virtualenvs/forgeapp-env"
PROJECT_PATH="/home/ForgeApp/forgeApp/forgeapp"
LOG_PATH="/home/ForgeApp/forgeApp/forgeapp/logs"

# Crear directorio de logs si no existe
mkdir -p "$LOG_PATH"

# Activar el entorno virtual
source "$VENV_PATH/bin/activate"

# Navegar al directorio del proyecto
cd "$PROJECT_PATH"

# Ejecutar el comando de Django
python manage.py generate_payment_links

# Guardar el código de salida
EXIT_CODE=$?

# Desactivar el entorno virtual
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Salir con el código de salida del comando
exit $EXIT_CODE
