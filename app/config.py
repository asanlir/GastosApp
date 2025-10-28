"""
Configuración de la aplicación para diferentes entornos.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
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


class DevelopmentConfig(BaseConfig):
    """Configuración de desarrollo"""
    DEBUG = True


class ProductionConfig(BaseConfig):
    """Configuración de producción"""
    DEBUG = False


# Alias para configuración por defecto
DefaultConfig = DevelopmentConfig


class TestingConfig(BaseConfig):
    """Configuración específica para testing."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Deshabilitar CSRF en tests
    DB_NAME = 'test_economia_db'  # Base de datos separada para tests
