"""
Script para intentar recuperar datos usando el comando SHOW BINLOG EVENTS de MySQL.
Este script extrae información de los logs binarios y la guarda en archivos de texto.
"""
import os
import subprocess
import getpass

# Pedir contraseña de root
print("Este script necesita la contraseña de root de MySQL para acceder a los logs binarios.")
root_password = getpass.getpass("Contraseña de root de MySQL: ")

# Logs que queremos procesar
logs_importantes = [
    'PC-LIROLA-bin.000221',  # 1194 bytes - contiene Write_rows
    'PC-LIROLA-bin.000255',  # 3575 bytes - contiene Update_rows
]

print("\nExtrayendo eventos de los logs binarios...")
print("=" * 80)

for log_file in logs_importantes:
    print(f"\nProcesando {log_file}...")
    output_file = f"binlog_events_{log_file}.txt"

    # Comando para extraer TODOS los eventos del log
    cmd = [
        'mysql',
        '-u', 'root',
        f'-p{root_password}',
        '-e', f"SHOW BINLOG EVENTS IN '{log_file}';"
    ]

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

        if result.returncode == 0:
            file_size = os.path.getsize(output_file)
            print(
                f"✓ Eventos de {log_file} guardados en {output_file} ({file_size} bytes)")
        else:
            print(f"✗ Error al procesar {log_file}: {result.stderr}")

    except Exception as e:
        print(f"✗ Excepción al procesar {log_file}: {e}")

print("\n" + "=" * 80)
print("Extracción completada.")
print("\nAhora necesitamos usar mysqlbinlog con privilegios de administrador")
print("para obtener los datos reales de los eventos Write_rows.")
print("\nPor favor, ejecuta el siguiente comando en PowerShell como Administrador:")
print()
print('cd "C:\\Program Files\\MySQL\\MySQL Server 9.1\\bin"')
print('mysqlbinlog --verbose --base64-output=DECODE-ROWS \\')
print('  "C:\\ProgramData\\MySQL\\MySQL Server 9.1\\Data\\PC-LIROLA-bin.000221" \\')
print('  > "C:\\Users\\alex0\\Documents\\Economía\\Gastos\\Casa\\recovered_data.sql"')
