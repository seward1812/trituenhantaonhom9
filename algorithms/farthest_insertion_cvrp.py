from algorithms.cvrp_utils import customer_ids, make_solution, validate_matrix


def farthest_insertion_cvrp(instance, matrix=None):
    matrix = instance.distance_matrix() if matrix is None else matrix
    validate_matrix(matrix, len(instance.node_ids))

    unvisited = set(customer_ids(instance))
    routes = []
    if unvisited:
        first = max(unvisited, key=lambda node: (matrix[0][node], -node))
        routes.append([0, first, 0])
        unvisited.remove(first)

    while unvisited:
        selected = max(
            unvisited,
            key=lambda node: (
                min(matrix[node][point] for route in routes for point in route[:-1]),
                -node,
            ),
        )
        best_route = None
        best_position = None
        best_increase = float("inf")
        demand = instance.demands[selected]

        for route_index, route in enumerate(routes):
            load = sum(instance.demands[node] for node in route[1:-1])
            if load + demand > instance.capacity:
                continue
            for position in range(len(route) - 1):
                before, after = route[position], route[position + 1]
                increase = (
                    matrix[before][selected]
                    + matrix[selected][after]
                    - matrix[before][after]
                )
                if increase < best_increase:
                    best_route = route_index
                    best_position = position + 1
                    best_increase = increase

        if best_route is None:
            routes.append([0, selected, 0])
        else:
            routes[best_route].insert(best_position, selected)
        unvisited.remove(selected)

    return make_solution(routes, instance, matrix)


solve = farthest_insertion_cvrp
solve_farthest_insertion_cvrp = farthest_insertion_cvrp
