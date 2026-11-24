
from distance import calculate_route_distance


def two_opt(route, matrix):
    n = len(route)

    if n < 4:
        return route[:]

    size = len(matrix)

    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("Ma tran phai la ma tran vuong")

    for point in route:
        if not isinstance(point, int) or not (0 <= point < size):
            raise ValueError("Chi so dia diem khong hop le")

    if route[0] != route[-1]:
        raise ValueError("Lo trinh phai bat dau va ket thuc tai cung mot diem")

    best_route = route[:]
    best_distance = calculate_route_distance(best_route, matrix)

    improved = True

    while improved:
        improved = False

        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):

                new_route = (
                    best_route[:i]
                    + best_route[i:j + 1][::-1]
                    + best_route[j + 1:]
                )

                new_distance = calculate_route_distance(
                    new_route, matrix
                )

                if new_distance < best_distance - 1e-9:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True
                    break

            if improved:
                break

    return best_route
