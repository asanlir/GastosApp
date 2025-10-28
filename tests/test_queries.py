"""
Tests unitarios para el módulo de queries SQL.

Verifican que cada función genera el SQL correcto con los parámetros esperados.
No requieren conexión a DB (son tests puros de lógica).
"""
from app.queries import (
    q_gasto_by_id,
    q_list_gastos,
    q_categoria_nombre_by_id,
    q_insert_gasto,
    q_update_gasto,
    q_delete_gasto,
    q_total_gastos,
    q_presupuesto_vigente,
    q_historial_presupuestos,
    q_presupuesto_exists,
    q_update_presupuesto,
    q_insert_presupuesto,
    q_sum_gastos_hasta_mes,
    q_list_categorias,
    q_insert_categoria,
    q_update_categoria,
    q_delete_categoria,
    q_gastos_por_categoria_mes,
    q_gasolina_por_mes,
    q_historico_categoria_grouped,
    q_gastos_mensuales_aggregates,
    q_presupuestos_mensuales_por_anio,
)


class TestGastosQueries:
    """Tests para queries de gastos."""

    def test_q_gasto_by_id(self):
        """Verifica query para obtener gasto por ID."""
        sql, params = q_gasto_by_id(42)

        assert "SELECT" in sql
        assert "FROM gastos g" in sql
        assert "LEFT JOIN categorias c" in sql
        assert "WHERE g.id = %s" in sql
        assert params == (42,)

    def test_q_list_gastos_sin_filtros(self):
        """Verifica query para listar todos los gastos."""
        sql, params = q_list_gastos()

        assert "SELECT" in sql
        assert "FROM gastos g" in sql
        assert "WHERE 1=1" in sql
        assert "ORDER BY" in sql
        assert params == []

    def test_q_list_gastos_con_mes_anio(self):
        """Verifica query con filtros de mes y año."""
        sql, params = q_list_gastos(mes="Octubre", anio=2025)

        assert "AND g.mes = %s" in sql
        assert "AND g.anio = %s" in sql
        assert params == ["Octubre", 2025]

    def test_q_list_gastos_con_categoria(self):
        """Verifica query con filtro de categoría."""
        sql, params = q_list_gastos(categoria="Compra")

        assert "AND g.categoria = %s" in sql
        assert params == ["Compra"]

    def test_q_list_gastos_con_todos_filtros(self):
        """Verifica query con todos los filtros combinados."""
        sql, params = q_list_gastos(
            mes="Octubre", anio=2025, categoria="Compra")

        assert "AND g.mes = %s" in sql
        assert "AND g.anio = %s" in sql
        assert "AND g.categoria = %s" in sql
        assert params == ["Octubre", 2025, "Compra"]

    def test_q_categoria_nombre_by_id(self):
        """Verifica query para obtener nombre de categoría."""
        sql = q_categoria_nombre_by_id()

        assert "SELECT nombre" in sql
        assert "FROM categorias" in sql
        assert "WHERE id = %s" in sql

    def test_q_insert_gasto(self):
        """Verifica query para insertar gasto."""
        sql = q_insert_gasto()

        assert "INSERT INTO gastos" in sql
        assert "(categoria, descripcion, monto, mes, anio)" in sql
        assert "VALUES (%s, %s, %s, %s, %s)" in sql

    def test_q_update_gasto(self):
        """Verifica query para actualizar gasto."""
        sql = q_update_gasto()

        assert "UPDATE gastos" in sql
        assert "SET categoria = %s, descripcion = %s, monto = %s" in sql
        assert "WHERE id = %s" in sql

    def test_q_delete_gasto(self):
        """Verifica query para eliminar gasto."""
        sql = q_delete_gasto()

        assert "DELETE FROM gastos" in sql
        assert "WHERE id = %s" in sql

    def test_q_total_gastos_sin_filtros(self):
        """Verifica query para total sin filtros."""
        sql, params = q_total_gastos()

        assert "SELECT SUM(monto) as total" in sql
        assert "FROM gastos" in sql
        assert "WHERE 1=1" in sql
        assert params == []

    def test_q_total_gastos_con_filtros(self):
        """Verifica query para total con filtros."""
        sql, params = q_total_gastos(mes="Octubre", anio=2025)

        assert "AND mes = %s" in sql
        assert "AND anio = %s" in sql
        assert params == ["Octubre", 2025]


