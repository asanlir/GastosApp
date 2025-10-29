# ========================================
# Script de Backup Automático de MySQL
# ========================================
# 
# Este script realiza un backup diario de la base de datos economia_db
# y mantiene una rotación de:
# - 7 backups diarios
# - 4 backups semanales (domingos)
# - 12 backups mensuales (primer día de cada mes)
#
# Uso:
#   .\backup_db.ps1
#
# Requisitos:
#   - MySQL Client instalado (mysqldump disponible en PATH)
#   - Variables de entorno configuradas (ver .env)
#   - Carpeta de backups creada (se crea automáticamente si no existe)
#   - (Opcional) WinRAR o 7-Zip para comprimir backups

param(
    [string]$BackupDir = "$PSScriptRoot\backups",
    [string]$DatabaseName = "economia_db",
    [string]$LogFile = "$PSScriptRoot\backups\backup.log"
)

# Función para escribir logs
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

# Función para cargar variables desde .env
function Load-EnvFile {
    param([string]$EnvPath)
    
    if (Test-Path $EnvPath) {
        Write-Log "Cargando variables de entorno desde .env"
        Get-Content $EnvPath | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remover comillas si existen
                $value = $value -replace '^["'']|["'']$', ''
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

# Cargar .env si existe
$envFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
Load-EnvFile -EnvPath $envFile

# Crear directorio de backups si no existe
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
    Write-Log "Directorio de backups creado: $BackupDir"
}

# Obtener credenciales desde variables de entorno
$env:MYSQL_HOST = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$env:MYSQL_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "3306" }
$env:MYSQL_USER = if ($env:DB_USER) { $env:DB_USER } else { "root" }
$env:MYSQL_PASSWORD = $env:DB_PASSWORD

if (-not $env:MYSQL_PASSWORD) {
    Write-Log "ERROR: DB_PASSWORD no está configurada en las variables de entorno"
    exit 1
}

# Generar timestamp y nombres de archivo
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dayOfWeek = (Get-Date).DayOfWeek
$dayOfMonth = (Get-Date).Day

# Determinar tipo de backup
$backupType = "daily"
$backupSubDir = "$BackupDir\daily"

if ($dayOfWeek -eq "Sunday") {
    $backupType = "weekly"
    $backupSubDir = "$BackupDir\weekly"
} elseif ($dayOfMonth -eq 1) {
    $backupType = "monthly"
    $backupSubDir = "$BackupDir\monthly"
}

# Crear subdirectorio si no existe
if (-not (Test-Path $backupSubDir)) {
    New-Item -ItemType Directory -Path $backupSubDir | Out-Null
}

$backupFile = "$backupSubDir\${DatabaseName}_${backupType}_${timestamp}.sql"
$backupFileGz = "$backupFile.gz"

Write-Log "=== Iniciando backup $backupType de $DatabaseName ==="

# Ejecutar mysqldump
try {
    # Usar MYSQL_PWD para evitar exponer la contraseña en la línea de comandos
    $env:MYSQL_PWD = $env:MYSQL_PASSWORD
    
    $mysqldumpArgs = @(
        "--host=$env:MYSQL_HOST",
        "--port=$env:MYSQL_PORT",
        "--user=$env:MYSQL_USER",
        "--databases", $DatabaseName,
        "--single-transaction",
        "--triggers",
        "--events",
        "--no-tablespaces",  # Evita PROCESS privilege requirement
        "--skip-lock-tables",  # Evita problemas de bloqueo
        "--column-statistics=0",  # Evita problemas con INFORMATION_SCHEMA
        "--result-file=`"$backupFile`""
    )
    
    # Ejecutar comando y capturar salida
    $output = & mysqldump @mysqldumpArgs 2>&1
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $backupFile)) {
        $fileSize = (Get-Item $backupFile).Length / 1MB
        Write-Log "Backup creado exitosamente: $backupFile ($([math]::Round($fileSize, 2)) MB)"
        
        # Comprimir backup (intenta WinRAR primero, luego 7-Zip)
        $compressed = $false
        
        # Intentar WinRAR
        $winrarPath = "C:\Program Files\WinRAR\WinRAR.exe"
        if (Test-Path $winrarPath) {
            try {
                & $winrarPath a -df -ep -m5 -inul "$backupFileGz" "$backupFile" 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    # WinRAR con -df ya eliminó el archivo fuente
                    if (Test-Path $backupFile) {
                        Remove-Item $backupFile -Force
                    }
                    Write-Log "Backup comprimido con WinRAR: $backupFileGz"
                    $compressed = $true
                }
            } catch {
                Write-Log "Advertencia: Error al comprimir con WinRAR, intentando alternativa..."
            }
        }
        
        # Intentar 7-Zip si WinRAR no funcionó
        if (-not $compressed -and (Get-Command "7z" -ErrorAction SilentlyContinue)) {
            try {
                7z a -sdel "$backupFileGz" "$backupFile" > $null
                Write-Log "Backup comprimido con 7-Zip: $backupFileGz"
                $compressed = $true
            } catch {
                Write-Log "Advertencia: Error al comprimir con 7-Zip"
            }
        }
        
        if (-not $compressed) {
            Write-Log "Compresor no encontrado (WinRAR/7-Zip), backup sin comprimir"
        }
    } else {
        Write-Log "ERROR: Fallo al crear backup (código de salida: $LASTEXITCODE)"
        if ($output) {
            Write-Log "Detalles del error: $output"
        }
        exit 1
    }
} catch {
    Write-Log "ERROR: Excepción durante backup: $_"
    exit 1
}

# Rotación de backups
Write-Log "Iniciando rotación de backups..."

# Mantener solo los últimos 7 backups diarios
$dailyBackups = Get-ChildItem "$BackupDir\daily\*.sql*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($dailyBackups.Count -gt 7) {
    $dailyBackups | Select-Object -Skip 7 | ForEach-Object {
        Remove-Item $_.FullName
        Write-Log "Eliminado backup antiguo: $($_.Name)"
    }
}

# Mantener solo los últimos 4 backups semanales
$weeklyBackups = Get-ChildItem "$BackupDir\weekly\*.sql*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($weeklyBackups.Count -gt 4) {
    $weeklyBackups | Select-Object -Skip 4 | ForEach-Object {
        Remove-Item $_.FullName
        Write-Log "Eliminado backup semanal antiguo: $($_.Name)"
    }
}

# Mantener solo los últimos 12 backups mensuales
$monthlyBackups = Get-ChildItem "$BackupDir\monthly\*.sql*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($monthlyBackups.Count -gt 12) {
    $monthlyBackups | Select-Object -Skip 12 | ForEach-Object {
        Remove-Item $_.FullName
        Write-Log "Eliminado backup mensual antiguo: $($_.Name)"
    }
}

Write-Log "=== Backup completado exitosamente ==="

# Sincronizar a la nube si el script existe
$syncScript = "$PSScriptRoot\sync_to_cloud.ps1"
if (Test-Path $syncScript) {
    Write-Log "Iniciando sincronización a la nube..."
    try {
        & $syncScript -BackupDir $BackupDir -ErrorAction Stop
    }
    catch {
        Write-Log "Advertencia: Error al sincronizar a la nube: $_"
    }
}

Write-Log ""
