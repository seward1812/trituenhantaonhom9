from pathlib import Path
from data.duannhom import generate_instance
from visualization.plot_route import solve_cvrp_heuristics, plot_matplotlib_comparison, plot_plotly_interactive


def test_solve_cvrp_heuristics():
    instance = generate_instance("123456", customer_count=10)
    results = solve_cvrp_heuristics(instance)

    assert "Nearest Neighbor" in results
    assert "2-Opt (cải tiến)" in results
    assert results["Nearest Neighbor"]["distance"] > 0
    assert results["2-Opt (cải tiến)"]["distance"] <= results["Nearest Neighbor"]["distance"] + 1e-5


def test_plot_generation(tmp_path):
    instance = generate_instance("123456", customer_count=8)
    results = solve_cvrp_heuristics(instance)

    png_path = tmp_path / "test_comparison.png"
    html_path = tmp_path / "test_vis.html"

    plot_matplotlib_comparison(instance, results, png_path)
    plot_plotly_interactive(instance, results, html_path)

    assert png_path.exists()
    assert png_path.stat().st_size > 0
    assert html_path.exists()
    assert html_path.stat().st_size > 0
