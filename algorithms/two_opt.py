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
