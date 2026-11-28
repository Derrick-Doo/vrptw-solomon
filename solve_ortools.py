# solve_ortools.py
# Method B: solve the full VRPTW (capacity + time windows) with Google OR-Tools.
import time

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from evaluate import distance_matrix, evaluate
from read_data import read_solomon

SCALE = 10                  # OR-Tools only accepts integers: work in 0.1 units
VEHICLE_FIXED_COST = 100_000  # large cost per truck used -> fewer trucks first, then shorter distance


def solve_ortools(df, n_vehicles, capacity, time_limit=30):
    """Return (routes, runtime in seconds). Each route is a list of customer numbers."""
    n = len(df)
    dist = distance_matrix(df)
    int_dist = [[round(d * SCALE) for d in row] for row in dist]
    demand = df["demand"].tolist()
    service = [s * SCALE for s in df["service_time"]]
    ready = [r * SCALE for r in df["ready_time"]]
    due = [d * SCALE for d in df["due_date"]]

    # Manager translates between our node numbers (0..100) and OR-Tools' internal indices.
    manager = pywrapcp.RoutingIndexManager(n, n_vehicles, 0)  # 0 = depot
    routing = pywrapcp.RoutingModel(manager)

    # 1) Cost of each arc = distance.
    def distance_cb(from_index, to_index):
        return int_dist[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    dist_cb_index = routing.RegisterTransitCallback(distance_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_index)
    routing.SetFixedCostOfAllVehicles(VEHICLE_FIXED_COST)

    # 2) Capacity: running load on each truck may not exceed capacity.
    def demand_cb(from_index):
        return demand[manager.IndexToNode(from_index)]

    demand_cb_index = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(
        demand_cb_index, 0, [capacity] * n_vehicles, True, "Load")

    # 3) Time windows: time from A to B = service time at A + travel time A->B.
    def time_cb(from_index, to_index):
        a = manager.IndexToNode(from_index)
        b = manager.IndexToNode(to_index)
        return service[a] + int_dist[a][b]

    time_cb_index = routing.RegisterTransitCallback(time_cb)
    horizon = due[0]  # depot closing time
    routing.AddDimension(time_cb_index, horizon, horizon, False, "Time")  # slack = waiting allowed
    time_dim = routing.GetDimensionOrDie("Time")
    for node in range(1, n):
        time_dim.CumulVar(manager.NodeToIndex(node)).SetRange(ready[node], due[node])
    for v in range(n_vehicles):
        time_dim.CumulVar(routing.Start(v)).SetRange(ready[0], due[0])
        time_dim.CumulVar(routing.End(v)).SetRange(ready[0], due[0])

    # 4) Search: build a first solution by cheapest insertion, then guided local search until the
    #    time limit. PATH_CHEAPEST_ARC (extend each route with the nearest next stop) could not
    #    build any feasible start on R101/RC101, whose time windows are tight; insertion can.
    #    On C101 both give the same final result (10 trucks, 828.94).
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(time_limit)

    t0 = time.perf_counter()
    solution = routing.SolveWithParameters(params)
    runtime = time.perf_counter() - t0
    if solution is None:
        raise RuntimeError("OR-Tools found no feasible solution")

    # 5) Read the routes back out (skip trucks that stay at the depot).
    routes = []
    for v in range(n_vehicles):
        index = routing.Start(v)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                route.append(node)
            index = solution.Value(routing.NextVar(index))
        if route:
            routes.append(route)

    # 6) Safety check: a valid OR-Tools plan can never be late or overloaded. If it is, stop loudly
    #    instead of saving a wrong result (this happened once on Windows, 2026-11-27, not reproduced).
    check = evaluate(routes, df, capacity)
    if check["late_customers"] or check["late_returns"] or check["overloaded_routes"]:
        raise RuntimeError(f"OR-Tools returned an invalid plan ({check['late_customers']} late "
                           "customers). Run the script again.")
    return routes, runtime


if __name__ == "__main__":
    n_vehicles, capacity, df = read_solomon("data/c101.txt")
    routes, runtime = solve_ortools(df, n_vehicles, capacity)
    result = evaluate(routes, df, capacity)
    print(f"OR-Tools on C101 ({runtime:.1f} s)")
    for i, r in enumerate(routes, 1):
        print(f"  truck {i:2d}: load {df['demand'][r].sum():3d}  0 -> {' -> '.join(map(str, r))} -> 0")
    print({k: v for k, v in result.items() if k != "late_list"})
