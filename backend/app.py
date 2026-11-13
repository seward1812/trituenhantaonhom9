import json
import math
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask, jsonify, request

from algorithms.distance import calculate_route_distance
from algorithms.farthest_insertion import farthest_insertion
from algorithms.nearest_insertion import nearest_insertion
from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt
from data.duannhom import CVRPInstance
from main import CVRP_ALGORITHMS, run_cvrp

app = Flask(__name__)
OSRM_URL = "https://router.project-osrm.org"


class OSRMError(Exception):
    pass


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _validate_matrix(matrix, size):
    if not isinstance(matrix, list) or len(matrix) != size:
        raise OSRMError("OSRM returned an invalid distance matrix.")
    if any(
        not isinstance(row, list)
        or len(row) != size
        or any(
            value is None
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            for value in row
        )
        for row in matrix
    ):
        raise OSRMError("OSRM returned an invalid distance matrix.")


def get_osrm_distance_matrix(points):
    coordinates = ";".join(f"{lng},{lat}" for lat, lng in points)
    url = f"{OSRM_URL}/table/v1/driving/{coordinates}?annotations=distance"
    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError) as error:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise OSRMError("OSRM returned invalid data.") from error

    if data.get("code") != "Ok":
        raise OSRMError("OSRM could not create a distance matrix.")
    distances = data.get("distances")
    _validate_matrix(distances, len(points))
    return [[value / 1000 for value in row] for row in distances]


def get_osrm_route(points, route):
    if not isinstance(route, list) or len(route) < 2:
        raise OSRMError("OSRM route must contain at least two points.")
    if any(not isinstance(index, int) or not 0 <= index < len(points) for index in route):
        raise OSRMError("Route contains an invalid point index.")

    ordered_points = [points[index] for index in route]
    coordinates = ";".join(f"{lng},{lat}" for lat, lng in ordered_points)
    url = (
        f"{OSRM_URL}/route/v1/driving/{coordinates}"
        "?overview=full&geometries=geojson&steps=true"
    )
    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError):
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise OSRMError("OSRM returned invalid route data.") from error

    if data.get("code") != "Ok" or not data.get("routes"):
        raise OSRMError("OSRM could not find the requested route.")
    selected_route = data["routes"][0]
    geometry = selected_route.get("geometry", {}).get("coordinates")
    distance = selected_route.get("distance")
    duration = selected_route.get("duration")
    if not isinstance(geometry, list) or len(geometry) < 2:
        raise OSRMError("OSRM returned an invalid route geometry.")
    if not isinstance(distance, (int, float)) or not isinstance(duration, (int, float)):
        raise OSRMError("OSRM returned invalid route metrics.")

    return {
        "geometry": geometry,
        "distance": round(distance / 1000, 3),
        "duration": round(duration / 60, 2),
        "steps": [
            {
                "instruction": step.get("name", ""),
                "distance": round(step.get("distance", 0), 1),
                "duration": round(step.get("duration", 0), 1),
            }
            for leg in selected_route.get("legs", [])
            for step in leg.get("steps", [])
        ],
    }


def get_algorithm_results(matrix):
    nn_route = nearest_neighbor(matrix, 0)
    routes = {
        "nearest_neighbor": nn_route,
        "two_opt": two_opt(nn_route, matrix),
        "nearest_insertion": nearest_insertion(matrix, 0),
        "farthest_insertion": farthest_insertion(matrix, 0),
    }
    results = {
        name: {
            "route": route,
            "distance": round(calculate_route_distance(route, matrix), 3),
        }
        for name, route in routes.items()
    }
    baseline = results["nearest_neighbor"]["distance"]
    for result in results.values():
        improvement = (baseline - result["distance"]) / baseline * 100 if baseline else 0
        result["improvement"] = round(improvement, 2)
    return results


def _error(message, status=400):
    return jsonify({"success": False, "error": message}), status


def _normalize_geo_points(points, label):
    if not isinstance(points, list) or not points:
        raise ValueError(f"{label} must contain at least one point.")
    normalized = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("Invalid coordinate format.")
        try:
            lat, lng = float(point[0]), float(point[1])
        except (TypeError, ValueError) as error:
            raise ValueError("Coordinates must be numbers.") from error
        if not math.isfinite(lat) or not math.isfinite(lng):
            raise ValueError("Coordinates must be finite.")
        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError("Coordinates are outside the valid range.")
        normalized.append((lat, lng))
    return normalized


