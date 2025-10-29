# 🧪 Guía de Testing

## Visión General

La suite de testing cubre **servicios, queries, endpoints y utilidades** con una combinación de **tests unitarios** y **tests de integración**.

**Cobertura actual**: ~85% (54 tests unitarios + 8 tests de integración)

---

## Estructura de Tests

```
tests/
├── __init__.py              # Configuración base
├── conftest.py              # Fixtures compartidas
├── test_services.py         # Tests de capa de servicios
├── test_queries.py          # Tests de capa de datos
├── test_endpoints.py        # Tests de rutas Flask
├── test_charts.py           # Tests de generación de gráficos
└── test_utils.py            # Tests de utilidades
```

---

## Configuración de Testing

### Fixtures Globales

```python
# tests/conftest.py

@pytest.fixture
def app():
    """Instancia de Flask configurada para testing."""
    app = create_app("testing")
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Cliente de test para hacer requests."""
    return app.test_client()

@pytest.fixture
def mock_cursor():
    """Cursor mockeado para simular BD."""
    cursor = MagicMock()
    cursor.description = [
        ("id",), ("categoria_id",), ("categoria",),
        ("descripcion",), ("monto",), ("mes",), ("anio",)
    ]
    return cursor
```

---

## Tipos de Tests

### 1. Tests Unitarios

**Objetivo**: Probar funciones individuales en aislamiento.

**Características**:
- Mocks de dependencias externas
- Ejecución rápida (< 1s total)
- No requieren BD real

**Ejemplo**:

```python
# tests/test_services.py

@patch("app.services.gastos_service.get_all_gastos")
def test_get_gastos_by_mes_anio_success(mock_get_all):
    """Test unitario: filtrar gastos por mes/año."""
    # Arrange
    mock_get_all.return_value = [
        {"mes": "Octubre", "anio": 2025, "monto": 100.0}
    ]
    
    # Act
    result = get_gastos_by_mes_anio("Octubre", 2025)
    
    # Assert
    assert len(result) == 1
    assert result[0]["mes"] == "Octubre"
    mock_get_all.assert_called_once()
```

---

### 2. Tests de Integración

**Objetivo**: Probar interacción entre capas.

**Características**:
- Usan BD real o mockeada a nivel de conexión
- Validan flujo completo
- Más lentos (~10s total)

**Configuración**:

```python
# conftest.py

@pytest.fixture(scope="session")
def test_database():
    """Crea BD de testing una vez por sesión."""
    db_config = get_db_config("testing")
    conn = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"]
    )
    
    with conn.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS gastos_test")
        cursor.execute("USE gastos_test")
        # Ejecutar schema.sql
        with open("database/schema.sql") as f:
            cursor.execute(f.read())
    
    conn.commit()
    yield db_config
    
    # Teardown
    with conn.cursor() as cursor:
        cursor.execute("DROP DATABASE gastos_test")
    conn.close()
```

---

## Estrategias de Mocking

### Mock de Queries

```python
# Mockear a nivel de función query
@patch("app.queries.get_all_gastos")
def test_service_layer(mock_query):
    mock_query.return_value = [{"id": 1, "monto": 50.0}]
    result = gastos_service.get_all_gastos()
    assert len(result) == 1
```

### Mock de Cursor

```python
# Mockear cursor de BD
def test_query_with_mock_cursor(mock_cursor):
    mock_cursor.fetchall.return_value = [
        (1, 1, "Compra", "Descripción", 50.0, "Octubre", 2025)
    ]
    
    with patch("app.database.get_cursor", return_value=mock_cursor):
        result = get_all_gastos()
        assert len(result) == 1
```

### Mock de Conexión

```python
# Mockear conexión completa
@patch("pymysql.connect")
def test_database_connection(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn
    
    conn = get_connection()
    assert conn == mock_conn
```

---

## Tests por Capa

### Services Layer

**Archivo**: `tests/test_services.py`

**Cobertura**: 18 tests

