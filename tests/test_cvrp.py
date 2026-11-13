import pytest

from algorithms.cvrp_utils import build_sequential_routes, validate_routes
from data.duannhom import CVRPInstance
from main import CVRP_ALGORITHMS, run_cvrp


@pytest.fixture
def instance():
    return CVRPInstance(
        name="test",
        node_ids=[0, 1, 2, 3, 4],
        coordinates=[(0, 0), (1, 0), (2, 0), (0, 2), (2, 2)],
        demands=[0, 2, 2, 3, 1],
        capacity=4,
    )


def assert_solution(solution, instance):
    matrix = instance.distance_matrix()
    loads, distance = validate_routes(solution["routes"], instance, matrix)
    assert solution["loads"] == loads
    assert solution["distance"] == round(distance, 6)
    assert solution["distance"] >= 0


@pytest.mark.parametrize("algorithm", CVRP_ALGORITHMS)
def test_each_cvrp_algorithm_returns_feasible_routes(instance, algorithm):
    solution = run_cvrp(instance, algorithm)[algorithm]
    assert_solution(solution, instance)


def test_cvrp_uses_multiple_routes_when_capacity_requires_it(instance):
    solution = run_cvrp(instance, "nearest_neighbor")["nearest_neighbor"]
    assert len(solution["routes"]) >= 2
    assert all(load <= instance.capacity for load in solution["loads"])


def test_two_opt_preserves_sequential_route_partition(instance):
    initial = build_sequential_routes(instance)
    solution = run_cvrp(instance, "two_opt")["two_opt"]
    assert [set(route[1:-1]) for route in solution["routes"]] == [
        set(route[1:-1]) for route in initial
    ]


def test_run_cvrp_all_runs_each_solver(instance):
    report = run_cvrp(instance)
    assert tuple(report) == CVRP_ALGORITHMS
    for solution in report.values():
        assert_solution(solution, instance)


def test_run_cvrp_reuses_custom_matrix(instance):
    matrix = instance.distance_matrix()
    report = run_cvrp(instance, "nearest_neighbor", matrix=matrix)
    assert "nearest_neighbor" in report
    assert_solution(report["nearest_neighbor"], instance)


def test_run_cvrp_rejects_unknown_algorithm(instance):
    with pytest.raises(ValueError, match="CVRP"):
        run_cvrp(instance, "unknown")


def test_cvrp_rejects_customer_demand_above_capacity():
    with pytest.raises(ValueError, match="capacity"):
        CVRPInstance(
            name="invalid",
            node_ids=[0, 1],
            coordinates=[(0, 0), (1, 1)],
            demands=[0, 5],
            capacity=4,
        )
