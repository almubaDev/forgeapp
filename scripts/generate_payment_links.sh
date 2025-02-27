#!/bin/bash

# Activar el entorno virtual
source ~/.virtualenvs/forgeapp/bin/activate

# Navegar al directorio del proyecto
cd ~/forgeapp

# Ejecutar el comando de Django
python manage.py generate_payment_links

# Desactivar el entorno virtual
deactivate
