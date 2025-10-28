"""
Configuración para testing que sobreescribe valores por defecto.
"""
from app.config import BaseConfig


class TestingConfig(BaseConfig):
    """Configuración específica para testing."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Deshabilitar CSRF en tests
    DB_NAME = 'test_economia_db'  # Base de datos separada para tests
