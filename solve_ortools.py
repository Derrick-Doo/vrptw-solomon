# solve_ortools.py
# Solve Solomon C101 with Google OR-Tools.
import math
from read_data import read_solomon

# Load C101: number of vehicles, vehicle capacity, customer table
num_vehicles, capacity, df = read_solomon("data/c101.txt")

# OR-Tools only accepts integers, so multiply distances by 10 (keeps one decimal)
SCALE = 10

# List of (x, y) for every point; index 0 is the depot
coords = list(zip(df["x"], df["y"]))
n = len(coords)

# Distance matrix: dist[i][j] = straight-line distance from point i to point j (scaled)
dist = []
for i in range(n):
    row = []
    for j in range(n):
        dx = coords[i][0] - coords[j][0]
        dy = coords[i][1] - coords[j][1]
        row.append(round(math.sqrt(dx * dx + dy * dy) * SCALE))
    dist.append(row)

print("matrix size:", len(dist), "x", len(dist[0]))
print("depot -> customer 1:", dist[0][1] / SCALE)
print("customer 1 -> customer 2:", dist[1][2] / SCALE)


# ---- Build the OR-Tools model ----
# Manager: translates between our point numbers (0..100) and OR-Tools' internal numbers
manager = pywrapcp.RoutingIndexManager(n, num_vehicles, 0)
# Routing model: the problem we want OR-Tools to solve
routing = pywrapcp.RoutingModel(manager)


def distance_callback(from_index, to_index):
    """Return the scaled distance between two points."""
    i = manager.IndexToNode(from_index)
    j = manager.IndexToNode(to_index)
    return dist[i][j]


transit_idx = routing.RegisterTransitCallback(distance_callback)
# The cost of driving from one point to the next = the distance
routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

# Search settings: how to build the first solution
params = pywrapcp.DefaultRoutingSearchParameters()
params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

solution = routing.SolveWithParameters(params)

if solution:
    print("total distance:", solution.ObjectiveValue() / SCALE)
    used = 0
    for v in range(num_vehicles):
        start = routing.Start(v)
        # If the stop after the start is already the end, this truck never left the depot
        if not routing.IsEnd(solution.Value(routing.NextVar(start))):
            used += 1
    print("vehicles used:", used)
else:
    print("no solution found")