class TestPresupuestoQueries:
    """Tests para queries de presupuesto."""

    def test_q_presupuesto_vigente(self):
        """Verifica query para presupuesto vigente."""
        sql = q_presupuesto_vigente()

        assert "SELECT monto" in sql
        assert "FROM presupuesto" in sql
        assert "WHERE (anio < %s)" in sql
        assert "ORDER BY anio DESC" in sql
        assert "LIMIT 1" in sql

    def test_q_historial_presupuestos(self):
        """Verifica query para historial de presupuestos."""
        sql = q_historial_presupuestos()

        assert "SELECT mes, anio, monto" in sql
        assert "FROM presupuesto" in sql
        assert "ORDER BY anio" in sql

    def test_q_presupuesto_exists(self):
        """Verifica query para verificar existencia de presupuesto."""
        sql = q_presupuesto_exists()

        assert "SELECT id" in sql
        assert "FROM presupuesto" in sql
        assert "WHERE mes = %s AND anio = %s" in sql

    def test_q_update_presupuesto(self):
        """Verifica query para actualizar presupuesto."""
        sql = q_update_presupuesto()

        assert "UPDATE presupuesto" in sql
        assert "SET monto = %s" in sql
        assert "WHERE mes = %s AND anio = %s" in sql

    def test_q_insert_presupuesto(self):
        """Verifica query para insertar presupuesto."""
        sql = q_insert_presupuesto()

        assert "INSERT INTO presupuesto" in sql
        assert "(mes, anio, monto)" in sql
        assert "VALUES (%s, %s, %s)" in sql

    def test_q_sum_gastos_hasta_mes(self):
        """Verifica query para suma de gastos hasta mes."""
        sql = q_sum_gastos_hasta_mes()

        assert "SELECT SUM(monto) AS total_gastos" in sql
        assert "FROM gastos" in sql
        assert "WHERE anio = %s" in sql
        assert "FIELD" in sql  # Ordenación por meses


class TestCategoriasQueries:
    """Tests para queries de categorías."""

    def test_q_list_categorias(self):
        """Verifica query para listar categorías."""
        sql = q_list_categorias()

        assert "SELECT *" in sql
        assert "FROM categorias" in sql
        assert "ORDER BY nombre ASC" in sql

    def test_q_insert_categoria(self):
        """Verifica query para insertar categoría."""
        sql = q_insert_categoria()

        assert "INSERT INTO categorias" in sql
        assert "(nombre)" in sql
        assert "VALUES (%s)" in sql

    def test_q_update_categoria(self):
        """Verifica query para actualizar categoría."""
        sql = q_update_categoria()

        assert "UPDATE categorias" in sql
        assert "SET nombre = %s" in sql
        assert "WHERE id = %s" in sql

    def test_q_delete_categoria(self):
        """Verifica query para eliminar categoría."""
        sql = q_delete_categoria()

        assert "DELETE FROM categorias" in sql
        assert "WHERE id = %s" in sql


class TestGraficosQueries:
    """Tests para queries de gráficos."""

    def test_q_gastos_por_categoria_mes(self):
        """Verifica query para gastos por categoría en un mes."""
        sql = q_gastos_por_categoria_mes()

        assert "SELECT categoria, SUM(monto) as total" in sql
        assert "FROM gastos" in sql
        assert "WHERE mes = %s AND anio = %s" in sql
        assert "GROUP BY categoria" in sql

    def test_q_gasolina_por_mes(self):
        """Verifica query para gastos de gasolina por mes."""
        sql = q_gasolina_por_mes()

        assert "SELECT mes, SUM(monto) AS total" in sql
        assert "FROM gastos" in sql
        assert "WHERE categoria = 'Gasolina'" in sql
        assert "GROUP BY mes" in sql

    def test_q_historico_categoria_grouped(self):
        """Verifica query para histórico de categoría agrupado."""
        sql = q_historico_categoria_grouped()

        assert "SELECT anio, mes, categoria, descripcion, SUM(monto) AS total" in sql
        assert "FROM gastos" in sql
        assert "WHERE categoria = %s" in sql
        assert "GROUP BY" in sql

    def test_q_gastos_mensuales_aggregates(self):
        """Verifica query para agregados mensuales."""
        sql = q_gastos_mensuales_aggregates()

        assert "SELECT mes" in sql
        assert "SUM(CASE WHEN categoria = 'Alquiler' THEN 0 ELSE monto END)" in sql
        assert "SUM(monto) as total_con_alquiler" in sql
        assert "WHERE anio = %s" in sql

    def test_q_presupuestos_mensuales_por_anio(self):
        """Verifica query para presupuestos mensuales por año."""
        sql = q_presupuestos_mensuales_por_anio()

        assert "SELECT mes, monto as presupuesto_mensual" in sql
        assert "FROM presupuesto" in sql
        assert "WHERE anio = %s" in sql


class TestPlaceholdersSeguros:
    """Tests que verifican el uso seguro de placeholders."""

    def test_no_sql_injection_en_params(self):
        """Verifica que no se formatean valores directamente en SQL."""
        # Intentar inyección SQL en parámetros
        sql, params = q_list_gastos(mes="'; DROP TABLE gastos; --")

        # El valor malicioso debe estar en params, no en sql
        assert "DROP TABLE" not in sql
        assert "'; DROP TABLE gastos; --" in params

    def test_todos_placeholders_son_percent_s(self):
        """Verifica que todos los placeholders usan %s."""
        queries_to_test = [
            q_insert_gasto(),
            q_update_gasto(),
            q_delete_gasto(),
            q_insert_categoria(),
            q_update_categoria(),
            q_delete_categoria(),
            q_insert_presupuesto(),
            q_update_presupuesto(),
        ]

        for sql in queries_to_test:
            # Contar placeholders %s
            placeholder_count = sql.count("%s")
            assert placeholder_count > 0, f"Query sin placeholders: {sql[:50]}..."

            # Verificar que no hay otros formatos peligrosos
            assert "%d" not in sql
            assert "%f" not in sql
            assert ".format" not in sql
