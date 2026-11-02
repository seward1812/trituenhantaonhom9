
import math


def calculate_distance(point_a, point_b):
    x1, y1 = point_a
    x2, y2 = point_b

    distance = math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )

    return distance


def create_distance_matrix(locations):
    n = len(locations)

    matrix = []

    for i in range(n):
        row = []

        for j in range(n):
            distance = calculate_distance(
                locations[i],
                locations[j]
            )

            row.append(distance)

        matrix.append(row)

    return matrix
