"""
Script para migrar datos de economia_db a economia_db_prod.

Este script:
1. Verifica que economia_db existe y tiene datos
2. Crea economia_db_prod si no existe
3. Copia todos los datos de economia_db a economia_db_prod
4. Verifica que la migración fue exitosa

Uso:
    python scripts/migrate_to_prod_db.py
"""

import pymysql
import os
from dotenv import load_dotenv

# Colores para terminal


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(message):
    """Imprime un paso del proceso"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {message}{Colors.END}")


def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_warning(message):
    """Imprime una advertencia"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message):
    """Imprime un error"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def get_db_config():
    """Obtiene la configuración de la base de datos"""
    load_dotenv()
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 3306))
    }


def check_database_exists(config, db_name):
    """Verifica si una base de datos existe"""
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print_error(f"Error al verificar base de datos: {e}")
        return False


def count_records(config, db_name):
    """Cuenta registros en las tablas principales"""
    try:
        config_with_db = config.copy()
        config_with_db['database'] = db_name
        conn = pymysql.connect(**config_with_db)
        cursor = conn.cursor()

        counts = {}
        tables = ['gastos', 'categorias', 'presupuesto']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count

        cursor.close()
        conn.close()
        return counts
    except Exception as e:
        print_error(f"Error al contar registros: {e}")
        return None


def migrate_database(config, source_db, target_db):
    """Migra datos de una base de datos a otra"""
    print_step(f"Migrando datos de '{source_db}' a '{target_db}'...")

    try:
        # Conectar sin especificar base de datos
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        # Verificar que la BD origen existe
        if not check_database_exists(config, source_db):
            print_error(f"La base de datos '{source_db}' no existe")
            return False

        # Verificar si la BD destino existe
        if check_database_exists(config, target_db):
            print_warning(f"La base de datos '{target_db}' ya existe")
            response = input(f"¿Quieres BORRARLA y recrearla? (s/n): ")

            if response.lower() != 's':
                print("Migración cancelada")
                return False

            print(f"Borrando '{target_db}'...")
            cursor.execute(f"DROP DATABASE {target_db}")

        # Crear BD destino
        print(f"Creando '{target_db}'...")
        cursor.execute(
            f"CREATE DATABASE {target_db} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print_success(f"Base de datos '{target_db}' creada")

        # Obtener lista de tablas
        cursor.execute(f"USE {source_db}")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        print(f"\nTablas a migrar: {', '.join(tables)}")

        # Copiar cada tabla
        for table in tables:
            print(f"\nCopiando tabla '{table}'...")

            # Obtener estructura de la tabla
            cursor.execute(f"SHOW CREATE TABLE {source_db}.{table}")
            create_statement = cursor.fetchone()[1]

            # Crear tabla en BD destino
            cursor.execute(f"USE {target_db}")
            cursor.execute(create_statement)

            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {source_db}.{table}")
            count = cursor.fetchone()[0]

            if count > 0:
                # Copiar datos
                cursor.execute(
                    f"INSERT INTO {target_db}.{table} "
                    f"SELECT * FROM {source_db}.{table}"
                )
                print_success(f"  {count} registros copiados")
            else:
                print(f"  Tabla vacía (0 registros)")

        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print_error(f"Error durante la migración: {e}")
        return False


def verify_migration(config, source_db, target_db):
    """Verifica que la migración fue exitosa"""
    print_step("Verificando migración...")

    source_counts = count_records(config, source_db)
    target_counts = count_records(config, target_db)

    if not source_counts or not target_counts:
        print_error("No se pudo verificar la migración")
        return False

    print("\n┌─────────────────┬──────────┬──────────┬────────┐")
    print("│ Tabla           │ Origen   │ Destino  │ Estado │")
    print("├─────────────────┼──────────┼──────────┼────────┤")

    all_match = True
    for table in source_counts.keys():
        source_count = source_counts[table]
        target_count = target_counts.get(table, 0)
        status = "✓" if source_count == target_count else "✗"

        if source_count != target_count:
            all_match = False

        print(
            f"│ {table:<15} │ {source_count:>8} │ {target_count:>8} │   {status}    │")

    print("└─────────────────┴──────────┴──────────┴────────┘")

    if all_match:
        print_success("\n✓ Migración completada exitosamente")
        print_success(
            f"Todos los datos han sido copiados de '{source_db}' a '{target_db}'")
        return True
    else:
        print_error("\n✗ La migración tiene discrepancias")
        return False


def main():
    """Función principal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("MIGRACIÓN DE BASE DE DATOS A PRODUCCIÓN")
    print(f"{'='*60}{Colors.END}\n")

    source_db = "economia_db"
    target_db = "economia_db_prod"

    # Obtener configuración
    config = get_db_config()

    # Verificar BD origen
    print_step(f"Verificando base de datos origen '{source_db}'...")
    if not check_database_exists(config, source_db):
        print_error(f"La base de datos '{source_db}' no existe")
        print("Asegúrate de tener datos en tu base de datos de desarrollo")
        return

    # Mostrar conteo de registros origen
    source_counts = count_records(config, source_db)
    if source_counts:
        print_success(f"Base de datos '{source_db}' encontrada:")
        for table, count in source_counts.items():
            print(f"  • {table}: {count} registros")

    # Confirmar migración
    print_warning(f"\nSe van a copiar todos los datos a '{target_db}'")
    response = input("¿Quieres continuar? (s/n): ")

    if response.lower() != 's':
        print("Migración cancelada")
        return

    # Realizar migración
    if migrate_database(config, source_db, target_db):
        # Verificar migración
        if verify_migration(config, source_db, target_db):
            print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
            print("✓ MIGRACIÓN COMPLETADA")
            print(f"{'='*60}{Colors.END}\n")

            print("Próximos pasos:")
            print(f"  1. El ejecutable usará '{target_db}' automáticamente")
            print(f"  2. Tu desarrollo seguirá usando '{source_db}'")
            print("  3. Ambas bases de datos son independientes")
            print("\nPuedes construir el ejecutable con:")
            print("  python scripts/build_exe.py\n")
    else:
        print_error("\nLa migración falló. Revisa los errores anteriores.")


if __name__ == '__main__':
    main()