```python
# Test de gastos_service
def test_agregar_gasto_success():
    """Agregar gasto con datos válidos."""
    with patch("app.queries.insert_gasto") as mock_insert:
        mock_insert.return_value = 1
        
        gasto_id = gastos_service.agregar_gasto(
            categoria_id=1,
            descripcion="Test",
            monto=100.0,
            mes="Octubre",
            anio=2025
        )
        
        assert gasto_id == 1
        mock_insert.assert_called_once()

def test_agregar_gasto_invalid_monto():
    """Validar que monto negativo lance excepción."""
    with pytest.raises(ValidationError):
        gastos_service.agregar_gasto(
            categoria_id=1,
            descripcion="Test",
            monto=-50.0,  # Inválido
            mes="Octubre",
            anio=2025
        )

# Test de categorias_service
def test_eliminar_categoria_con_gastos():
    """No permitir eliminar categoría con gastos asociados."""
    with patch("app.queries.categoria_tiene_gastos") as mock_check:
        mock_check.return_value = True
        
        with pytest.raises(ValidationError):
            categorias_service.eliminar_categoria(1)

# Test de presupuesto_service
def test_establecer_presupuesto():
    """Establecer presupuesto mensual."""
    with patch("app.queries.insert_or_update_presupuesto"):
        result = presupuesto_service.establecer_presupuesto(
            mes="Octubre",
            anio=2025,
            monto=1500.0
        )
        assert result is True
```

---

### Queries Layer

**Archivo**: `tests/test_queries.py`

**Cobertura**: 12 tests

```python
def test_get_all_gastos(mock_cursor):
    """Obtener todos los gastos."""
    mock_cursor.fetchall.return_value = [
        (1, 1, "Compra", "Supermercado", 85.5, "Octubre", 2025)
    ]
    
    with patch("app.database.get_cursor", return_value=mock_cursor):
        gastos = get_all_gastos()
        
        assert len(gastos) == 1
        assert gastos[0]["monto"] == 85.5
        assert gastos[0]["categoria"] == "Compra"

def test_insert_gasto(mock_cursor):
    """Insertar nuevo gasto."""
    mock_cursor.lastrowid = 42
    
    with patch("app.database.get_cursor", return_value=mock_cursor):
        gasto_id = insert_gasto(
            categoria_id=1,
            descripcion="Test",
            monto=100.0,
            mes="Octubre",
            anio=2025
        )
        
        assert gasto_id == 42
        mock_cursor.execute.assert_called_once()
```

---

### Endpoints Layer

**Archivo**: `tests/test_endpoints.py`

**Cobertura**: 14 tests

```python
def test_index_get(client):
    """GET / devuelve dashboard."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert b"Agregar Gasto" in response.data

def test_index_post_agregar_gasto(client):
    """POST / agrega gasto."""
    with patch("app.services.gastos_service.agregar_gasto"):
        response = client.post("/", data={
            "categoria": "1",
            "descripcion": "Test",
            "monto": "100.50",
            "mes": "Octubre",
            "anio": "2025"
        })
        
        assert response.status_code == 302  # Redirect

def test_delete_gasto(client):
    """GET /delete/<id> elimina gasto."""
    with patch("app.services.gastos_service.eliminar_gasto"):
        response = client.get("/delete/1")
        assert response.status_code == 302

def test_edit_gasto_get(client):
    """GET /edit/<id> muestra formulario."""
    with patch("app.services.gastos_service.get_gasto_by_id") as mock:
        mock.return_value = {
            "id": 1, "categoria_id": 1, "descripcion": "Test",
            "monto": 100.0, "mes": "Octubre", "anio": 2025
        }
        
        response = client.get("/edit/1")
        assert response.status_code == 200
        assert b"Editar Gasto" in response.data
```

---

### Charts Layer

**Archivo**: `tests/test_charts.py`

**Cobertura**: 6 tests

