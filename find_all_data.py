"""
Script para buscar datos en todos los logs binarios disponibles.
"""
import subprocess

print("Buscando logs con datos de gastos, categorías y presupuestos...")
print("=" * 80)

# Obtener lista de todos los logs
cmd = ['mysql', '-u', 'root', '-p', '-e', 'SHOW BINARY LOGS;']
result = subprocess.run(cmd, capture_output=True, text=True, check=False)

if result.returncode != 0:
    print("Error obteniendo lista de logs")
    exit(1)

# Extraer nombres de logs
lines = result.stdout.strip().split('\n')[1:]  # Skip header
logs = [line.split()[0] for line in lines if line.strip()]

print(f"Encontrados {len(logs)} logs binarios")
print("\nAnalizando cada log para encontrar operaciones de datos...")
print("-" * 80)

logs_with_data = []

for log in logs:
    # Buscar eventos Write_rows (INSERT) en cada log
    cmd = ['mysql', '-u', 'root', '-p', '-e',
           f"SHOW BINLOG EVENTS IN '{log}';"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        if 'Write_rows' in result.stdout or 'Update_rows' in result.stdout:
            # Contar operaciones
            write_count = result.stdout.count('Write_rows')
            update_count = result.stdout.count('Update_rows')

            if write_count > 0 or update_count > 0:
                logs_with_data.append((log, write_count, update_count))
                print(f"✓ {log}: {write_count} INSERTs, {update_count} UPDATEs")

print("\n" + "=" * 80)
print(f"\nLogs con datos encontrados: {len(logs_with_data)}")
print("\nLogs a procesar con mysqlbinlog:")
for log, writes, updates in logs_with_data:
    if writes > 0:  # Solo los que tienen INSERTs
        print(f"  - {log} ({writes} INSERT operations)")

print("\n" + "=" * 80)
print("\nPara recuperar los datos, ejecuta como Administrador:")
print()
for log, writes, updates in logs_with_data:
    if writes > 0:
        safe_name = log.replace('.', '_')
        print(
            f'mysqlbinlog --verbose --base64-output=DECODE-ROWS "C:\\ProgramData\\MySQL\\MySQL Server 9.1\\Data\\{log}" > "C:\\Users\\alex0\\Documents\\Economía\\Gastos\\Casa\\recovered_{safe_name}.sql"')
