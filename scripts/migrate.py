"""
Runner seguro de migraciones no destructivas para el repositorio público.

Ejecuta scripts de migrations/ en orden secuencial (001_, 002_, ...).
Flags:
  --dry-run: muestra qué haría sin ejecutar.
  --db-name: selecciona BD objetivo (por defecto: DefaultConfig.DB_NAME).
  --force: omite confirmación interactiva.

Seguridad:
- Solo ejecuta archivos .py que empiecen con XXX_ (número).
- Requiere confirmación interactiva salvo --force.
- No hace DROP/TRUNCATE; las migraciones deben ser idempotentes.
"""
import pymysql
from app.config import DefaultConfig
import argparse
import os
import sys
from pathlib import Path

# Ajustar path para importar app.config
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def discover_migrations(migrations_dir: Path):
    """Devuelve lista de scripts de migración ordenados por prefijo numérico."""
    if not migrations_dir.exists():
        return []
    files = [
        f for f in migrations_dir.iterdir()
        if f.is_file() and f.suffix == ".py" and f.stem[0].isdigit()
    ]
    return sorted(files, key=lambda x: x.stem)


def run_migration_script(script_path: Path, db_params: dict, dry_run: bool):
    """Ejecuta un script de migración pasándole parámetros de BD como env vars."""
    if dry_run:
        print(f"[DRY-RUN] Would execute: {script_path.name}")
        return

    # Las migraciones se importan dinámicamente y llaman a su main()
    # o bien se ejecutan como subprocess con env vars.
    # Aquí usamos subprocess para evitar problemas de importación cíclica.
    import subprocess
    env = os.environ.copy()
    env.update({
        "DB_HOST": db_params["host"],
        "DB_USER": db_params["user"],
        "DB_PASSWORD": db_params["password"],
        "DB_NAME": db_params["database"],
        "DB_PORT": str(db_params["port"]),
    })
    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Error ejecutando {script_path.name}:")
        print(result.stderr)
        sys.exit(1)
    else:
        print(result.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta migraciones no destructivas de BD en orden."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué migraciones se ejecutarían sin aplicarlas.",
    )
    parser.add_argument(
        "--db-name",
        default=DefaultConfig.DB_NAME,
        help=f"Nombre de la BD objetivo (por defecto: {DefaultConfig.DB_NAME}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Omitir confirmación interactiva.",
    )
    args = parser.parse_args()

    migrations_dir = ROOT / "scripts" / "migrations"
    scripts = discover_migrations(migrations_dir)

    if not scripts:
        print("ℹ️  No hay migraciones pendientes en scripts/migrations/.")
        return

    print("\n" + "="*70)
    print("🔄 RUNNER DE MIGRACIONES")
    print("="*70)
    print(f"\nBD objetivo: {args.db_name}")
    print(
        f"Modo: {'DRY-RUN (sin cambios)' if args.dry_run else 'EJECUCIÓN REAL'}")
    print(f"\nMigraciones a ejecutar ({len(scripts)}):")
    for s in scripts:
        print(f"  - {s.name}")

    if not args.dry_run and not args.force:
        print("\n⚠️  Esto aplicará cambios no destructivos (CREATE INDEX, etc.).")
        confirm = input("\n¿Continuar? Escribe 'SI' para confirmar: ").strip()
        if confirm != "SI":
            print("❌ Operación cancelada.")
            sys.exit(0)

    db_params = {
        "host": DefaultConfig.DB_HOST,
        "user": DefaultConfig.DB_USER,
        "password": DefaultConfig.DB_PASSWORD,
        "database": args.db_name,
        "port": DefaultConfig.DB_PORT,
    }

    # Comprobar conectividad
    if not args.dry_run:
        try:
            conn = pymysql.connect(**db_params, connect_timeout=5)
            conn.close()
        except pymysql.Error as e:
            print(f"\n❌ No se puede conectar a la BD: {e}")
            sys.exit(1)

    print("\n" + "-"*70)
    for script in scripts:
        run_migration_script(script, db_params, args.dry_run)

    if args.dry_run:
        print("\n✅ DRY-RUN completo (sin cambios aplicados).")
    else:
        print("\n✅ Migraciones aplicadas correctamente.")


if __name__ == "__main__":
    main()
