import os
from datetime import datetime
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv


# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la base de datos usando variables de entorno
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    'port': os.getenv('DB_PORT', 3306)
}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Prueba de conexión a la base de datos
try:
    conn = mysql.connector.connect(**db_config)
    print("✅ Conexión a la base de datos exitosa")
    conn.close()
except mysql.connector.Error as err:
    print(f"❌ Error al conectar con la base de datos: {err}")


@app.route("/", methods=['GET', 'POST'])
def index():
    # Obtener la fecha actual
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = request.args.get("mes", meses[datetime.now().month - 1])
    anio_actual = request.args.get("anio", datetime.now().year, type=int)

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener el presupuesto más reciente
    cursor.execute("""
                SELECT monto 
                FROM presupuesto 
                WHERE (anio < %s) 
                OR (anio = %s AND FIELD(mes, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre') 
                    <= FIELD(%s, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'))
                ORDER BY anio DESC, 
                FIELD(mes, 'Diciembre', 'Noviembre', 'Octubre', 'Septiembre', 'Agosto', 'Julio', 
                        'Junio', 'Mayo', 'Abril', 'Marzo', 'Febrero', 'Enero') 
                LIMIT 1;
                """,
                (anio_actual, anio_actual, mes_actual))
    presupuesto_result = cursor.fetchone()
    presupuesto_mensual = presupuesto_result["monto"] if presupuesto_result else 0

    # Obtener la lista de categorías
    cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC;")
    categorias = cursor.fetchall()

    # Si se envía un formulario para agregar un gasto
    if request.method == "POST" and "categoria" in request.form:
        categoria = request.form["categoria"].strip()
        descripcion = request.form["descripcion"].strip()
        monto = request.form["monto"]
        mes = request.form["mes"]
        anio = request.form["anio"]

        # Validar datos
        if not categoria or not monto or not mes or not anio:
            flash('Todos los campos son obligatorios', 'error')
        else:
            try:
                # Obtener el nombre real de la categoría (evita que se guarde un valor incorrecto)
                cursor.execute("SELECT nombre FROM categorias WHERE id = %s;", (categoria,))
                categoria_result = cursor.fetchone()

                if categoria_result:
                    categoria = categoria_result["nombre"]
                else:
                    categoria = "Sin categoría"  # Si no existe, evitar errores
                
                # Insertar datos en la base de datos
                query = """INSERT INTO gastos (categoria, descripcion, monto, mes, anio)
                        VALUES (%s, %s, %s, %s, %s);"""
                cursor.execute(query, (categoria, descripcion, float(monto), mes, int(anio)))

                # Confirmar cambios
                conn.commit()

                flash('Gasto agregado correctamente', 'success')
            except Exception as e:
                flash(f"Error al agregar el gasto: {e}", 'error')

            return redirect(url_for('index', mes=mes, anio=anio))

    # Si se está filtrando por mes y año
    if request.method == "POST" and "mes" in request.form:
        mes_actual = request.form["mes"]
        anio_actual = int(request.form["anio"]) if request.form["anio"] else anio_actual
        return redirect(url_for('index', mes=mes_actual, anio=anio_actual))

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener los gastos del mes y año seleccionados
    cursor.execute("""
            SELECT gastos.id, 
                categorias.nombre AS categoria, 
                gastos.descripcion, 
                gastos.monto, 
                gastos.mes, 
                gastos.anio
            FROM gastos
            LEFT JOIN categorias 
                ON gastos.categoria = categorias.nombre
            WHERE gastos.mes = %s AND gastos.anio = %s
            ORDER BY gastos.id ASC;
            """,
            (mes_actual, anio_actual))
    gastos = cursor.fetchall()

    # Calcular la suma de los gastos
    total_gastos = sum(gasto['monto'] for gasto in gastos)

    cursor.close()
    conn.close()

    # Renderizar la plantilla
    return render_template(
        "index.html", 
        categorias=categorias,
        gastos=gastos,
        total_gastos=total_gastos,
        presupuesto_mensual=presupuesto_mensual,
        mes_actual=mes_actual,
        anio_actual=anio_actual
    )


