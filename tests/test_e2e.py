import json
import subprocess
import sys


def test_cvrp_cli_json(tmp_path):
    source = tmp_path / "instance.json"
    source.write_text(
        json.dumps({
            "name": "cli",
            "depot_index": 0,
            "capacity": 3,
            "nodes": [
                {"id": 0, "x": 0, "y": 0, "demand": 0},
                {"id": 1, "x": 1, "y": 0, "demand": 2},
                {"id": 2, "x": 2, "y": 0, "demand": 1},
            ],
        }),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, "main.py", "--cvrp-input", str(source), "--cvrp-algorithm", "two_opt"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["name"] == "cli"
    solution = report["solutions"]["two_opt"]
    assert sorted(node for route in solution["routes"] for node in route[1:-1]) == [1, 2]
    assert all(load <= report["capacity"] for load in solution["loads"])


def test_legacy_cli_still_works():
    completed = subprocess.run(
        [sys.executable, "main.py", "--json", "--algorithm", "two_opt"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert "results" in report
    assert report["results"]["two_opt"]["route"][0] == 0
