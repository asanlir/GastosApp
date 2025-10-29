# 🌐 Documentación de API y Endpoints

## Visión General

La aplicación expone endpoints web tradicionales (HTML) para la gestión de gastos. No es una REST API, sino una aplicación web con formularios HTML.

---

## Endpoints Principales

### 🏠 Dashboard

#### `GET /`

Muestra el dashboard principal con gastos del mes actual.

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|---------|-----------|--------------|----------------------|
| `mes` | string | No | Mes actual | Mes a visualizar |
| `anio` | integer | No | Año actual | Año a visualizar |

**Ejemplo**:

```
GET /?mes=Octubre&anio=2025
```

**Respuesta**:

- Página HTML con tabla de gastos
- Total de gastos del mes
- Comparativa con presupuesto
- Formulario para agregar nuevo gasto

---

#### `POST /`

Agrega un nuevo gasto o cambia el mes/año seleccionado.

**Form Data** (Agregar gasto):
| Campo | Tipo | Requerido | Descripción |
|---------------|---------|-----------|----------------------------|
| `categoria` | string | Sí | ID de categoría |
| `descripcion` | string | Sí | Descripción del gasto |
| `monto` | float | Sí | Monto en euros |
| `mes` | string | Sí | Mes del gasto |
| `anio` | integer | Sí | Año del gasto |

**Form Data** (Cambiar mes):
| Campo | Tipo | Requerido | Descripción |
|--------|---------|-----------|-------------------|
| `mes` | string | Sí | Nuevo mes |
| `anio` | integer | Sí | Nuevo año |

**Respuestas**:

- `302 Redirect` → Dashboard actualizado
- Flash message: "Gasto agregado correctamente" o "Error..."

**Validaciones**:

- Todos los campos son obligatorios
- Monto debe ser un número válido
- Categoría debe existir

---

### 🗑️ Eliminar Gasto

#### `GET /delete/<int:gasto_id>`

Elimina un gasto existente.

**Path Parameters**:
| Parámetro | Tipo | Descripción |
|------------|---------|-------------------|
| `gasto_id` | integer | ID del gasto |

**Ejemplo**:

```
GET /delete/123
```

**Respuestas**:

- `302 Redirect` → Dashboard (mes/año del gasto eliminado)
- Flash message: "Gasto eliminado correctamente" o "Gasto no encontrado"

---

### ✏️ Editar Gasto

#### `GET /edit/<int:gasto_id>`

Muestra formulario para editar un gasto.

**Path Parameters**:
| Parámetro | Tipo | Descripción |
|------------|---------|-------------------|
| `gasto_id` | integer | ID del gasto |

**Respuesta**:

- Página HTML con formulario pre-rellenado
- Lista de categorías disponibles

---

#### `POST /edit/<int:gasto_id>`

Guarda los cambios de un gasto.

**Path Parameters**:
| Parámetro | Tipo | Descripción |
|------------|---------|-------------------|
| `gasto_id` | integer | ID del gasto |

**Form Data**:
| Campo | Tipo | Requerido | Descripción |
|---------------|--------|-----------|-----------------------|
| `categoria` | string | Sí | Nueva categoría |
| `descripcion` | string | Sí | Nueva descripción |
| `monto` | float | Sí | Nuevo monto |

**Respuestas**:

- `302 Redirect` → Dashboard
- Flash message: "Gasto actualizado correctamente"

---

### 📊 Histórico de Gastos

#### `GET /gastos`

Muestra todos los gastos sin filtros.

**Respuesta**:

- Página HTML con tabla completa de gastos
- Formulario de filtros

---

#### `POST /gastos`

Aplica filtros al histórico de gastos.

**Form Data**:
| Campo | Tipo | Requerido | Descripción |
|------------|---------|-----------|----------------------|
| `mes` | string | No | Filtrar por mes |
| `anio` | integer | No | Filtrar por año |
| `categoria`| string | No | Filtrar por categoría|

**Ejemplo**:

