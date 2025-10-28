"""
Archivo runner mínimo: se mantiene `app.py` como punto de entrada compatible.
Usa la factory `create_app` y arranca la aplicación en modo desarrollo.
"""
import webbrowser
from threading import Thread
from app import create_app


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    app = create_app('development')
    app.run(debug=True)
