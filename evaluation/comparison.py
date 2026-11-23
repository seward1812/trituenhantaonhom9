import time
import pandas as pd
import matplotlib.pyplot as plt

from algorithms.nearest_neighbor_cvrp import nearest_neighbor_cvrp
from algorithms.nearest_insertion_cvrp import nearest_insertion_cvrp
from algorithms.farthest_insertion_cvrp import farthest_insertion_cvrp


def evaluate_algorithm(algo_name, algo_func, data_points, demands, capacity, depot=0):
    start_time = time.time()
    routes, total_distance = algo_func(data_points, demands, capacity, depot)
    end_time = time.time()
    execution_time = end_time - start_time
    num_vehicles = len(routes)

    return {
        "Algorithm": algo_name,
        "Total Distance": total_distance,
        "Execution Time (s)": execution_time,
        "Vehicles Used": num_vehicles,
    }


def run_comparison(data_points, demands, capacity, depot=0):
    results = []
    algorithms = [
        ("Nearest Neighbor", nearest_neighbor_cvrp),
        ("Nearest Insertion", nearest_insertion_cvrp),
        ("Farthest Insertion", farthest_insertion_cvrp),
    ]

    for name, func in algorithms:
        try:
            res = evaluate_algorithm(name, func, data_points, demands, capacity, depot)
            results.append(res)
        except Exception as e:
            print(f"Lỗi khi chạy {name}: {e}")

    return pd.DataFrame(results)


def plot_comparison(df_results):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(
        df_results["Algorithm"],
        df_results["Total Distance"],
        color=["blue", "green", "orange"],
    )
    axes[0].set_title("So sánh Tổng quãng đường (Cost)")
    axes[0].set_ylabel("Khoảng cách")

    axes[1].bar(
        df_results["Algorithm"],
        df_results["Execution Time (s)"],
        color=["blue", "green", "orange"],
    )
    axes[1].set_title("So sánh Thời gian thực thi")
    axes[1].set_ylabel("Thời gian (giây)")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    from data.duannhom import data_points, demands, capacity

    df = run_comparison(data_points, demands, capacity)
    print(df.to_string(index=False))
    plot_comparison(df)