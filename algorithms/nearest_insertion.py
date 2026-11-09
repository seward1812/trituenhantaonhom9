def nearest_insertion(matrix, depot=0):
    n = len(matrix)

    if n == 0:
        raise ValueError("Ma tran khoang cach rong")

    if any(len(row) != n for row in matrix):
        raise ValueError("Ma tran phai la ma tran vuong")

    if not isinstance(depot, int) or isinstance(depot, bool):
        raise ValueError("Depot phai la so nguyen")

    if depot < 0 or depot >= n:
        raise ValueError("Depot khong hop le")

    if n == 1:
        return [depot, depot]

    nearest = -1
    min_distance = float("inf")

    for i in range(n):
        if i != depot and matrix[depot][i] < min_distance:
            min_distance = matrix[depot][i]
            nearest = i

    if nearest == -1 or min_distance == float("inf"):
        raise ValueError("Khong tim duoc dia diem hop le")

    route = [depot, nearest, depot]
    unvisited = set(range(n)) - {depot, nearest}

    while unvisited:
        selected = -1
        min_distance = float("inf")

        for city in sorted(unvisited):
            for point in route[:-1]:
                if matrix[city][point] < min_distance:
                    min_distance = matrix[city][point]
                    selected = city

        if selected == -1 or min_distance == float("inf"):
            raise ValueError("Khong tim duoc dia diem hop le")

        best_position = -1
        min_increase = float("inf")

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]

            increase = (
                matrix[a][selected]
                + matrix[selected][b]
                - matrix[a][b]
            )

            if increase < min_increase:
                min_increase = increase
                best_position = i + 1

        if best_position == -1:
            raise ValueError("Khong tim duoc vi tri chen")

        route.insert(best_position, selected)
        unvisited.remove(selected)

    return route