def _validate_cvrp(data):
    points = _normalize_geo_points(data.get("points"), "points")
    if len(points) > 100:
        raise ValueError("Maximum 100 customers allowed.")
    depot = _normalize_geo_points([data.get("depot")], "depot")[0]
    demands = data.get("demands")
    if not isinstance(demands, list) or len(demands) != len(points):
        raise ValueError("demands must match the number of customers.")
    if any(
        isinstance(demand, bool)
        or not isinstance(demand, int)
        or demand <= 0
        for demand in demands
    ):
        raise ValueError("Customer demands must be positive integers.")
    capacity = data.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer.")
    if any(demand > capacity for demand in demands):
        raise ValueError("A customer demand exceeds vehicle capacity.")
    vehicle_count = data.get("vehicle_count")
    if vehicle_count is not None and (
        isinstance(vehicle_count, bool)
        or not isinstance(vehicle_count, int)
        or vehicle_count <= 0
    ):
        raise ValueError("vehicle_count must be a positive integer.")
    if vehicle_count is not None and sum(demands) > capacity * vehicle_count:
        raise ValueError("Total demand exceeds the available vehicle capacity.")
    algorithm = data.get("algorithm", "two_opt")
    if algorithm not in (*CVRP_ALGORITHMS, "all"):
        raise ValueError("Unknown CVRP algorithm.")
    return depot, points, demands, capacity, vehicle_count, algorithm


def _cvrp_response(data):
    depot, customers, demands, capacity, vehicle_count, algorithm = _validate_cvrp(data)
    points = [depot, *customers]
    instance = CVRPInstance(
        name="api_request",
        node_ids=list(range(len(points))),
        coordinates=points,
        demands=[0, *demands],
        capacity=capacity,
    )
    matrix = get_osrm_distance_matrix(points)
    solutions = run_cvrp(instance, "all", matrix=matrix)
    selected_name = algorithm
    if algorithm == "all":
        selected_name = min(solutions, key=lambda name: solutions[name]["distance"])
    selected = solutions[selected_name]
    if vehicle_count is not None and len(selected["routes"]) > vehicle_count:
        raise ValueError(
            f"{selected_name} requires {len(selected['routes'])} vehicles; "
            f"only {vehicle_count} were allowed."
        )

    route_details = []
    for index, (route, load) in enumerate(zip(selected["routes"], selected["loads"]), 1):
        road = get_osrm_route(points, route)
        route_details.append({
            "vehicle": index,
            "route": route,
            "load": load,
            "capacity": capacity,
            "geometry": road["geometry"],
            "distance_km": road["distance"],
            "duration_minutes": road["duration"],
            "steps": road["steps"],
        })

    baseline = solutions["nearest_neighbor"]["distance"]
    comparison = {}
    for name, solution in solutions.items():
        improvement = (baseline - solution["distance"]) / baseline * 100 if baseline else 0
        comparison[name] = {
            "routes": solution["routes"],
            "loads": solution["loads"],
            "optimization_distance_km": solution["distance"],
            "improvement": round(improvement, 2),
        }

    durations = [detail["duration_minutes"] for detail in route_details]
    road_distance = round(sum(detail["distance_km"] for detail in route_details), 3)
    return {
        "success": True,
        "mode": "cvrp",
        "algorithm": selected_name,
        "requested_algorithm": algorithm,
        "depot": depot,
        "demands": demands,
        "capacity": capacity,
        "vehicle_count": vehicle_count or len(route_details),
        "routes": selected["routes"],
        "loads": selected["loads"],
        "route_details": route_details,
        "optimization_distance_km": selected["distance"],
        "road_distance_km": road_distance,
        "total_route_duration_minutes": round(sum(durations), 2),
        "estimated_makespan_minutes": round(max(durations, default=0), 2),
        "comparison": comparison,
        "unit": "km",
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "RouteOpt Backend is running",
        "routing_engine": "OSRM",
    })


@app.route("/api/optimize", methods=["POST"])
def optimize():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "points" not in data:
            return _error("Missing points")
        if data.get("mode") == "cvrp":
            return jsonify(_cvrp_response(data))

        points = _normalize_geo_points(data["points"], "points")
        if len(points) < 2:
            return _error("Please provide at least 2 points")
        if len(points) > 100:
            return _error("Maximum 100 points allowed")
        algorithm = data.get("algorithm", "two_opt")
        allowed = {"nearest_neighbor", "two_opt", "nearest_insertion", "farthest_insertion", "all"}
        if algorithm not in allowed:
            return _error("Unknown algorithm")
        matrix = get_osrm_distance_matrix(points)
        results = get_algorithm_results(matrix)
        selected_name = min(results, key=lambda name: results[name]["distance"]) if algorithm == "all" else algorithm
        selected = results[selected_name]
        road_route = get_osrm_route(points, selected["route"])
        return jsonify({
            "success": True,
            "algorithm": selected_name,
            "requested_algorithm": algorithm,
            "route": selected["route"],
            "route_geometry": road_route["geometry"],
            "total_distance": selected["distance"],
            "road_distance": road_route["distance"],
            "duration_minutes": road_route["duration"],
            "improvement": selected["improvement"],
            "comparison": results,
            "steps": road_route["steps"],
            "unit": "km",
        })
    except (ValueError, TypeError) as error:
        return _error(str(error))
    except (OSRMError, URLError, HTTPError, TimeoutError):
        app.logger.exception("OSRM error")
        return _error("Không kết nối được OSRM. Hãy thử lại sau.", 503)
    except Exception:
        app.logger.exception("Optimization error")
        return _error("Internal server error", 500)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
