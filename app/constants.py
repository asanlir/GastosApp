"""
Constantes utilizadas en toda la aplicación.
"""

# Lista de meses ordenada
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Fragmento SQL para ordenar por meses (usado en varias consultas)
SQL_MONTH_FIELD = f"""FIELD(mes, '{("', '").join(MESES)}')"""

# Fragmento SQL para ordenar meses en orden inverso (usado en algunas consultas)
SQL_MONTH_FIELD_DESC = f"""FIELD(mes, '{("', '").join(reversed(MESES))}')"""

# Constantes de estado para mensajes flash
FLASH_SUCCESS = 'success'
FLASH_ERROR = 'error'

# Categoría por defecto
CATEGORIA_DEFAULT = 'Sin categoría'