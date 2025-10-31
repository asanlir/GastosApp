"""
Inicializador del paquete app.
Contiene la factory de la aplicación Flask y configuración inicial.
"""
from flask import Flask
import os
from app.logging_config import setup_logging

# Importar utilidades para modo frozen
try:
    from app.frozen_utils import resource_path, is_frozen
except ImportError:
    # Fallback si no existe el módulo
    def resource_path(path):
        return path

    def is_frozen():
        return False


def create_app(config_name='default'):
    """
    Factory pattern para crear la aplicación Flask.
    Args:
        config_name (str): Nombre de la configuración a usar ('default', 'development', 'production')
    Returns:
        Flask: Instancia configurada de la aplicación Flask
    """
    # Configurar rutas según modo de ejecución
    if is_frozen():
        # En modo frozen (ejecutable), usar rutas empaquetadas
        template_path = resource_path('templates')
        static_path = resource_path('static')
    else:
        # En desarrollo, usar rutas absolutas del proyecto
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

    mode = "FROZEN (ejecutable)" if is_frozen() else "desarrollo"
    app.logger.info(f"Aplicación Flask iniciada correctamente en modo {mode}")
    return app
