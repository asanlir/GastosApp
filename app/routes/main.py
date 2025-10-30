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
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import csv
from io import StringIO

from app.services import gastos_service, presupuesto_service, categorias_service, charts_service
from app.logging_config import get_logger
from app.exceptions import DatabaseError, ValidationError

logger = get_logger(__name__)

main_bp = Blueprint('main', __name__)


# Lista de rutas para crear aliases y mantener compatibilidad con llamadas a url_for('index') etc.
LEGACY_ROUTES = [
    ("/", "index", ["GET", "POST"]),
    ("/delete/<int:id>", "delete_gasto", ["GET"]),
    ("/edit/<int:id>", "edit_gasto", ["POST"]),
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
                try:
                    if gastos_service.add_gasto(categoria, descripcion, float(monto), mes, int(anio)):
                        flash('Gasto agregado correctamente', 'success')
                    else:
                        flash('Error al agregar el gasto', 'error')
                    return redirect(url_for('main.index', mes=mes, anio=anio))
                except ValidationError as e:
                    flash(str(e), 'error')

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
    logger.info("Intentando eliminar gasto ID: %s", gasto_id)
    gasto = gastos_service.get_gasto_by_id(gasto_id)

    if gasto:
        if gastos_service.delete_gasto(gasto_id):
            flash('Gasto eliminado correctamente')
        else:
            flash('Error al eliminar el gasto', 'error')
        return redirect(url_for('index', mes=gasto['mes'], anio=gasto['anio']))

    flash('Gasto no encontrado', 'error')
    return redirect(url_for('index'))


@main_bp.route('/edit/<int:gasto_id>', methods=['POST'])
def edit_gasto(gasto_id):
    """
    Edita un gasto existente vía POST.

    Args:
        gasto_id (int): ID del gasto a editar

    Form data (POST):
        categoria (str): Nueva categoría
        descripcion (str): Nueva descripción
        monto (float): Nuevo monto
        mes (str): Mes del gasto (para redirección)
        anio (int): Año del gasto (para redirección)

    Returns:
        Redirect a página principal con mensaje flash
    """
    logger.info("Editando gasto ID: %s", gasto_id)

    # Obtener el gasto para verificar que existe
    gasto = gastos_service.get_gasto_by_id(gasto_id)
    if not gasto:
        flash('Gasto no encontrado', 'error')
        return redirect(url_for('main.index'))

    # Obtener datos del formulario
    categoria = request.form['categoria']
    descripcion = request.form['descripcion'].strip()
    monto = request.form['monto']
    mes = request.form.get('mes', gasto['mes'])
    anio = request.form.get('anio', gasto['anio'])

    if gastos_service.update_gasto(gasto_id, categoria, descripcion, float(monto)):
        flash('Gasto actualizado correctamente', 'success')
    else:
        flash('Error al actualizar el gasto', 'error')

    return redirect(url_for('main.index', mes=mes, anio=anio))


@main_bp.route('/get_gasto/<int:gasto_id>', methods=['GET'])
def get_gasto(gasto_id):
    """
    Obtiene los datos de un gasto en formato JSON para el modal de edición.

    Args:
        gasto_id (int): ID del gasto a obtener

    Returns:
        JSON con los datos del gasto o error 404
    """
    from flask import jsonify

    gasto = gastos_service.get_gasto_by_id(gasto_id)
    if not gasto:
        return jsonify({'error': 'Gasto no encontrado'}), 404

    return jsonify(gasto)


@main_bp.route('/gastos', methods=['GET', 'POST'])
def ver_gastos():
    """
    Vista de histórico de gastos con filtros opcionales y paginación.

    GET: Muestra gastos con filtros de URL
    POST: Aplica filtros y redirige a GET con parámetros

    Form data (POST):
        mes (str, opcional): Filtrar por mes
        anio (int, opcional): Filtrar por año
        categoria (str, opcional): Filtrar por categoría

    Query params:
        page (int): Número de página (default: 1)
        mes (str, opcional): Filtro de mes
        anio (int, opcional): Filtro de año
        categoria (str, opcional): Filtro de categoría

    Returns:
        Template 'gastos.html' con lista de gastos filtrados y paginados
    """
    logger.debug("Acceso a histórico de gastos")
    categorias = categorias_service.list_categorias()
    categorias_nombres = [cat['nombre'] for cat in categorias]

    # Si es POST, redirigir a GET con los filtros en la URL
    if request.method == "POST":
        mes = request.form.get("mes", "")
        anio = request.form.get("anio", "")
        categoria = request.form.get("categoria", "")

        return redirect(url_for('main.ver_gastos',
                                mes=mes,
                                anio=anio,
                                categoria=categoria,
                                page=1))

    # Obtener filtros de los parámetros de la URL (GET)
    filtros = {}
    mes = request.args.get("mes", "")
    if mes and mes.strip():
        filtros["mes"] = mes

    anio = request.args.get("anio", "")
    if anio and anio.strip():
        filtros["anio"] = int(anio)

    categoria = request.args.get("categoria", "")
    if categoria and categoria.strip():
        filtros["categoria"] = categoria

    # Obtener gastos filtrados
    gastos_completos = gastos_service.list_gastos(**filtros)

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 20
    total_gastos = len(gastos_completos)
    # Redondeo hacia arriba
    total_pages = (total_gastos + per_page - 1) // per_page

    # Calcular índices de slice
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    gastos_pagina = gastos_completos[start_idx:end_idx]

    return render_template('gastos.html',
                           gastos=gastos_pagina,
                           categorias=categorias_nombres,
                           filtros=filtros,
                           page=page,
                           total_pages=total_pages,
                           total_gastos=total_gastos)


@main_bp.route('/gastos/descargar', methods=['GET'])
def descargar_gastos():
    """
    Descarga los gastos filtrados en formato CSV.

    Query params:
        mes (str, opcional): Filtrar por mes
        anio (int, opcional): Filtrar por año
        categoria (str, opcional): Filtrar por categoría

    Returns:
        Archivo CSV con los gastos filtrados
    """
    logger.debug("Descargando gastos en CSV")
    filtros = {}

    # Solo añadir filtros si tienen valor (no vacíos)
    mes = request.args.get("mes", "")
    if mes and mes.strip():
        filtros["mes"] = mes

    anio = request.args.get("anio", "")
    if anio and anio.strip():
        filtros["anio"] = int(anio)

    categoria = request.args.get("categoria", "")
    if categoria and categoria.strip():
        filtros["categoria"] = categoria

    # Obtener gastos filtrados
    gastos = gastos_service.list_gastos(**filtros)

    # Crear CSV en memoria
    si = StringIO()
    writer = csv.writer(si)

    # Escribir encabezados
    writer.writerow(['ID', 'Categoría', 'Descripción',
                    'Monto (€)', 'Mes', 'Año'])

    # Escribir datos
    for gasto in gastos:
        writer.writerow([
            gasto.get('id', ''),
            gasto.get('categoria', ''),
            gasto.get('descripcion', ''),
            gasto.get('monto', ''),
            gasto.get('mes', ''),
            gasto.get('anio', '')
        ])

    # Crear respuesta
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=gastos.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"

    return output


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
    total_gastos = float(sum(gasto['monto'] for gasto in gastos_mes))

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
                           gastos_mes=gastos_mes,
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
            return redirect(url_for('main.config'))

        elif "eliminar_categoria" in request.form:
            try:
                categoria_id = int(request.form["eliminar_categoria"])
                if categorias_service.delete_categoria(categoria_id):
                    flash("Categoría eliminada correctamente", "success")
                else:
                    flash("Error al eliminar la categoría", "error")
            except ValueError as e:
                flash(str(e), "error")
            except DatabaseError as e:
                logger.error(
                    "Error de base de datos al eliminar categoría: %s", e)
                flash("Error inesperado al eliminar la categoría", "error")
            return redirect(url_for('main.config'))

        elif "editar_categoria" in request.form:
            try:
                categoria_id = int(request.form["categoria_id"])
                nuevo_nombre = request.form["editar_categoria"].strip()
                logger.debug(
                    "Intentando editar categoría ID %s con nuevo nombre: %s", categoria_id, nuevo_nombre)
                if nuevo_nombre and categorias_service.update_categoria(categoria_id, nuevo_nombre):
                    flash("Categoría actualizada correctamente", "success")
                    logger.info(
                        "Categoría %s actualizada a '%s'", categoria_id, nuevo_nombre)
                else:
                    flash("Error al actualizar la categoría", "error")
                    logger.warning(
                        "Fallo al actualizar categoría %s", categoria_id)
            except (ValueError, ValidationError) as e:
                flash(str(e), "error")
                logger.error(
                    "Error de validación al actualizar categoría: %s", e)
            except DatabaseError as e:
                logger.error(
                    "Error de base de datos al actualizar categoría: %s", e)
                flash("Error inesperado al actualizar la categoría", "error")
            return redirect(url_for('main.config'))

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
            return redirect(url_for('main.config'))

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
