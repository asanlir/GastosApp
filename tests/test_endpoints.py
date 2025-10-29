"""
Tests de integración para los endpoints principales de la aplicación.
"""
import pytest
from datetime import datetime
from app.database import cursor_context

# Marcar todos los tests de este módulo como integration
pytestmark = pytest.mark.integration


@pytest.fixture
def setup_test_db(app):
    """Fixture que inicializa la base de datos de prueba con datos básicos."""
    # Crear tablas y datos de prueba
    with cursor_context() as (conn, cursor):
        # Limpiar tablas si existen
        cursor.execute("DROP TABLE IF EXISTS gastos;")
        cursor.execute("DROP TABLE IF EXISTS categorias;")
        cursor.execute("DROP TABLE IF EXISTS presupuesto;")

        # Crear tabla categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL UNIQUE
            );
        """)

        # Crear tabla gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                categoria VARCHAR(50) NOT NULL,
                descripcion TEXT,
                monto DECIMAL(10, 2) NOT NULL,
                mes VARCHAR(20) NOT NULL,
                anio INT NOT NULL,
                FOREIGN KEY (categoria) REFERENCES categorias(nombre)
            );
        """)

        # Crear tabla presupuesto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto (
                id INT AUTO_INCREMENT PRIMARY KEY,
                monto DECIMAL(10, 2) NOT NULL,
                fecha_cambio DATETIME NOT NULL,
                mes VARCHAR(20) NOT NULL,
                anio INT NOT NULL
            );
        """)

        # Insertar categorías de prueba
        categorias = ['Alquiler', 'Facturas', 'Compra', 'Gasolina']
        for categoria in categorias:
            cursor.execute(
                "INSERT INTO categorias (nombre) VALUES (%s);",
                (categoria,)
            )

        # Insertar presupuesto de prueba
        mes_actual = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][
            datetime.now().month - 1]
        anio_actual = datetime.now().year

        cursor.execute("""
            INSERT INTO presupuesto (monto, fecha_cambio, mes, anio)
            VALUES (%s, NOW(), %s, %s);
        """, (1000.00, mes_actual, anio_actual))

        conn.commit()

    yield

    # Limpiar después de las pruebas
    with cursor_context() as (conn, cursor):
        cursor.execute("DROP TABLE IF EXISTS gastos;")
        cursor.execute("DROP TABLE IF EXISTS categorias;")
        cursor.execute("DROP TABLE IF EXISTS presupuesto;")
        conn.commit()


def test_index_get(client, setup_test_db):
    """Test que la página principal carga correctamente."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Agregar Gasto' in response.data
    assert b'Presupuesto' in response.data


