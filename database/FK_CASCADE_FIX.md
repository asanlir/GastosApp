# Fix: Foreign Key Constraint para Edición de Categorías

## Problema

Al intentar editar una categoría, MySQL generaba el siguiente error:

```
(1451, 'Cannot delete or update a parent row: a foreign key constraint fails')
```

## Causa Raíz

La foreign key `gastos_ibfk_1` estaba configurada sin `ON UPDATE CASCADE`, lo que impedía actualizar el nombre de una categoría en `categorias.nombre` porque había referencias en `gastos.categoria`.

## Solución Implementada

### 1. Base de Datos

Se modificó la constraint para añadir `ON UPDATE CASCADE`:

```sql
ALTER TABLE gastos
DROP FOREIGN KEY gastos_ibfk_1;

ALTER TABLE gastos
ADD CONSTRAINT gastos_ibfk_1
FOREIGN KEY (categoria) REFERENCES categorias(nombre)
ON UPDATE CASCADE
ON DELETE RESTRICT;
```

**Efecto**: Cuando se actualiza `categorias.nombre`, MySQL actualiza automáticamente todas las filas en `gastos.categoria` que referencian ese nombre.

### 2. Schema

Se actualizó `database/schema.sql` para que futuras instalaciones tengan la constraint correcta:

```sql
FOREIGN KEY (categoria) REFERENCES categorias(nombre)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
```

### 3. Código

Se simplificó `categorias_service.update_categoria()`:

- **Antes**: Hacía UPDATE manual en ambas tablas (`categorias` y `gastos`)
- **Ahora**: Solo actualiza `categorias`, MySQL se encarga de `gastos` automáticamente vía CASCADE

## Archivos Modificados

- `database/fix_fk_cascade.sql` (nuevo): Script de migración para BD existentes
- `database/schema.sql`: Schema actualizado con ON UPDATE CASCADE
- `app/services/categorias_service.py`: Función simplificada

## Cómo Aplicar en BD Existente

```bash
mysql -u root -p < database/fix_fk_cascade.sql
```

## Beneficios

- ✅ Permite editar categorías con gastos asociados
- ✅ Mantiene integridad referencial automáticamente
- ✅ Código más simple y menos propenso a errores
- ✅ Mejor rendimiento (1 query en vez de 2)
