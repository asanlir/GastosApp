"""
Script para restaurar un backup de la base de datos.
"""
import pymysql
import gzip
import sys
import os
from app.config import DefaultConfig


def restore_backup(backup_file):
    """Restaura un backup de la base de datos."""
    print(f"🔄 Restaurando backup desde: {backup_file}")

    # Verificar que el archivo existe
    if not os.path.exists(backup_file):
        print(f"❌ Error: El archivo {backup_file} no existe")
        return False

    # Conectar a MySQL
    try:
        conn = pymysql.connect(
            host=DefaultConfig.DB_HOST,
            user=DefaultConfig.DB_USER,
            password=DefaultConfig.DB_PASSWORD,
            port=DefaultConfig.DB_PORT
        )
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return False

    cursor = conn.cursor()

    # Seleccionar la base de datos
    try:
        cursor.execute("USE economia_db;")
        print("✓ Base de datos seleccionada")
    except Exception as e:
        print(f"❌ Error seleccionando BD: {e}")
        return False

    # Leer el archivo comprimido o sin comprimir
    try:
        print("📖 Leyendo archivo de backup...")
        # Intentar primero como gzip
        try:
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                sql_content = f.read()
            print(
                f"✓ Archivo gzip leído correctamente ({len(sql_content)} caracteres)")
        except (gzip.BadGzipFile, OSError):
            # Si falla, intentar como archivo de texto plano con diferentes encodings
            print("ℹ️  No es gzip, intentando como texto plano...")
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for enc in encodings:
                try:
                    with open(backup_file, 'r', encoding=enc) as f:
                        sql_content = f.read()
                    print(
                        f"✓ Archivo de texto leído correctamente con {enc} ({len(sql_content)} caracteres)")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(
                    "No se pudo decodificar el archivo con ningún encoding")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return False

    # Ejecutar cada comando SQL
    print("⚙️  Ejecutando comandos SQL...")
    commands = [cmd.strip() for cmd in sql_content.split(';\n') if cmd.strip()]
    total = len(commands)
    print(f"Total de comandos a ejecutar: {total}")

    ejecutados = 0
    errores = 0

    for i, command in enumerate(commands, 1):
        try:
            cursor.execute(command)
            ejecutados += 1
            if i % 50 == 0:
                print(
                    f"  Progreso: {i}/{total} comandos ({ejecutados} ok, {errores} errores)")
        except pymysql.Error as e:
            errores += 1
            if errores <= 5:  # Solo mostrar los primeros 5 errores
                print(f"⚠️  Error en comando {i}: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(
        f"\n✅ Restauración completada: {ejecutados} comandos ejecutados, {errores} errores")
    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        backup_file = sys.argv[1]
    else:
        # Usar el backup más reciente
        backup_file = 'scripts/backups/daily/economia_db_daily_2025-10-30_08-33-30.sql.gz'

    restore_backup(backup_file)
