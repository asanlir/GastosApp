"""
Excepciones personalizadas para la aplicación de control de gastos.
"""


class GastosBaseException(Exception):
    """Excepción base para todas las excepciones personalizadas de la aplicación."""
    pass


class DatabaseError(GastosBaseException):
    """Excepción para errores relacionados con la base de datos."""
    pass


class ValidationError(GastosBaseException):
    """Excepción para errores de validación de datos."""
    pass


class NotFoundError(GastosBaseException):
    """Excepción para recursos no encontrados."""
    pass


class DuplicateError(GastosBaseException):
    """Excepción para recursos duplicados."""
    pass
