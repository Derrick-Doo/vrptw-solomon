# plot_routes.py
# Draw Method A and OR-Tools routes side by side. Run compare.py first.
#
#   python plot_routes.py             # all three: c101, r101, rc101
#   python plot_routes.py r101        # just one
import json
import os
import sys

import matplotlib.pyplot as plt

from evaluate import evaluate
from read_data import read_solomon

INSTANCES = ["c101", "r101", "rc101"]


def plot_instance(instance):
    n_vehicles, capacity, df = read_solomon(f"data/{instance}.txt")
    with open(f"results/{instance}_routes.json") as f:
        all_routes = json.load(f)

    method_a = "Method A (cluster by load, shortest path)"
    or_tools = next(name for name in all_routes if name.startswith("OR-Tools"))
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    for ax, name in zip(axes, [method_a, or_tools]):
        routes = all_routes[name]
        result = evaluate(routes, df, capacity)
        for route in routes:
            path = [0] + route + [0]
            ax.plot(df["x"][path], df["y"][path], "-o", markersize=3, linewidth=1)
        late = [c for c, _ in result["late_list"]]
        if late:
            ax.scatter(df["x"][late], df["y"][late], s=80, facecolors="none",
                       edgecolors="red", linewidths=1.5, label=f"Late customers ({len(late)})")
            ax.legend(loc="lower right")
        ax.scatter(df["x"][0], df["y"][0], s=150, marker="s", color="black", zorder=5)
        ax.set_title(f"{instance.upper()} - {name}\n{result['vehicles']} trucks, "
                     f"distance {result['total_distance']}, {result['late_customers']} late")
        ax.set_aspect("equal")

    os.makedirs("figures", exist_ok=True)
    path = f"figures/{instance}_routes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}")


if __name__ == "__main__":
    for instance in [a.lower() for a in sys.argv[1:]] or INSTANCES:
        plot_instance(instance)