@app.route('/delete/<int:id>', methods=['GET'])
def delete_gasto(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener el mes y año del gasto antes de eliminarlo
    cursor.execute("SELECT mes, anio FROM gastos WHERE id = %s;", (id,))
    gasto = cursor.fetchone()

    # Eliminar el gasto de la base de datos
    if gasto:
        cursor.execute("DELETE FROM gastos WHERE id = %s;", (id,))
        conn.commit()
        flash('Gasto eliminado correctamente')

    cursor.close()
    conn.close()

    return redirect(url_for('index', mes=gasto['mes'], anio=gasto['anio']) if gasto else url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_gasto(id):

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener el gasto a editar
    cursor.execute("SELECT * FROM gastos WHERE id = %s;", (id,))
    gasto = cursor.fetchone()

    # Obtener la lista de categorías para el desplegable
    cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC;")
    categorias = cursor.fetchall()

    if request.method == 'POST':
        categoria = request.form['categoria']
        descripcion = request.form['descripcion'].strip()
        monto = float(request.form['monto'])

        # Actualizar el gasto en la base de datos
        cursor.execute("""
                    UPDATE gastos
                    SET categoria = %s, descripcion = %s, monto = %s
                    WHERE id = %s;
                    """,
                    (categoria, descripcion, monto, id))
        conn.commit()

        cursor.close()
        conn.close()

        flash('Gasto actualizado correctamente')
        return redirect(url_for('index', mes=gasto['mes'], anio=gasto['anio']))

    cursor.close()
    conn.close()

    return render_template('edit_gasto.html', gasto=gasto, categorias=categorias)


# Ruta para ver todos los gastos
@app.route('/gastos', methods=['GET', 'POST'])
def ver_gastos():

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener todas las categorías para el filtro
    cursor.execute("SELECT nombre FROM categorias ORDER BY nombre ASC;")
    categorias = [row['nombre'] for row in cursor.fetchall()]

    # Valores por defecto: sin filtros (mostrar todos los gastos)
    query = "SELECT * FROM gastos"
    params = []
    filtros = {}

    if request.method == "POST":
        condiciones = []

        # Verificar si se filtró por mes
        if request.form.get("mes"):
            filtros["mes"] = request.form["mes"]
            condiciones.append("mes = %s")
            params.append(request.form["mes"])

        # Verificar si se filtró por año
        if request.form.get("anio"):
            filtros["anio"] = int(request.form["anio"])
            condiciones.append("anio = %s")
            params.append(filtros["anio"])

        # Verificar si se filtró por categoría
        if request.form.get("categoria"):
            filtros["categoria"] = request.form["categoria"]
            condiciones.append("categoria = %s")
            params.append(filtros["categoria"])

        # Construir la consulta SQL con filtros si existen
        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

    # Ordenar los gastos por año y mes de forma descendente
    query += """ ORDER BY anio DESC,
                FIELD(mes, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre') DESC;
                """

    cursor.execute(query, tuple(params))
    gastos = cursor.fetchall()

    # Cerrar la conexión
    cursor.close()
    conn.close()

    return render_template('gastos.html', gastos=gastos, categorias=categorias, filtros=filtros)


@app.route("/report", methods=["GET", "POST"])
def report():
    # Obtener el mes y año seleccionados (o usar los valores actuales por defecto)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = meses[datetime.now().month - 1]
    anio_actual = datetime.now().year

    # Si se selecciona otro mes, obtenemos la fecha desde el formulario
    if request.method == "POST" and "mes" in request.form and "anio" in request.form:
        mes_actual = request.form["mes"]
        anio_actual = int(request.form["anio"])

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener el presupuesto mensual desde la base de datos
    cursor.execute("""
                SELECT monto 
                FROM presupuesto 
                WHERE (anio < %s) 
                OR (anio = %s AND FIELD(mes, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre') 
                    <= FIELD(%s, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'))
                ORDER BY anio DESC, 
                FIELD(mes, 'Diciembre', 'Noviembre', 'Octubre', 'Septiembre', 'Agosto', 'Julio', 
                        'Junio', 'Mayo', 'Abril', 'Marzo', 'Febrero', 'Enero') 
                LIMIT 1;
                """,
                (anio_actual, anio_actual, mes_actual))
    presupuesto_mensual = cursor.fetchone()
    presupuesto_mensual = presupuesto_mensual['monto'] if presupuesto_mensual else 0

    # Obtener los gastos del mes y año seleccionados
    cursor.execute("SELECT * FROM gastos WHERE mes = %s AND anio = %s;",
                (mes_actual, anio_actual))
    gastos_mes = cursor.fetchall()
    total_gastos = sum(gasto['monto'] for gasto in gastos_mes)

    # GRÁFICO DE TORTA
    cursor.execute("""SELECT categoria, SUM(monto) as total FROM gastos
                WHERE mes = %s AND anio = %s
                GROUP BY categoria
                ORDER BY categoria;""",
                (mes_actual, anio_actual))
    gastos_por_categoria = cursor.fetchall()

    # Crear un gráfico de torta con Plotly
    if gastos_por_categoria:
        #gastos_por_categoria = sorted(gastos_mes, key=lambda x: x['categoria'])
        categorias = [gasto['categoria'] for gasto in gastos_por_categoria]
        montos = [gasto['total'] for gasto in gastos_por_categoria]
        fig_pie = go.Figure(data=[go.Pie(labels=categorias, values=montos, sort=False)])
    else:
        fig_pie = None # Evita errores si no hay gastos

    # Obtener los datos para los gráficos de barras apiladas
    cursor.execute("""
                SELECT anio, mes, categoria, descripcion, SUM(monto) AS total
                FROM gastos
                WHERE categoria IN ('Facturas', 'Gasolina', 'Compra')
                GROUP BY anio, mes, categoria, descripcion
                ORDER BY anio ASC, FIELD(mes, %s);""",
                (",".join(meses),)
            )

    datos_historico = cursor.fetchall()
    conn.close()

    # Crear un DataFrame de Pandas con los datos
    df = pd.DataFrame(datos_historico, columns=["anio", "mes", "categoria", "descripcion", "total"])

    # Crear un DataFrame con todos los meses del año actual
    df_fechas = pd.DataFrame({
        "anio": [anio_actual] * 12,
        "mes": meses
    })

    # Unir ambos DataFrames para tener todos los meses, incluso si no hay gastos
    df = df_fechas.merge(df, on=["anio", "mes"], how="left").fillna(0)

    # Asegurar que los meses están ordenados correctamente
    df["mes"] = pd.Categorical(df['mes'], categories=meses, ordered=True)
    df = df.sort_values(["anio", "mes"])

    # Crear la columna orden_fecha en formato "Enero 2025"
    df["orden_fecha"] = df.apply(lambda row: f"{row['mes']} {row['anio']}", axis=1)

    # GRÁFICAS DE BARRAS APILADAS los últimos 12 meses
    def crear_grafico_barras(categoria):
        df_categoria = df[df['categoria'] == categoria]

        # Lista de todos los meses, incluso los que tienen 0 gastos
        meses_completos = df['orden_fecha'].unique()

        # Obtener TODAS las descripciones posibles de esta categoría en cualquier mes
        orden_descripciones = sorted(df[df['categoria'] == categoria]['descripcion'].unique())

        fig = go.Figure()

        # Ordenamos los conceptos de acuerdo a la aparición en el dataset
        for descripcion in orden_descripciones:
            df_desc = df_categoria[df_categoria['descripcion'] == descripcion].copy()

            # Crear un DataFrame vacío con todos los meses y unirlo a los datos existentes
            df_meses_vacios = pd.DataFrame({"orden_fecha": meses_completos})
            df_desc = pd.merge(df_meses_vacios, df_desc, on="orden_fecha", how="left").fillna({"total": 0})

            fig.add_trace(go.Bar(
                x=df_desc['orden_fecha'],
                y=df_desc['total'],
                name=descripcion,
                visible=True, # Asegura que se rendericen todas las barras
                hovertemplate=f"{descripcion} " + "%{y:.2f}€<extra></extra>"
            ))

        fig.update_layout(
            barmode='stack',
            title=f"Gastos de {categoria}",
            yaxis_title="Monto (€)",
            xaxis=dict(type='category', tickangle=-30),
            legend_title="Conceptos dentro de la categoría"
        )
        return fig

    # Generar gráficos de barras apiladas para cada categoría
    fig_compras = crear_grafico_barras("Compra").to_html(full_html=False)
    fig_facturas = crear_grafico_barras("Facturas").to_html(full_html=False)
    fig_gasolina = crear_grafico_barras("Gasolina").to_html(full_html=False)

    # Renderizar la plantilla con los gráficos
    return render_template("report.html",
                        total_gastos=total_gastos if gastos_mes else 0,
                        presupuesto_mensual=presupuesto_mensual,
                        mes_actual=mes_actual,
                        anio_actual=anio_actual,
                        gastos_mes=gastos_mes,
                        fig_pie=fig_pie.to_html(full_html=False) if fig_pie else None,
                        fig_facturas=fig_facturas,
                        fig_gasolina=fig_gasolina,
                        fig_compras=fig_compras)


@app.route("/config", methods=["GET", "POST"])
def config():
    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Obtener la fecha actual
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = request.args.get("mes", meses[datetime.now().month - 1])
    anio_actual = request.args.get("anio", datetime.now().year, type=int)

    if request.method == "POST":
        if "nueva_categoria" in request.form:
            nueva_categoria = request.form["nueva_categoria"].strip()

            if nueva_categoria:
                cursor.execute("INSERT INTO categorias (nombre) VALUES (%s);", (nueva_categoria,))
                conn.commit()
                flash("Categoría agregada correctamente", "success")

        elif "eliminar_categoria" in request.form:
            categoria_id = request.form["eliminar_categoria"]
            cursor.execute("DELETE FROM categorias WHERE id = %s;", (categoria_id,))
            conn.commit()
            flash("Categoría eliminada correctamente", "success")

        elif "presupuesto_mensual" in request.form:
            nuevo_presupuesto = request.form["presupuesto_mensual"].strip()

            if nuevo_presupuesto:
                try:
                    nuevo_presupuesto = float(nuevo_presupuesto)

                    # Insertar el nuevo presupuesto para el mes actual
                    cursor.execute("""
                            INSERT INTO presupuesto (monto, fecha_cambio, mes, anio) 
                            VALUES (%s, NOW(), %s, %s);
                            """,
                            (nuevo_presupuesto, mes_actual, anio_actual))

                    conn.commit()
                    flash("Presupuesto actualizado correctamente", "success")

                except ValueError:
                    flash("Por favor, introduce un valor numérico válido para el presupuesto", "error")

    # Obtener lista de categorías
    cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC;")
    categorias = cursor.fetchall()

    # Obtener el presupuesto más reciente
    cursor.execute("""
                SELECT monto 
                FROM presupuesto 
                WHERE (anio < %s) 
                OR (anio = %s AND FIELD(mes, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre') 
                    <= FIELD(%s, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'))
                ORDER BY anio DESC, 
                FIELD(mes, 'Diciembre', 'Noviembre', 'Octubre', 'Septiembre', 'Agosto', 'Julio', 
                        'Junio', 'Mayo', 'Abril', 'Marzo', 'Febrero', 'Enero') 
                LIMIT 1;
                """,
                (anio_actual, anio_actual, mes_actual))

    presupuesto_actual = cursor.fetchone()
    presupuesto_actual = presupuesto_actual["monto"] if presupuesto_actual else 0

    cursor.close()
    conn.close()

    return render_template("config.html", categorias=categorias, presupuesto_actual=presupuesto_actual)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
