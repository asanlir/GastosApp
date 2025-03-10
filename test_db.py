import mysql.connector

# Configuración de la base de datos (debe coincidir con la de app.py)
db_config = {
    'host': 'localhost',
    'user': 'asanlir',
    'password': 'L@nc3r0S',
    'database': 'economia_db'
}


def test_connection():
    try:
        # Intentar conectar con la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Ejecutar una consulta para comprobar la conexión
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        print("Conexión exitosa. Tablas en la base de datos:", tables)

    except mysql.connector.Error as e:
        print("Error al conectar con la base de datos:", e)


if __name__ == "__main__":
    test_connection()
