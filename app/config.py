"""
Configuración de la aplicación para diferentes entornos.
"""
import os
from dotenv import load_dotenv

# Importar utilidades para modo frozen
try:
    from app.frozen_utils import is_frozen, get_env_file
except ImportError:
    # Fallback si no existe el módulo
    def is_frozen():
        return False

    def get_env_file():
        return '.env'

# Cargar variables de entorno
# En modo frozen, cargar .env.exe empaquetado
# En desarrollo, cargar .env del proyecto
env_file = get_env_file()
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Si no existe el archivo, cargar por defecto
    load_dotenv()


class BaseConfig:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-temporal')

    # Configuración de base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'economia_db')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))

    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(BaseConfig):
    """Configuración de desarrollo"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(BaseConfig):
    """Configuración de producción"""
    DEBUG = False
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')

    # Validar SECRET_KEY en producción
    def __init__(self):
        if self.SECRET_KEY == 'dev-key-temporal':
            raise ValueError(
                "SEGURIDAD: Debes configurar SECRET_KEY en .env para producción. "
                "Genera una con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )


# Alias para configuración por defecto
DefaultConfig = DevelopmentConfig


class TestingConfig(BaseConfig):
    """Configuración específica para testing."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Deshabilitar CSRF en tests
    DB_NAME = 'test_economia_db'  # Base de datos separada para tests
