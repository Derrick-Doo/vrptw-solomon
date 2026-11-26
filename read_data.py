# read_data.py
# Read a Solomon VRPTW instance into a pandas DataFrame.
from pathlib import Path
import pandas as pd

COLUMNS = ["cust_no", "x", "y", "demand", "ready_time", "due_date", "service_time"]


def read_solomon(path):
    """Return (vehicle_count, capacity, customers DataFrame). Row 0 is the depot."""
    lines = Path(path).read_text().splitlines()
    vehicle_count, capacity = map(int, lines[4].split())
    rows = []
    for line in lines[9:]:
        parts = line.split()
        if len(parts) == 7:  # keep only data rows: exactly 7 numbers
            rows.append([int(p) for p in parts])
    df = pd.DataFrame(rows, columns=COLUMNS)
    return vehicle_count, capacity, df


if __name__ == "__main__":
    n_vehicles, capacity, df = read_solomon("data/c101.txt")
    print("vehicles:", n_vehicles, "capacity:", capacity)
    print("rows:", len(df))
    print(df.head())
    print(df.tail(3))
    print("total demand:", df["demand"].sum())