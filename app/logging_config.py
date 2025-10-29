"""
Configuración del sistema de logging para la aplicación.
"""
import logging
import logging.handlers
from pathlib import Path


def setup_logging(app):
    """
    Configura el sistema de logging para la aplicación Flask.

    Args:
        app: Instancia de la aplicación Flask
    """
    # Crear directorio de logs si no existe
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Obtener el nivel de logging desde la configuración
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))

    # Configurar formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para archivo (con rotación)
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'gastos.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Handler para consola (solo en desarrollo)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Configurar logger de la aplicación
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)

    if app.config.get('DEBUG', False):
        app.logger.addHandler(console_handler)

    # Suprimir logs excesivos de werkzeug en producción
    if not app.config.get('DEBUG', False):
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)

    app.logger.info(
        f"Sistema de logging inicializado - Nivel: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.

    Args:
        name: Nombre del módulo (usualmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
