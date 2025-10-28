"""
Tests para las funciones de utilidad.
"""
from decimal import Decimal
from app.utils import safe_float, safe_get, format_currency


def test_safe_float():
    """Test la función safe_float con diferentes tipos de entrada"""
    assert safe_float(None) == 0.0
    assert safe_float("123.45") == 123.45
    assert safe_float(123.45) == 123.45
    assert safe_float(Decimal("123.45")) == 123.45
    assert safe_float("invalid") == 0.0
    assert safe_float("invalid", default=1.0) == 1.0


def test_safe_get():
    """Test la función safe_get con diferentes escenarios"""
    test_dict = {"a": 1, "b": "test", "c": None}

    assert safe_get(test_dict, "a") == 1
    assert safe_get(test_dict, "b") == "test"
    assert safe_get(test_dict, "c") is None
    assert safe_get(test_dict, "d") is None
    assert safe_get(test_dict, "d", default=0) == 0
    assert safe_get(None, "any_key") is None
    assert safe_get(None, "any_key", default="default") == "default"


def test_format_currency():
    """Test la función format_currency para formato correcto de moneda"""
    assert format_currency(1234.56) == "1.234,56 €"
    assert format_currency(0) == "0,00 €"
    assert format_currency(1000000.99) == "1.000.000,99 €"
    assert format_currency(-1234.56) == "-1.234,56 €"
