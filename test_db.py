from app.database import get_connection


def test_connection():
    try:
        # Intentar conectar con la base de datos usando el helper central
        conn = get_connection()
        cursor = conn.cursor()

        # Ejecutar una consulta para comprobar la conexión
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        print("Conexión exitosa. Tablas en la base de datos:", tables)

    except Exception as e:
        print("Error al conectar con la base de datos:", e)


if __name__ == "__main__":
    test_connection()
