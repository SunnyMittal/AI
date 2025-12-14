"""Tests for calculator operations."""
import pytest
from calculator.calculator import Calculator

def test_addition():
    calc = Calculator()
    assert calc.calculate("add", 2, 3) == 5
    assert calc.calculate("add", -1, 1) == 0
    assert calc.calculate("add", 0.1, 0.2) == pytest.approx(0.3)

def test_subtraction():
    calc = Calculator()
    assert calc.calculate("subtract", 5, 3) == 2
    assert calc.calculate("subtract", -1, -1) == 0
    assert calc.calculate("subtract", 0.5, 0.3) == pytest.approx(0.2)

def test_multiplication():
    calc = Calculator()
    assert calc.calculate("multiply", 2, 3) == 6
    assert calc.calculate("multiply", -2, 3) == -6
    assert calc.calculate("multiply", 0.5, 2) == pytest.approx(1.0)

def test_division():
    calc = Calculator()
    assert calc.calculate("divide", 6, 2) == 3
    assert calc.calculate("divide", -6, 2) == -3
    assert calc.calculate("divide", 1, 2) == pytest.approx(0.5)

def test_division_by_zero():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.calculate("divide", 1, 0)

def test_invalid_operation():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.calculate("power", 2, 3)