# compare.py
# Run every method on C101, score them with the same checker, and save a comparison table.
import json
import os

import pandas as pd

from evaluate import evaluate
from method_a import solve_method_a
from read_data import read_solomon
from solve_ortools import solve_ortools

INSTANCE = "c101"
# Best known solution from SINTEF (checked 2026-11-26): vehicles first, then distance.
BEST_KNOWN = {"vehicles": 10, "total_distance": 828.94}

n_vehicles, capacity, df = read_solomon(f"data/{INSTANCE}.txt")

runs = {
    "Method A (cluster by load, shortest path)": solve_method_a(df, capacity, "distance"),
    "Method A2 (cluster by load, time order)": solve_method_a(df, capacity, "time"),
    "OR-Tools (capacity + time windows, 30 s)": solve_ortools(df, n_vehicles, capacity, 30),
}

rows, all_routes = [], {}
for name, (routes, runtime) in runs.items():
    r = evaluate(routes, df, capacity)
    gap = (r["total_distance"] / BEST_KNOWN["total_distance"] - 1) * 100
    rows.append({
        "method": name,
        "vehicles": r["vehicles"],
        "total_distance": r["total_distance"],
        "gap_vs_best_%": round(gap, 1),
        "late_customers": r["late_customers"],
        "total_lateness": r["total_lateness"],
        "late_returns": r["late_returns"],
        "overloaded_routes": r["overloaded_routes"],
        "runtime_s": round(runtime, 3),
    })
    all_routes[name] = routes

rows.append({"method": "Best known (SINTEF)", **BEST_KNOWN, "gap_vs_best_%": 0.0,
             "late_customers": 0})
table = pd.DataFrame(rows)
for col in ["late_customers", "late_returns", "overloaded_routes"]:
    table[col] = table[col].astype("Int64")  # whole numbers; blank for the best-known row

os.makedirs("results", exist_ok=True)
table.to_csv(f"results/{INSTANCE}_comparison.csv", index=False)
with open(f"results/{INSTANCE}_routes.json", "w") as f:
    json.dump(all_routes, f, indent=1)

pd.set_option("display.width", 200)
print(table.to_string(index=False))
print(f"\nSaved results/{INSTANCE}_comparison.csv and results/{INSTANCE}_routes.json")
