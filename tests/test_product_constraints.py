import sys
import os
import pytest

# ensure domain is importable
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root, 'src', 'domain'))

from product import Product


def test_valid_product_at_limits():
    p = Product(name="A", weight=10_000, length=100, width=50, height=50)
    assert p.weight == 10_000
    assert p.length == 100
    assert p.width == 50
    assert p.height == 50
    assert p.volume == 100*50*50


def test_dimension_single_side_exceeds():
    with pytest.raises(ValueError, match=r"length.*<= 100 cm"):
        Product(name="B", weight=100, length=101, width=10, height=10)


def test_sum_of_dimensions_exceeds():
    with pytest.raises(ValueError, match=r"soma das dimensões.*<= 200 cm"):
        Product(name="C", weight=100, length=100, width=60, height=50)  # 210


def test_overweight_exceeds():
    with pytest.raises(ValueError, match=r"peso.*<= 10000 g"):
        Product(name="D", weight=10001, length=10, width=10, height=10)


def test_zero_or_negative_values():
    with pytest.raises(ValueError, match=r"peso deve ser > 0 g"):
        Product(name="E", weight=0, length=10, width=10, height=10)
    with pytest.raises(ValueError, match=r"length deve ser > 0 cm"):
        Product(name="F", weight=10, length=0, width=10, height=10)
    with pytest.raises(ValueError, match=r"width deve ser > 0 cm"):
        Product(name="G", weight=10, length=10, width=-5, height=10)
