"""
Tests unitarios para el módulo de services.

Usan mocks de base de datos para aislar la lógica de negocio.
"""
from unittest.mock import patch, MagicMock
import pytest
from app.services import gastos_service, presupuesto_service, categorias_service
from app.exceptions import ValidationError, DatabaseError


class TestGastosService:
    """Tests unitarios para gastos_service."""

    @patch('app.services.gastos_service.cursor_context')
    def test_get_gasto_by_id_existente(self, mock_cursor_context):
        """Test obtener gasto por ID cuando existe."""
        # Mock del cursor y resultado
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'categoria': 'Compra',
            'descripcion': 'Test',
            'monto': 100.0,
            'mes': 'Octubre',
            'anio': 2025
        }
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = gastos_service.get_gasto_by_id(1)

        # Verificar
        assert resultado is not None
        assert resultado['id'] == 1
        assert resultado['categoria'] == 'Compra'
        mock_cursor.execute.assert_called_once()

    @patch('app.services.gastos_service.cursor_context')
    def test_get_gasto_by_id_no_existe(self, mock_cursor_context):
        """Test obtener gasto por ID cuando no existe."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = gastos_service.get_gasto_by_id(999)

        assert resultado is None

    @patch('app.services.gastos_service.cursor_context')
    def test_list_gastos_sin_filtros(self, mock_cursor_context):
        """Test listar gastos sin filtros."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'categoria': 'Compra', 'monto': 50.0},
            {'id': 2, 'categoria': 'Gasolina', 'monto': 30.0}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = gastos_service.list_gastos()

        assert len(resultado) == 2
        assert resultado[0]['id'] == 1
        mock_cursor.execute.assert_called_once()

    @patch('app.services.gastos_service.cursor_context')
    def test_list_gastos_con_filtros(self, mock_cursor_context):
        """Test listar gastos con filtros de mes y año."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'mes': 'Octubre', 'anio': 2025}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = gastos_service.list_gastos(mes='Octubre', anio=2025)

        assert len(resultado) == 1
        # Verificar que se llamó execute con parámetros
        call_args = mock_cursor.execute.call_args
        assert 'Octubre' in call_args[0][1]
        assert 2025 in call_args[0][1]

    @patch('app.services.gastos_service.cursor_context')
    def test_add_gasto_exitoso(self, mock_cursor_context):
        """Test agregar gasto con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'nombre': 'Compra'}
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = gastos_service.add_gasto(
            '1', 'Test', 100.0, 'Octubre', 2025)

        assert resultado is True
        mock_conn.commit.assert_called_once()
        assert mock_cursor.execute.call_count == 2  # lookup + insert

    @patch('app.services.gastos_service.cursor_context')
    def test_add_gasto_categoria_no_existe(self, mock_cursor_context):
        """Test agregar gasto con categoría inexistente lanza ValidationError."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        with pytest.raises(ValidationError, match="Categoría con ID 999 no existe"):
            gastos_service.add_gasto('999', 'Test', 100.0, 'Octubre', 2025)

    @patch('app.services.gastos_service.cursor_context')
    def test_update_gasto_exitoso(self, mock_cursor_context):
        """Test actualizar gasto con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'nombre': 'Compra'}
        mock_cursor.rowcount = 1
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = gastos_service.update_gasto(1, '1', 'Updated', 150.0)

        assert resultado is True
        mock_conn.commit.assert_called_once()

    @patch('app.services.gastos_service.cursor_context')
    def test_delete_gasto_exitoso(self, mock_cursor_context):
        """Test eliminar gasto con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = gastos_service.delete_gasto(1)

        assert resultado is True
        mock_conn.commit.assert_called_once()

    @patch('app.services.gastos_service.cursor_context')
    def test_delete_gasto_no_existe(self, mock_cursor_context):
        """Test eliminar gasto que no existe."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = gastos_service.delete_gasto(999)

        assert resultado is False

    @patch('app.services.gastos_service.cursor_context')
    def test_get_total_gastos(self, mock_cursor_context):
        """Test calcular total de gastos."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'total': 1250.50}
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = gastos_service.get_total_gastos('Octubre', 2025)

        assert resultado == 1250.50

    @patch('app.services.gastos_service.cursor_context')
    def test_get_total_gastos_vacio(self, mock_cursor_context):
        """Test calcular total cuando no hay gastos."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'total': None}
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = gastos_service.get_total_gastos()

        assert resultado == 0.0


