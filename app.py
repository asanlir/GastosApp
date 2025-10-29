"""
Punto de entrada principal de la aplicación Flask.

Este módulo mantiene compatibilidad con el runner tradicional `app.py`
mientras usa internamente el patrón factory de `create_app()`.

Uso:
    python app.py  # Inicia la aplicación en modo desarrollo

La aplicación se ejecuta en http://127.0.0.1:5000 con debug=True.
"""
import webbrowser
from threading import Thread
from app import create_app


def abrir_navegador():
    """
    Abre el navegador web por defecto apuntando a la aplicación.

    Se ejecuta después de iniciar el servidor Flask para proporcionar
    una mejor experiencia de usuario al abrir automáticamente la app.
    """
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    app = create_app('development')
    app.run(debug=True)
