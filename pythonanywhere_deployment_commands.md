# Configuración de Generación Automática de Links de Pago en PythonAnywhere

## 1. Crear directorios necesarios

```bash
# Crear directorio para scripts
mkdir -p /home/ForgeApp/forgeApp/forgeapp/scripts

# Crear directorio para logs
mkdir -p /home/ForgeApp/forgeApp/forgeapp/logs

# Asegurar permisos
chmod 755 /home/ForgeApp/forgeApp/forgeapp/scripts
chmod 755 /home/ForgeApp/forgeApp/forgeapp/logs
```

## 2. Copiar y configurar el script

```bash
# Copiar el script al directorio correcto
cp scripts/generate_payment_links.sh /home/ForgeApp/forgeApp/forgeapp/scripts/

# Dar permisos de ejecución
chmod +x /home/ForgeApp/forgeApp/forgeapp/scripts/generate_payment_links.sh
```

## 3. Probar el script manualmente

```bash
# Ejecutar el script
/home/ForgeApp/forgeApp/forgeapp/scripts/generate_payment_links.sh

# Verificar la salida
cat /home/ForgeApp/forgeApp/forgeapp/logs/cron.log
```

## 4. Configurar las tareas programadas en PythonAnywhere

1. Ve a la pestaña "Tasks" en PythonAnywhere

2. Agrega las siguientes tareas:

Para las 8:00 AM (hora de Chile):
```
0 8 * * * /home/ForgeApp/forgeApp/forgeapp/scripts/generate_payment_links.sh >> /home/ForgeApp/forgeApp/forgeapp/logs/cron.log 2>&1
```

Para las 8:00 PM (hora de Chile):
```
0 20 * * * /home/ForgeApp/forgeApp/forgeapp/scripts/generate_payment_links.sh >> /home/ForgeApp/forgeApp/forgeapp/logs/cron.log 2>&1
```

## 5. Verificar la configuración

```bash
# Verificar los permisos del script
ls -l /home/ForgeApp/forgeApp/forgeapp/scripts/generate_payment_links.sh

# Verificar los permisos del directorio de logs
ls -l /home/ForgeApp/forgeApp/forgeapp/logs

# Verificar que el script puede acceder al entorno virtual
ls -l /home/ForgeApp/.virtualenvs/forgeapp-env/bin/activate

# Verificar que el script puede acceder al proyecto
ls -l /home/ForgeApp/forgeApp/forgeapp/manage.py
```

## 6. Monitorear los logs

```bash
# Ver los últimos logs del cron
tail -f /home/ForgeApp/forgeApp/forgeapp/logs/cron.log

# Ver los logs de Django
tail -f /home/ForgeApp/forgeApp/forgeapp/logs/django.log
```

## Solución de problemas

Si el script falla, verifica:

1. Rutas del entorno virtual:
```bash
ls -l /home/ForgeApp/.virtualenvs/forgeapp-env/bin/activate
echo $VIRTUAL_ENV
```

2. Permisos:
```bash
ls -la /home/ForgeApp/forgeApp/forgeapp/scripts/
ls -la /home/ForgeApp/forgeApp/forgeapp/logs/
```

3. Variables de entorno:
```bash
# Dentro del entorno virtual
source /home/ForgeApp/.virtualenvs/forgeapp-env/bin/activate
python -c "import os; print(os.environ.get('DJANGO_SETTINGS_MODULE'))"
```

4. Logs detallados:
```bash
# Ver los últimos errores
tail -n 50 /home/ForgeApp/forgeApp/forgeapp/logs/cron.log
tail -n 50 /home/ForgeApp/forgeApp/forgeapp/logs/django.log
```

## Notas importantes

1. Asegúrate de que todas las rutas usen el caso correcto (ForgeApp vs forgeapp)
2. El entorno virtual debe llamarse exactamente 'forgeapp-env'
3. Los logs se guardarán en `/home/ForgeApp/forgeApp/forgeapp/logs/`
4. El script necesita permisos de ejecución (chmod +x)
5. Los directorios necesitan permisos adecuados (chmod 755)
