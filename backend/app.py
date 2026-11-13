
import os
import sys
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from flask import Flask, request, jsonify

from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt
from algorithms.nearest_insertion import nearest_insertion
from algorithms.farthest_insertion import farthest_insertion
from algorithms.distance import calculate_route_distance

app = Flask(__name__)

OSRM_URL = "https://router.project-osrm.org"


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def get_osrm_distance_matrix(points):
    # OSRM nhận tọa độ theo thứ tự longitude,latitude
    coordinates = ";".join(
        f"{lng},{lat}" for lat, lng in points
    )

    url = (
        f"{OSRM_URL}/table/v1/driving/{coordinates}"
        "?annotations=distance"
    )

    with urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("code") != "Ok":
        raise ValueError("OSRM không thể tạo ma trận khoảng cách.")

    distances = data.get("distances")

    if not distances:
        raise ValueError("OSRM không trả về dữ liệu khoảng cách.")

    # Chuyển mét sang kilomet
    matrix = []

    for row in distances:
        if any(value is None for value in row):
            raise ValueError(
                "Có hai điểm không tìm được đường kết nối."
            )

        matrix.append([
            value / 1000 for value in row
        ])

    return matrix


def get_osrm_route(points, route):
    # Lấy tọa độ theo thứ tự mà thuật toán AI đã tối ưu
    ordered_points = [points[index] for index in route]

    coordinates = ";".join(
        f"{lng},{lat}" for lat, lng in ordered_points
    )

    url = (
        f"{OSRM_URL}/route/v1/driving/{coordinates}"
        "?overview=full&geometries=geojson&steps=true"
    )

    with urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("OSRM không tìm được tuyến đường thực tế.")

    selected_route = data["routes"][0]

    return {
        "geometry": selected_route["geometry"]["coordinates"],
        "distance": round(selected_route["distance"] / 1000, 3),
        "duration": round(selected_route["duration"] / 60, 2),
        "steps": [
            {
                "instruction": step.get("name", ""),
                "distance": round(step.get("distance", 0), 1),
                "duration": round(step.get("duration", 0), 1)
            }
            for leg in selected_route.get("legs", [])
            for step in leg.get("steps", [])
        ]
    }


def get_algorithm_results(matrix):
    nn_route = nearest_neighbor(matrix, 0)
    optimized_route = two_opt(nn_route, matrix)

    routes = {
        "nearest_neighbor": nn_route,
        "two_opt": optimized_route,
        "nearest_insertion": nearest_insertion(matrix, 0),
        "farthest_insertion": farthest_insertion(matrix, 0)
    }

    results = {}

    for name, route in routes.items():
        distance = calculate_route_distance(route, matrix)

        results[name] = {
            "route": route,
            "distance": round(distance, 3)
        }

    baseline = results["nearest_neighbor"]["distance"]

    for name in results:
        distance = results[name]["distance"]

        improvement = (
            (baseline - distance) / baseline * 100
            if baseline > 0 else 0
        )

        results[name]["improvement"] = round(improvement, 2)

    return results


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "RouteOpt Backend is running",
        "routing_engine": "OSRM"
    })


@app.route("/api/optimize", methods=["POST"])
def optimize():
    try:
        data = request.get_json()

        if not data or "points" not in data:
            return jsonify({
                "success": False,
                "error": "Missing points"
            }), 400

        points = data["points"]
        algorithm = data.get("algorithm", "two_opt")

        if not isinstance(points, list) or len(points) < 2:
            return jsonify({
                "success": False,
                "error": "Please provide at least 2 points"
            }), 400

        if len(points) > 100:
            return jsonify({
                "success": False,
                "error": "Maximum 100 points allowed"
            }), 400

        normalized_points = []

        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                return jsonify({
                    "success": False,
                    "error": "Invalid coordinate format"
                }), 400

            lat = float(point[0])
            lng = float(point[1])

            if not (-90 <= lat <= 90):
                return jsonify({
                    "success": False,
                    "error": "Invalid latitude"
                }), 400

            if not (-180 <= lng <= 180):
                return jsonify({
                    "success": False,
                    "error": "Invalid longitude"
                }), 400

            normalized_points.append((lat, lng))

        # 1. Lấy ma trận khoảng cách đường bộ từ OSRM
        matrix = get_osrm_distance_matrix(normalized_points)

        # 2. Chạy các thuật toán tối ưu
        results = get_algorithm_results(matrix)

        if algorithm not in results:
            return jsonify({
                "success": False,
                "error": "Unknown algorithm"
            }), 400

        selected = results[algorithm]

        # 3. Lấy hình dạng đường đi thực tế từ OSRM
        road_route = get_osrm_route(
            normalized_points,
            selected["route"]
        )

        return jsonify({
            "success": True,
            "algorithm": algorithm,
            "route": selected["route"],
            "route_geometry": road_route["geometry"],
            "total_distance": selected["distance"],
            "road_distance": road_route["distance"],
            "duration_minutes": road_route["duration"],
            "improvement": selected["improvement"],
            "comparison": results,
            "steps": road_route["steps"],
            "unit": "km"
        })

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except (URLError, HTTPError, TimeoutError) as error:
        app.logger.exception("OSRM connection error")

        return jsonify({
            "success": False,
            "error": "Không kết nối được OSRM. Hãy thử lại sau."
        }), 503

    except Exception:
        app.logger.exception("Optimization error")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
