# Pasos para Configurar la Generación Automática de Links de Pago en PythonAnywhere

## 1. Subir los cambios al repositorio

```bash
git add .
git commit -m "Implementar generación automática de links de pago"
git push
```

## 2. Actualizar el código en PythonAnywhere

```bash
# Conectarse a PythonAnywhere
ssh username@ssh.pythonanywhere.com

# Ir al directorio del proyecto
cd ~/forgeapp

# Actualizar el código
git pull origin main

# Activar el entorno virtual
source ~/.virtualenvs/forgeapp/bin/activate

# Instalar cualquier nueva dependencia (si las hay)
pip install -r requirements.txt

# Aplicar migraciones (si las hay)
python manage.py migrate

# Recolectar archivos estáticos (si hay cambios)
python manage.py collectstatic --noinput
```

## 3. Configurar directorios y permisos

```bash
# Crear directorio para scripts
mkdir -p ~/forgeapp/scripts

# Crear directorio para logs
mkdir -p ~/forgeapp/logs

# Copiar el script a su ubicación
cp forgeapp/management/commands/generate_payment_links.sh ~/forgeapp/scripts/

# Dar permisos de ejecución al script
chmod +x ~/forgeapp/scripts/generate_payment_links.sh

# Asegurar que el directorio de logs sea escribible
chmod 755 ~/forgeapp/logs
```

## 4. Configurar las tareas programadas

1. En PythonAnywhere, ve a la pestaña "Tasks"

2. Agrega las siguientes tareas programadas:

Para las 8:00 AM (hora de Chile):
```
0 8 * * * ~/forgeapp/scripts/generate_payment_links.sh >> ~/forgeapp/logs/cron.log 2>&1
```

Para las 8:00 PM (hora de Chile):
```
0 20 * * * ~/forgeapp/scripts/generate_payment_links.sh >> ~/forgeapp/logs/cron.log 2>&1
```

## 5. Probar la configuración

```bash
# Probar el script manualmente
~/forgeapp/scripts/generate_payment_links.sh

# Verificar los logs
tail -f ~/forgeapp/logs/cron.log

# Verificar que no haya errores en el log de la aplicación
tail -f ~/forgeapp/logs/django.log
```

## 6. Reiniciar la aplicación

1. Ve a la pestaña "Web" en PythonAnywhere
2. Haz clic en el botón "Reload" para tu aplicación

## Verificación final

1. Revisa los logs para asegurarte de que no hay errores:
```bash
tail -f ~/forgeapp/logs/cron.log
tail -f ~/forgeapp/logs/django.log
```

2. Espera a que se ejecute la primera tarea programada y verifica que:
   - Se generan los links de pago cuando corresponde
   - Se envían los emails correctamente
   - Los logs muestran la información esperada

## Solución de problemas

Si encuentras algún problema:

1. Verifica los permisos:
```bash
ls -la ~/forgeapp/scripts/generate_payment_links.sh
ls -la ~/forgeapp/logs
```

2. Verifica que el script use el path correcto al entorno virtual:
```bash
which python
echo $VIRTUAL_ENV
```

3. Verifica las variables de entorno:
```bash
printenv | grep DJANGO
printenv | grep PYTHONPATH
```

4. Revisa los logs detallados:
```bash
cat ~/forgeapp/logs/cron.log
cat ~/forgeapp/logs/django.log
