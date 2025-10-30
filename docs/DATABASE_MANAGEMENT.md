# 🗄️ Guía de Gestión de Base de Datos

## ⚠️ IMPORTANTE: Prevención de Pérdida de Datos

Esta guía explica cómo gestionar la base de datos de forma segura para **evitar pérdida accidental de datos**.

---

## 📋 Scripts Disponibles

### 1. `init_db.py` - Inicializar Base de Datos VACÍA

**⛔ NO ejecutar si la base de datos tiene datos**

```bash
python init_db.py
```

**Cuándo usar:**

- ✅ Primera instalación del sistema
- ✅ Base de datos completamente vacía
- ✅ Ambiente de desarrollo nuevo

**Cuándo NO usar:**

- ❌ Base de datos con datos existentes
- ❌ Producción con registros guardados
- ❌ Para agregar una tabla faltante

**Protecciones:**

- Verifica si hay datos antes de ejecutar
- Requiere confirmación con `--force` si hay datos
- Muestra advertencia clara

---

### 2. `add_table.py` - Agregar Tabla Específica (SEGURO)

**✅ Seguro de usar con datos existentes**

```bash
python add_table.py <nombre_tabla>
```

**Ejemplos:**

```bash
# Agregar la tabla presupuesto
python add_table.py presupuesto

# Agregar la tabla categorias
python add_table.py categorias
```

**Cuándo usar:**

- ✅ Agregar una tabla faltante
- ✅ Base de datos con datos existentes
- ✅ Producción (es seguro)

**Características:**

- Usa `CREATE TABLE IF NOT EXISTS` (no destruye datos)
- Verifica si la tabla ya existe
- Muestra estructura y cantidad de registros
- No afecta datos existentes

---

### 3. `seed_db.py` - Datos Iniciales

**✅ Seguro de usar con datos existentes**

```bash
python seed_db.py
```

**Qué hace:**

- Inserta categorías básicas si no existen
- Usa `INSERT IGNORE` (no duplica ni borra)

---

### 4. `check_db.py` - Verificar Estado

**✅ Solo lectura, completamente seguro**

```bash
python check_db.py
```

**Qué muestra:**

- Categorías existentes
- Presupuestos configurados
- Total de gastos
- Resumen por mes

---

### 5. `restore_backup.py` - Restaurar Backup

**⚠️ Sobrescribe datos actuales**

```bash
# Con backup descomprimido
python restore_backup.py "ruta/al/backup.sql"

# Con backup por defecto (más reciente)
python restore_backup.py
```

**Proceso completo de restauración:**

1. **Descomprimir backup** (son archivos RAR):

   ```bash
   "C:/Program Files/WinRAR/WinRAR.exe" x -o+ "scripts/backups/daily/backup.sql.gz" "temp_restore/"
   ```

2. **Restaurar**:
   ```bash
   python restore_backup.py "temp_restore/backup.sql"
   ```

---

## 🛡️ Mejores Prácticas

### Para Evitar Pérdida de Datos:

1. **NUNCA ejecutes `init_db.py` con datos existentes**

   - Primero verifica con `python check_db.py`
   - Si hay datos, usa `add_table.py` en su lugar

2. **Para agregar una tabla faltante:**

   ```bash
   # ✅ CORRECTO
   python add_table.py presupuesto

   # ❌ INCORRECTO
   python init_db.py
   ```

3. **Verifica backups regularmente:**

   ```bash
   ls -lh scripts/backups/daily/
   ```

   - Backups automáticos diarios a las 08:33 AM
   - Formato: `economia_db_daily_YYYY-MM-DD_HH-mm-ss.sql.gz` (RAR)

4. **Antes de operaciones riesgosas:**
   - Verifica que hay backups recientes
   - Considera hacer un backup manual con el script de PowerShell

---

## 🚨 En Caso de Pérdida de Datos

Si perdiste datos accidentalmente:

1. **Detén la aplicación inmediatamente:**

   ```bash
   # Ctrl+C en la terminal donde corre app.py
   ```

2. **Verifica backups disponibles:**

   ```bash
   ls -lh scripts/backups/daily/
   ```

3. **Descomprime el backup más reciente:**

   ```bash
   "C:/Program Files/WinRAR/WinRAR.exe" x -o+ "scripts/backups/daily/economia_db_daily_2025-10-30_08-33-30.sql.gz" "temp_restore/"
   ```

4. **Restaura:**

   ```bash
   python restore_backup.py "temp_restore/economia_db_daily_2025-10-30_08-33-30.sql"
   ```

5. **Verifica la restauración:**
   ```bash
   python check_db.py
   ```

---

## 📊 Resumen de Seguridad

| Script              | Seguro con Datos | Propósito            | Riesgo     |
| ------------------- | ---------------- | -------------------- | ---------- |
| `check_db.py`       | ✅ Sí            | Ver estado BD        | 🟢 Ninguno |
| `add_table.py`      | ✅ Sí            | Agregar tabla        | 🟢 Bajo    |
| `seed_db.py`        | ✅ Sí            | Datos iniciales      | 🟢 Bajo    |
| `init_db.py`        | ❌ No            | Inicializar BD vacía | 🔴 Alto    |
| `restore_backup.py` | ⚠️ Precaución    | Restaurar backup     | 🟡 Medio   |

---

## 📝 Notas Importantes

- **Formato de backups**: Los archivos `.sql.gz` son en realidad archivos RAR v5
- **Backups automáticos**: Se ejecutan diariamente a las 08:33 AM
- **Base de datos de tests**: Los tests usan `test_economia_db` (separada, no afecta datos reales)
- **Foreign Keys**: La tabla `gastos` tiene FK a `categorias`, por eso es crítico no recrear tablas con datos

---

## 🆘 Soporte

Si tienes dudas sobre qué script usar:

1. Primero ejecuta `python check_db.py` para ver el estado actual
2. Si solo falta una tabla, usa `python add_table.py <tabla>`
3. Si hay pérdida de datos, sigue el proceso de restauración
4. **Nunca** ejecutes `init_db.py` si `check_db.py` muestra datos
