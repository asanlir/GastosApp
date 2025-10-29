"""
Módulo de rutas principales de la aplicación Flask.

Este módulo contiene todos los endpoints web de la aplicación:
- Gestión de gastos (CRUD completo)
- Visualización de reportes y estadísticas
- Configuración de categorías y presupuestos

Todas las rutas están registradas en el blueprint 'main' y se mantiene
compatibilidad con endpoints legacy mediante LEGACY_ROUTES.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.services import gastos_service, presupuesto_service, categorias_service, charts_service
from app.logging_config import get_logger

logger = get_logger(__name__)

main_bp = Blueprint('main', __name__)


# Lista de rutas para crear aliases y mantener compatibilidad con llamadas a url_for('index') etc.
LEGACY_ROUTES = [
    ("/", "index", ["GET", "POST"]),
    ("/delete/<int:id>", "delete_gasto", ["GET"]),
    ("/edit/<int:id>", "edit_gasto", ["GET", "POST"]),
    ("/gastos", "ver_gastos", ["GET", "POST"]),
    ("/report", "report", ["GET", "POST"]),
    ("/config", "config", ["GET", "POST"]),
]


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Página principal de la aplicación - Dashboard de gastos.

    GET: Muestra el dashboard con gastos del mes actual/seleccionado
    POST: Procesa nuevo gasto o cambio de mes/año

    Query params:
        mes (str): Mes a visualizar (default: mes actual)
        anio (int): Año a visualizar (default: año actual)

    Form data (POST):
        - Para agregar gasto: categoria, descripcion, monto, mes, anio
        - Para cambiar mes: mes, anio

    Returns:
        Template 'index.html' con gastos, categorías y presupuesto
    """
    logger.debug("Acceso a página principal")
    # Usar la fuente única de meses desde charts_service/constants
    meses = charts_service.get_months()
    mes_actual = request.args.get("mes", meses[datetime.now().month - 1])
    anio_actual = request.args.get("anio", datetime.now().year, type=int)

    # Obtener presupuesto vigente y categorías
    presupuesto_mensual = presupuesto_service.get_presupuesto_mensual(
        mes_actual, anio_actual)
    categorias = categorias_service.list_categorias()

    if request.method == "POST":
        if "categoria" in request.form:
            # Procesar nuevo gasto
            categoria = request.form["categoria"].strip()
            descripcion = request.form["descripcion"].strip()
            monto = request.form["monto"]
            mes = request.form["mes"]
            anio = request.form["anio"]

            if not categoria or not monto or not mes or not anio:
                flash('Todos los campos son obligatorios', 'error')
            else:
                if gastos_service.add_gasto(categoria, descripcion, float(monto), mes, int(anio)):
                    flash('Gasto agregado correctamente', 'success')
                else:
                    flash('Error al agregar el gasto', 'error')
                return redirect(url_for('main.index', mes=mes, anio=anio))

        elif "mes" in request.form:
            # Cambiar mes/año seleccionado
            mes_actual = request.form["mes"]
            anio_actual = int(
                request.form["anio"]) if request.form["anio"] else anio_actual
            return redirect(url_for('main.index', mes=mes_actual, anio=anio_actual))

    # Obtener datos del mes actual
    gastos = gastos_service.list_gastos(mes=mes_actual, anio=anio_actual)
    total_gastos = gastos_service.get_total_gastos(mes_actual, anio_actual)
    acumulado_presupuesto = presupuesto_service.calcular_acumulado(
        mes_actual, anio_actual)
    return render_template(
        "index.html",
        categorias=categorias,
        gastos=gastos,
        total_gastos=total_gastos,
        presupuesto_mensual=presupuesto_mensual,
        acumulado_presupuesto=acumulado_presupuesto,
        mes_actual=mes_actual,
        anio_actual=anio_actual
    )


