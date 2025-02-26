#!/usr/bin/env python
"""
Script para verificar que todo esté listo para el despliegue en PythonAnywhere.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

# Colores para la salida
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(message, status, details=None):
    """Imprime un mensaje de estado con formato."""
    status_color = {
        'OK': Colors.OKGREEN,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.FAIL,
        'INFO': Colors.OKBLUE
    }
    
    print(f"{message:.<50} {status_color.get(status, '')}{status}{Colors.ENDC}")
    if details:
        print(f"  {details}")

def check_file_exists(file_path, required=True):
    """Verifica si un archivo existe."""
    exists = os.path.exists(file_path)
    status = 'OK' if exists else ('ERROR' if required else 'WARNING')
    print_status(f"Verificando {file_path}", status)
    return exists

def check_django_settings():
    """Verifica la configuración de Django."""
    try:
        # Intentar importar settings
        from django.conf import settings
        
        # Verificar DEBUG
        debug_status = 'WARNING' if settings.DEBUG else 'OK'
        print_status("Verificando DEBUG", debug_status, 
                    "DEBUG está activado. Desactívalo en producción." if settings.DEBUG else None)
        
        # Verificar ALLOWED_HOSTS
        allowed_hosts_status = 'OK' if settings.ALLOWED_HOSTS and '*' not in settings.ALLOWED_HOSTS else 'WARNING'
        print_status("Verificando ALLOWED_HOSTS", allowed_hosts_status,
                    "ALLOWED_HOSTS contiene '*'. Especifica los hosts permitidos en producción." 
                    if '*' in settings.ALLOWED_HOSTS else None)
        
        # Verificar configuración de archivos estáticos
        static_status = 'OK' if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT else 'WARNING'
        print_status("Verificando STATIC_ROOT", static_status,
                    "STATIC_ROOT no está configurado." if not (hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT) else None)
        
        # Verificar configuración de Mercado Pago
        mp_status = 'OK' if all([
            hasattr(settings, 'MP_PUBLIC_KEY') and settings.MP_PUBLIC_KEY,
            hasattr(settings, 'MP_ACCESS_TOKEN') and settings.MP_ACCESS_TOKEN,
            hasattr(settings, 'MP_CLIENT_ID') and settings.MP_CLIENT_ID,
            hasattr(settings, 'MP_CLIENT_SECRET') and settings.MP_CLIENT_SECRET
        ]) else 'WARNING'
        print_status("Verificando configuración de Mercado Pago", mp_status,
                    "Faltan algunas configuraciones de Mercado Pago." if mp_status != 'OK' else None)
        
        # Verificar middleware CSP
        csp_middleware = 'core.middleware.MercadoPagoCSPMiddleware'
        csp_status = 'OK' if csp_middleware in settings.MIDDLEWARE else 'WARNING'
        print_status("Verificando middleware CSP", csp_status,
                    f"El middleware {csp_middleware} no está en MIDDLEWARE." if csp_status != 'OK' else None)
        
        return True
    except Exception as e:
        print_status("Verificando configuración de Django", 'ERROR', str(e))
        return False

def check_requirements():
    """Verifica que todos los requisitos estén instalados."""
    try:
        # Verificar si existe requirements.txt
        if not check_file_exists('requirements.txt'):
            return False
        
        # Leer requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Verificar cada requisito
        all_installed = True
        for req in requirements:
            # Extraer el nombre del paquete (sin versión)
            package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
            
            try:
                importlib.import_module(package_name)
                print_status(f"Verificando {package_name}", 'OK')
            except ImportError:
                print_status(f"Verificando {package_name}", 'WARNING', "No instalado o no importable.")
                all_installed = False
        
        return all_installed
    except Exception as e:
        print_status("Verificando requisitos", 'ERROR', str(e))
        return False

def check_static_files():
    """Verifica la configuración de archivos estáticos."""
    try:
        # Verificar si existe el directorio staticfiles
        staticfiles_exists = os.path.exists('staticfiles')
        status = 'OK' if staticfiles_exists else 'WARNING'
        print_status("Verificando directorio staticfiles", status,
                    "El directorio staticfiles no existe. Ejecuta 'python manage.py collectstatic'." if not staticfiles_exists else None)
        
        # Verificar si existe el directorio media
        media_exists = os.path.exists('media')
        status = 'OK' if media_exists else 'WARNING'
        print_status("Verificando directorio media", status,
                    "El directorio media no existe." if not media_exists else None)
        
        return staticfiles_exists
    except Exception as e:
        print_status("Verificando archivos estáticos", 'ERROR', str(e))
        return False

def check_env_file():
    """Verifica el archivo .env."""
    try:
        # Verificar si existe el archivo .env
        if not check_file_exists('.env'):
            return False
        
        # Leer el archivo .env
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Verificar variables requeridas
        required_vars = [
            'SECRET_KEY',
            'DEBUG',
            'MP_PUBLIC_KEY',
            'MP_ACCESS_TOKEN',
            'MP_CLIENT_ID',
            'MP_CLIENT_SECRET',
            'SITE_URL',
            'MP_WEBHOOK_ENABLED',
            'MP_SANDBOX_MODE'
        ]
        
        all_vars_present = True
        for var in required_vars:
            var_present = var in env_content
            status = 'OK' if var_present else 'WARNING'
            print_status(f"Verificando {var} en .env", status,
                        f"La variable {var} no está en .env." if not var_present else None)
            all_vars_present = all_vars_present and var_present
        
        # Verificar DEBUG en producción
        if 'DEBUG=True' in env_content:
            print_status("Verificando DEBUG en .env", 'WARNING', 
                        "DEBUG está establecido como True. Cámbialo a False para producción.")
        
        # Verificar SITE_URL
        if 'SITE_URL=http://localhost' in env_content or 'SITE_URL=https://localhost' in env_content:
            print_status("Verificando SITE_URL en .env", 'WARNING',
                        "SITE_URL está configurado como localhost. Cámbialo a tu dominio de PythonAnywhere.")
        
        return all_vars_present
    except Exception as e:
        print_status("Verificando archivo .env", 'ERROR', str(e))
        return False

def main():
    """Función principal."""
    print(f"\n{Colors.HEADER}Verificando preparación para despliegue en PythonAnywhere{Colors.ENDC}\n")
    
    # Verificar archivos esenciales
    print(f"\n{Colors.BOLD}Verificando archivos esenciales:{Colors.ENDC}")
    check_file_exists('manage.py')
    check_file_exists('core/settings.py')
    check_file_exists('core/wsgi.py')
    check_file_exists('core/urls.py')
    check_file_exists('requirements.txt')
    check_file_exists('.env')
    check_file_exists('pythonanywhere_wsgi.py', required=False)
    check_file_exists('pythonanywhere_deployment_guide.md', required=False)
    
    # Verificar configuración de Django
    print(f"\n{Colors.BOLD}Verificando configuración de Django:{Colors.ENDC}")
    check_django_settings()
    
    # Verificar requisitos
    print(f"\n{Colors.BOLD}Verificando requisitos:{Colors.ENDC}")
    check_requirements()
    
    # Verificar archivos estáticos
    print(f"\n{Colors.BOLD}Verificando archivos estáticos:{Colors.ENDC}")
    check_static_files()
    
    # Verificar archivo .env
    print(f"\n{Colors.BOLD}Verificando archivo .env:{Colors.ENDC}")
    check_env_file()
    
    print(f"\n{Colors.HEADER}Verificación completada{Colors.ENDC}")
    print(f"\nConsulta la guía de despliegue en pythonanywhere_deployment_guide.md para más detalles.")

if __name__ == "__main__":
    main()
