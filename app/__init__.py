"""
Inicializador del paquete app.
Contiene la factory de la aplicación Flask y configuración inicial.
"""
from flask import Flask
import os
import sys
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

    # Verificar si existe .env antes de inicializar BD
    if config_name != 'testing':
        from app.utils import env_file_exists

        # Si no existe .env, necesitamos redirigir a /setup
        # Pero no podemos hacer redirect aquí, así que registramos el blueprint primero
        # y la ruta /setup manejará la configuración inicial

        if env_file_exists():
            # Solo inicializar BD si .env existe
            try:
                from app.database import ensure_database_exists
                from app.exceptions import DatabaseError

                print("\n🔍 Verificando base de datos...")
                ensure_database_exists()
                print("✅ Base de datos lista\n")

            except DatabaseError as e:
                print(f"\n{e}\n", file=sys.stderr)
                print("❌ No se pudo inicializar la base de datos.", file=sys.stderr)
                print("   Por favor revisa tu configuración en .env\n",
                    file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}\n", file=sys.stderr)
                sys.exit(1)
        else:
            print("\n⚠️  No se encontró archivo .env")
            print("📋 Abre http://127.0.0.1:5000/setup para configurar la aplicación\n")

    # Registrar blueprints
    # Importar el módulo donde definimos el blueprint
    from app.routes import main as main_module

    # Registrar el blueprint principal
    app.register_blueprint(main_module.main_bp)

    # Middleware para redirigir a /setup si no existe .env
    if config_name != 'testing':
        @app.before_request
        def check_env_file():
            from flask import request, redirect, url_for
            from app.utils import env_file_exists

            # Permitir acceso a /setup y recursos estáticos sin .env
            if request.endpoint in ['main.setup', 'main.test_setup', 'static'] or request.path.startswith('/static/'):
                return None

            # Si no existe .env y no estamos en /setup, redirigir
            if not env_file_exists():
                return redirect(url_for('main.setup'))

            return None

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
