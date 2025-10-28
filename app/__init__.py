"""
Inicializador del paquete app.
Contiene la factory de la aplicación Flask y configuración inicial.
"""
from flask import Flask

def create_app(config_name='default'):
    """
    Factory pattern para crear la aplicación Flask.
    Args:
        config_name (str): Nombre de la configuración a usar ('default', 'development', 'production')
    Returns:
        Flask: Instancia configurada de la aplicación Flask
    """
    app = Flask(__name__)
    
    # Configuración inicial - será expandida en PRs posteriores
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Los blueprints se registrarán aquí en PRs posteriores
    
    return app