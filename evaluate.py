# evaluate.py
# Shared helpers used by BOTH methods, so they are scored by exactly the same rules.
import math


def distance_matrix(df):
    """Straight-line (Euclidean) distance between every pair of points, in double precision."""
    xs = df["x"].tolist()
    ys = df["y"].tolist()
    n = len(xs)
    return [[math.hypot(xs[i] - xs[j], ys[i] - ys[j]) for j in range(n)] for i in range(n)]


def evaluate(routes, df, capacity):
    """Score a solution.

    routes: list of routes; each route is a list of customer numbers (depot 0 not included).
    Rules (standard Solomon VRPTW):
      - travel time = distance
      - arriving before ready_time -> the truck waits (allowed)
      - arriving after due_date    -> time-window violation
      - total demand on a truck must not exceed capacity
    """
    dist = distance_matrix(df)
    demand = df["demand"].tolist()
    ready = df["ready_time"].tolist()
    due = df["due_date"].tolist()
    service = df["service_time"].tolist()

    # Every customer must be visited exactly once.
    visited = sorted(c for route in routes for c in route)
    assert visited == list(range(1, len(df))), "some customers are missing or visited twice"

    total_distance = 0.0
    late_customers = []       # (customer, minutes late)
    overloaded_routes = 0
    late_returns = 0          # trucks back at the depot after it closes

    for route in routes:
        if sum(demand[c] for c in route) > capacity:
            overloaded_routes += 1

        time = 0.0            # truck leaves the depot at time 0
        prev = 0
        for c in route:
            arrival = time + dist[prev][c]
            total_distance += dist[prev][c]
            if arrival > due[c] + 1e-6:
                late_customers.append((c, arrival - due[c]))
            start = max(arrival, ready[c])   # wait if early
            time = start + service[c]        # leave after service
            prev = c
        back = time + dist[prev][0]
        total_distance += dist[prev][0]
        if back > due[0] + 1e-6:
            late_returns += 1

    return {
        "vehicles": len(routes),
        "total_distance": round(total_distance, 2),
        "late_customers": len(late_customers),
        "total_lateness": round(sum(m for _, m in late_customers), 1),
        "overloaded_routes": overloaded_routes,
        "late_returns": late_returns,
        "late_list": late_customers,
    }