@main_bp.route('/delete/<int:gasto_id>', methods=['GET'])
def delete_gasto(gasto_id):
    """
    Elimina un gasto existente.

    Args:
        gasto_id (int): ID del gasto a eliminar

    Returns:
        Redirect a la página principal con mensaje flash
    """
    logger.info(f"Intentando eliminar gasto ID: {gasto_id}")
    gasto = gastos_service.get_gasto_by_id(gasto_id)

    if gasto:
        if gastos_service.delete_gasto(gasto_id):
            flash('Gasto eliminado correctamente')
        else:
            flash('Error al eliminar el gasto', 'error')
        return redirect(url_for('index', mes=gasto['mes'], anio=gasto['anio']))

    flash('Gasto no encontrado', 'error')
    return redirect(url_for('index'))


@main_bp.route('/edit/<int:gasto_id>', methods=['GET', 'POST'])
def edit_gasto(gasto_id):
    """
    Edita un gasto existente.

    GET: Muestra formulario de edición con datos actuales
    POST: Procesa la actualización del gasto

    Args:
        gasto_id (int): ID del gasto a editar

    Form data (POST):
        categoria (str): Nueva categoría
        descripcion (str): Nueva descripción
        monto (float): Nuevo monto

    Returns:
        GET: Template 'edit_gasto.html'
        POST: Redirect a página principal
    """
    logger.info(f"Editando gasto ID: {gasto_id}")
    # Obtener el gasto
    gasto = gastos_service.get_gasto_by_id(gasto_id)
    if not gasto:
        flash('Gasto no encontrado')
        return redirect(url_for('index'))

    if request.method == 'POST':
        categoria_id = request.form['categoria']
        descripcion = request.form['descripcion'].strip()
        monto = request.form['monto']

        if gastos_service.update_gasto(gasto_id, categoria_id, descripcion, float(monto)):
            flash('Gasto actualizado correctamente')
        else:
            flash('Error al actualizar el gasto', 'error')

        return redirect(url_for('index', mes=gasto['mes'], anio=gasto['anio']))

    categorias = categorias_service.list_categorias()
    return render_template('edit_gasto.html', gasto=gasto, categorias=categorias)


@main_bp.route('/gastos', methods=['GET', 'POST'])
def ver_gastos():
    """
    Vista de histórico de gastos con filtros opcionales.

    GET: Muestra todos los gastos sin filtros
    POST: Aplica filtros de búsqueda

    Form data (POST):
        mes (str, opcional): Filtrar por mes
        anio (int, opcional): Filtrar por año
        categoria (str, opcional): Filtrar por categoría

    Returns:
        Template 'gastos.html' con lista de gastos filtrados
    """
    logger.debug("Acceso a histórico de gastos")
    categorias = categorias_service.list_categorias()
    categorias_nombres = [cat['nombre'] for cat in categorias]
    filtros = {}

    if request.method == "POST":
        if request.form.get("mes"):
            filtros["mes"] = request.form["mes"]
        if request.form.get("anio"):
            filtros["anio"] = int(request.form["anio"])
        if request.form.get("categoria"):
            filtros["categoria"] = request.form["categoria"]

    # Obtener gastos filtrados
    gastos = gastos_service.list_gastos(**filtros)

    return render_template('gastos.html',
                           gastos=gastos,
                           categorias=categorias_nombres,
                           filtros=filtros)


