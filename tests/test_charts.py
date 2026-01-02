"""
Tests unitarios esenciales para el módulo de charts_service.

Solo cubre las funciones críticas para prevenir fallos visibles al usuario.
"""
from unittest.mock import patch, MagicMock
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestChartsService:
    """Tests esenciales para generación de gráficos."""

    def test_get_last_12_months(self):
        """Test que get_last_12_months devuelve 12 meses correctamente."""
        from app.services.charts_service import get_last_12_months

        result = get_last_12_months()

        # Verificar que devuelve 12 meses
        assert len(result) == 12

        # Verificar que son tuplas (mes, año)
        assert all(isinstance(item, tuple) and len(
            item) == 2 for item in result)

        # Verificar que el último mes es el mes actual
        today = datetime.now()
        last_month, last_year = result[-1]
        from app.constants import MESES
        assert last_month == MESES[today.month - 1]
        assert last_year == today.year

        # Verificar orden cronológico (el primero es 11 meses atrás)
        first_date = today - relativedelta(months=11)
        first_month, first_year = result[0]
        assert first_month == MESES[first_date.month - 1]
        assert first_year == first_date.year

    def test_format_month_year(self):
        """Test formato de mes y año."""
        from app.services.charts_service import format_month_year

        assert format_month_year('Enero', 2026) == "Enero '26"
        assert format_month_year('Diciembre', 2025) == "Diciembre '25"

    @patch('app.services.charts_service.cursor_context')
    def test_generate_pie_chart_con_datos(self, mock_cursor_context):
        """Test generar gráfico de torta cuando hay datos."""
        from app.services.charts_service import generate_pie_chart

        # Mock de datos
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'categoria': 'Compra', 'total': 250.0},
            {'categoria': 'Gasolina', 'total': 150.0}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = generate_pie_chart('Octubre', 2025)

        # Verificar
        assert resultado is not None
        assert isinstance(resultado, str)
        assert 'plotly' in resultado.lower() or 'div' in resultado.lower()
        mock_cursor.execute.assert_called_once()

    @patch('app.services.charts_service.cursor_context')
    def test_generate_pie_chart_sin_datos(self, mock_cursor_context):
        """Test generar gráfico de torta cuando NO hay datos (caso crítico)."""
        from app.services.charts_service import generate_pie_chart

        # Mock sin datos
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = generate_pie_chart('Enero', 2026)

        # Verificar que NO falla, retorna None correctamente
        assert resultado is None

    @patch('app.services.charts_service.cursor_context')
    def test_generate_gas_chart_con_ventana_deslizante(self, mock_cursor_context):
        """Test generar gráfico de gasolina con ventana deslizante de 12 meses."""
        from app.services.charts_service import generate_gas_chart

        # Mock con datos de múltiples meses/años
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'mes': 'Febrero', 'anio': 2025, 'total': 50.0},
            {'mes': 'Marzo', 'anio': 2025, 'total': 60.0},
            {'mes': 'Enero', 'anio': 2026, 'total': 55.0}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar (anio es ignorado ahora)
        resultado = generate_gas_chart()

        # Verificar que NO falla y genera HTML
        assert resultado is not None
        assert isinstance(resultado, str)
        assert 'plotly' in resultado.lower() or 'div' in resultado.lower()

        # Verificar que la query se ejecutó
        mock_cursor.execute.assert_called_once()

        # Verificar que el título menciona 12 meses (evitando problemas con ú en unicode)
        assert '12 meses' in resultado.lower() and 'gasolina' in resultado.lower()

    @patch('app.services.charts_service.cursor_context')
    def test_generate_category_chart_con_ventana_deslizante(self, mock_cursor_context):
        """Test generar gráfico de categoría con ventana deslizante."""
        from app.services.charts_service import generate_category_chart

        # Mock con datos apilados por descripción
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'anio': 2025, 'mes': 'Febrero', 'categoria': 'Compras',
                'descripcion': 'Mercadona', 'total': 100.0},
            {'anio': 2025, 'mes': 'Febrero', 'categoria': 'Compras',
                'descripcion': 'Lidl', 'total': 50.0},
            {'anio': 2025, 'mes': 'Marzo', 'categoria': 'Compras',
                'descripcion': 'Mercadona', 'total': 120.0},
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = generate_category_chart('Compras')

        # Verificar
        assert resultado is not None
        assert isinstance(resultado, str)
        assert 'plotly' in resultado.lower() or 'div' in resultado.lower()
        assert '12 meses' in resultado.lower() and 'compras' in resultado.lower()

    @patch('app.services.charts_service.cursor_context')
    def test_generate_comparison_chart_con_ventana_deslizante(self, mock_cursor_context):
        """Test generar gráfico de comparación con ventana deslizante."""
        from app.services.charts_service import generate_comparison_chart

        # Mock con gastos y presupuestos
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # Primera llamada: gastos
            [
                {'mes': 'Febrero', 'anio': 2025,
                    'total_incluido_resumen': 500.0, 'total_con_todas': 600.0},
                {'mes': 'Marzo', 'anio': 2025,
                    'total_incluido_resumen': 450.0, 'total_con_todas': 550.0}
            ],
            # Segunda llamada: presupuestos
            [
                {'mes': 'Febrero', 'anio': 2025, 'presupuesto_mensual': 700.0},
                {'mes': 'Marzo', 'anio': 2025, 'presupuesto_mensual': 700.0}
            ]
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = generate_comparison_chart()

        # Verificar
        assert resultado is not None
        assert isinstance(resultado, dict)
        assert 'chart' in resultado
        assert 'df_comparacion' in resultado
        assert isinstance(resultado['chart'], str)
        assert 'plotly' in resultado['chart'].lower(
        ) or 'div' in resultado['chart'].lower()
        assert '12 meses' in resultado['chart'].lower(
        ) and 'presupuesto' in resultado['chart'].lower()

        # Verificar que se ejecutaron 2 queries (gastos y presupuestos)
        assert mock_cursor.execute.call_count == 2
