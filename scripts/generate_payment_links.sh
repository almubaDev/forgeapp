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
mkdir -p "$LOG_PATH" || {
    echo "ERROR: No se pudo crear el directorio de logs"
    exit 1
}

# Crear archivos de log si no existen
touch "$LOG_FILE" "$DJANGO_LOG_FILE" || {
    echo "ERROR: No se pudieron crear los archivos de log"
    exit 1
}

# Verificar que los archivos sean escribibles
if [ ! -w "$LOG_FILE" ] || [ ! -w "$DJANGO_LOG_FILE" ]; then
    echo "ERROR: No se puede escribir en los archivos de log"
    echo "Por favor, verifica los permisos de $LOG_PATH"
    exit 1
fi

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

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE="core.settings"
export PYTHONPATH="$PROJECT_PATH:$PYTHONPATH"

# Verificar y cargar archivo .env
ENV_FILE="$PROJECT_PATH/.env"
if [ ! -f "$ENV_FILE" ]; then
    log "ERROR: No se encontró el archivo .env en $ENV_FILE"
    log "Copiando archivo .env de ejemplo..."
    cp "$PROJECT_PATH/.env.example" "$ENV_FILE" || {
        log "ERROR: No se pudo copiar el archivo .env.example"
        exit 1
    }
fi

log "Usando archivo .env en: $ENV_FILE"

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
