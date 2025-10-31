"""
Migración 002: Añadir columna mostrar_en_graficas a tabla categorias

Esta migración añade un campo booleano para controlar qué categorías
se muestran en las gráficas de reportes.

Por defecto, todas las categorías existentes se marcarán como visibles (TRUE),
excepto 'Alquiler' que se marca como FALSE por ser un gasto fijo constante.
"""


def up(cursor):
    """Aplicar migración: añadir columna mostrar_en_graficas."""
    # Añadir columna con valor por defecto TRUE
    cursor.execute("""
        ALTER TABLE categorias
        ADD COLUMN mostrar_en_graficas BOOLEAN NOT NULL DEFAULT TRUE
    """)

    # Marcar 'Alquiler' como no visible en gráficas (si existe)
    cursor.execute("""
        UPDATE categorias
        SET mostrar_en_graficas = FALSE
        WHERE nombre = 'Alquiler'
    """)

    print("✓ Columna 'mostrar_en_graficas' añadida a tabla categorias")
    print("✓ Categoría 'Alquiler' marcada como no visible en gráficas")


def down(cursor):
    """Revertir migración: eliminar columna mostrar_en_graficas."""
    cursor.execute("""
        ALTER TABLE categorias
        DROP COLUMN mostrar_en_graficas
    """)

    print("✓ Columna 'mostrar_en_graficas' eliminada de tabla categorias")