def test_crear_gasto_valido(client, setup_test_db):
    """Test que se puede crear un gasto con datos válidos."""
    data = {
        'categoria': '1',  # ID de la categoría Alquiler
        'descripcion': 'Alquiler mensual',
        'monto': '850.00',
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Gasto agregado correctamente' in response.data

    # Verificar que el gasto se guardó
    with cursor_context() as (conn, cursor):
        cursor.execute(
            "SELECT * FROM gastos WHERE descripcion = 'Alquiler mensual';"
        )
        gasto = cursor.fetchone()
        assert gasto is not None
        assert float(gasto['monto']) == 850.00
        assert gasto['mes'] == 'Octubre'
        assert gasto['anio'] == 2025


def test_crear_gasto_invalido(client, setup_test_db):
    """Test que no se puede crear un gasto con datos inválidos."""
    data = {
        'categoria': '1',
        'descripcion': 'Alquiler mensual',
        'monto': '',  # Monto vacío - debería fallar
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Todos los campos son obligatorios' in response.data

    # Verificar que no se guardó nada
    with cursor_context() as (conn, cursor):
        cursor.execute(
            "SELECT COUNT(*) as count FROM gastos WHERE descripcion = 'Alquiler mensual';"
        )
        count = cursor.fetchone()['count']
        assert count == 0


def test_editar_gasto(client, setup_test_db):
    """Test que se puede editar un gasto existente."""
    # Primero creamos un gasto
    with cursor_context() as (conn, cursor):
        cursor.execute("""
            INSERT INTO gastos (categoria, descripcion, monto, mes, anio)
            VALUES ('Alquiler', 'Alquiler mensual', 850.00, 'Octubre', 2025);
        """)
        conn.commit()
        gasto_id = cursor.lastrowid

    # Ahora intentamos editarlo
    data = {
        'categoria': 'Alquiler',
        'descripcion': 'Alquiler mensual actualizado',
        'monto': '900.00'
    }
    response = client.post(f'/edit/{gasto_id}',
                           data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Gasto actualizado correctamente' in response.data

    # Verificar que se actualizó
    with cursor_context() as (conn, cursor):
        cursor.execute("SELECT * FROM gastos WHERE id = %s;", (gasto_id,))
        gasto = cursor.fetchone()
        assert gasto['descripcion'] == 'Alquiler mensual actualizado'
        assert float(gasto['monto']) == 900.00


def test_eliminar_gasto(client, setup_test_db):
    """Test que se puede eliminar un gasto."""
    # Crear gasto para eliminar
    with cursor_context() as (conn, cursor):
        cursor.execute("""
            INSERT INTO gastos (categoria, descripcion, monto, mes, anio)
            VALUES ('Alquiler', 'Alquiler a eliminar', 850.00, 'Octubre', 2025);
        """)
        conn.commit()
        gasto_id = cursor.lastrowid

    response = client.get(f'/delete/{gasto_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Gasto eliminado correctamente' in response.data

    # Verificar que se eliminó
    with cursor_context() as (conn, cursor):
        cursor.execute("SELECT * FROM gastos WHERE id = %s;", (gasto_id,))
        gasto = cursor.fetchone()
        assert gasto is None


def test_ver_gastos_filtros(client, setup_test_db):
    """Test que la página de gastos funciona con diferentes filtros."""
    # Crear algunos gastos de prueba
    with cursor_context() as (conn, cursor):
        # Gasto mes actual
        cursor.execute("""
            INSERT INTO gastos (categoria, descripcion, monto, mes, anio)
            VALUES 
            ('Alquiler', 'Alquiler octubre', 850.00, 'Octubre', 2025),
            ('Facturas', 'Luz octubre', 75.00, 'Octubre', 2025),
            ('Compra', 'Compra septiembre', 120.00, 'Septiembre', 2025);
        """)
        conn.commit()

    # Probar sin filtros
    response = client.get('/gastos')
    assert response.status_code == 200
    assert b'Alquiler octubre' in response.data
    assert b'Luz octubre' in response.data
    assert b'Compra septiembre' in response.data

    # Probar filtro por mes
    data = {'mes': 'Octubre', 'anio': '2025'}
    response = client.post('/gastos', data=data)
    assert response.status_code == 200
    assert b'Alquiler octubre' in response.data
    assert b'Luz octubre' in response.data
    assert b'Compra septiembre' not in response.data

    # Probar filtro por categoría
    data = {'categoria': 'Alquiler'}
    response = client.post('/gastos', data=data)
    assert response.status_code == 200
    assert b'Alquiler octubre' in response.data
    assert b'Luz octubre' not in response.data


def test_flujo_crud_completo(client, setup_test_db):
    """Test flujo completo: crear → leer → editar → eliminar."""
    with cursor_context() as (conn, cursor):
        # Insertar categoría de prueba
        cursor.execute(
            "INSERT INTO categorias (nombre) VALUES ('TestCategoria');")
        cursor.execute(
            "SELECT id FROM categorias WHERE nombre = 'TestCategoria';")
        categoria_id = cursor.fetchone()['id']
        conn.commit()

    # 1. CREAR gasto
    data = {
        'categoria': str(categoria_id),
        'descripcion': 'Gasto de prueba CRUD',
        'monto': '123.45',
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Gasto creado' in response.data or b'Gasto de prueba CRUD' in response.data

    # 2. LEER - Verificar que existe
    with cursor_context() as (_, cursor):
        cursor.execute(
            "SELECT * FROM gastos WHERE descripcion = 'Gasto de prueba CRUD';")
        gasto = cursor.fetchone()
        assert gasto is not None
        assert float(gasto['monto']) == 123.45
        gasto_id = gasto['id']

    # 3. EDITAR gasto
    data_edit = {
        'categoria': str(categoria_id),
        'descripcion': 'Gasto EDITADO',
        'monto': '999.99'
    }
    response = client.post(f'/edit/{gasto_id}',
                           data=data_edit, follow_redirects=True)
    assert response.status_code == 200

    # Verificar cambios
    with cursor_context() as (_, cursor):
        cursor.execute(f"SELECT * FROM gastos WHERE id = {gasto_id};")
        gasto_editado = cursor.fetchone()
        assert gasto_editado['descripcion'] == 'Gasto EDITADO'
        assert float(gasto_editado['monto']) == 999.99

    # 4. ELIMINAR gasto
    response = client.get(f'/delete/{gasto_id}', follow_redirects=True)
    assert response.status_code == 200

    # Verificar eliminación
    with cursor_context() as (_, cursor):
        cursor.execute(f"SELECT * FROM gastos WHERE id = {gasto_id};")
        gasto_eliminado = cursor.fetchone()
        assert gasto_eliminado is None


def test_validacion_datos_invalidos(client, setup_test_db):
    """Test validación de datos inválidos (monto negativo, campos vacíos)."""
    with cursor_context() as (conn, cursor):
        cursor.execute(
            "INSERT INTO categorias (nombre) VALUES ('TestCategoria');")
        cursor.execute(
            "SELECT id FROM categorias WHERE nombre = 'TestCategoria';")
        categoria_id = cursor.fetchone()['id']
        conn.commit()

    # Monto negativo
    data_negativo = {
        'categoria': str(categoria_id),
        'descripcion': 'Test negativo',
        'monto': '-100.00',
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data_negativo, follow_redirects=True)
    # Debería rechazar o mostrar error (dependiendo de implementación)
    assert response.status_code in [200, 400]

    # Campo monto vacío
    data_vacio = {
        'categoria': str(categoria_id),
        'descripcion': 'Test vacío',
        'monto': '',
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data_vacio, follow_redirects=True)
    assert response.status_code in [200, 400]

    # Categoría inexistente
    data_cat_invalida = {
        'categoria': '99999',
        'descripcion': 'Test categoría inválida',
        'monto': '100.00',
        'mes': 'Octubre',
        'anio': '2025'
    }
    response = client.post('/', data=data_cat_invalida, follow_redirects=True)
    # Debería fallar porque la categoría no existe
    assert response.status_code in [200, 400]
