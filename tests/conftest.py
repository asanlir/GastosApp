"""
Test configuration file
"""
import os
import sys
import pytest
from app import create_app

# Añadir el directorio raíz al path para poder importar app
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Configuración de pytest
pytest_plugins = [
    "pytest_mock",
]


def pytest_configure(config):
    """Registrar marcadores personalizados."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring database"
    )


@pytest.fixture
def app():
    """Fixture que crea una instancia de la app en modo testing."""
    test_app = create_app('testing')
    test_app.config.update({
        'TESTING': True,
        'DB_NAME': 'test_economia_db',  # Usamos una BD de test separada
        'TEMPLATES_AUTO_RELOAD': True
    })
    return test_app


@pytest.fixture
def client(app):  # noqa: F811
    """Fixture que provee un cliente HTTP para hacer requests."""
    return app.test_client()


@pytest.fixture
def runner(app):  # noqa: F811
    """Fixture que provee un runner para ejecutar comandos CLI."""
    return app.test_cli_runner()