```python
def test_generar_grafico_torta():
    """Generar gráfico de torta."""
    gastos = [
        {"categoria": "Compra", "monto": 100.0},
        {"categoria": "Servicios", "monto": 200.0}
    ]
    
    html = charts_service.generar_grafico_torta(gastos)
    
    assert "<div>" in html
    assert "Compra" in html
    assert "Servicios" in html

def test_generar_grafico_barras():
    """Generar gráfico de barras."""
    gastos = [
        {"categoria": "Compra", "monto": 100.0, "mes": "Octubre"}
    ]
    
    html = charts_service.generar_grafico_barras(gastos)
    
    assert "plotly" in html.lower()
```

---

### Utils Layer

**Archivo**: `tests/test_utils.py`

**Cobertura**: 4 tests

```python
def test_validar_monto_positivo():
    """Validar monto positivo."""
    assert validar_monto(100.0) is True
    assert validar_monto(0.01) is True

def test_validar_monto_negativo():
    """Rechazar monto negativo."""
    with pytest.raises(ValidationError):
        validar_monto(-10.0)

def test_mes_valido():
    """Validar meses correctos."""
    assert mes_valido("Enero") is True
    assert mes_valido("Diciembre") is True
    assert mes_valido("Invalid") is False
```

---

## Comandos de Testing

### Ejecutar Todos los Tests

```bash
pytest
```

**Output esperado**:
```
======================== test session starts =========================
collected 54 items

tests/test_services.py ..................                    [ 33%]
tests/test_queries.py ............                           [ 55%]
tests/test_endpoints.py ..............                       [ 81%]
tests/test_charts.py ......                                  [ 92%]
tests/test_utils.py ....                                     [100%]

===================== 54 passed in 2.34s =========================
```

---

### Ejecutar Tests Específicos

```bash
# Por archivo
pytest tests/test_services.py

# Por función
pytest tests/test_services.py::test_agregar_gasto_success

# Por patrón
pytest -k "gasto"
```

---

### Modo Verbose

```bash
pytest -v
```

**Output**:
```
tests/test_services.py::test_agregar_gasto_success PASSED      [  1%]
tests/test_services.py::test_agregar_gasto_invalid_monto PASSED [  3%]
...
```

---

### Ver Prints y Logs

```bash
pytest -s
```

---

### Cobertura de Código

```bash
# Instalar coverage
pip install pytest-cov

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ver reporte
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

**Output esperado**:
```
---------- coverage: platform win32, python 3.11.9 -----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
app/__init__.py                       20      2    90%
app/services/gastos_service.py        45      5    89%
app/queries.py                        78      8    90%
app/routes/main.py                    92     15    84%
------------------------------------------------------
TOTAL                                458     61    87%
```

---

### Stop on First Failure

```bash
pytest -x
```

---

### Mostrar Locals en Failures

```bash
pytest -l
```

---

## Markers de Pytest

### Definir Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Tests unitarios rápidos
    integration: Tests de integración lentos
    slow: Tests que tardan >1s
```

### Usar Markers

```python
@pytest.mark.unit
def test_rapido():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.slow
def test_lento():
    # Test que requiere BD
    pass
```

### Ejecutar por Marker

```bash
# Solo tests unitarios
pytest -m unit

# Excluir tests lentos
pytest -m "not slow"

# Combinar markers
pytest -m "unit and not slow"
```

---

## Patrones de Testing

### Patrón AAA (Arrange-Act-Assert)

```python
def test_calcular_total():
    # Arrange - Preparar datos
    gastos = [
        {"monto": 100.0},
        {"monto": 50.0}
    ]
    
    # Act - Ejecutar función
    total = calcular_total(gastos)
    
    # Assert - Verificar resultado
    assert total == 150.0
```

---

### Parametrización

```python
@pytest.mark.parametrize("monto,esperado", [
    (100.0, True),
    (0.01, True),
    (-10.0, False),
    (0.0, False)
])
def test_validar_monto(monto, esperado):
    resultado = validar_monto(monto) if monto > 0 else False
    assert resultado == esperado
```

---

### Testing de Excepciones

```python
def test_excepcion_validation_error():
    """Verificar que se lance ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        validar_monto(-100.0)
    
    assert "negativo" in str(exc_info.value).lower()
```

---

