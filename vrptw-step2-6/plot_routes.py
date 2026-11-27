# plot_routes.py
# Draw Method A and OR-Tools routes side by side. Run compare.py first.
import json
import os

import matplotlib.pyplot as plt

from evaluate import evaluate
from read_data import read_solomon

n_vehicles, capacity, df = read_solomon("data/c101.txt")
with open("results/c101_routes.json") as f:
    all_routes = json.load(f)

to_plot = ["Method A (cluster by load, shortest path)", "OR-Tools (capacity + time windows, 30 s)"]
fig, axes = plt.subplots(1, 2, figsize=(14, 7))

for ax, name in zip(axes, to_plot):
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
    ax.set_title(f"{name}\n{result['vehicles']} trucks, distance {result['total_distance']}, "
                 f"{result['late_customers']} late")
    ax.set_aspect("equal")

os.makedirs("figures", exist_ok=True)
fig.savefig("figures/c101_routes.png", dpi=150, bbox_inches="tight")
print("Saved figures/c101_routes.png")
plt.show()