```
POST /gastos
mes=Octubre&categoria=Compra
```

**Respuesta**:

- Página HTML con gastos filtrados
- Filtros aplicados visibles

---

### 📈 Reportes y Estadísticas

#### `GET /report`

Muestra reportes del mes actual.

**Query Parameters**:
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|---------|-----------|------------|-------------------|
| `mes` | string | No | Mes actual | Mes a analizar |
| `anio` | integer | No | Año actual | Año a analizar |

**Ejemplo**:

```
GET /report?mes=Septiembre&anio=2025
```

**Respuesta**:

- Página HTML con gráficos Plotly:
  - Gráfico de torta (distribución por categoría)
  - Gráficos de barras (evolución por categoría)
  - Comparativa gastos vs presupuesto

---

#### `POST /report`

Actualiza reportes según mes/año seleccionado.

**Form Data**:
| Campo | Tipo | Requerido | Descripción |
|--------|---------|-----------|----------------|
| `mes` | string | Sí | Mes a reportar |
| `anio` | integer | Sí | Año a reportar |

**Respuesta**:

- Misma página con gráficos actualizados

---

### ⚙️ Configuración

#### `GET /config`

Muestra página de configuración.

**Respuesta**:

- Formularios para:
  - Gestionar categorías
  - Establecer presupuesto mensual
- Lista de categorías existentes

---

#### `POST /config`

Procesa operaciones de configuración.

**Form Data** (Agregar categoría):
| Campo | Tipo | Descripción |
|------------------|--------|------------------------|
| `nueva_categoria`| string | Nombre de categoría |

**Form Data** (Eliminar categoría):
| Campo | Tipo | Descripción |
|----------------------|---------|---------------------|
| `eliminar_categoria` | integer | ID de categoría |

**Form Data** (Editar categoría):
| Campo | Tipo | Descripción |
|----------------------|---------|---------------------|
| `editar_categoria` | integer | ID de categoría |
| `nombre_categoria` | string | Nuevo nombre |

**Form Data** (Establecer presupuesto):
| Campo | Tipo | Descripción |
|--------|---------|------------------------|
| `monto`| float | Presupuesto mensual |
| `mes` | string | Mes del presupuesto |
| `anio` | integer | Año del presupuesto |

**Respuestas**:

- `302 Redirect` → Configuración actualizada
- Flash messages específicos por operación

---

## Mensajes Flash

### Tipos

| Categoría | Uso                         | Color/Estilo |
| --------- | --------------------------- | ------------ |
| `success` | Operación exitosa           | Verde        |
| `error`   | Error de validación/sistema | Rojo         |
| `info`    | Información general         | Azul         |

### Ejemplos

```python
flash('Gasto agregado correctamente', 'success')
flash('Error al agregar el gasto', 'error')
flash('Todos los campos son obligatorios', 'error')
flash('Categoría eliminada correctamente', 'success')
```

---

## Validaciones

### Gasto

| Campo         | Validación                       |
| ------------- | -------------------------------- |
| `categoria`   | Debe existir en BD               |
| `descripcion` | No vacío, max 255 caracteres     |
| `monto`       | Número positivo, max 2 decimales |
| `mes`         | Uno de los 12 meses válidos      |
| `anio`        | Entero entre 2000 y 2100         |

### Categoría

| Campo    | Validación                    |
| -------- | ----------------------------- |
| `nombre` | No vacío, único, max 50 chars |

### Presupuesto

| Campo   | Validación          |
| ------- | ------------------- |
| `monto` | Número positivo > 0 |
| `mes`   | Mes válido          |
| `anio`  | Año válido          |

---

## Códigos de Estado HTTP

| Código | Descripción           | Uso               |
| ------ | --------------------- | ----------------- |
| `200`  | OK                    | GET exitoso       |
| `302`  | Found (Redirect)      | POST exitoso      |
| `404`  | Not Found             | Recurso no existe |
| `500`  | Internal Server Error | Error de servidor |

---

