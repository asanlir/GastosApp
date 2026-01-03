"""
Configuración del sistema de logging para la aplicación.
"""
import logging
import logging.handlers
from pathlib import Path
import os
from app.frozen_utils import is_frozen


def setup_logging(app):
    """
    Configura el sistema de logging para la aplicación Flask.

    Args:
        app: Instancia de la aplicación Flask
    """
    # Si ya hay handlers configurados (reloader de Werkzeug), no reconfigurar
    if app.logger.handlers:
        return

    # Obtener el nivel de logging desde la configuración
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))

    # Configurar formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # En modo testing, solo usar StreamHandler
    if app.config.get('TESTING', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        app.logger.setLevel(log_level)
        app.logger.addHandler(console_handler)
    else:
        # Crear directorio de logs si no existe
        # En modo frozen, usar el directorio del ejecutable
        if is_frozen():
            logs_dir = Path(os.path.dirname(
                os.path.abspath(__file__))).parent / 'logs'
        else:
            logs_dir = Path('logs')
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Handler para archivo (con rotación)
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'gastos.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        # Handler para consola
        # En modo frozen (ejecutable), solo mostrar WARNING o superior
        console_handler = logging.StreamHandler()
        if is_frozen():
            console_handler.setLevel(logging.WARNING)
        else:
            console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Configurar logger de la aplicación
        app.logger.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)

    # Suprimir logs excesivos de werkzeug
    if is_frozen():
        # En ejecutable, suprimir COMPLETAMENTE werkzeug y todos sus módulos en consola
        for logger_name in ['werkzeug', 'werkzeug.serving', 'werkzeug.wsgi']:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.setLevel(logging.CRITICAL)
            logger.propagate = False
    else:
        werkzeug_logger = logging.getLogger('werkzeug')
        if not app.config.get('DEBUG', False):
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


def print_operation(operation: str, details: str = ""):
    """
    Imprime un mensaje de operación en la consola con estilo.

    Solo se ejecuta en modo frozen (ejecutable).
    Mantiene un estilo visual consistente con los mensajes de inicio.

    Args:
        operation: Tipo de operación (ej: 'GASTO AGREGADO', 'GASTO MODIFICADO')
        details: Detalles adicionales (ej: descripción del gasto)
    """
    if is_frozen():
        # Mapeo de operaciones a emojis
        emojis = {
            'agregado': '✅',
            'modificado': '✏️ ',
            'eliminado': '🗑️ ',
            'categoría agregada': '📁',
            'categoría eliminada': '📁',
            'presupuesto actualizado': '💰',
            'error': '❌'
        }

        emoji = emojis.get(operation.lower(), '📝')
        print(f"{emoji} {operation}: {details}" if details else f"{emoji} {operation}")