class TestPresupuestoService:
    """Tests unitarios para presupuesto_service."""

    @patch('app.services.presupuesto_service.cursor_context')
    def test_get_presupuesto_mensual_existe(self, mock_cursor_context):
        """Test obtener presupuesto mensual cuando existe."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'monto': 1500.0}
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = presupuesto_service.get_presupuesto_mensual(
            'Octubre', 2025)

        assert resultado == 1500.0

    @patch('app.services.presupuesto_service.cursor_context')
    def test_get_presupuesto_mensual_no_existe(self, mock_cursor_context):
        """Test obtener presupuesto mensual cuando no existe."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = presupuesto_service.get_presupuesto_mensual('Enero', 2026)

        assert resultado == 0.0

    @patch('app.services.presupuesto_service.cursor_context')
    def test_update_presupuesto_crear_nuevo(self, mock_cursor_context):
        """Test crear nuevo presupuesto cuando no existe."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No existe
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = presupuesto_service.update_presupuesto(
            'Octubre', 2025, 1500.0)

        assert resultado is True
        mock_conn.commit.assert_called_once()
        # Verificar que se llamó INSERT
        assert mock_cursor.execute.call_count == 2

    @patch('app.services.presupuesto_service.cursor_context')
    def test_update_presupuesto_actualizar_existente(self, mock_cursor_context):
        """Test actualizar presupuesto existente."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}  # Existe
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = presupuesto_service.update_presupuesto(
            'Octubre', 2025, 1800.0)

        assert resultado is True
        mock_conn.commit.assert_called_once()

    @patch('app.services.presupuesto_service.cursor_context')
    @patch('app.services.presupuesto_service.get_presupuesto_mensual')
    def test_calcular_acumulado(self, mock_get_presupuesto, mock_cursor_context):
        """Test calcular presupuesto acumulado."""
        # Mock presupuesto mensual
        mock_get_presupuesto.return_value = 1000.0

        # Mock gastos acumulados
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'total_gastos': 2500.0}
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Octubre = mes 10, por tanto 10 meses
        resultado = presupuesto_service.calcular_acumulado('Octubre', 2025)

        # 1000 * 10 = 10000 (presupuesto) - 2500 (gastos) = 7500
        assert resultado == 7500.0


class TestCategoriasService:
    """Tests unitarios para categorias_service."""

    @patch('app.services.categorias_service.cursor_context')
    def test_list_categorias(self, mock_cursor_context):
        """Test listar categorías."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nombre': 'Compra'},
            {'id': 2, 'nombre': 'Gasolina'}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        resultado = categorias_service.list_categorias()

        assert len(resultado) == 2
        assert resultado[0]['nombre'] == 'Compra'

    @patch('app.services.categorias_service.cursor_context')
    def test_add_categoria_exitoso(self, mock_cursor_context):
        """Test agregar categoría con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = categorias_service.add_categoria('Nueva')

        assert resultado is True
        mock_conn.commit.assert_called_once()

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_exitoso(self, mock_cursor_context):
        """Test actualizar categoría con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simular que la categoría existe con nombre diferente
        mock_cursor.fetchone.return_value = {'nombre': 'NombreViejo'}
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = categorias_service.update_categoria(1, 'Actualizada')

        assert resultado is True
        mock_conn.commit.assert_called_once()

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_no_existe(self, mock_cursor_context):
        """Test actualizar categoría que no existe."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simular que la categoría no existe
        mock_cursor.fetchone.return_value = None
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = categorias_service.update_categoria(999, 'NoExiste')

        assert resultado is False
        # No debería hacer commit porque no existe
        mock_conn.commit.assert_not_called()

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_nombre_duplicado(self, mock_cursor_context):
        """Test actualizar categoría con nombre duplicado."""
        import pymysql
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Primera llamada: simular que la categoría existe
        # Segunda llamada (UPDATE): simular IntegrityError
        mock_cursor.fetchone.return_value = {'nombre': 'NombreViejo'}
        mock_cursor.execute.side_effect = [
            None,  # Primera llamada SELECT exitosa
            pymysql.IntegrityError(1062, "Duplicate entry 'Test' for key 'nombre'")
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        with pytest.raises(ValidationError, match="Ya existe"):
            categorias_service.update_categoria(1, 'Duplicado')

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_mismo_nombre(self, mock_cursor_context):
        """Test actualizar categoría con el mismo nombre."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simular que la categoría existe con el mismo nombre
        mock_cursor.fetchone.return_value = {'nombre': 'MismoNombre'}
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = categorias_service.update_categoria(1, 'MismoNombre')

        assert resultado is True
        # No debería hacer commit porque el nombre no cambió
        mock_conn.commit.assert_not_called()

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_nombre_vacio(self, mock_cursor_context):
        """Test actualizar categoría con nombre vacío."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            categorias_service.update_categoria(1, '')

    @patch('app.services.categorias_service.cursor_context')
    def test_update_categoria_nombre_vacio_whitespace(self, mock_cursor_context):
        """Test actualizar categoría con nombre solo espacios."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            categorias_service.update_categoria(1, '   ')

    @patch('app.services.categorias_service.cursor_context')
    def test_delete_categoria_exitoso(self, mock_cursor_context):
        """Test eliminar categoría con éxito."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Simular que no hay gastos asociados
        mock_cursor.fetchone.return_value = {'count': 0}
        mock_cursor.rowcount = 1
        mock_cursor_context.return_value.__enter__.return_value = (
            mock_conn, mock_cursor)

        resultado = categorias_service.delete_categoria(1)

        assert resultado is True
        mock_conn.commit.assert_called_once()
