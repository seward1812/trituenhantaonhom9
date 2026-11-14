import pytest

flask = pytest.importorskip("flask")

from backend import app as backend


@pytest.fixture
def client(monkeypatch):
    def fake_matrix(points):
        return [
            [abs(index - other) for other in range(len(points))]
            for index in range(len(points))
        ]

    def fake_route(points, route):
        return {
            "geometry": [[points[index][1], points[index][0]] for index in route],
            "distance": float(len(route) - 1),
            "duration": float(len(route) - 1) * 2,
            "steps": [],
        }

    monkeypatch.setattr(backend, "get_osrm_distance_matrix", fake_matrix)
    monkeypatch.setattr(backend, "get_osrm_route", fake_route)
    return backend.app.test_client()


def test_legacy_tsp_response_is_preserved(client):
    response = client.post(
        "/api/optimize",
        json={"points": [[10, 106], [10.1, 106.1]], "algorithm": "two_opt"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["route"][0] == 0
    assert "route_geometry" in payload
    assert "routes" not in payload


def test_cvrp_returns_multiple_route_details(client):
    response = client.post(
        "/api/optimize",
        json={
            "mode": "cvrp",
            "depot": [10, 106],
            "points": [[10.1, 106.1], [10.2, 106.2], [10.3, 106.3]],
            "demands": [2, 2, 2],
            "capacity": 3,
            "algorithm": "nearest_neighbor",
        },
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["mode"] == "cvrp"
    assert len(payload["routes"]) == len(payload["route_details"]) == 3
    assert all(detail["route"][0] == 0 for detail in payload["route_details"])
    assert all(load <= 3 for load in payload["loads"])


def test_cvrp_validation_happens_before_routing(client):
    response = client.post(
        "/api/optimize",
        json={
            "mode": "cvrp",
            "depot": [10, 106],
            "points": [[10.1, 106.1]],
            "demands": [5],
            "capacity": 4,
        },
    )
    assert response.status_code == 400
    assert "capacity" in response.get_json()["error"].lower()


def test_unknown_algorithm_is_rejected(client):
    response = client.post(
        "/api/optimize",
        json={"points": [[10, 106], [10.1, 106.1]], "algorithm": "bad"},
    )
    assert response.status_code == 400


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["success"] is True
