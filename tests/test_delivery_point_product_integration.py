import os
import sys
import pytest

# Ensure project src/domain is importable before any domain imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src', 'domain'))

from delivery_point import DeliveryPoint
from product import Product
from route import Route

def test_delivery_point_holds_product_and_distances_work():
    prod = Product(name="Box", weight=500, length=10, width=10, height=10)
    p1 = DeliveryPoint(0.0, 0.0, product=prod)
    p2 = DeliveryPoint(3.0, 4.0, product=Product(name="Light", weight=200, length=10, width=10, height=5))

    # distances should remain correct
    assert p1.distancia_pura(p2) == pytest.approx(5.0, rel=1e-6)
    # __repr__ includes product name when present
    s = repr(p1)
    assert "Box" in s

    # Route operations still work
    r = Route([p1, p2])
    assert r.distancia_total() == pytest.approx(10.0, rel=1e-6)  # 5 there + 5 back in cycle