## Formatos de Datos

### Fechas

- **Meses**: String en español (`"Enero"`, `"Febrero"`, etc.)
- **Años**: Integer (ej: `2025`)

### Montos

- **Formato**: Float con 2 decimales
- **Separador**: Punto (`.`) para decimales
- **Ejemplo**: `123.45`

### IDs

- **Formato**: Integer autoincremental
- **Ejemplo**: `1`, `42`, `123`

---

## Compatibilidad Legacy

La aplicación mantiene **compatibilidad con endpoints legacy**:

```python
# LEGACY_ROUTES en routes/main.py
[
    ("/", "index", ["GET", "POST"]),
    ("/delete/<int:id>", "delete_gasto", ["GET"]),
    ("/edit/<int:id>", "edit_gasto", ["GET", "POST"]),
    # ...
]
```

Esto permite que `url_for('index')` funcione sin necesidad de `url_for('main.index')`.

---

## Ejemplos de Uso

### Flujo: Agregar un Gasto

```http
1. GET / → Ver dashboard

2. POST /
   categoria=1
   descripcion=Compra semanal
   monto=87.50
   mes=Octubre
   anio=2025

3. 302 Redirect → /?mes=Octubre&anio=2025

4. Flash: "Gasto agregado correctamente"
```

### Flujo: Ver Estadísticas

```http
1. GET /report → Ver reportes mes actual

2. POST /report
   mes=Septiembre
   anio=2025

3. 200 OK → Página con gráficos de Septiembre 2025
```

### Flujo: Editar Gasto

```http
1. GET /edit/123 → Formulario pre-rellenado

2. POST /edit/123
   categoria=2
   descripcion=Factura luz actualizada
   monto=65.00

3. 302 Redirect → /

4. Flash: "Gasto actualizado correctamente"
```

---

## Errores Comunes

### Error: "Todos los campos son obligatorios"

**Causa**: Algún campo del formulario está vacío.

**Solución**: Completar todos los campos obligatorios.

---

### Error: "Categoría con ID X no existe"

**Causa**: Se intenta agregar gasto con categoría inexistente.

**Solución**: Verificar que la categoría exista en `/config`.

---

### Error: "Gasto no encontrado"

**Causa**: Se intenta editar/eliminar un gasto que no existe.

**Solución**: Verificar que el ID del gasto sea válido.

---

## Seguridad

### Prevención SQL Injection

✅ Todos los endpoints usan **queries parametrizados**:

```python
# NUNCA:
f"SELECT * FROM gastos WHERE id = {gasto_id}"

# SIEMPRE:
cursor.execute("SELECT * FROM gastos WHERE id = %s", (gasto_id,))
```

### CSRF Protection

⚠️ **Nota**: La aplicación actual **NO** implementa CSRF tokens.

**Recomendación para producción**:

```python
# Agregar Flask-WTF
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### XSS Protection

✅ Jinja2 auto-escapa variables por defecto:

```html
{{ gasto.descripcion }}
<!-- Auto-escaped -->
{{ gasto.descripcion|safe }}
<!-- NO usar sin validar -->
```

---

## Performance

### Queries Optimizados

Todos los endpoints críticos usan índices:

- `idx_gastos_mes_anio` → Dashboard por mes
- `idx_gastos_categoria` → Filtros por categoría
- `idx_gastos_anio_mes` → Reportes históricos

### Límites

| Endpoint  | Límite           | Paginación |
| --------- | ---------------- | ---------- |
| `/`       | 1 mes de gastos  | No         |
| `/gastos` | Todos los gastos | No         |
| `/report` | 12 meses         | No         |

**Recomendación**: Implementar paginación si > 1000 gastos.

---

## Testing

### Test de Endpoints

```python
# tests/test_endpoints.py
def test_index_get(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Agregar Gasto' in response.data
```

Ver `docs/TESTING.md` para más detalles.

---

## Referencias

- [Flask Routing](https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

---

**Última actualización**: 29 de octubre de 2025
