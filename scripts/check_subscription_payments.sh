#!/bin/bash
# Script para verificar suscripciones que necesitan pago
# Este script debe configurarse como una tarea programada en PythonAnywhere

# Cambiar al directorio del proyecto
cd /home/ForgeApp/forgeApp

# Activar el entorno virtual
source /home/ForgeApp/.virtualenvs/forgeapp-env/bin/activate

# Ejecutar el comando de gestión con la configuración de PythonAnywhere
python manage.py check_subscription_payments --settings=core.pythonanywhere_settings

# Registrar la ejecución
echo "$(date): Verificación de pagos de suscripciones completada" >> /home/ForgeApp/forgeApp/logs/cron.log
