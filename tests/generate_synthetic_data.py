"""
Generates a SYNTHETIC Superstore-shaped dataset for smoke-testing the pipeline.
It is NOT real data and its findings mean nothing. Use the real Superstore file for the project.

Run:  python tests/generate_synthetic_data.py
Writes data/raw/synthetic_superstore.xlsx  (delete it before adding the real file)
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
ROOT = Path(__file__).resolve().parents[1]

catalog = {
    "Furniture": {"Tables": (0.02, 400), "Bookcases": (0.05, 300), "Chairs": (0.14, 250), "Furnishings": (0.17, 60)},
    "Office Supplies": {"Binders": (0.30, 25), "Paper": (0.40, 15), "Storage": (0.10, 80), "Supplies": (0.05, 40)},
    "Technology": {"Phones": (0.15, 350), "Accessories": (0.25, 50), "Copiers": (0.35, 900), "Machines": (0.05, 700)},
}
regions = {"West": ["California", "Washington"], "East": ["New York", "Pennsylvania"],
           "Central": ["Texas", "Illinois"], "South": ["Florida", "Georgia"]}
state_to_region = {s: r for r, ss in regions.items() for s in ss}
states = list(state_to_region)

n_cust = 700
cust_ids = [f"CU-{i:04d}" for i in range(n_cust)]
cust_state = {c: rng.choice(states) for c in cust_ids}
cust_activity = rng.pareto(1.5, n_cust) + 0.3

rows, rid, oid = [], 1, 1
dates = pd.date_range("2022-01-01", "2025-12-31")
for _ in range(5200):
    c = rng.choice(cust_ids, p=cust_activity / cust_activity.sum())
    d = rng.choice(dates)
    st = cust_state[c]
    for _ in range(rng.integers(1, 5)):
        cat = rng.choice(list(catalog))
        sub = rng.choice(list(catalog[cat]))
        base_margin, price = catalog[cat][sub]
        sales = max(2, rng.normal(price, price * 0.3)) * rng.integers(1, 6)
        year_boost = 0.04 * (pd.Timestamp(d).year - 2022)  # discounting creeps up over time
        discount = rng.choice([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7], p=[0.45 - year_boost, .1, .15, .1 + year_boost / 2, .1, .06 + year_boost / 2, .04])
        margin = base_margin + 0.15 - 1.1 * discount + rng.normal(0, 0.05)
        rows.append(dict(**{
            "Row ID": rid, "Order ID": f"US-{oid:05d}", "Order Date": pd.Timestamp(d),
            "Ship Date": pd.Timestamp(d) + pd.Timedelta(days=int(rng.integers(2, 8))),
            "Ship Mode": rng.choice(["Standard Class", "Second Class", "First Class"]),
            "Customer ID": c, "Customer Name": f"Name {c}", "Segment": rng.choice(["Consumer", "Corporate", "Home Office"]),
            "Country": "United States", "City": "City", "State": st, "Postal Code": 10000,
            "Region": state_to_region[st], "Product ID": f"P-{sub[:3]}-{rng.integers(1, 30)}",
            "Category": cat, "Sub-Category": sub, "Product Name": f"{sub} item", "Sales": round(sales, 2),
            "Quantity": int(rng.integers(1, 6)), "Discount": discount, "Profit": round(sales * margin, 2)}))
        rid += 1
    oid += 1

orders = pd.DataFrame(rows)
ret_ids = rng.choice(orders["Order ID"].unique(), 300, replace=False)
returns = pd.DataFrame({"Returned": "Yes", "Order ID": ret_ids})
people = pd.DataFrame({"Person": ["A", "B", "C", "D"], "Region": list(regions)})

out = ROOT / "data" / "raw" / "synthetic_superstore.xlsx"
with pd.ExcelWriter(out) as w:
    orders.to_excel(w, sheet_name="Orders", index=False)
    returns.to_excel(w, sheet_name="Returns", index=False)
    people.to_excel(w, sheet_name="People", index=False)
print(f"Wrote {out} ({len(orders)} order lines)")
