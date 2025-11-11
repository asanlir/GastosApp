# Configuración de Backups Automáticos

Este directorio contiene scripts para realizar backups automáticos de la base de datos.

## Requisitos

- MySQL Client instalado (mysqldump disponible en PATH)
- PowerShell 5.0 o superior
- Variables de entorno configuradas (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
- (Opcional) WinRAR o 7-Zip instalado para comprimir backups

## Script de Backup: `backup_db.ps1`

### Características

- **Backups automáticos** con rotación inteligente:
  - 7 backups diarios
  - 4 backups semanales (domingos)
  - 12 backups mensuales (primer día del mes)
- **Compresión automática** con WinRAR (preferido) o 7-Zip
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
   - Argumentos: `-ExecutionPolicy Bypass -File "C:\ruta\a\tu\proyecto\scripts\backup_db.ps1"`
   - Iniciar en: `C:\ruta\a\tu\proyecto`

5. **Configuración Adicional**

   - En "Condiciones": Desmarcar "Iniciar solo si el equipo está conectado a la corriente alterna" (si es laptop)
   - En "Configuración": Marcar "Ejecutar la tarea tan pronto como sea posible después de perder un inicio programado"

   **Importante:** Si el PC está apagado a las 3:00 AM, el backup se ejecutará automáticamente en cuanto enciendas el ordenador. Esto está configurado con `-StartWhenAvailable` en el script de setup.

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

## Sincronización con la Nube 🌐

Los backups se pueden sincronizar automáticamente con tu servicio de nube preferido para mayor seguridad.

### ✅ Configuración Automática (Recomendado)

El sistema incluye `sync_to_cloud.ps1` que detecta automáticamente tu proveedor de nube:

- **OneDrive** (incluido en Windows)
- **Google Drive Desktop**
- **Dropbox**
- O cualquier carpeta sincronizada personalizada

**El script de backup ya llama automáticamente a la sincronización**, no necesitas hacer nada adicional.

### 📋 Requisitos

1. Tener instalado y configurado uno de estos servicios:

   - OneDrive (viene con Windows, solo necesitas iniciar sesión)
   - Google Drive Desktop: https://www.google.com/drive/download/
   - Dropbox Desktop: https://www.dropbox.com/install

2. Asegúrate de que el servicio esté sincronizando (ícono en la bandeja del sistema)

### 🧪 Prueba Manual

Para probar la sincronización manualmente:

```powershell
.\scripts\sync_to_cloud.ps1
```

Esto sincronizará todos los backups existentes a la nube.

### 🔧 Configuración Personalizada

Si quieres usar una carpeta específica:

```powershell
.\scripts\sync_to_cloud.ps1 -CloudProvider Custom -CustomCloudPath "D:\MiCarpetaSincronizada\Backups\Gastos"
```

### 📊 ¿Qué se sincroniza?

- Solo los backups **comprimidos** (.rar o .gz)
- Se mantiene la misma estructura: `daily/`, `weekly/`, `monthly/`
- Se aplica la misma rotación en la nube (7/4/12)
- Solo se copian archivos nuevos o modificados (eficiente)

### 📁 Ubicación en la Nube

Los backups se sincronizan en:

- **OneDrive**: `C:\Users\TuUsuario\OneDrive\Backups\Gastos\`
- **Google Drive**: `C:\Users\TuUsuario\Google Drive\Backups\Gastos\`
- **Dropbox**: `C:\Users\TuUsuario\Dropbox\Backups\Gastos\`

### 📝 Log de Sincronización

Revisa `backups\sync.log` para ver el estado de las sincronizaciones:

```powershell
Get-Content .\backups\sync.log -Tail 20
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

Instala WinRAR (https://www.win-rar.com/) o 7-Zip (https://www.7-zip.org/download.html).
El script detecta automáticamente cuál está instalado y lo usa (WinRAR tiene prioridad).

## FAQ

### ¿Qué pasa si el PC está apagado a las 3:00 AM?

El backup se ejecutará **automáticamente en cuanto enciendas el ordenador**. La tarea está configurada con `-StartWhenAvailable`, lo que significa que si se pierde la hora programada (3:00 AM), Windows ejecutará el backup tan pronto como el sistema esté disponible.

### ¿Puedo cambiar la hora del backup?

Sí, puedes modificar el parámetro `-StartTime` al ejecutar el script de setup:

```powershell
.\scripts\setup_backup_task.ps1 -StartTime "10:00"
```

O editar manualmente la tarea en el Programador de tareas de Windows.

### ¿Los backups ocupan mucho espacio?

No, están comprimidos con WinRAR (nivel 5) o 7-Zip, y además se aplica rotación automática:

- Solo se mantienen los últimos 7 backups diarios
- Solo los últimos 4 backups semanales (domingos)
- Solo los últimos 12 backups mensuales (día 1 de cada mes)

### ¿Puedo hacer backups manuales además de los automáticos?

Sí, simplemente ejecuta:

```powershell
.\scripts\backup_db.ps1
```

Esto no afecta a los backups automáticos programados.

### ¿Cómo sé si la sincronización con la nube funciona?

Revisa el log de sincronización:

```powershell
Get-Content .\backups\sync.log -Tail 20
```

También verás los archivos en tu carpeta de OneDrive/Google Drive/Dropbox en `Backups\Gastos\`.

### ¿Qué pasa si no tengo ningún servicio de nube?

La sincronización se salta automáticamente y el backup local se realiza sin problemas. No es obligatorio tener sincronización en la nube.

### ¿Puedo desactivar la sincronización a la nube?

Sí, simplemente renombra o elimina el archivo `sync_to_cloud.ps1`. El backup local seguirá funcionando normalmente.

### ¿La sincronización consume mucho ancho de banda?

No, el script solo sincroniza archivos **nuevos o modificados**. Además, los backups ya están comprimidos (típicamente 1-5 MB cada uno), por lo que el impacto es mínimo.
