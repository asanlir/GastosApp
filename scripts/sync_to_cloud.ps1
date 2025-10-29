# Script para sincronizar backups a la nube
# Soporta: OneDrive, Google Drive (Desktop), Dropbox, o cualquier carpeta sincronizada

param(
    [string]$BackupDir = "$PSScriptRoot\..\backups",
    [string]$CloudProvider = "Auto",  # Auto, OneDrive, GoogleDrive, Dropbox, Custom
    [string]$CustomCloudPath = ""     # Ruta personalizada si CloudProvider=Custom
)

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    
    # Crear directorio de backups si no existe
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    
    Add-Content -Path "$BackupDir\sync.log" -Value $logMessage
}

Write-Log "=== Iniciando sincronización a la nube ==="

# Detectar proveedor de nube automáticamente
$cloudPath = $null

if ($CloudProvider -eq "Custom" -and $CustomCloudPath) {
    $cloudPath = $CustomCloudPath
    Write-Log "Usando ruta personalizada: $cloudPath"
}
elseif ($CloudProvider -eq "OneDrive" -or $CloudProvider -eq "Auto") {
    # Intentar OneDrive
    $oneDrivePaths = @(
        "$env:OneDrive",
        "$env:OneDriveConsumer",
        "$env:OneDriveCommercial",
        "$env:USERPROFILE\OneDrive"
    )
    
    foreach ($path in $oneDrivePaths) {
        if ($path -and (Test-Path $path)) {
            $cloudPath = "$path\Backups\Gastos"
            Write-Log "OneDrive detectado: $cloudPath"
            break
        }
    }
}

if (-not $cloudPath -and ($CloudProvider -eq "GoogleDrive" -or $CloudProvider -eq "Auto")) {
    # Intentar Google Drive
    $googleDrivePath = "$env:USERPROFILE\Google Drive\Backups\Gastos"
    if (Test-Path (Split-Path $googleDrivePath -Parent)) {
        $cloudPath = $googleDrivePath
        Write-Log "Google Drive detectado: $cloudPath"
    }
}

if (-not $cloudPath -and ($CloudProvider -eq "Dropbox" -or $CloudProvider -eq "Auto")) {
    # Intentar Dropbox
    $dropboxPath = "$env:USERPROFILE\Dropbox\Backups\Gastos"
    if (Test-Path (Split-Path $dropboxPath -Parent)) {
        $cloudPath = $dropboxPath
        Write-Log "Dropbox detectado: $cloudPath"
    }
}

# Verificar que se encontró una ruta de nube
if (-not $cloudPath) {
    Write-Log "ERROR: No se pudo detectar ningún proveedor de nube instalado"
    Write-Log "Opciones:"
    Write-Log "  1. Instala OneDrive, Google Drive Desktop o Dropbox"
    Write-Log "  2. Usa -CloudProvider Custom -CustomCloudPath 'C:\Tu\Carpeta\Sincronizada'"
    exit 1
}

# Crear carpeta de destino si no existe
if (-not (Test-Path $cloudPath)) {
    New-Item -ItemType Directory -Path $cloudPath -Force | Out-Null
    Write-Log "Carpeta de destino creada: $cloudPath"
}

# Verificar que existe la carpeta de backups local
if (-not (Test-Path $BackupDir)) {
    Write-Log "Advertencia: No existe la carpeta de backups local: $BackupDir"
    Write-Log "La sincronización se ejecutará cuando se cree el primer backup"
    exit 0
}

# Sincronizar cada tipo de backup (solo los comprimidos)
$types = @("daily", "weekly", "monthly")
$totalSynced = 0
$totalSize = 0

foreach ($type in $types) {
    $sourceFolder = "$BackupDir\$type"
    $destFolder = "$cloudPath\$type"
    
    if (-not (Test-Path $sourceFolder)) {
        continue
    }
    
    # Crear subcarpeta en la nube si no existe
    if (-not (Test-Path $destFolder)) {
        New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
    }
    
    # Obtener backups comprimidos (.rar o .gz)
    $backups = Get-ChildItem -Path $sourceFolder -Filter "*.rar" -ErrorAction SilentlyContinue
    if (-not $backups) {
        $backups = Get-ChildItem -Path $sourceFolder -Filter "*.gz" -ErrorAction SilentlyContinue
    }
    
    foreach ($backup in $backups) {
        $destFile = Join-Path $destFolder $backup.Name
        
        # Copiar solo si no existe o si el local es más reciente
        if (-not (Test-Path $destFile) -or $backup.LastWriteTime -gt (Get-Item $destFile).LastWriteTime) {
            try {
                Copy-Item -Path $backup.FullName -Destination $destFile -Force
                $totalSynced++
                $totalSize += $backup.Length
                Write-Log "Sincronizado: $type\$($backup.Name)"
            }
            catch {
                Write-Log "ERROR al sincronizar $($backup.Name): $_"
            }
        }
    }
}

# Limpiar backups antiguos en la nube (mantener misma política de rotación)
Write-Log "Aplicando rotación en la nube..."

# Daily: últimos 7
$cloudDailyBackups = Get-ChildItem "$cloudPath\daily\*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($cloudDailyBackups.Count -gt 7) {
    $cloudDailyBackups | Select-Object -Skip 7 | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Log "Eliminado de la nube: daily\$($_.Name)"
    }
}

# Weekly: últimos 4
$cloudWeeklyBackups = Get-ChildItem "$cloudPath\weekly\*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($cloudWeeklyBackups.Count -gt 4) {
    $cloudWeeklyBackups | Select-Object -Skip 4 | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Log "Eliminado de la nube: weekly\$($_.Name)"
    }
}

# Monthly: últimos 12
$cloudMonthlyBackups = Get-ChildItem "$cloudPath\monthly\*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($cloudMonthlyBackups.Count -gt 12) {
    $cloudMonthlyBackups | Select-Object -Skip 12 | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Log "Eliminado de la nube: monthly\$($_.Name)"
    }
}

# Resumen
$sizeMB = [math]::Round($totalSize / 1MB, 2)
Write-Log "=== Sincronización completada ==="
Write-Log "Archivos sincronizados: $totalSynced"
Write-Log "Tamaño total: $sizeMB MB"
Write-Log "Destino: $cloudPath"
Write-Log ""
