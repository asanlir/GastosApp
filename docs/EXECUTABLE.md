# 📦 Construcción de Ejecutable Aislado

Este documento explica cómo construir un ejecutable (.exe) aislado de la aplicación de gastos que:

- ✅ Usa su propia base de datos (separada del desarrollo)
- ✅ Tiene configuración embebida (no depende de archivos externos)
- ✅ No se ve afectado por cambios en el código fuente
- ✅ Incluye todos los recursos necesarios (templates, static)

## 🎯 ¿Por qué un ejecutable aislado?

El ejecutable aislado te permite:

1. **Usar la aplicación de forma estable** mientras desarrollas nuevas features
2. **No preocuparte por romper tu app en producción** al experimentar con el código
3. **Tener dos entornos completamente separados**: desarrollo y producción
4. **Distribuir la aplicación** fácilmente sin necesidad de instalar Python

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│  Código Fuente (Desarrollo)            │
│  • economia_db (BD desarrollo)          │
│  • .env (configuración dev)             │
│  • Modificable sin restricciones        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  GastosApp.exe (Producción)             │
│  • economia_db_prod (BD separada)       │
│  • .env.exe empaquetado                 │
│  • Aislado de cambios externos          │
└─────────────────────────────────────────┘
```

## 📋 Prerrequisitos

1. **PyInstaller** instalado:

   ```bash
   pip install pyinstaller
   ```

2. **Base de datos MySQL** funcionando

3. **.env.exe configurado** con SECRET_KEY única

## 🚀 Construcción del Ejecutable

### Paso 0: Migrar Datos (Primera vez)

Si ya tienes datos en `economia_db` y quieres usarlos en el ejecutable:

```bash
# Migrar todos los datos a economia_db_prod
python scripts/migrate_to_prod_db.py
```

Este script:

- ✅ Copia todos los datos de `economia_db` a `economia_db_prod`
- ✅ Verifica que todos los registros se copiaron correctamente
- ✅ Mantiene ambas bases de datos separadas

### Paso 1: Construcción

#### Opción 1: Script Automatizado (Recomendado)

```bash
# Con valores por defecto (nombre: GastosApp, icono: calc.ico)
python scripts/build_exe.py

# Con nombre personalizado
python scripts/build_exe.py --name MiGastos

# Con icono personalizado
python scripts/build_exe.py --icon static/pig.ico

# Con ambos personalizados
python scripts/build_exe.py --name ControlGastos --icon static/pig.ico
```

Este script:

- ✅ Verifica que .env.exe esté configurado
- ✅ Genera SECRET_KEY si no existe
- ✅ Construye el ejecutable con tu nombre e icono elegidos
- ✅ Verifica/crea la base de datos de producción
- ✅ Muestra instrucciones de uso

**Opciones disponibles:**

| Opción   | Descripción                      | Por defecto       |
| -------- | -------------------------------- | ----------------- |
| `--name` | Nombre del ejecutable (sin .exe) | `GastosApp`       |
| `--icon` | Ruta al archivo .ico             | `static/calc.ico` |

**Iconos disponibles:**

- `static/calc.ico` - Icono de calculadora
- `static/pig.ico` - Icono de alcancía

#### Opción 2: Manual

```bash
# 1. Asegúrate de que .env.exe tiene SECRET_KEY configurada
# 2. Construir con PyInstaller
pyinstaller --name MiGastos --icon static/pig.ico --onefile app.py

# 3. El ejecutable estará en: dist/MiGastos.exe
```

## ⚙️ Configuración

### Archivo .env.exe

Este archivo contiene la configuración embebida en el ejecutable:

```env
# Base de datos de producción (separada del desarrollo)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=economia_db_prod      # ← BD separada
DB_PORT=3306

# SECRET_KEY única (generada automáticamente)
SECRET_KEY=<generada_por_script>

# Logging
LOG_LEVEL=INFO

