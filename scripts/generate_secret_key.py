"""
Script para generar una SECRET_KEY segura para Flask.

Uso:
    python scripts/generate_secret_key.py

El script genera una clave criptográficamente segura de 32 bytes
codificada en base64 URL-safe.
"""
import secrets


def generate_secret_key():
    """Genera una SECRET_KEY segura para Flask."""
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔑 GENERADOR DE SECRET_KEY PARA FLASK")
    print("="*70)

    key = generate_secret_key()

    print("\nTu nueva SECRET_KEY es:\n")
    print(f"SECRET_KEY={key}")
    print("\n📋 Copia esta línea en tu archivo .env")
    print("\n⚠️  IMPORTANTE:")
    print("   - NO compartas esta clave con nadie")
    print("   - NO la subas al repositorio")
    print("   - Usa una clave diferente para cada entorno")
    print("\n" + "="*70 + "\n")
