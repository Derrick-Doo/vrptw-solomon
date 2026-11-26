# Plot the customer locations of Solomon instance C101.
import os
import matplotlib.pyplot as plt
from read_data import read_solomon

n_vehicles, capacity, df = read_solomon("data/c101.txt")

depot = df[df["cust_no"] == 0]
customers = df[df["cust_no"] != 0]

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(customers["x"], customers["y"], s=20, label="Customers (100)")
ax.scatter(depot["x"], depot["y"], s=150, marker="s", color="red", label="Depot")
ax.set_title("Solomon C101: customer locations")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend()
ax.set_aspect("equal")

os.makedirs("figures", exist_ok=True)
fig.savefig("figures/c101_customers.png", dpi=150, bbox_inches="tight")
print("Saved figures/c101_customers.png")
plt.show()