@main_bp.route('/report', methods=['GET', 'POST'])
def report():
    """
    Página de reportes y estadísticas visuales.

    Genera gráficos interactivos con Plotly:
    - Gráfico de torta: distribución de gastos por categoría
    - Gráficos de barras: evolución de gastos por categoría
    - Gráfico de barras: total de gastos vs presupuesto

    GET: Muestra reportes del mes actual
    POST: Actualiza reportes según mes/año seleccionado

    Query params / Form data:
        mes (str): Mes a visualizar (default: mes actual)
        anio (int): Año a visualizar (default: año actual)

    Returns:
        Template 'report.html' con gráficos HTML generados
    """
    logger.debug("Generando reportes y gráficos")
    meses = charts_service.get_months()
    mes_actual = meses[datetime.now().month - 1]
    anio_actual = datetime.now().year

    if request.method == "POST" and "mes" in request.form and "anio" in request.form:
        mes_actual = request.form["mes"]
        anio_actual = int(request.form["anio"])

    # Obtener presupuesto y gastos del mes
    presupuesto_mensual = presupuesto_service.get_presupuesto_mensual(
        mes_actual, anio_actual)
    gastos_mes = gastos_service.list_gastos(mes=mes_actual, anio=anio_actual)
    total_gastos = sum(gasto['monto'] for gasto in gastos_mes)

    # Generar gráficos
    fig_pie = charts_service.generate_pie_chart(mes_actual, anio_actual)
    fig_compras = charts_service.generate_category_bar_chart(
        "Compra", anio_actual)
    fig_facturas = charts_service.generate_category_bar_chart(
        "Facturas", anio_actual)
    fig_gasolina = charts_service.generate_category_bar_chart(
        "Gasolina", anio_actual)

    comparison_data = charts_service.generate_comparison_chart(anio_actual)
    fig_sin_alquiler = comparison_data['chart']

    return render_template('report.html',
                           meses=meses,
                           mes_actual=mes_actual,
                           anio_actual=anio_actual,
                           presupuesto_mensual=presupuesto_mensual,
                           total_gastos=total_gastos,
                           fig_pie=fig_pie,
                           fig_compras=fig_compras,
                           fig_facturas=fig_facturas,
                           fig_gasolina=fig_gasolina,
                           fig_sin_alquiler=fig_sin_alquiler)


@main_bp.route('/config', methods=['GET', 'POST'])
def config():
    """
    Página de configuración de la aplicación.

    Permite gestionar:
    - Categorías de gastos (crear, editar, eliminar)
    - Presupuesto mensual (establecer/actualizar)

    GET: Muestra formularios de configuración
    POST: Procesa operaciones de gestión

    Form data (POST):
        - Para categoría: nueva_categoria, eliminar_categoria, editar_categoria
        - Para presupuesto: monto, mes, anio

    Returns:
        Template 'config.html' con categorías y presupuestos
    """
    logger.debug("Acceso a página de configuración")
    meses = charts_service.get_months()
    mes_actual = request.args.get("mes", meses[datetime.now().month - 1])
    anio_actual = request.args.get("anio", datetime.now().year, type=int)

    if request.method == "POST":
        if "nueva_categoria" in request.form:
            nueva_categoria = request.form["nueva_categoria"].strip()
            if nueva_categoria and categorias_service.add_categoria(nueva_categoria):
                flash("Categoría agregada correctamente", "success")
            else:
                flash("Error al agregar la categoría", "error")

        elif "eliminar_categoria" in request.form:
            categoria_id = int(request.form["eliminar_categoria"])
            if categorias_service.delete_categoria(categoria_id):
                flash("Categoría eliminada correctamente", "success")
            else:
                flash("Error al eliminar la categoría", "error")

        elif "presupuesto_mensual" in request.form:
            try:
                nuevo_presupuesto = float(
                    request.form["presupuesto_mensual"].strip())
                if presupuesto_service.update_presupuesto(mes_actual, anio_actual, nuevo_presupuesto):
                    flash("Presupuesto actualizado correctamente", "success")
                else:
                    flash("Error al actualizar el presupuesto", "error")
            except ValueError:
                flash(
                    "Por favor, introduce un valor numérico válido para el presupuesto", "error")

    categorias = categorias_service.list_categorias()
    presupuesto_actual = presupuesto_service.get_presupuesto_mensual(
        mes_actual, anio_actual)

    return render_template(
        "config.html",
        categorias=categorias,
        presupuesto_actual=presupuesto_actual,
        mes_actual=mes_actual,
        anio_actual=anio_actual,
        meses=meses
    )
