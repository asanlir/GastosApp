# 🏗️ Arquitectura del Sistema

## Visión General

El sistema de Control de Gastos está diseñado con una **arquitectura en capas** (layered architecture) que separa responsabilidades y facilita el mantenimiento y testing.

```
┌─────────────────────────────────────┐
│      Capa de Presentación          │  ← Flask Routes (templates HTML)
├─────────────────────────────────────┤
│      Capa de Lógica de Negocio     │  ← Services (gastos, categorías, etc.)
├─────────────────────────────────────┤
│      Capa de Acceso a Datos        │  ← Queries (SQL parametrizado)
├─────────────────────────────────────┤
│      Capa de Persistencia          │  ← MySQL Database
└─────────────────────────────────────┘
```

---

## Componentes Principales

### 1. Capa de Presentación (`app/routes/`)

**Responsabilidad**: Manejar requests HTTP y renderizar respuestas.

```python
# routes/main.py
@main_bp.route('/', methods=['GET', 'POST'])
def index():
    # 1. Validar input
    # 2. Llamar a servicios
    # 3. Renderizar template
```

**Características**:

- Blueprint Flask para modularidad
- Validación de formularios
- Manejo de flash messages
- Renderizado de templates Jinja2

**Flujo**:

1. Usuario hace request → Flask Router
2. Router ejecuta función de vista
3. Vista llama a servicios
4. Vista renderiza template con datos

---

### 2. Capa de Lógica de Negocio (`app/services/`)

**Responsabilidad**: Implementar reglas de negocio y orquestar operaciones.

```python
# services/gastos_service.py
def add_gasto(categoria_id, descripcion, monto, mes, anio):
    # 1. Validar categoría existe
    # 2. Ejecutar query de inserción
    # 3. Manejar excepciones
    # 4. Retornar resultado
```

**Módulos**:

- `gastos_service.py`: CRUD de gastos
- `categorias_service.py`: Gestión de categorías
- `presupuesto_service.py`: Manejo de presupuestos
- `charts_service.py`: Generación de gráficos

**Ventajas**:

- ✅ Reutilizable desde cualquier ruta
- ✅ Testeable sin base de datos (mocks)
- ✅ Lógica centralizada
- ✅ Desacoplado de presentación

---

### 3. Capa de Acceso a Datos (`app/queries.py`)

**Responsabilidad**: Proveer queries SQL seguros y parametrizados.

```python
# queries.py
def q_insert_gasto() -> Tuple[str, tuple]:
    query = """
        INSERT INTO gastos (categoria, descripcion, monto, mes, anio)
        VALUES (%s, %s, %s, %s, %s);
    """
    return query, ()
```

**Características**:

- Queries parametrizados (prevención SQL injection)
- Retorna tupla `(query, params)`
- Queries complejos con JOINs documentados
- Constantes SQL centralizadas (`constants.py`)

**Beneficios**:

- ✅ Anti-SQL injection
- ✅ Queries reutilizables
- ✅ Fácil testing
- ✅ Mantenimiento centralizado

---

### 4. Gestión de Conexiones (`app/database.py`)

**Responsabilidad**: Proveer conexiones seguras a MySQL.

```python
# database.py
@contextmanager
def cursor_context():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()
```

**Patrón**: Context Manager

- Cierre automático de conexiones
- Manejo de excepciones
- Pool implícito de pymysql

---

## Patrones de Diseño

### 1. Factory Pattern

**Ubicación**: `app/__init__.py`

```python
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(f'app.config.{config_name}Config')
    # Setup logging, blueprints, etc.
    return app
```

**Beneficios**:

- Múltiples instancias (dev, prod, test)
- Configuración por entorno
- Testing simplificado

---

### 2. Service Layer Pattern

**Ubicación**: `app/services/`

```python
# Separación de responsabilidades
routes → services → queries → database
```

**Ventajas**:

- Lógica de negocio reutilizable
- Testing independiente
- Cambios de BD no afectan rutas

---

### 3. Repository Pattern (implícito)

**Ubicación**: `app/queries.py`

Aunque no es un repository completo, centraliza el acceso a datos:

```python
# En vez de SQL disperso:
cursor.execute("SELECT * FROM gastos WHERE...")

# Usamos:
query, params = q_list_gastos(mes="Enero")
cursor.execute(query, params)
```

---

### 4. Context Manager Pattern

**Ubicación**: `app/database.py`

```python
with cursor_context() as (conn, cursor):
    cursor.execute(...)
    conn.commit()
# Auto-cierre garantizado
```

---

## Flujo de Datos

### Ejemplo: Agregar un Gasto

```
Usuario → POST /
    ↓
routes/main.py::index()
    ↓
gastos_service.add_gasto()
    ↓
queries.q_categoria_nombre_by_id()  ← Validar categoría
queries.q_insert_gasto()             ← Insertar gasto
    ↓
database.cursor_context()            ← Ejecutar query
    ↓
MySQL economia_db
    ↓
flash('Gasto agregado')
    ↓
redirect('/')
```

---

## Manejo de Errores

