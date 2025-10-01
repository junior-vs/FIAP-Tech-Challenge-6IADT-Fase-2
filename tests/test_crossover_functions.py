import sys
import os
import random

# ensure domain is importable BEFORE imports
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root, 'src', 'domain'))
sys.path.insert(0, os.path.join(root, 'src', 'functions'))

from delivery_point import DeliveryPoint
from route import Route
from crossover_function import Crossover
from product import Product
from product import Product


def make_points(n=6):
    # generate n points on a circle for variety
    pts = []
    for i in range(n):
        prod = Product(name=f"P{i}", weight=100, length=10, width=10, height=10)
        pts.append(DeliveryPoint(i * 10, (i % 2) * 5, product=prod))
    return pts


def points_set(route: Route):
    return sorted((p.x, p.y) for p in route.delivery_points)


def test_order_crossover_basic():
    random.seed(0)
    pts = make_points(6)
    p1 = Route(pts)
    p2 = Route(list(reversed(pts)))
    child = Crossover.order_crossover(p1, p2)
    assert isinstance(child, Route)
    assert len(child) == len(p1)
    assert points_set(child) == points_set(p1)


def test_erx_crossover_basic():
    random.seed(1)
    pts = make_points(6)
    p1 = Route(pts)
    p2 = Route(list(reversed(pts)))
    child = Crossover.erx_crossover(p1, p2)
    assert isinstance(child, Route)
    assert len(child) == len(p1)
    assert points_set(child) == points_set(p1)


def test_crossover_ordenado_ox1_returns_pair():
    random.seed(2)
    pts = make_points(6)
    p1 = Route(pts)
    p2 = Route(list(reversed(pts)))
    c1, c2 = Crossover.crossover_ordenado_ox1(p1, p2)
    assert isinstance(c1, Route) and isinstance(c2, Route)
    assert points_set(c1) == points_set(p1)
    assert points_set(c2) == points_set(p1)


def test_pmx_preserves_points_and_length():
    random.seed(3)
    pts = make_points(6)
    p1 = Route(pts)
    p2 = Route(list(reversed(pts)))
    c1, c2 = Crossover.crossover_parcialmente_mapeado_pmx(p1, p2)
    assert isinstance(c1, Route) and isinstance(c2, Route)
    assert len(c1) == len(p1) and len(c2) == len(p1)
    assert points_set(c1) == points_set(p1)
    assert points_set(c2) == points_set(p1)


def test_cx_and_kpoint_preserve_points():
    random.seed(4)
    pts = make_points(6)
    p1 = Route(pts)
    p2 = Route(list(reversed(pts)))
    # cycle crossover
    cx1, cx2 = Crossover.crossover_de_ciclo_cx(p1, p2)
    assert isinstance(cx1, Route) and isinstance(cx2, Route)
    assert points_set(cx1) == points_set(p1)
    assert points_set(cx2) == points_set(p1)
    # k-point (test k=2 and k=1 edge)
    k1, k2 = Crossover.crossover_multiplos_pontos_kpoint(p1, p2, k=2)
    assert points_set(k1) == points_set(p1)
    assert points_set(k2) == points_set(p1)
    k1b, k2b = Crossover.crossover_multiplos_pontos_kpoint(p1, p2, k=1)
    assert points_set(k1b) == points_set(p1)
    assert points_set(k2b) == points_set(p1)


def test_short_routes_return_copies():
    # when size < 2, functions should return copies or tuples of copies
    pts = make_points(1)
    p = Route(pts)
    # order_crossover and erx should return copy
    oc = Crossover.order_crossover(p, p)
    assert isinstance(oc, Route)
    assert points_set(oc) == points_set(p)
    erx = Crossover.erx_crossover(p, p)
    assert isinstance(erx, Route)
    assert points_set(erx) == points_set(p)
    # two-child crossovers should return tuples of Routes
    ox1_a, ox1_b = Crossover.crossover_ordenado_ox1(p, p)
    assert isinstance(ox1_a, Route) and isinstance(ox1_b, Route)
    pmx_a, pmx_b = Crossover.crossover_parcialmente_mapeado_pmx(p, p)
    assert isinstance(pmx_a, Route) and isinstance(pmx_b, Route)

