# Script para configurar automáticamente la tarea programada de backup
# Ejecutar como Administrador

param(
    [string]$ScriptPath = "$PSScriptRoot\backup_db.ps1",
    [string]$TaskName = "Backup Base de Datos - Gastos",
    [string]$TaskDescription = "Backup diario automático de economia_db a las 3:00 AM",
    [string]$StartTime = "03:00"
)

# Verificar si se está ejecutando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host "Haz clic derecho en PowerShell y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Configurando Tarea Programada de Backup ===" -ForegroundColor Cyan

# Verificar que el script de backup existe
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: No se encuentra el script de backup en: $ScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "Script de backup encontrado: $ScriptPath" -ForegroundColor Green

# Eliminar tarea existente si existe
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Eliminando tarea programada existente..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Crear acción (ejecutar PowerShell con el script)
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -File `"$ScriptPath`"" `
    -WorkingDirectory (Split-Path $ScriptPath -Parent)

# Crear desencadenador (diariamente a las 3:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime

# Configurar ajustes adicionales
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -DontStopOnIdleEnd

# Crear principal (usuario actual)
# S4U permite ejecutar aunque el usuario no esté logueado
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Limited

# Registrar la tarea
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $TaskDescription `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "✓ Tarea programada creada exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuración:" -ForegroundColor Cyan
    Write-Host "  Nombre: $TaskName"
    Write-Host "  Horario: Diariamente a las $StartTime"
    Write-Host "  Script: $ScriptPath"
    Write-Host ""
    Write-Host "Para verificar la tarea:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Para ejecutar manualmente:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Para ver el historial:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTaskInfo -TaskName '$TaskName'"
    Write-Host ""
    
} catch {
    Write-Host "ERROR al crear la tarea programada: $_" -ForegroundColor Red
    exit 1
}

# Preguntar si quiere ejecutar un backup de prueba
$runTest = Read-Host "¿Deseas ejecutar un backup de prueba ahora? (S/N)"
if ($runTest -eq "S" -or $runTest -eq "s") {
    Write-Host ""
    Write-Host "Ejecutando backup de prueba..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "Estado: $($taskInfo.LastTaskResult)" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { "Green" } else { "Red" })
    
    if ($taskInfo.LastTaskResult -eq 0) {
        Write-Host "✓ Backup de prueba completado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "⚠ El backup falló. Revisa el log en backups/backup.log" -ForegroundColor Red
    }
}
