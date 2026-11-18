"""Route and Algorithm Comparison Visualization for CVRP and TSP.

Đề tài: Tối ưu tuyến đường giao hàng nhiều điểm (Smart Logistics).
- So sánh tối thiểu 2 heuristic: Nearest Neighbor và 2-opt (cùng Nearest/Farthest Insertion).
- Đánh giá định lượng mức cải thiện khoảng cách/chi phí.
- Xuất trực quan hóa ra file HTML tương tác (Plotly) và ảnh tĩnh (Matplotlib).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from algorithms.distance import calculate_route_distance, create_distance_matrix
from algorithms.farthest_insertion import farthest_insertion
from algorithms.farthest_insertion_cvrp import farthest_insertion_cvrp
from algorithms.nearest_insertion import nearest_insertion
from algorithms.nearest_insertion_cvrp import nearest_insertion_cvrp
from algorithms.nearest_neighbor import nearest_neighbor
from algorithms.nearest_neighbor_cvrp import nearest_neighbor_cvrp
from algorithms.two_opt import two_opt
from algorithms.two_opt_cvrp import two_opt_cvrp
from data.duannhom import CVRPInstance, generate_instance, load_cvrplib, load_json
from data.locations import DEPOT, locations

OUTPUT_DIR = Path(__file__).resolve().parent

# Color palette for multi-vehicle CVRP routes
ROUTE_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#3366cc", "#dc3912", "#ff9900", "#109618", "#990099",
]


def solve_cvrp_heuristics(instance: CVRPInstance) -> dict[str, dict[str, Any]]:
    """Solve CVRP using multiple heuristics and compute improvement against Nearest Neighbor."""
    matrix = instance.distance_matrix()

    nn_solution = nearest_neighbor_cvrp(instance, matrix=matrix)
    # 2-Opt cải tiến trực tiếp từ kết quả của Nearest Neighbor
    two_opt_solution = two_opt_cvrp(instance, routes=nn_solution["routes"], matrix=matrix)
    ni_solution = nearest_insertion_cvrp(instance, matrix=matrix)
    fi_solution = farthest_insertion_cvrp(instance, matrix=matrix)

    solutions = {
        "Nearest Neighbor": nn_solution,
        "2-Opt (cải tiến)": two_opt_solution,
        "Nearest Insertion": ni_solution,
        "Farthest Insertion": fi_solution,
    }

    baseline_dist = nn_solution["distance"]
    results = {}
    for name, sol in solutions.items():
        dist = sol["distance"]
        improvement = ((baseline_dist - dist) / baseline_dist * 100) if baseline_dist > 0 else 0.0
        results[name] = {
            "routes": sol["routes"],
            "loads": sol["loads"],
            "distance": round(dist, 2),
            "improvement_pct": round(improvement, 2),
            "vehicle_count": len(sol["routes"]),
        }
    return results


def plot_matplotlib_comparison(
    instance: CVRPInstance,
    results: dict[str, dict[str, Any]],
    output_png: Path,
) -> None:
    """Export static PNG comparing Nearest Neighbor vs 2-Opt and summary chart."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    coords = instance.coordinates
    depot_x, depot_y = coords[0]
    cust_x = [p[0] for p in coords[1:]]
    cust_y = [p[1] for p in coords[1:]]

    algorithms_to_plot = ["Nearest Neighbor", "2-Opt (cải tiến)"]

    for ax_idx, algo_name in enumerate(algorithms_to_plot):
        ax = axes[ax_idx]
        sol = results[algo_name]

        # Draw customer points
        ax.scatter(cust_x, cust_y, c="#4a90e2", s=80, zorder=4, label="Khách hàng")
        for i, (x, y) in enumerate(coords[1:], start=1):
            ax.annotate(
                f"{i} (d={instance.demands[i]})",
                (x, y),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

        # Draw depot
        ax.scatter([depot_x], [depot_y], c="#e74c3c", s=180, marker="*", zorder=5, label="Depot (Kho)")
        ax.annotate("Depot", (depot_x, depot_y), textcoords="offset points", xytext=(0, -14), ha="center", fontweight="bold", color="#c0392b")

        # Draw routes
        for v_idx, route in enumerate(sol["routes"]):
            color = ROUTE_COLORS[v_idx % len(ROUTE_COLORS)]
            rx = [coords[node][0] for node in route]
            ry = [coords[node][1] for node in route]
            load = sol["loads"][v_idx]
            ax.plot(
                rx, ry,
                color=color,
                linewidth=2,
                linestyle="-",
                marker="o",
                markersize=4,
                alpha=0.85,
                label=f"Xe {v_idx + 1} (tải: {load}/{instance.capacity})",
            )

        subtitle = f"Tổng quãng đường: {sol['distance']:.2f}"
        if sol["improvement_pct"] > 0:
            subtitle += f" (Cải thiện: {sol['improvement_pct']:.2f}%)"
        ax.set_title(f"{algo_name}\n{subtitle}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Tọa độ X")
        ax.set_ylabel("Tọa độ Y")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=8)

    # Subplot 3: Bar chart comparison
    ax_bar = axes[2]
    algo_names = list(results.keys())
    distances = [results[k]["distance"] for k in algo_names]
    improvements = [results[k]["improvement_pct"] for k in algo_names]

    colors = ["#95a5a6", "#2ecc71", "#3498db", "#9b59b6"]
    bars = ax_bar.bar(algo_names, distances, color=colors, width=0.55, edgecolor="black", alpha=0.85)

    for bar, dist, imp in zip(bars, distances, improvements):
        height = bar.get_height()
        label = f"{dist:.1f}"
        if imp > 0:
            label += f"\n(-{imp:.1f}%)"
        ax_bar.annotate(
            label,
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax_bar.set_title("So sánh quãng đường giữa các Heuristic\n(Càng thấp càng tối ưu)", fontsize=11, fontweight="bold")
    ax_bar.set_ylabel("Tổng quãng đường")
    ax_bar.set_xticks(range(len(algo_names)))
    ax_bar.set_xticklabels(algo_names, rotation=20, ha="right")
    ax_bar.grid(axis="y", linestyle="--", alpha=0.5)

    plt.suptitle(
        f"ĐỀ TÀI: TỐI ƯU TUYẾN ĐƯỜNG GIAO HÀNG (CVRP)\nInstance: {instance.name} | Số điểm: {len(coords)-1} | Tải trọng xe: {instance.capacity}",
        fontsize=13,
        fontweight="bold",
        y=1.03,
    )
    plt.tight_layout()
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Đã lưu biểu đồ ảnh tĩnh tại: {output_png}")


def plot_plotly_interactive(
    instance: CVRPInstance,
    results: dict[str, dict[str, Any]],
    output_html: Path,
) -> None:
    """Export interactive HTML with side-by-side subplots for Nearest Neighbor and 2-Opt."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Nearest Neighbor (Khoảng cách: {results['Nearest Neighbor']['distance']})",
            f"2-Opt Cải tiến (Khoảng cách: {results['2-Opt (cải tiến)']['distance']} | Cải thiện: {results['2-Opt (cải tiến)']['improvement_pct']}%)",
        ),
        horizontal_spacing=0.08,
    )

    coords = instance.coordinates
    depot_x, depot_y = coords[0]

    for col_idx, algo_name in enumerate(["Nearest Neighbor", "2-Opt (cải tiến)"], start=1):
        sol = results[algo_name]

        # 1. Plot Depot
        fig.add_trace(
            go.Scatter(
                x=[depot_x],
                y=[depot_y],
                mode="markers+text",
                name="Depot (Kho)",
                text=["Depot"],
                textposition="bottom center",
                marker=dict(size=16, color="#e74c3c", symbol="star", line=dict(width=1, color="black")),
                showlegend=(col_idx == 1),
            ),
            row=1, col=col_idx,
        )

        # 2. Plot Customers
        cust_x = [coords[i][0] for i in range(1, len(coords))]
        cust_y = [coords[i][1] for i in range(1, len(coords))]
        cust_text = [f"KH {i}<br>Demand: {instance.demands[i]}" for i in range(1, len(coords))]
        fig.add_trace(
            go.Scatter(
                x=cust_x,
                y=cust_y,
                mode="markers+text",
                name="Khách hàng",
                text=[str(i) for i in range(1, len(coords))],
                hovertext=cust_text,
                hoverinfo="text+x+y",
                textposition="top center",
                marker=dict(size=9, color="#3498db", line=dict(width=1, color="navy")),
                showlegend=(col_idx == 1),
            ),
            row=1, col=col_idx,
        )

        # 3. Plot Routes for each vehicle
        for v_idx, route in enumerate(sol["routes"]):
            color = ROUTE_COLORS[v_idx % len(ROUTE_COLORS)]
            rx = [coords[node][0] for node in route]
            ry = [coords[node][1] for node in route]
            load = sol["loads"][v_idx]
            route_name = f"Xe {v_idx + 1} ({algo_name}) - Tải: {load}/{instance.capacity}"

            fig.add_trace(
                go.Scatter(
                    x=rx,
                    y=ry,
                    mode="lines+markers",
                    name=route_name,
                    line=dict(color=color, width=3),
                    marker=dict(size=5, color=color),
                    hoverinfo="name",
                    legendgroup=f"v{v_idx}",
                ),
                row=1, col=col_idx,
            )

    fig.update_layout(
        title=dict(
            text=f"<b>TRỰC QUAN HÓA SO SÁNH TUYẾN ĐƯỜNG GIAO HÀNG (CVRP)</b><br>"
                 f"Instance: {instance.name} | {len(coords)-1} Khách hàng | Tải trọng xe: {instance.capacity}",
            x=0.5,
            xanchor="center",
        ),
        template="plotly_white",
        height=650,
        margin=dict(l=40, r=40, t=90, b=40),
    )

    fig.write_html(str(output_html))
    print(f"[OK] Đã lưu giao diện tương tác HTML tại: {output_html}")


def print_summary_table(results: dict[str, dict[str, Any]]) -> None:
    """Print quantitative comparison table to terminal."""
    print("\n" + "=" * 70)
    print(f"{'Thuật toán Heuristic':<25} | {'Số xe':<8} | {'Tổng quãng đường':<18} | {'Cải thiện (%)':<12}")
    print("-" * 70)
    for algo_name, data in results.items():
        imp_str = f"{data['improvement_pct']:+.2f}%" if data["improvement_pct"] != 0 else "Gốc (0.0%)"
        print(f"{algo_name:<25} | {data['vehicle_count']:<8} | {data['distance']:<18.2f} | {imp_str:<12}")
    print("=" * 70 + "\n")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trực quan hóa và so sánh tuyến đường giao hàng CVRP/TSP.")
    parser.add_argument("--mssv", type=str, default="22110001", help="Mã số sinh viên để sinh bộ dữ liệu mẫu (mặc định: 22110001)")
    parser.add_argument("--customers", type=int, default=20, help="Số điểm giao hàng (mặc định: 20)")
    parser.add_argument("--cvrp-input", type=str, help="Đường dẫn file JSON CVRP (hoặc CVRPLIB)")
    parser.add_argument("--output-html", type=str, default=str(OUTPUT_DIR / "route_visualization.html"), help="Đường dẫn lưu file HTML tương tác")
    parser.add_argument("--output-png", type=str, default=str(OUTPUT_DIR / "route_comparison.png"), help="Đường dẫn lưu file ảnh tĩnh PNG")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.cvrp_input:
        input_path = Path(args.cvrp_input)
        if not input_path.exists():
            print(f"[ERROR] Không tìm thấy file: {input_path}")
            sys.exit(1)
        if input_path.suffix.lower() == ".vrp":
            instance = load_cvrplib(str(input_path))
        else:
            instance = load_json(str(input_path))
    else:
        print(f"[INFO] Sinh ngẫu nhiên bộ dữ liệu theo MSSV: {args.mssv} với {args.customers} khách hàng...")
        instance = generate_instance(mssv=args.mssv, customer_count=args.customers)

    results = solve_cvrp_heuristics(instance)
    print_summary_table(results)

    output_html = Path(args.output_html)
    output_png = Path(args.output_png)

    plot_matplotlib_comparison(instance, results, output_png)
    plot_plotly_interactive(instance, results, output_html)

    print(f"\n[HOÀN THÀNH] Bạn có thể mở '{output_html}' trong trình duyệt để khám phá tương tác")
    print(f"            và sử dụng '{output_png}' để chèn vào báo cáo đề tài.\n")


if __name__ == "__main__":
    main()
