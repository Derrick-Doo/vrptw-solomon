# compare.py
# Run every method on one or more Solomon instances, score them with the same checker,
# and save a comparison table per instance plus one summary table.
#
#   python compare.py                 # all three: c101, r101, rc101
#   python compare.py r101            # just one
import json
import os
import sys

import pandas as pd

from evaluate import evaluate
from method_a import solve_method_a
from read_data import read_solomon
from solve_ortools import solve_ortools

INSTANCES = ["c101", "r101", "rc101"]

# Best known solutions from SINTEF: vehicles first, then distance.
# https://www.sintef.no/projectweb/top/vrptw/100-customers/
# C101 checked 2026-11-26; all three re-checked 2026-11-28.
# RC101: SINTEF lists 1696.95 and notes that the 1696.94 reported in the paper is a rounding error.
BEST_KNOWN = {
    "c101": {"vehicles": 10, "total_distance": 828.94},
    "r101": {"vehicles": 19, "total_distance": 1650.80},
    "rc101": {"vehicles": 14, "total_distance": 1696.95},
}

OR_TOOLS_SECONDS = 30


def gap_vs_best(result, best):
    """Distance gap in %, only when the truck count matches the best known solution.

    Solutions are ranked by trucks first, so a plan with more trucks may be shorter than the
    best known one; comparing distances then would be misleading.
    """
    if best is None or result["vehicles"] != best["vehicles"]:
        return None
    return round((result["total_distance"] / best["total_distance"] - 1) * 100, 1)


def run_instance(instance):
    n_vehicles, capacity, df = read_solomon(f"data/{instance}.txt")
    best = BEST_KNOWN.get(instance)

    runs = {
        "Method A (cluster by load, shortest path)": solve_method_a(df, capacity, "distance"),
        "Method A2 (cluster by load, time order)": solve_method_a(df, capacity, "time"),
        f"OR-Tools (capacity + time windows, {OR_TOOLS_SECONDS} s)":
            solve_ortools(df, n_vehicles, capacity, OR_TOOLS_SECONDS),
    }

    rows, all_routes = [], {}
    for name, (routes, runtime) in runs.items():
        r = evaluate(routes, df, capacity)
        rows.append({
            "instance": instance.upper(),
            "method": name,
            "vehicles": r["vehicles"],
            "total_distance": r["total_distance"],
            "gap_vs_best_%": gap_vs_best(r, best),
            "late_customers": r["late_customers"],
            "total_lateness": r["total_lateness"],
            "late_returns": r["late_returns"],
            "overloaded_routes": r["overloaded_routes"],
            "runtime_s": round(runtime, 3),
        })
        all_routes[name] = routes

    if best is not None:
        rows.append({"instance": instance.upper(), "method": "Best known (SINTEF)", **best,
                     "gap_vs_best_%": 0.0, "late_customers": 0})

    table = pd.DataFrame(rows)
    for col in ["late_customers", "late_returns", "overloaded_routes"]:
        table[col] = table[col].astype("Int64")  # whole numbers; blank for the best-known row

    os.makedirs("results", exist_ok=True)
    table.to_csv(f"results/{instance}_comparison.csv", index=False)
    with open(f"results/{instance}_routes.json", "w") as f:
        json.dump(all_routes, f, indent=1)
    return table


if __name__ == "__main__":
    chosen = [a.lower() for a in sys.argv[1:]] or INSTANCES
    pd.set_option("display.width", 220)
    tables = []
    for instance in chosen:
        table = run_instance(instance)
        print(table.drop(columns="instance").to_string(index=False))
        print(f"Saved results/{instance}_comparison.csv and results/{instance}_routes.json\n")
        tables.append(table)

    if chosen == INSTANCES:
        pd.concat(tables).to_csv("results/summary.csv", index=False)
        print("Saved results/summary.csv")
