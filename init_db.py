"""
Script para inicializar la base de datos SIN depender de archivos .sql externos (repo público).

Seguridad primero:
- No borra datos ni tablas existentes.
- Usa CREATE DATABASE/TABLE IF NOT EXISTS y crea índices/constraints si faltan.
- Bloquea si detecta datos en la BD objetivo, salvo que se indique --force.
"""
import argparse
import sys
from datetime import datetime
import pymysql

from app.config import DefaultConfig


def _exec(cursor, sql: str):
    """Ejecuta un SQL mostrando feedback. Ignora errores benignos de duplicados.

    No lanza si el error es por entidad ya existente (índice/clave duplicada).
    """
    try:
        cursor.execute(sql)
        preview = sql.replace("\n", " ")[:80]
        print(f"✅ Ejecutado: {preview}...")
    except pymysql.err.OperationalError as e:
        # MySQL 1061: Duplicate key name, 1826: Duplicate foreign key name
        if getattr(e, 'args', [None])[0] in (1061, 1826):
            print(f"ℹ️  Ya existía, omitido: {sql.splitlines()[0][:60]}...")
        else:
            raise
    except pymysql.err.InternalError as e:
        if getattr(e, 'args', [None])[0] in (1007,):  # ER_DB_CREATE_EXISTS
            print("ℹ️  Base de datos ya existía, omitido.")
        else:
            raise


def check_database_has_data(cursor, db_name: str) -> bool:
    """Verifica si la base de datos destino existe y contiene datos relevantes."""
    try:
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        if not cursor.fetchone():
            return False  # La base no existe aún

        cursor.execute(f"USE `{db_name}`")

        # Si no hay tablas, es seguro
        cursor.execute("SHOW TABLES")
        if not cursor.fetchall():
            return False

        # Revisar conteos en tablas clave si existen
        for table in ("gastos", "categorias", "presupuesto"):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                if count and count > 0:
                    return True
            except pymysql.err.ProgrammingError:
                # Tabla no existe aún
                continue
        return False
    except pymysql.err.ProgrammingError:
        # Problemas de uso/tabla inexistente
        return False


