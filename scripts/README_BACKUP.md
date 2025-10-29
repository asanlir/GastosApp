# Configuración de Backups Automáticos

Este directorio contiene scripts para realizar backups automáticos de la base de datos.

## Requisitos

- MySQL Client instalado (mysqldump disponible en PATH)
- PowerShell 5.0 o superior
- Variables de entorno configuradas (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
- (Opcional) 7-Zip instalado para comprimir backups

## Script de Backup: `backup_db.ps1`

### Características

- **Backups automáticos** con rotación inteligente:
  - 7 backups diarios
  - 4 backups semanales (domingos)
  - 12 backups mensuales (primer día del mes)
- **Compresión automática** si 7-Zip está disponible
- **Logging** de todas las operaciones

### Uso Manual

```powershell
# Desde el directorio raíz del proyecto
.\scripts\backup_db.ps1
```

### Configurar Backup Automático en Windows (Task Scheduler)

#### Opción 1: Usar el script de instalación automática

```powershell
# Ejecutar como Administrador
.\scripts\setup_backup_task.ps1
```

#### Opción 2: Configuración manual

1. **Abrir Programador de Tareas** (Task Scheduler)
   - Presiona `Win + R` y escribe `taskschd.msc`

2. **Crear Tarea Básica**
   - Clic derecho en "Biblioteca del Programador de tareas" → "Crear tarea básica..."
   - Nombre: `Backup Base de Datos - Gastos`
   - Descripción: `Backup diario automático de economia_db`

3. **Configurar Desencadenador**
   - Seleccionar "Diariamente"
   - Hora: 03:00 AM (o la hora que prefieras)
   - Repetir cada: 1 día

4. **Configurar Acción**
   - Acción: "Iniciar un programa"
   - Programa: `powershell.exe`
   - Argumentos: `-ExecutionPolicy Bypass -File "C:\Users\alex0\Documents\Economía\Gastos\Casa\scripts\backup_db.ps1"`
   - Iniciar en: `C:\Users\alex0\Documents\Economía\Gastos\Casa`

5. **Configuración Adicional**
   - En "Condiciones": Desmarcar "Iniciar solo si el equipo está conectado a la corriente alterna" (si es laptop)
   - En "Configuración": Marcar "Ejecutar la tarea tan pronto como sea posible después de perder un inicio programado"

6. **Variables de Entorno**
   - Asegúrate de que las variables DB_HOST, DB_USER, DB_PASSWORD estén configuradas a nivel de sistema o usuario
   - O crea un archivo `.env.backup` con las credenciales y modifica el script para cargarlo

## Estructura de Backups

```
backups/
├── daily/          # 7 últimos backups diarios
├── weekly/         # 4 últimos backups semanales (domingos)
├── monthly/        # 12 últimos backups mensuales
└── backup.log      # Log de todas las operaciones
```

## Restaurar un Backup

```powershell
# Descomprimir si está comprimido
7z x backup_file.sql.gz

# Restaurar
mysql -u root -p economia_db < backup_file.sql
```

O desde PowerShell:

```powershell
$env:MYSQL_PWD = "tu_password"
Get-Content "backup_file.sql" | mysql -u root economia_db
```

## Backup a la Nube (Opcional)

Para sincronizar los backups a OneDrive/Google Drive:

1. Configura la carpeta `backups/` para sincronizarse con tu servicio de nube
2. O añade al final de `backup_db.ps1`:

```powershell
# Copiar a OneDrive
Copy-Item -Path $backupFileGz -Destination "$env:OneDrive\Backups\Gastos\"
```

## Monitoreo

Revisa el archivo `backups/backup.log` para verificar que los backups se ejecutan correctamente:

```powershell
Get-Content .\backups\backup.log -Tail 20
```

## Troubleshooting

### Error: "mysqldump no se reconoce"

Añade MySQL a tu PATH:
```powershell
$env:PATH += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"
```

### Error: "DB_PASSWORD no está configurada"

Configura las variables de entorno o crea un archivo `.env` en el directorio del proyecto.

### Los backups no se comprimen

Instala 7-Zip: https://www.7-zip.org/download.html
