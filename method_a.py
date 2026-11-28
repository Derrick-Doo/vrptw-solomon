# method_a.py
# Method A: "cluster by capacity first, route each truck second" (the Capgemini-style approach).
# Step 1 groups customers into trucks by load only; step 2 orders each truck by distance only.
# Time windows are NOT used when building the plan - they are only checked afterwards.
import math
import time

from evaluate import distance_matrix, evaluate
from read_data import read_solomon


def sweep_clusters(df, capacity):
    """Sort customers by angle around the depot, then fill trucks one by one up to capacity."""
    depot_x, depot_y = df.loc[0, "x"], df.loc[0, "y"]
    customers = df[df["cust_no"] != 0].copy()
    customers["angle"] = [math.atan2(y - depot_y, x - depot_x)
                          for x, y in zip(customers["x"], customers["y"])]
    customers = customers.sort_values("angle")

    clusters, current, load = [], [], 0
    for c, d in zip(customers["cust_no"], customers["demand"]):
        if load + d > capacity:      # truck full -> start a new one
            clusters.append(current)
            current, load = [], 0
        current.append(int(c))
        load += d
    if current:
        clusters.append(current)
    return clusters


def nearest_neighbour(cluster, dist):
    """Start at the depot, always drive to the closest customer not yet visited."""
    route, current, left = [], 0, set(cluster)
    while left:
        nxt = min(left, key=lambda c: dist[current][c])
        route.append(nxt)
        left.remove(nxt)
        current = nxt
    return route


def route_length(route, dist):
    path = [0] + route + [0]
    return sum(dist[a][b] for a, b in zip(path, path[1:]))


def two_opt(route, dist):
    """Improve a route by reversing segments while that makes it shorter."""
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if route_length(candidate, dist) < route_length(best, dist) - 1e-9:
                    best, improved = candidate, True
    return best


def solve_method_a(df, capacity, order="distance"):
    """Return (routes, runtime in seconds).

    order="distance": inside each truck, shortest path (nearest neighbour + 2-opt).
    order="time":     inside each truck, visit customers by earliest ready_time (variant A2).
    Both use the SAME trucks from sweep_clusters, so any difference comes from the order only.
    """
    t0 = time.perf_counter()
    dist = distance_matrix(df)
    clusters = sweep_clusters(df, capacity)
    if order == "distance":
        routes = [two_opt(nearest_neighbour(c, dist), dist) for c in clusters]
    else:
        ready = df["ready_time"].tolist()
        routes = [sorted(c, key=lambda x: ready[x]) for c in clusters]
    return routes, time.perf_counter() - t0


if __name__ == "__main__":
    n_vehicles, capacity, df = read_solomon("data/c101.txt")
    for order in ["distance", "time"]:
        routes, runtime = solve_method_a(df, capacity, order)
        result = evaluate(routes, df, capacity)
        print(f"Method A (order by {order}) on C101 ({runtime:.3f} s)")
        for i, r in enumerate(routes, 1):
            print(f"  truck {i:2d}: load {df['demand'][r].sum():3d}  0 -> {' -> '.join(map(str, r))} -> 0")
        print({k: v for k, v in result.items() if k != "late_list"})
        print()