def create_schema(cursor, db_name: str):
    """Crea la base y el esquema mínimo para ejecutar la app."""
    _exec(cursor, (
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    ))
    _exec(cursor, f"USE `{db_name}`;")

    # categorias
    _exec(cursor, (
        """
        CREATE TABLE IF NOT EXISTS categorias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    ))

    # gastos (FK a categorias.nombre con ON UPDATE CASCADE)
    _exec(cursor, (
        """
        CREATE TABLE IF NOT EXISTS gastos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            categoria VARCHAR(50) NOT NULL,
            descripcion TEXT,
            monto DECIMAL(10,2) NOT NULL,
            mes VARCHAR(20) NOT NULL,
            anio INT NOT NULL,
            CONSTRAINT gastos_ibfk_1
                FOREIGN KEY (categoria) REFERENCES categorias(nombre)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    ))

    # Índices gastos (algunos pueden fallar si ya existen → ignoramos 1061)
    for idx_sql in (
        "CREATE INDEX idx_categoria ON gastos (categoria);",
        "CREATE INDEX idx_mes_anio ON gastos (mes, anio);",
        "CREATE INDEX idx_anio_mes ON gastos (anio, mes);",
        "CREATE INDEX idx_anio ON gastos (anio);",
        "CREATE INDEX idx_categoria_anio_mes ON gastos (categoria, anio, mes);",
    ):
        try:
            _exec(cursor, idx_sql)
        except pymysql.Error as e:  # Seguridad adicional
            if getattr(e, 'args', [None])[0] != 1061:
                raise

    # presupuesto
    _exec(cursor, (
        """
        CREATE TABLE IF NOT EXISTS presupuesto (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mes VARCHAR(20) NOT NULL,
            anio INT NOT NULL,
            monto DECIMAL(10,2) NOT NULL,
            fecha_cambio DATETIME NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    ))

    for idx_sql in (
        "CREATE INDEX idx_presupuesto_mes_anio ON presupuesto (mes, anio);",
        "CREATE INDEX idx_presupuesto_anio_mes ON presupuesto (anio, mes);",
    ):
        try:
            _exec(cursor, idx_sql)
        except pymysql.Error as e:
            if getattr(e, 'args', [None])[0] != 1061:
                raise


def seed_sample_data(cursor, db_name: str):
    """Inserta datos de ejemplo seguros (categorías y un presupuesto actual)."""
    _exec(cursor, f"USE `{db_name}`;")

    categorias = ['Alquiler', 'Facturas', 'Compra', 'Gasolina']
    for cat in categorias:
        cursor.execute(
            "INSERT IGNORE INTO categorias (nombre) VALUES (%s);", (cat,))

    mes_actual = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ][datetime.now().month - 1]
    anio_actual = datetime.now().year
    # Evitar duplicado exacto
    cursor.execute(
        "SELECT id FROM presupuesto WHERE mes=%s AND anio=%s LIMIT 1;",
        (mes_actual, anio_actual)
    )
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO presupuesto (mes, anio, monto, fecha_cambio) VALUES (%s, %s, %s, NOW());",
            (mes_actual, anio_actual, 1000.00)
        )


def init_database(db_name: str, force: bool = False, with_sample: bool = False):
    """Inicializa la base de datos objetivo de forma segura para el repo público."""
    # Conectar sin seleccionar BD
    conn = pymysql.connect(
        host=DefaultConfig.DB_HOST,
        user=DefaultConfig.DB_USER,
        password=DefaultConfig.DB_PASSWORD,
        port=DefaultConfig.DB_PORT,
    )
    cursor = conn.cursor()

    # PROTECCIÓN: Bloquear si ya hay datos, salvo --force
    if not force and check_database_has_data(cursor, db_name):
        print("\n" + "="*70)
        print("⛔ ERROR: La base de datos contiene datos existentes")
        print("="*70)
        print("\n❌ Este script NO debe ejecutarse sobre una BD con datos.")
        print("   Riesgo: Podría causar pérdida de información.\n")
        print("Sugerencias:")
        print("  - Usa scripts de migración específicos para cambios en producción.")
        print("  - Si comprendes los riesgos, puedes usar --force (no borra datos, solo ignora este aviso).\n")
        cursor.close()
        conn.close()
        sys.exit(1)

    print("\n🔧 Creando esquema mínimo en la BD:", db_name)
    create_schema(cursor, db_name)

    if with_sample:
        print("\n🌱 Insertando datos de ejemplo seguros...")
        seed_sample_data(cursor, db_name)

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ Base de datos inicializada correctamente (sin borrar datos existentes)")


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Inicializa la BD para el repo público, sin .sql.")
    parser.add_argument("--db-name", dest="db_name", default=DefaultConfig.DB_NAME,
                        help="Nombre de la base de datos destino (por defecto: valor de config DB_NAME)")
    parser.add_argument("--force", action="store_true",
                        help="Ignora la detección de datos existentes (NO borra datos)")
    parser.add_argument("--seed-sample", action="store_true",
                        help="Inserta categorías y un presupuesto de ejemplo")
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()

    print("\n" + "="*70)
    print("⚠️  ⚠️  ⚠️  ADVERTENCIA CRÍTICA ⚠️  ⚠️  ⚠️")
    print("="*70)
    print("\nEste script SOLO debe usarse para INICIALIZAR una base de datos NUEVA.")
    print("No realiza DROP ni TRUNCATE, pero puede CREAR tablas e ÍNDICES.")
    print("\nObjetivo:", args.db_name)
    print("\n¿Estás COMPLETAMENTE seguro de que quieres continuar?")
    print("Escribe 'INICIALIZAR' (en mayúsculas) para continuar, o cualquier otra cosa para cancelar.\n")

    confirm_init = input("Tu respuesta: ").strip()
    if confirm_init != 'INICIALIZAR':
        print("\n✅ Operación cancelada correctamente. Tu base de datos está segura.")
        sys.exit(0)

    if args.force:
        print("\n" + "="*70)
        print("⚠️  MODO --force ACTIVADO")
        print("="*70)
        print("\nIgnorará la detección de datos existentes (no borra datos).")
        confirm = input("\n¿Estás seguro? Escribe 'SI' para continuar: ")
        if confirm != 'SI':
            print("❌ Operación cancelada.")
            sys.exit(0)

    init_database(db_name=args.db_name, force=args.force,
                  with_sample=args.seed_sample)