### Testing de Logs

```python
def test_logging(caplog):
    """Verificar que se genere log."""
    with caplog.at_level(logging.INFO):
        logger.info("Test log")
    
    assert "Test log" in caplog.text
```

---

## Debugging Tests

### PDB (Python Debugger)

```python
def test_con_debugging():
    resultado = funcion_compleja()
    import pdb; pdb.set_trace()  # Breakpoint
    assert resultado == esperado
```

**Comandos PDB**:
- `n` → Next line
- `s` → Step into
- `c` → Continue
- `p variable` → Print variable
- `q` → Quit

---

### Pytest Debugging

```bash
# Entrar en PDB en failures
pytest --pdb

# Entrar en PDB en primer failure
pytest -x --pdb
```

---

## Mocking Avanzado

### Mock de Múltiples Llamadas

```python
def test_multiples_llamadas():
    with patch("app.queries.get_all_gastos") as mock:
        mock.side_effect = [
            [{"id": 1}],  # Primera llamada
            [{"id": 2}]   # Segunda llamada
        ]
        
        result1 = get_all_gastos()
        result2 = get_all_gastos()
        
        assert result1[0]["id"] == 1
        assert result2[0]["id"] == 2
```

---

### Mock con Excepciones

```python
def test_manejo_de_error():
    with patch("app.queries.insert_gasto") as mock:
        mock.side_effect = DatabaseError("Error de BD")
        
        with pytest.raises(DatabaseError):
            agregar_gasto(...)
```

---

### Verificar Llamadas

```python
def test_verificar_llamadas():
    with patch("app.queries.insert_gasto") as mock:
        agregar_gasto(categoria_id=1, descripcion="Test", ...)
        
        # Verificar que se llamó
        mock.assert_called_once()
        
        # Verificar argumentos
        mock.assert_called_with(
            categoria_id=1,
            descripcion="Test",
            ...
        )
        
        # Verificar número de llamadas
        assert mock.call_count == 1
```

---

## Testing de Flask

### Testing de Sesión

```python
def test_flash_message(client):
    """Verificar mensajes flash."""
    with client.session_transaction() as sess:
        sess["_flashes"] = [("success", "Test message")]
    
    response = client.get("/")
    assert b"Test message" in response.data
```

---

### Testing de Context Processors

```python
def test_context_processor(app, client):
    """Verificar variables globales de template."""
    with app.test_request_context():
        # Simular request
        pass
```

---

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Best Practices

### ✅ DO

- **Nombrar tests descriptivamente**: `test_agregar_gasto_con_monto_negativo_lanza_excepcion`
- **Un assert por test** (cuando sea posible)
- **Usar fixtures** para setup repetitivo
- **Mockear dependencias externas** (BD, APIs)
- **Tests independientes**: no depender de orden de ejecución
- **Seguir patrón AAA**: Arrange, Act, Assert

### ❌ DON'T

- Tests que dependen de otros tests
- Tests que modifican estado global
- Tests sin asserts
- Nombres genéricos: `test1`, `test_func`
- Mockear todo: algunas cosas deben ser reales
- Tests con lógica compleja

---

## Troubleshooting

### Error: `ModuleNotFoundError`

**Causa**: pytest no encuentra módulos de `app/`.

**Solución**:
```bash
# Asegurarse de tener __init__.py en todos los directorios
touch tests/__init__.py
touch app/__init__.py
```

---

### Error: `fixture not found`

**Causa**: Fixture no definida o mal importada.

**Solución**: Verificar que fixture esté en `conftest.py`:

```python
# conftest.py
@pytest.fixture
def mi_fixture():
    return "valor"
```

---

### Tests Pasan Localmente pero Fallan en CI

**Causas comunes**:
- Variables de entorno faltantes
- Dependencias de sistema diferentes
- Zona horaria diferente

**Solución**:
```yaml
# .github/workflows/tests.yml
env:
  TZ: Europe/Madrid
  DB_HOST: localhost
```

---

## Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Flask Testing](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Última actualización**: 29 de octubre de 2025
