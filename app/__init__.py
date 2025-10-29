"""
Inicializador del paquete app.
Contiene la factory de la aplicación Flask y configuración inicial.
"""
from flask import Flask
import os
from app.logging_config import setup_logging


def create_app(config_name='default'):
    """
    Factory pattern para crear la aplicación Flask.
    Args:
        config_name (str): Nombre de la configuración a usar ('default', 'development', 'production')
    Returns:
        Flask: Instancia configurada de la aplicación Flask
    """
    # Configura la ubicación de los templates y archivos estáticos usando ruta absoluta
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    template_path = os.path.join(parent_dir, 'templates')
    static_path = os.path.join(parent_dir, 'static')
    app = Flask(__name__, template_folder=template_path,
                static_folder=static_path)

    # Configuración inicial - será expandida en PRs posteriores
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')

    # Configurar logging
    setup_logging(app)

    # Registrar blueprints
    # Importar el módulo donde definimos el blueprint
    from app.routes import main as main_module

    # Registrar el blueprint principal
    app.register_blueprint(main_module.main_bp)

    # Crear aliases para mantener compatibilidad con endpoints existentes
    for rule, endpoint, methods in main_module.LEGACY_ROUTES:
        namespaced = f"{main_module.main_bp.name}.{endpoint}"
        view_func = app.view_functions.get(namespaced)
        if view_func:
            # Añadimos una regla duplicada con el endpoint original
            app.add_url_rule(rule, endpoint=endpoint,
                             view_func=view_func, methods=methods)

    app.logger.info("Aplicación Flask iniciada correctamente")
    return app
