import argparse
import json
import math
import sys
import time
from pathlib import Path

from algorithms.distance import calculate_route_distance, create_distance_matrix
from algorithms.farthest_insertion import farthest_insertion
from algorithms.nearest_insertion import nearest_insertion
from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt
from algorithms.farthest_insertion_cvrp import farthest_insertion_cvrp
from algorithms.nearest_insertion_cvrp import nearest_insertion_cvrp
from algorithms.nearest_neighbor_cvrp import nearest_neighbor_cvrp
from algorithms.two_opt_cvrp import two_opt_cvrp
from data.duannhom import load_json as load_cvrp_json
from data.locations import DEPOT, locations


ALGORITHMS = (
    "nearest_neighbor",
    "two_opt",
    "nearest_insertion",
    "farthest_insertion",
)


def _validate_points(points):
    if not isinstance(points, list) or len(points) < 2:
        raise ValueError("Can it nhat 2 dia diem")

    normalized = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("Moi dia diem phai co dang [latitude, longitude]")
        try:
            coordinate = (float(point[0]), float(point[1]))
        except (TypeError, ValueError) as error:
            raise ValueError("Toa do phai la so") from error
        latitude, longitude = coordinate
        if not all(math.isfinite(value) for value in coordinate):
            raise ValueError("Toa do phai la so huu han")
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude phai nam trong khoang -90 den 90")
        if not -180 <= longitude <= 180:
            raise ValueError("Longitude phai nam trong khoang -180 den 180")
        normalized.append(coordinate)
    return normalized


def load_input(path):
    with Path(path).open(encoding="utf-8") as input_file:
        payload = json.load(input_file)

    input_depot = None
    if isinstance(payload, dict):
        points = payload.get("points", payload.get("locations"))
        input_depot = payload.get("depot")
    else:
        points = payload

    normalized_points = _validate_points(points)
    if input_depot is not None:
        if not isinstance(input_depot, int) or isinstance(input_depot, bool):
            raise ValueError("Depot phai la chi so nguyen")
    return normalized_points, input_depot


def _validate_route(route, node_count, depot):
    if len(route) != node_count + 1:
        raise ValueError("Lo trinh khong di qua day du cac diem")
    if route[0] != depot or route[-1] != depot:
        raise ValueError("Lo trinh phai bat dau va ket thuc tai depot")
    if sorted(route[:-1]) != list(range(node_count)):
        raise ValueError("Lo trinh phai di qua moi diem dung mot lan")


def _run_algorithm(name, matrix, depot, baseline_route=None):
    started_at = time.perf_counter()
    if name == "nearest_neighbor":
        route = nearest_neighbor(matrix, depot)
    elif name == "two_opt":
        route = two_opt(baseline_route, matrix)
    elif name == "nearest_insertion":
        route = nearest_insertion(matrix, depot)
    elif name == "farthest_insertion":
        route = farthest_insertion(matrix, depot)
    else:
        raise ValueError(f"Thuat toan khong duoc ho tro: {name}")

    runtime_ms = (time.perf_counter() - started_at) * 1000
    _validate_route(route, len(matrix), depot)
    return {
        "route": route,
        "distance_km": round(calculate_route_distance(route, matrix), 3),
        "runtime_ms": round(runtime_ms, 3),
    }


def run_comparison(points, depot=DEPOT, algorithm="all"):
    points = _validate_points(points)
    matrix = create_distance_matrix(points)
    node_count = len(matrix)
    if not isinstance(depot, int) or isinstance(depot, bool) or not 0 <= depot < node_count:
        raise ValueError("Depot khong hop le")
    if algorithm not in ("all", *ALGORITHMS):
        raise ValueError(f"Thuat toan khong duoc ho tro: {algorithm}")

    baseline = _run_algorithm("nearest_neighbor", matrix, depot)
    results = {"nearest_neighbor": baseline}
    selected = ALGORITHMS if algorithm == "all" else (algorithm,)
    for name in selected:
        if name == "nearest_neighbor":
            continue
        results[name] = _run_algorithm(
            name,
            matrix,
            depot,
            baseline_route=baseline["route"],
        )

    baseline_distance = baseline["distance_km"]
    for result in results.values():
        improvement_km = baseline_distance - result["distance_km"]
        result["improvement_km"] = round(improvement_km, 3)
        result["improvement_pct"] = round(
            improvement_km / baseline_distance * 100
            if baseline_distance > 0
            else 0,
            2,
        )

    best_algorithm = min(
        results,
        key=lambda name: results[name]["distance_km"],
    )
    return {
        "points_count": node_count,
        "depot": depot,
        "metric": "Haversine",
        "unit": "km",
        "baseline": "nearest_neighbor",
        "best_algorithm": best_algorithm,
        "results": results,
    }


