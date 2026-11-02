
def nearest_neighbor(matrix, depot=0):
    n = len(matrix)

    visited = [False] * n
    route = [depot]

    visited[depot] = True
    current = depot

    while len(route) < n:
        next_point = -1
        min_distance = float("inf")

        for i in range(n):
            if not visited[i] and matrix[current][i] < min_distance:
                min_distance = matrix[current][i]
                next_point = i

        route.append(next_point)
        visited[next_point] = True
        current = next_point

    route.append(depot)

    return route
    