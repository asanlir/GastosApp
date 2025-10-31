"""
Script para construir el ejecutable aislado de la aplicación de gastos.

Este script:
1. Verifica que .env.exe tenga una SECRET_KEY configurada
2. Permite elegir nombre e icono del ejecutable
3. Genera el ejecutable con PyInstaller usando app.spec
4. Crea la base de datos de producción si no existe
5. Muestra instrucciones de uso

Uso:
    python scripts/build_exe.py [--name NOMBRE] [--icon ICONO]
    
Ejemplos:
    python scripts/build_exe.py
    python scripts/build_exe.py --name MiGastos --icon pig.ico
"""

import os
import sys
import subprocess
import secrets
import argparse
from pathlib import Path

# Colores para terminal


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(message):
    """Imprime un paso del proceso"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {message}{Colors.END}")


def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_warning(message):
    """Imprime una advertencia"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message):
    """Imprime un error"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def check_env_file():
    """Verifica y configura el archivo .env.exe"""
    print_step("Verificando archivo .env.exe...")

    env_file = Path('.env.exe')

    if not env_file.exists():
        print_error(".env.exe no encontrado")
        print("Creando .env.exe desde plantilla...")
        # Aquí deberías tener una plantilla
        return False

    # Leer contenido
    content = env_file.read_text(encoding='utf-8')

    # Verificar SECRET_KEY
    if 'SECRET_KEY=CHANGE_THIS_IN_PRODUCTION' in content:
        print_warning("SECRET_KEY no configurada en .env.exe")
        response = input(
            "¿Quieres generar una SECRET_KEY automáticamente? (s/n): ")

        if response.lower() == 's':
            new_key = secrets.token_urlsafe(32)
            content = content.replace(
                'SECRET_KEY=CHANGE_THIS_IN_PRODUCTION',
                f'SECRET_KEY={new_key}'
            )
            env_file.write_text(content, encoding='utf-8')
            print_success(f"SECRET_KEY generada y guardada en .env.exe")
        else:
            print_error(
                "Debes configurar SECRET_KEY en .env.exe antes de continuar")
            return False

    print_success(".env.exe configurado correctamente")
    return True


def check_pyinstaller():
    """Verifica que PyInstaller esté instalado"""
    print_step("Verificando PyInstaller...")

    try:
        result = subprocess.run(
            ['pyinstaller', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"PyInstaller {version} instalado")
            return True
    except FileNotFoundError:
        pass

    print_error("PyInstaller no está instalado")
    print("Instálalo con: pip install pyinstaller")
    return False


def build_executable(exe_name='GastosApp', icon_path='static/calc.ico'):
    """Construye el ejecutable usando PyInstaller con configuración personalizada"""
    print_step(f"Construyendo ejecutable '{exe_name}.exe' con PyInstaller...")
    print("Esto puede tardar varios minutos...")

    # Verificar que el icono existe
    if not Path(icon_path).exists():
        print_warning(
            f"Icono '{icon_path}' no encontrado, usando icono por defecto")
        icon_path = 'static/calc.ico'

    print(f"  • Nombre: {exe_name}.exe")
    print(f"  • Icono: {icon_path}")

    try:
        # Construir comando de PyInstaller con configuración personalizada
        cmd = [
            'pyinstaller',
            '--name', exe_name,
            '--onefile',
            '--icon', icon_path,
            '--add-data', 'static;static',
            '--add-data', 'templates;templates',
            '--add-data', '.env.exe;.',
            '--hidden-import', 'pymysql',
            '--hidden-import', 'cryptography',
            '--hidden-import', 'cryptography.hazmat.backends',
            '--hidden-import', 'cryptography.hazmat.backends.openssl',
            '--hidden-import', 'cryptography.hazmat.primitives',
            '--hidden-import', 'cryptography.hazmat.primitives.asymmetric',
            '--hidden-import', 'cryptography.hazmat.primitives.asymmetric.rsa',
            '--hidden-import', 'cryptography.hazmat.primitives.asymmetric.padding',
            '--hidden-import', 'plotly',
            '--hidden-import', 'pandas',
            '--hidden-import', 'dotenv',
            '--collect-all', 'cryptography',
            '--exclude-module', 'pytest',
            '--exclude-module', 'tests',
            '--clean',
            '--noconfirm',
            'app.py'
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        print_success("Ejecutable construido exitosamente")
        return True

    except subprocess.CalledProcessError as e:
        print_error("Error al construir el ejecutable")
        print(e.stderr)
        return False


def check_database():
    """Verifica si existe la base de datos de producción"""
    print_step("Verificando base de datos de producción...")

    try:
        import pymysql
        from dotenv import load_dotenv

        # Cargar .env.exe para obtener configuración
        load_dotenv('.env.exe')

        db_name = os.getenv('DB_NAME', 'economia_db_prod')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')

        # Conectar sin especificar base de datos
        conn = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        # Verificar si existe la BD
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        exists = cursor.fetchone() is not None

        if not exists:
            print_warning(f"Base de datos '{db_name}' no existe")
            response = input("¿Quieres crearla ahora? (s/n): ")

            if response.lower() == 's':
                cursor.execute(
                    f"CREATE DATABASE {db_name} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                print_success(f"Base de datos '{db_name}' creada")

                print_warning(
                    f"\n⚠ IMPORTANTE: Debes inicializar la base de datos '{db_name}' "
                    "antes de usar el ejecutable."
                )
                print("Ejecuta:")
                print(f"  python init_db.py --db-name {db_name} --seed-sample")
        else:
            print_success(f"Base de datos '{db_name}' existe")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error al verificar la base de datos: {e}")
        return False


def print_instructions(exe_name='GastosApp'):
    """Imprime instrucciones finales"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("✓ EJECUTABLE CREADO EXITOSAMENTE")
    print(f"{'='*60}{Colors.END}\n")

    exe_path = Path(f'dist/{exe_name}.exe')
    if exe_path.exists():
        print(f"📦 Ubicación: {Colors.BOLD}{exe_path.absolute()}{Colors.END}\n")

    print(f"{Colors.BOLD}Características del ejecutable:{Colors.END}")
    print("  • Base de datos separada (economia_db_prod)")
    print("  • Configuración aislada (.env.exe empaquetado)")
    print("  • No afectado por cambios en el código fuente")
    print("  • Archivos estáticos y templates incluidos\n")

    print(f"{Colors.BOLD}Uso:{Colors.END}")
    print(f"  1. Ejecuta: dist\\{exe_name}.exe")
    print("  2. Abre el navegador en: http://127.0.0.1:5000")
    print("  3. Para detener: Ctrl+C en la consola\n")

    print(f"{Colors.BOLD}Notas importantes:{Colors.END}")
    print("  • El ejecutable usa su propia base de datos")
    print("  • Puedes seguir modificando el código sin afectar el .exe")
    print("  • Para actualizar el .exe, vuelve a ejecutar este script")
    print(f"  • Los logs se guardan en: logs/\n")


def main():
    """Función principal"""
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Construir ejecutable aislado de la aplicación de gastos'
    )
    parser.add_argument(
        '--name',
        default='GastosApp',
        help='Nombre del ejecutable (sin .exe). Por defecto: GastosApp'
    )
    parser.add_argument(
        '--icon',
        default='static/calc.ico',
        help='Ruta al icono (.ico). Por defecto: static/calc.ico'
    )
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("CONSTRUCCIÓN DE EJECUTABLE AISLADO")
    print(f"{'='*60}{Colors.END}\n")

    print(f"Configuración:")
    print(f"  • Nombre: {args.name}.exe")
    print(f"  • Icono: {args.icon}")

    # Verificaciones
    if not check_env_file():
        sys.exit(1)

    if not check_pyinstaller():
        sys.exit(1)

    # Construir con configuración personalizada
    if not build_executable(args.name, args.icon):
        sys.exit(1)

    # Verificar BD (opcional, no detiene el proceso)
    check_database()

    # Instrucciones
    print_instructions(args.name)


if __name__ == '__main__':
    main()