CVRP_ALGORITHMS = (
    "nearest_neighbor",
    "nearest_insertion",
    "farthest_insertion",
    "two_opt",
)

CVRP_SOLVERS = {
    "nearest_neighbor": nearest_neighbor_cvrp,
    "nearest_insertion": nearest_insertion_cvrp,
    "farthest_insertion": farthest_insertion_cvrp,
    "two_opt": two_opt_cvrp,
}


def run_cvrp(instance, algorithm="all", matrix=None):
    if algorithm != "all" and algorithm not in CVRP_SOLVERS:
        raise ValueError(f"Thuat toan CVRP khong duoc ho tro: {algorithm}")

    matrix = instance.distance_matrix() if matrix is None else matrix
    selected = CVRP_ALGORITHMS if algorithm == "all" else (algorithm,)
    return {
        name: CVRP_SOLVERS[name](instance, matrix=matrix)
        for name in selected
    }


def _format_route(route):
    return " -> ".join(str(point) for point in route)


def print_report(report):
    print(f"So diem: {report['points_count']} | Depot: {report['depot']}")
    print("Metric: Haversine | Don vi: km | Baseline: Nearest Neighbor")
    print()
    print(
        f"{'Algorithm':<22} {'Distance (km)':>15} "
        f"{'Runtime (ms)':>14} {'Improvement':>14}"
    )
    print("-" * 70)
    for name, result in report["results"].items():
        improvement = (
            f"{result['improvement_km']:.3f} km "
            f"({result['improvement_pct']:.2f}%)"
        )
        print(
            f"{name:<22} {result['distance_km']:>15.3f} "
            f"{result['runtime_ms']:>14.3f} {improvement:>14}"
        )
        print(f"  Route: {_format_route(result['route'])}")
    print()
    print(f"Tot nhat: {report['best_algorithm']}")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Dieu phoi cac heuristic toi uu tuyen giao hang"
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--input",
        type=Path,
        help="File JSON chua points hoac locations va tuy chon depot",
    )
    input_group.add_argument(
        "--cvrp-input",
        type=Path,
        help="File JSON CVRP theo schema nodes/capacity",
    )

    parser.add_argument(
        "--cvrp-algorithm",
        choices=("all", *CVRP_ALGORITHMS),
        help="Thuat toan CVRP khi dung --cvrp-input",
    )
    parser.add_argument(
        "--depot",
        type=int,
        help="Chi so depot, mac dinh lay tu input hoac 0",
    )
    parser.add_argument(
        "--algorithm",
        choices=("all", *ALGORITHMS),
        default="all",
        help="Thuat toan can chay",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Xuat ket qua dang JSON",
    )
    return parser


def cvrp_report(instance, algorithm="all"):
    solutions = run_cvrp(instance, algorithm)
    return {
        "name": instance.name,
        "node_count": len(instance.node_ids),
        "customer_count": len(instance.node_ids) - 1,
        "node_ids": instance.node_ids,
        "capacity": instance.capacity,
        "algorithm": algorithm,
        "metric": "Euclidean",
        "unit": "distance units",
        "solutions": solutions,
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.cvrp_input:
            if args.algorithm != "all" or args.depot is not None:
                raise ValueError("Use --cvrp-algorithm with --cvrp-input")
            instance = load_cvrp_json(args.cvrp_input)
            report = cvrp_report(
                instance,
                args.cvrp_algorithm or "all",
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0

        if args.input:
            points, input_depot = load_input(args.input)
            depot = args.depot if args.depot is not None else input_depot
            depot = DEPOT if depot is None else depot
        else:
            points = list(locations.values())
            depot = DEPOT if args.depot is None else args.depot

        report = run_comparison(points, depot, args.algorithm)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Loi: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
