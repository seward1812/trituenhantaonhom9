from algorithms.cvrp_utils import (
    build_sequential_routes,
    make_solution,
    validate_matrix,
    validate_routes,
)


def _route_distance(route, matrix):
    return sum(matrix[route[index]][route[index + 1]] for index in range(len(route) - 1))


def _improve_route(route, matrix):
    best = list(route)
    improved = True
    while improved:
        improved = False
        current_distance = _route_distance(best, matrix)
        for start in range(1, len(best) - 2):
            for end in range(start + 1, len(best) - 1):
                candidate = best[:start] + best[start:end + 1][::-1] + best[end + 1:]
                if _route_distance(candidate, matrix) < current_distance:
                    best = candidate
                    improved = True
                    current_distance = _route_distance(best, matrix)
    return best


def two_opt_cvrp(instance, routes=None, matrix=None):
    matrix = instance.distance_matrix() if matrix is None else matrix
    validate_matrix(matrix, len(instance.node_ids))
    source_routes = build_sequential_routes(instance) if routes is None else routes
    validate_routes(source_routes, instance, matrix)
    optimized = [_improve_route(route, matrix) for route in source_routes]
    return make_solution(optimized, instance, matrix)


solve = two_opt_cvrp
solve_two_opt_cvrp = two_opt_cvrp