### Jerarquía de Excepciones

```python
GastosBaseException
├── DatabaseError         # Errores de BD
├── ValidationError       # Datos inválidos
├── NotFoundError        # Recurso no existe
└── DuplicateError       # Duplicado
```

### Flujo de Excepciones

```python
try:
    gastos_service.add_gasto(...)
except ValidationError as e:
    flash(str(e), 'error')
except DatabaseError as e:
    logger.error(f"DB Error: {e}")
    flash('Error de sistema', 'error')
```

---

## Logging

### Niveles por Entorno

| Entorno     | Nivel   | Destino        |
| ----------- | ------- | -------------- |
| Development | DEBUG   | Console + File |
| Production  | WARNING | File only      |
| Testing     | INFO    | Null           |

### Configuración

```python
# app/logging_config.py
def setup_logging(app):
    # Rotación: 10MB, 5 backups
    file_handler = RotatingFileHandler('logs/gastos.log', ...)
    app.logger.addHandler(file_handler)
```

---

## Base de Datos

### Esquema

```sql
gastos (id, categoria, descripcion, monto, mes, anio)
    ↓ FOREIGN KEY
categorias (id, nombre)

presupuesto (id, mes, anio, monto)
```

### Índices

```sql
-- Búsquedas por mes/año
CREATE INDEX idx_gastos_mes_anio ON gastos(mes, anio);

-- Agregaciones por categoría
CREATE INDEX idx_gastos_categoria ON gastos(categoria);

-- Históricos completos
CREATE INDEX idx_gastos_anio_mes ON gastos(anio, mes);
```

Ver `database/INDEXES.md` para detalles.

---

## Testing

### Estrategia de Testing

```
tests/
├── test_queries.py      # Unitarios: Queries SQL
├── test_services.py     # Unitarios: Lógica negocio (mocks)
├── test_utils.py        # Unitarios: Utilidades
└── test_endpoints.py    # Integración: E2E con BD
```

### Mocking en Services

```python
@patch('app.services.gastos_service.cursor_context')
def test_add_gasto(mock_cursor_context):
    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor_context.return_value.__enter__.return_value = (None, mock_cursor)

    # Test sin BD real
    result = gastos_service.add_gasto(...)
    assert result is True
```

---

## Configuración

### Múltiples Entornos

```python
# app/config.py
class BaseConfig:
    DB_HOST = os.getenv('DB_HOST')

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = 'WARNING'
```

### Variables de Entorno

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=***
DB_NAME=economia_db
SECRET_KEY=***
LOG_LEVEL=INFO
```

---

## Seguridad

### Prevención SQL Injection

✅ **Queries parametrizados**:

```python
# NUNCA:
f"SELECT * FROM gastos WHERE mes = '{mes}'"

# SIEMPRE:
cursor.execute("SELECT * FROM gastos WHERE mes = %s", (mes,))
```

### Validación de Input

```python
# services/gastos_service.py
if monto <= 0:
    raise ValidationError("Monto debe ser positivo")
```

### Secrets Management

- ✅ Variables sensibles en `.env`
- ✅ `.env` en `.gitignore`
- ✅ Secret key aleatorio en producción

---

## Performance

### Optimizaciones Implementadas

1. **Índices en BD**: Queries rápidos en tablas grandes
2. **Connection Pooling**: pymysql maneja pool automáticamente
3. **Query Optimization**: JOINs eficientes, evitar N+1
4. **Caching implícito**: Queries repetitivos optimizados por MySQL

### Bottlenecks Potenciales

| Componente         | Riesgo | Solución                     |
| ------------------ | ------ | ---------------------------- |
| Gráficos Plotly    | Alto   | Limitar a 12 meses           |
| Queries históricos | Medio  | Índices + LIMIT              |
| Uploads grandes    | Bajo   | No aplica (solo formularios) |

---

## Escalabilidad

### Crecimiento Previsto

| Métrica    | Actual    | 1 año  | 5 años |
| ---------- | --------- | ------ | ------ |
| Gastos/mes | ~50       | ~600   | ~3,000 |
| Usuarios   | 1 (local) | 1      | 1      |
| Tamaño BD  | < 1 MB    | ~10 MB | ~50 MB |

### Estrategias

- **Corto plazo**: Índices suficientes
- **Mediano plazo**: Particionamiento de tablas por año
- **Largo plazo**: Migración a PostgreSQL + Redis cache

---

## Decisiones de Diseño

### ¿Por qué Flask y no Django?

- ✅ Ligero y flexible
- ✅ Curva de aprendizaje suave
- ✅ Sin ORM innecesario (queries simples)

### ¿Por qué MySQL y no PostgreSQL?

- ✅ Ya instalado localmente
- ✅ Suficiente para caso de uso
- ✅ Backups simples con mysqldump

### ¿Por qué Plotly y no Chart.js?

- ✅ Gráficos interactivos sin JS
- ✅ Mejor integración con pandas
- ✅ Exportable a diferentes formatos

---

## Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Layered Architecture](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/)

---

**Última actualización**: 29 de octubre de 2025
