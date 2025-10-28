# Índices de Base de Datos - Guía de Optimización

## Resumen de Índices Implementados

### Tabla: `gastos`

| Índice                   | Columnas               | Propósito                                                  |
| ------------------------ | ---------------------- | ---------------------------------------------------------- |
| `PRIMARY`                | `id`                   | Clave primaria                                             |
| `idx_categoria`          | `categoria`            | Filtros por categoría, JOIN con categorias                 |
| `idx_mes_anio`           | `mes, anio`            | Filtros mes+año combinados                                 |
| `idx_anio_mes`           | `anio, mes`            | Ordenación DESC por año/mes, filtros por año               |
| `idx_anio`               | `anio`                 | Agregaciones anuales (gráficos)                            |
| `idx_categoria_anio_mes` | `categoria, anio, mes` | Filtros combinados frecuentes (gráficos por categoría/año) |

### Tabla: `presupuesto`

| Índice         | Columnas    | Propósito                               |
| -------------- | ----------- | --------------------------------------- |
| `PRIMARY`      | `id`        | Clave primaria                          |
| `idx_mes_anio` | `mes, anio` | Búsquedas de presupuesto por mes/año    |
| `idx_anio_mes` | `anio, mes` | Presupuesto vigente con ordenación DESC |

## Queries Optimizadas

### 1. Listar gastos por mes/año (más frecuente)

```sql
SELECT * FROM gastos WHERE mes = 'Octubre' AND anio = 2025;
```

**Usa:** `idx_mes_anio` o `idx_anio_mes` dependiendo del optimizer.

### 2. Gastos por categoría en un año

```sql
SELECT * FROM gastos WHERE categoria = 'Compra' AND anio = 2025;
```

**Usa:** `idx_categoria_anio_mes` (covering index parcial).

### 3. Total de gastos por año (gráficos)

```sql
SELECT SUM(monto) FROM gastos WHERE anio = 2025;
```

**Usa:** `idx_anio` para scan rápido.

### 4. Ordenar gastos DESC por año/mes

```sql
SELECT * FROM gastos ORDER BY anio DESC, mes DESC;
```

**Usa:** `idx_anio_mes` para ordenación nativa.

### 5. Presupuesto vigente

```sql
SELECT monto FROM presupuesto
WHERE anio <= 2025
ORDER BY anio DESC, mes DESC
LIMIT 1;
```

**Usa:** `idx_anio_mes` para ordenación y filtro eficiente.

## Notas de Rendimiento

- **Cobertura:** Los índices compuestos permiten que MySQL resuelva queries sin acceder a la tabla (index-only scan) cuando solo se consultan las columnas indexadas.
- **Memoria:** Cada índice adicional consume espacio en disco y RAM. Los 6 índices en `gastos` son justificables dado el patrón de acceso frecuente.
- **Escritura:** Los índices ralentizan ligeramente INSERTs/UPDATEs. Para esta aplicación (más lecturas que escrituras), el trade-off es positivo.

## Mantenimiento

- **Análisis periódico:** Ejecutar `ANALYZE TABLE gastos, presupuesto;` mensualmente para actualizar estadísticas del optimizer.
- **Fragmentación:** Si notas lentitud tras muchas operaciones, ejecutar `OPTIMIZE TABLE gastos, presupuesto;` para reorganizar índices.

## Verificación

Comprobar uso de índices con EXPLAIN:

```sql
EXPLAIN SELECT * FROM gastos WHERE mes = 'Octubre' AND anio = 2025;
```

Buscar en el output:

- `type: ref` o `range` (bueno)
- `key: idx_mes_anio` o similar
- `rows: <bajo>` (menos escaneos)
