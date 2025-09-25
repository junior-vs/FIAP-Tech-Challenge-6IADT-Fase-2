import sys
import os
import pytest
from delivery_point import DeliveryPoint
from route import Route
from crossover_function import Crossover
from mutation_function import Mutation
from selection_functions import Selection

# ensure domain and functions are importable
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root, 'src', 'domain'))
sys.path.insert(0, os.path.join(root, 'src', 'functions'))


def make_square_points():
    # Return 4 points forming a unit square
    return [DeliveryPoint(0,0), DeliveryPoint(0,1), DeliveryPoint(1,1), DeliveryPoint(1,0)]


def test_route_distance_and_copy():
    pts = make_square_points()
    r = Route(pts)
    assert len(r) == 4
    d = r.distancia_total()
    # 4 edges of length 1 => distance 4
    assert d == pytest.approx(4.0, rel=1e-6)
    r2 = r.copy()
    assert isinstance(r2, Route)
    assert r2 is not r
    assert r2.delivery_points == r.delivery_points


def test_mutation_operators_return_route_and_preserve_points():
    pts = make_square_points()
    r = Route(pts)
    m1 = Mutation.mutacao_por_troca(r)
    m2 = Mutation.mutacao_por_inversao(r)
    m3 = Mutation.mutacao_por_embaralhamento(r)
    for m in (m1, m2, m3):
        assert isinstance(m, Route)
        assert sorted((p.x,p.y) for p in m.delivery_points) == sorted((p.x,p.y) for p in pts)


def test_crossover_ox1_returns_two_routes_with_same_points():
    pts = make_square_points()
    r1 = Route(pts)
    r2 = Route(list(reversed(pts)))
    c1, c2 = Crossover.crossover_ordenado_ox1(r1, r2)
    assert isinstance(c1, Route) and isinstance(c2, Route)
    assert len(c1) == len(r1) and len(c2) == len(r1)
    # Both children should contain the same set of points
    assert sorted((p.x,p.y) for p in c1.delivery_points) == sorted((p.x,p.y) for p in pts)
    assert sorted((p.x,p.y) for p in c2.delivery_points) == sorted((p.x,p.y) for p in pts)


def test_selection_tournament_and_roulette_operate_on_routes():
    pts = make_square_points()
    pop = [Route(pts) for _ in range(5)]
    # distances (lower is better) -> aptitudes as 1/distance
    distances = [r.distancia_total() for r in pop]
    aptitudes = [1.0/d for d in distances]
    winner = Selection.tournament(pop, aptitudes, tournament_size=3)
    assert isinstance(winner, Route)
    winner2 = Selection.roulette(pop, aptitudes)
    assert isinstance(winner2, Route)


def test_erx_and_kpoint_and_cx_and_pmx_preserve_points():
    pts = make_square_points()
    r1 = Route(pts)
    r2 = Route(list(reversed(pts)))
    # ERX returns a single Route
    erx_child = Crossover.erx_crossover(r1, r2)
    assert isinstance(erx_child, Route)
    # k-point, cx and pmx return tuples
    k1, k2 = Crossover.crossover_multiplos_pontos_kpoint(r1, r2, k=2)
    cx1, cx2 = Crossover.crossover_de_ciclo_cx(r1, r2)
    pmx1, pmx2 = Crossover.crossover_parcialmente_mapeado_pmx(r1, r2)
    for ch in (k1, k2, cx1, cx2, pmx1, pmx2):
        assert isinstance(ch, Route)
        assert sorted((p.x,p.y) for p in ch.delivery_points) == sorted((p.x,p.y) for p in pts)
