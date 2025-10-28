"""
Script para recuperar datos desde los logs binarios de MySQL.
"""
import subprocess
import sys

# Lista de logs que queremos procesar (los que tienen más de 1000 bytes)
logs_to_check = ['PC-LIROLA-bin.000221', 'PC-LIROLA-bin.000255']

print("Intentando recuperar datos de los logs binarios...")
print("=" * 80)

for log_file in logs_to_check:
    print(f"\nProcesando {log_file}...")
    try:
        # Intentar extraer eventos del log binario
        cmd = f'mysql -u root -p -e "SHOW BINLOG EVENTS IN \'{log_file}\';" > binlog_{log_file}.txt'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Log {log_file} exportado a binlog_{log_file}.txt")
        else:
            print(f"✗ Error al procesar {log_file}: {result.stderr}")
    except Exception as e:
        print(f"✗ Excepción al procesar {log_file}: {e}")

print("\n" + "=" * 80)
print("Proceso completado. Revisa los archivos generados.")