# Modo de ejecución
FLASK_ENV=production
```

**⚠️ IMPORTANTE:**

- `.env.exe` está en `.gitignore` (contiene SECRET_KEY)
- Usa `.env.exe.example` como plantilla
- Nunca compartas `.env.exe` públicamente

### Inicializar Base de Datos de Producción

```bash
# Crear base de datos con datos de ejemplo
python init_db.py --db-name economia_db_prod --seed-sample

# O migrar desde tu BD actual
mysqldump -u root -p economia_db > backup.sql
mysql -u root -p economia_db_prod < backup.sql
```

## 🎮 Uso del Ejecutable

1. **Ejecutar la aplicación:**

   ```bash
   cd dist
   GastosApp.exe
   ```

2. **Abrir en navegador:**

   ```
   http://127.0.0.1:5000
   ```

3. **Detener:**
   - Presiona `Ctrl+C` en la consola

## 📊 Diferencias entre Entornos

| Característica        | Desarrollo                 | Ejecutable            |
| --------------------- | -------------------------- | --------------------- |
| **Comando**           | `python app.py`            | `GastosApp.exe`       |
| **Base de Datos**     | `economia_db`              | `economia_db_prod`    |
| **Configuración**     | `.env`                     | `.env.exe` (embebido) |
| **Logs**              | `DEBUG`                    | `INFO`                |
| **Cambios en código** | ✅ Se aplican al reiniciar | ❌ Requiere rebuild   |
| **Recursos**          | Rutas del proyecto         | Empaquetados en .exe  |

## 🔄 Actualizar el Ejecutable

Si haces cambios en el código que quieres en el ejecutable:

```bash
# Reconstruir el ejecutable
python scripts/build_exe.py

# O manualmente
pyinstaller app.spec --clean
```

**Nota:** El ejecutable anterior seguirá funcionando hasta que lo reemplaces.

## 🐛 Solución de Problemas

### El ejecutable no encuentra templates/static

**Solución:** Verifica que `app.spec` incluye los datas:

```python
datas=[
    ('static', 'static'),
    ('templates', 'templates'),
    ('.env.exe', '.'),
],
```

### Error de conexión a base de datos

**Solución:** Verifica `.env.exe`:

- DB_NAME apunta a `economia_db_prod`
- Usuario y contraseña son correctos
- La base de datos existe

### El ejecutable usa la BD de desarrollo

**Solución:** El ejecutable lee `.env.exe` empaquetado. Verifica:

```bash
# En app/config.py debe cargar .env.exe en modo frozen
env_file = get_env_file()  # Retorna .env.exe si is_frozen()
load_dotenv(env_file)
```

### Cambios en código no se reflejan en el ejecutable

**Respuesta:** Esto es **normal y esperado**. El ejecutable está aislado.
Para aplicar cambios, debes reconstruirlo con `python scripts/build_exe.py`.

## 📁 Archivos Relevantes

| Archivo                | Propósito                                    |
| ---------------------- | -------------------------------------------- |
| `app.spec`             | Configuración de PyInstaller                 |
| `.env.exe`             | Configuración del ejecutable (no versionado) |
| `.env.exe.example`     | Plantilla de configuración                   |
| `app/frozen_utils.py`  | Utilidades para modo frozen                  |
| `scripts/build_exe.py` | Script de construcción automatizado          |
| `dist/GastosApp.exe`   | Ejecutable generado                          |

## 🔐 Seguridad

- ✅ `.env.exe` está en `.gitignore`
- ✅ SECRET_KEY única generada automáticamente
- ✅ Base de datos separada (economia_db_prod)
- ⚠️ El ejecutable puede ser descompilado (PyInstaller no ofrece ofuscación completa)
- ⚠️ No incluir credenciales sensibles en el código

## 📚 Documentación Adicional

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Flask Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [MySQL Backup/Restore](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)

---

**💡 Tip:** Mantén el ejecutable en una carpeta separada de tu código fuente para evitar confusiones entre desarrollo y producción.
