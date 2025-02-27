#!/bin/bash

# Definir rutas
VENV_PATH="/home/ForgeApp/.virtualenvs/forgeapp-env"
PROJECT_PATH="/home/ForgeApp/forgeApp/forgeapp"
LOG_PATH="/home/ForgeApp/forgeApp/forgeapp/logs"
LOG_FILE="$LOG_PATH/cron.log"
DJANGO_LOG_FILE="$LOG_PATH/django.log"

# Función para escribir en el log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Crear directorio de logs si no existe
mkdir -p "$LOG_PATH"
touch "$LOG_FILE"
touch "$DJANGO_LOG_FILE"

# Configurar permisos
chmod 755 "$LOG_PATH"
chmod 644 "$LOG_FILE"
chmod 644 "$DJANGO_LOG_FILE"

log "Iniciando script de generación de links de pago"

# Verificar entorno virtual
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    log "ERROR: No se encontró el entorno virtual en $VENV_PATH"
    exit 1
fi

# Activar el entorno virtual
log "Activando entorno virtual"
source "$VENV_PATH/bin/activate"

# Verificar directorio del proyecto
if [ ! -f "$PROJECT_PATH/manage.py" ]; then
    log "ERROR: No se encontró manage.py en $PROJECT_PATH"
    deactivate
    exit 1
fi

# Navegar al directorio del proyecto
log "Navegando al directorio del proyecto"
cd "$PROJECT_PATH"

# Configurar variables de entorno de Django
export DJANGO_SETTINGS_MODULE="core.settings"
export PYTHONPATH="$PROJECT_PATH:$PYTHONPATH"

# Ejecutar el comando de Django
log "Ejecutando comando de Django"
python manage.py generate_payment_links 2>&1 | tee -a "$LOG_FILE"

# Guardar el código de salida
EXIT_CODE=$?

# Registrar el resultado
if [ $EXIT_CODE -eq 0 ]; then
    log "Comando ejecutado exitosamente"
else
    log "Error al ejecutar el comando (código: $EXIT_CODE)"
fi

# Desactivar el entorno virtual
if [ -n "$VIRTUAL_ENV" ]; then
    log "Desactivando entorno virtual"
    deactivate
fi

log "Script finalizado"

# Salir con el código de salida del comando
exit $EXIT_CODE
