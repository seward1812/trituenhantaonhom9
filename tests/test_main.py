import json
import subprocess
import sys

import pytest

from data.locations import locations
from main import load_input, run_comparison


@pytest.fixture
def default_points():
    return list(locations.values())


def test_default_comparison_has_closed_routes(default_points):
    report = run_comparison(default_points)

    assert report["points_count"] == 7
    assert report["baseline"] == "nearest_neighbor"
    assert set(report["results"]) == {
        "nearest_neighbor",
        "two_opt",
        "nearest_insertion",
        "farthest_insertion",
    }
    for result in report["results"].values():
        route = result["route"]
        assert route[0] == 0
        assert route[-1] == 0
        assert sorted(route[:-1]) == list(range(7))
        assert result["runtime_ms"] >= 0


def test_two_opt_does_not_increase_distance(default_points):
    report = run_comparison(default_points)
    results = report["results"]

    assert results["two_opt"]["distance_km"] <= results["nearest_neighbor"]["distance_km"]
    assert results["nearest_neighbor"]["improvement_pct"] == 0
    assert results["two_opt"]["improvement_km"] == round(
        results["nearest_neighbor"]["distance_km"]
        - results["two_opt"]["distance_km"],
        3,
    )


def test_load_input_supports_points_and_depot(tmp_path):
    path = tmp_path / "locations.json"
    path.write_text(
        json.dumps({"points": [[0, 0], [1, 1]], "depot": 1}),
        encoding="utf-8",
    )

    points, depot = load_input(path)

    assert points == [(0.0, 0.0), (1.0, 1.0)]
    assert depot == 1


def test_invalid_depot_is_rejected(default_points):
    with pytest.raises(ValueError, match="Depot"):
        run_comparison(default_points, depot=7)


def test_invalid_coordinate_range_is_rejected():
    with pytest.raises(ValueError, match="Latitude"):
        run_comparison([[91, 0], [0, 0]])


def test_cli_json_output():
    completed = subprocess.run(
        [sys.executable, "main.py", "--json", "--algorithm", "two_opt"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["results"]["two_opt"]["route"][0] == 0
    assert report["results"]["two_opt"]["improvement_pct"] >= 0
    assert "nearest_neighbor" in report["results"]
