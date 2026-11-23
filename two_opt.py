from algorithms.distance import (
    create_distance_matrix,
    calculate_route_distance
)

from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.two_opt import two_opt

locations = [
    (0, 0),
    (2, 3),
    (5, 4),
    (6, 1),
    (3, 0)
]

matrix = create_distance_matrix(locations)

route_nn = nearest_neighbor(matrix, depot=0)

route_2opt = two_opt(route_nn, matrix)

distance_nn = calculate_route_distance(route_nn, matrix)

distance_2opt = calculate_route_distance(route_2opt, matrix)

print("Nearest Neighbor:", route_nn)
print("Khoang cach NN:", distance_nn)

print("Nearest Neighbor + 2-opt:", route_2opt)
print("Khoang cach 2-opt:", distance_2opt)

print("Co cai thien:", distance_2opt <= distance_nn)
def two_opt(route, matrix):
    n = len(route)

    if n < 4:
        return route[:]

    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Ma tran phai la ma tran vuong")

    best_route = route[:]
    improved = True

    while improved:
        improved = False

        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                new_route = (
                    best_route[:i]
                    + best_route[i:j + 1][::-1]
                    + best_route[j + 1:]
                )

                old_distance = sum(
                    matrix[best_route[k]][best_route[k + 1]]
                    for k in range(n - 1)
                )

                new_distance = sum(
                    matrix[new_route[k]][new_route[k + 1]]
                    for k in range(n - 1)
                )

                if new_distance < old_distance:
                    best_route = new_route
                    improved = True

    return best_route
