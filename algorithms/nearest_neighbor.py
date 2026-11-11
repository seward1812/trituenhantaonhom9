
def nearest_neighbor(matrix, depot=0):
    n = len(matrix)

    if n == 0:
        raise ValueError("Ma tran khoang cach rong")

    if any(len(row) != n for row in matrix):
        raise ValueError("Ma tran phai la ma tran vuong")

    if not isinstance(depot, int) or not 0 <= depot < n:
        raise ValueError("Vi tri kho khong hop le")

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

        if next_point == -1:
            raise ValueError("Khong tim duoc diem tiep theo")

        route.append(next_point)
        visited[next_point] = True
        current = next_point

    route.append(depot)

    return route
