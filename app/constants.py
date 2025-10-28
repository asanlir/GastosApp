"""
Constantes utilizadas en toda la aplicación.
"""
from typing import List

# Lista de meses ordenada
MESES: List[str] = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Fragmentos SQL para ordenamiento de meses
SQL_MONTH_FIELD = f"""FIELD(mes, '{("', '").join(MESES)}')"""
SQL_MONTH_FIELD_DESC = f"""FIELD(mes, '{("', '").join(reversed(MESES))}')"""

# Fragmento SQL para SELECT de presupuesto más reciente
SQL_LATEST_BUDGET = f"""
    SELECT monto 
    FROM presupuesto 
    WHERE (anio < %s) 
    OR (anio = %s AND {SQL_MONTH_FIELD} <= FIELD(%s, '{("', '").join(MESES)}'))
    ORDER BY anio DESC, 
    FIELD(mes, '{("', '").join(reversed(MESES))}'), 
    fecha_cambio DESC 
    LIMIT 1
"""

# Mensajes Flash
FLASH_SUCCESS = 'success'
FLASH_ERROR = 'error'
FLASH_REQUIRED_FIELDS = 'Todos los campos son obligatorios'
FLASH_EXPENSE_ADDED = 'Gasto agregado correctamente'
FLASH_EXPENSE_UPDATED = 'Gasto actualizado correctamente'
FLASH_EXPENSE_DELETED = 'Gasto eliminado correctamente'
FLASH_CATEGORY_ADDED = 'Categoría agregada correctamente'
FLASH_CATEGORY_DELETED = 'Categoría eliminada correctamente'
FLASH_BUDGET_UPDATED = 'Presupuesto actualizado correctamente'
FLASH_INVALID_AMOUNT = 'Por favor, introduce un valor numérico válido para el presupuesto'

# Valores por defecto
CATEGORIA_DEFAULT = 'Sin categoría'
DEFAULT_PORT = 3306
