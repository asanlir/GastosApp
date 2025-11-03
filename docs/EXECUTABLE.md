# 📦 Construcción de Ejecutable Aislado

Este documento explica cómo construir un ejecutable (.exe) de la aplicación de gastos que:

- ✅ Usa la misma base de datos que el desarrollo (economia_db)
- ✅ Tiene configuración embebida (no depende de archivos externos)
- ✅ Incluye todos los recursos necesarios (templates, static)
- ✅ Lanza automáticamente el navegador al ejecutarse

## 🎯 ¿Por qué un ejecutable?

El ejecutable te permite:

1. **Usar la aplicación sin abrir VS Code o terminal**
2. **Acceso rápido** desde el escritorio o menú inicio
3. **Experiencia de usuario más amigable** con auto-lanzamiento del navegador
4. **Mismo conjunto de datos** que cuando desarrollas

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│  Código Fuente (Desarrollo)            │
│  • python app.py                        │
│  • .env (configuración dev)             │
│  • economia_db (BD unificada)           │
└─────────────────────────────────────────┘
              ↕ (comparten la misma BD)
┌─────────────────────────────────────────┐
│  Gastos.exe (Ejecutable)                │
│  • .env.exe empaquetado                 │
│  • economia_db (BD unificada)           │
│  • Auto-lanza navegador                 │
└─────────────────────────────────────────┘
```

## 📋 Prerrequisitos

1. **PyInstaller** instalado:

   ```bash
   pip install pyinstaller
   ```

2. **Base de datos MySQL** funcionando con `economia_db`

3. **.env.exe configurado** con SECRET_KEY única

## 🚀 Construcción del Ejecutable

### Construcción

#### Opción 1: Script Automatizado (Recomendado)

```bash
# Con valores por defecto (nombre: GastosApp, icono: calc.ico)
python scripts/build_exe.py

# Con nombre personalizado
python scripts/build_exe.py --name Gastos

# Con icono personalizado
python scripts/build_exe.py --icon static/casa.ico

# Con ambos personalizados
python scripts/build_exe.py --name Gastos --icon static/casa.ico
```

Este script:

- ✅ Verifica que .env.exe esté configurado
- ✅ Genera SECRET_KEY si no existe
- ✅ Construye el ejecutable con tu nombre e icono elegidos
- ✅ Verifica la base de datos
- ✅ Muestra instrucciones de uso

**Opciones disponibles:**

| Opción   | Descripción                      | Por defecto       |
| -------- | -------------------------------- | ----------------- |
| `--name` | Nombre del ejecutable (sin .exe) | `GastosApp`       |
| `--icon` | Ruta al archivo .ico             | `static/calc.ico` |

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
# Base de datos unificada (compartida con desarrollo)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=economia_db      # ← Misma BD que desarrollo
DB_PORT=3306

# SECRET_KEY única (generada automáticamente)
SECRET_KEY=<generada_por_script>

# Logging
LOG_LEVEL=INFO

# Modo de ejecución
FLASK_ENV=production
```

**⚠️ IMPORTANTE:**

- `.env.exe` está en `.gitignore` (contiene SECRET_KEY y password)
- Usa `.env.exe.example` como plantilla
- Nunca compartas `.env.exe` públicamente
- El ejecutable y el desarrollo usan la misma base de datos

## 🎮 Uso del Ejecutable

1. **Ejecutar la aplicación:**

   ```bash
   cd dist
   Gastos.exe
   ```

   El navegador se abrirá automáticamente en `http://127.0.0.1:5000`

2. **Detener:**
   - Presiona `Ctrl+C` en la consola

## 📊 Diferencias entre Entornos

| Característica        | Desarrollo                 | Ejecutable            |
| --------------------- | -------------------------- | --------------------- |
| **Comando**           | `python app.py`            | `Gastos.exe`          |
| **Base de Datos**     | `economia_db`              | `economia_db`         |
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
