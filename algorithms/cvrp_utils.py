from algorithms.distance import calculate_route_distance


def validate_matrix(matrix, node_count):
    if len(matrix) != node_count or any(len(row) != node_count for row in matrix):
        raise ValueError("Ma tran khoang cach phai co kich thuoc hop le")
    if any(distance < 0 for row in matrix for distance in row):
        raise ValueError("Khoang cach khong duoc am")
    return matrix


def customer_ids(instance):
    return range(1, len(instance.node_ids))


def route_load(route, demands):
    return sum(demands[node] for node in route if node != 0)


def validate_routes(routes, instance, matrix):
    validate_matrix(matrix, len(instance.node_ids))
    if not routes:
        raise ValueError("Phai co it nhat mot tuyen")

    expected = set(customer_ids(instance))
    seen = []
    loads = []
    distance = 0.0
    for route in routes:
        if len(route) < 3 or route[0] != 0 or route[-1] != 0:
            raise ValueError("Moi tuyen phai bat dau va ket thuc tai depot")
        if any(node < 0 or node >= len(instance.node_ids) for node in route):
            raise ValueError("Tuyen chua chi so diem hop le")
        load = route_load(route, instance.demands)
        if load > instance.capacity:
            raise ValueError("Tai cua tuyen vuot qua suc chua xe")
        seen.extend(route[1:-1])
        loads.append(load)
        distance += calculate_route_distance(route, matrix)

    if set(seen) != expected or len(seen) != len(expected):
        raise ValueError("Moi khach hang phai duoc phuc vu dung mot lan")
    return loads, distance


def make_solution(routes, instance, matrix):
    loads, distance = validate_routes(routes, instance, matrix)
    return {
        "routes": [list(route) for route in routes],
        "loads": loads,
        "distance": round(distance, 6),
    }


def build_sequential_routes(instance):
    routes = []
    route = [0]
    load = 0
    for customer in customer_ids(instance):
        demand = instance.demands[customer]
        if route != [0] and load + demand > instance.capacity:
            routes.append(route + [0])
            route = [0]
            load = 0
        route.append(customer)
        load += demand
    if len(route) > 1:
        routes.append(route + [0])
    return routes
