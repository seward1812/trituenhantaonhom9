
import math


def calculate_distance(point_a, point_b):
    lat1, lon1 = point_a
    lat2, lon2 = point_b

    radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius * c


def create_distance_matrix(locations):
    if isinstance(locations, dict):
        points = list(locations.values())
    else:
        points = list(locations)

    if len(points) == 0:
        raise ValueError("Danh sach dia diem khong duoc rong")

    n = len(points)
    matrix = []

    for i in range(n):
        row = []

        for j in range(n):
            distance = calculate_distance(points[i], points[j])
            row.append(distance)

        matrix.append(row)

    return matrix


def calculate_route_distance(route, matrix):
    n = len(matrix)

    if n == 0:
        raise ValueError("Ma tran khoang cach rong")

    if any(len(row) != n for row in matrix):
        raise ValueError("Ma tran phai la ma tran vuong")

    if len(route) < 2:
        raise ValueError("Lo trinh phai co it nhat 2 diem")

    total = 0

    for i in range(len(route) - 1):
        current = route[i]
        next_point = route[i + 1]

        if not (0 <= current < n and 0 <= next_point < n):
            raise ValueError("Chi so dia diem khong hop le")

        total += matrix[current][next_point]

    return total
