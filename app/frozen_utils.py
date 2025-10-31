"""
Utilidades para manejar recursos en modo frozen (PyInstaller).
"""
import sys
import os


def is_frozen():
    """
    Detecta si la aplicación está ejecutándose como ejecutable frozen (PyInstaller).

    Returns:
        bool: True si está frozen, False si está en desarrollo
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_base_path():
    """
    Obtiene el directorio base de la aplicación.

    En modo frozen: Retorna el directorio temporal de PyInstaller (_MEIPASS)
    En desarrollo: Retorna el directorio del proyecto

    Returns:
        str: Ruta absoluta al directorio base
    """
    if is_frozen():
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        return sys._MEIPASS
    else:
        # En desarrollo, usar el directorio del proyecto
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona tanto en desarrollo como en frozen.

    Args:
        relative_path (str): Ruta relativa al recurso desde la raíz del proyecto

    Returns:
        str: Ruta absoluta al recurso

    Examples:
        >>> resource_path('templates/index.html')
        'C:\\Users\\...\\templates\\index.html'  # En desarrollo
        'C:\\Users\\...\\Temp\\_MEI123456\\templates\\index.html'  # En frozen
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)


def get_env_file():
    """
    Obtiene la ruta al archivo .env correcto según el modo de ejecución.

    En modo frozen: Usa .env.exe empaquetado
    En desarrollo: Usa .env del proyecto

    Returns:
        str: Ruta absoluta al archivo .env
    """
    if is_frozen():
        # En modo frozen, usar .env.exe empaquetado
        return resource_path('.env.exe')
    else:
        # En desarrollo, usar .env del proyecto
        return os.path.join(get_base_path(), '.env')
