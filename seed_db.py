"""Script para insertar datos iniciales."""
import pymysql
from app.config import DefaultConfig

conn = pymysql.connect(
    host=DefaultConfig.DB_HOST,
    user=DefaultConfig.DB_USER,
    password=DefaultConfig.DB_PASSWORD,
    database=DefaultConfig.DB_NAME,
    port=DefaultConfig.DB_PORT
)

cursor = conn.cursor()

# Insertar categorías
categorias = ['Alquiler', 'Facturas', 'Compra', 'Gasolina', 'Otros']
for cat in categorias:
    try:
        cursor.execute(
            "INSERT IGNORE INTO categorias (nombre) VALUES (%s)", (cat,))
        print(f"✅ Categoría '{cat}' insertada")
    except Exception as e:
        print(f"⚠️  Error insertando '{cat}': {e}")

conn.commit()
cursor.close()
conn.close()
print("\n✅ Datos iniciales insertados correctamente")
