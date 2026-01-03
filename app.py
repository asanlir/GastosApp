"""
Punto de entrada principal de la aplicación Flask.

Este módulo mantiene compatibilidad con el runner tradicional `app.py`
mientras usa internamente el patrón factory de `create_app()`.

Uso:
    python app.py  # Inicia la aplicación en modo desarrollo
    Gastos.exe     # Inicia la aplicación desde ejecutable

La aplicación se ejecuta en http://127.0.0.1:5000
"""
import os
import sys
import webbrowser
from threading import Thread
from app import create_app

# Detectar si estamos en modo frozen (ejecutable)


def is_frozen():
    """Detecta si la aplicación está ejecutándose como ejecutable"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def abrir_navegador():
    """
    Abre el navegador web por defecto apuntando a la aplicación.

    Se ejecuta después de iniciar el servidor Flask para proporcionar
    una mejor experiencia de usuario al abrir automáticamente la app.
    """
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    try:
        # Configurar entorno según modo de ejecución
        if is_frozen():
            # En modo ejecutable, suprimir logs de werkzeug
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.CRITICAL)
            log.disabled = True

            # Modo ejecutable: usar producción y abrir navegador siempre
            print("="*60)
            print("🏠 Aplicación de Gastos Domésticos")
            print("="*60)
            print("\n⏳ Iniciando aplicación...")

            try:
                app = create_app('production')
                print("✓ Aplicación creada correctamente")
            except Exception as e:
                print(f"✗ Error al crear la aplicación: {e}")
                print(f"\nDetalles del error:")
                import traceback
                traceback.print_exc()
                input("\nPresiona Enter para cerrar...")
                sys.exit(1)

            # Abrir navegador después de un pequeño delay
            def delayed_browser():
                import time
                time.sleep(1.5)
                abrir_navegador()

            Thread(target=delayed_browser, daemon=True).start()

            # Ejecutar sin debug en producción
            print("✓ Servidor iniciado en: http://127.0.0.1:5000")
            print("✓ Abriendo navegador automáticamente...")
            print("\n⚠  Para detener el servidor, presiona Ctrl+C\n")

            try:
                app.run(debug=False, use_reloader=False)
            except Exception as e:
                print(f"\n✗ Error al ejecutar el servidor: {e}")
                import traceback
                traceback.print_exc()
                input("\nPresiona Enter para cerrar...")
                sys.exit(1)
        else:
            # Modo desarrollo: comportamiento normal con debug
            app = create_app('development')

            # Abrir navegador solo en el proceso principal (evita duplicación con el reloader)
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
                import time

                def delayed_browser():
                    time.sleep(1.5)
                    abrir_navegador()

                Thread(target=delayed_browser, daemon=True).start()

            app.run(debug=True)

    except Exception as e:
        print(f"\n✗ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para cerrar...")
        sys.exit(1)
