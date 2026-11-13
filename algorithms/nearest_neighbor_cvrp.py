from algorithms.cvrp_utils import customer_ids, make_solution, validate_matrix


def nearest_neighbor_cvrp(instance, matrix=None):
    matrix = instance.distance_matrix() if matrix is None else matrix
    validate_matrix(matrix, len(instance.node_ids))

    unvisited = set(customer_ids(instance))
    routes = []
    while unvisited:
        route = [0]
        load = 0
        current = 0
        while True:
            feasible = [
                customer for customer in unvisited
                if load + instance.demands[customer] <= instance.capacity
            ]
            if not feasible:
                break
            customer = min(feasible, key=lambda node: (matrix[current][node], node))
            route.append(customer)
            unvisited.remove(customer)
            load += instance.demands[customer]
            current = customer
        routes.append(route + [0])

    return make_solution(routes, instance, matrix)


solve = nearest_neighbor_cvrp
solve_nearest_neighbor_cvrp = nearest_neighbor_cvrp
