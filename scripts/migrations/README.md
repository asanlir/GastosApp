# Migraciones de Base de Datos

Este directorio contiene scripts de migración **no destructivos** para actualizar el esquema de la base de datos de manera segura e idempotente.

## Convenciones

### Nomenclatura

Los archivos de migración deben seguir el formato:

```
XXX_descripcion.py
```

Donde:

- `XXX`: Número secuencial de 3 dígitos (001, 002, 003, ...)
- `descripcion`: Breve descripción en snake_case del cambio

Ejemplos:

- `001_add_presupuesto_indexes.py`
- `002_add_unique_constraint_categorias.py`
- `003_create_audit_table.py`

### Estructura de un Script de Migración

Cada migración debe:

1. **Ser idempotente**: Ejecutable múltiples veces sin errores
2. **Consultar antes de cambiar**: Usar `INFORMATION_SCHEMA` para verificar si el cambio ya existe
3. **No ser destructivo**: Solo `CREATE`, `ALTER ADD`, `CREATE INDEX`. Nunca `DROP`, `TRUNCATE` o `DELETE`
4. **Reportar acciones**: Usar `print()` para indicar qué se hizo
5. **Leer config de env vars**: Para permitir que `migrate.py` inyecte parámetros de BD

### Plantilla Básica

```python
"""
Breve descripción del cambio que aplica esta migración.
"""
import os
import sys

# Ajustar path para importar app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pymysql
from app.config import DefaultConfig


def main():
    # Leer params de env vars (inyectadas por migrate.py) o usar DefaultConfig
    params = {
        "host": os.getenv("DB_HOST", DefaultConfig.DB_HOST),
        "user": os.getenv("DB_USER", DefaultConfig.DB_USER),
        "password": os.getenv("DB_PASSWORD", DefaultConfig.DB_PASSWORD),
        "database": os.getenv("DB_NAME", DefaultConfig.DB_NAME),
        "port": int(os.getenv("DB_PORT", DefaultConfig.DB_PORT)),
        "cursorclass": pymysql.cursors.DictCursor,
    }

    conn = pymysql.connect(**params)
    try:
        cur = conn.cursor()

        # Consultar si el cambio ya existe
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS WHERE ...")
        exists = cur.fetchone()

        if exists:
            print("[OK] Cambio ya aplicado")
        else:
            # Aplicar cambio
            cur.execute("CREATE INDEX ...")
            print("[CREATED] Cambio aplicado")

        conn.commit()
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
```

## Ejecución

### Desde el runner (recomendado)

```bash
# Ver qué se ejecutaría
python scripts/migrate.py --db-name economia_db --dry-run

# Ejecutar migraciones
python scripts/migrate.py --db-name economia_db
```

### Directamente (debugging)

```bash
python scripts/migrations/001_add_presupuesto_indexes.py
```

## Notas de Seguridad

- **No hacer DROP/TRUNCATE**: Las migraciones son solo aditivas
- **Probar en test primero**: Usar `--db-name test_economia_db` para validar
- **Idempotencia obligatoria**: Debe poder ejecutarse N veces sin errores
- **Sin emojis Unicode**: Usar `[OK]`, `[CREATED]`, `[WARN]` para evitar problemas de encoding en Windows

## Ejemplos de Cambios Permitidos

✅ Permitidos:

- Crear índices (`CREATE INDEX IF NOT EXISTS`)
- Añadir columnas opcionales (`ALTER TABLE ADD COLUMN IF NOT EXISTS`)
- Crear tablas nuevas (`CREATE TABLE IF NOT EXISTS`)
- Añadir constraints no destructivos (`ALTER TABLE ADD CONSTRAINT`)

❌ Prohibidos:

- Eliminar tablas (`DROP TABLE`)
- Eliminar columnas (`ALTER TABLE DROP COLUMN`)
- Borrar datos (`DELETE`, `TRUNCATE`)
- Renombrar columnas sin migración de datos

## Añadir una Nueva Migración

1. Crea el archivo con el siguiente número secuencial disponible
2. Implementa siguiendo la plantilla y las convenciones
3. Prueba en local con `--dry-run` y luego contra `test_economia_db`
4. Documenta en el commit qué problema resuelve
5. Avisa a otros desarrolladores para que ejecuten `migrate.py` tras hacer pull
