"""
Tests unitarios esenciales para el módulo de charts_service.

Solo cubre las funciones críticas para prevenir fallos visibles al usuario.
"""
from unittest.mock import patch, MagicMock


class TestChartsService:
    """Tests esenciales para generación de gráficos."""

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
    def test_generate_gas_chart_maneja_datos_vacios(self, mock_cursor_context):
        """Test generar gráfico de gasolina con meses vacíos (caso común)."""
        from app.services.charts_service import generate_gas_chart

        # Mock con datos parciales (solo algunos meses)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'mes': 'Enero', 'total': 50.0},
            {'mes': 'Marzo', 'total': 60.0}
        ]
        mock_cursor_context.return_value.__enter__.return_value = (
            None, mock_cursor)

        # Ejecutar
        resultado = generate_gas_chart(2025)

        # Verificar que NO falla con datos parciales
        assert resultado is not None
        assert isinstance(resultado, str)
        assert 'plotly' in resultado.lower() or 'div' in resultado.lower()
