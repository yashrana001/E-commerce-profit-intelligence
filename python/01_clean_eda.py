
import re
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DISCOUNT_BINS, DISCOUNT_LABELS, FIG, PROC, find_raw_file

warnings.filterwarnings("ignore", category=FutureWarning)


def snake(col: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", col.strip().lower()).strip("_")


def load_raw():
    path = find_raw_file()
    print(f"Loading {path.name}")
    returns = None
    if path.suffix.lower() in (".xlsx", ".xls"):
        sheets = pd.ExcelFile(path).sheet_names
        orders = pd.read_excel(path, sheet_name="Orders")
        if "Returns" in sheets:
            returns = pd.read_excel(path, sheet_name="Returns")
    else:
        try:
            orders = pd.read_csv(path)
        except UnicodeDecodeError:  # Kaggle copy is often latin-1
            orders = pd.read_csv(path, encoding="latin-1")
    orders.columns = [snake(c) for c in orders.columns]
    if returns is not None:
        returns.columns = [snake(c) for c in returns.columns]
    return orders, returns


def clean(orders: pd.DataFrame, returns) -> pd.DataFrame:
    n0 = len(orders)
    orders = orders.drop_duplicates().copy()
    print(f"Dropped {n0 - len(orders)} duplicate rows")

    for c in ("order_date", "ship_date"):
        orders[c] = pd.to_datetime(orders[c], errors="coerce")
    bad = orders["order_date"].isna().sum()
    if bad:
        print(f"WARNING: {bad} rows with unparseable order_date dropped")
        orders = orders.dropna(subset=["order_date"])

    for c in ("sales", "profit", "discount", "quantity"):
        orders[c] = pd.to_numeric(orders[c], errors="coerce")
    orders = orders.dropna(subset=["sales", "profit", "discount"])

    # Text hygiene
    for c in orders.select_dtypes(include=["object", "string"]).columns:
        orders[c] = orders[c].astype("string").str.strip()

    # Feature engineering
    orders["margin"] = np.where(orders["sales"] != 0, orders["profit"] / orders["sales"], np.nan)
    orders["loss_making"] = orders["profit"] < 0
    orders["discount_band"] = pd.cut(
        orders["discount"], bins=DISCOUNT_BINS, labels=DISCOUNT_LABELS
    ).astype(str)
    orders["order_year"] = orders["order_date"].dt.year
    orders["order_month"] = orders["order_date"].dt.to_period("M").dt.to_timestamp()
    orders["ship_days"] = (orders["ship_date"] - orders["order_date"]).dt.days

    if returns is not None:
        returned_ids = set(returns["order_id"].astype(str).str.strip())
        orders["returned"] = orders["order_id"].astype(str).isin(returned_ids)
    else:
        orders["returned"] = False
    return orders


def summarise(df: pd.DataFrame, by) -> pd.DataFrame:
    g = df.groupby(by, observed=True).agg(
        orders=("order_id", "nunique"),
        lines=("order_id", "size"),
        revenue=("sales", "sum"),
        profit=("profit", "sum"),
        avg_discount=("discount", "mean"),
        loss_lines=("loss_making", "sum"),
    )
    g["margin_pct"] = 100 * g["profit"] / g["revenue"]
    g["loss_line_pct"] = 100 * g["loss_lines"] / g["lines"]
    return g.reset_index()


def make_charts(df, monthly, sub, bands):
    plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})

    fig, ax1 = plt.subplots(figsize=(11, 4.5))
    ax1.plot(monthly["order_month"], monthly["revenue"], color="#1f77b4", label="Revenue")
    ax1.plot(monthly["order_month"], monthly["profit"], color="#2ca02c", label="Profit")
    ax1.set_ylabel("Revenue / Profit")
    ax2 = ax1.twinx()
    ax2.plot(monthly["order_month"], monthly["margin_pct"], color="#d62728", ls="--", label="Margin %")
    ax2.set_ylabel("Margin %")
    ax2.spines["right"].set_visible(True)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    ax1.set_title("Revenue vs profit vs margin, monthly")
    fig.tight_layout()
    fig.savefig(FIG / "01_revenue_vs_profit.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#2ca02c" if m >= 0 else "#d62728" for m in bands["margin_pct"]]
    ax.bar(bands["discount_band"], bands["margin_pct"], color=colors)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("Profit margin by discount band")
    ax.set_ylabel("Margin %")
    fig.tight_layout()
    fig.savefig(FIG / "02_margin_by_discount_band.png")
    plt.close(fig)

    s = sub.sort_values("profit")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(s["sub_category"], s["profit"], color=["#d62728" if p < 0 else "#2ca02c" for p in s["profit"]])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title("Profit by sub-category")
    fig.tight_layout()
    fig.savefig(FIG / "03_profit_by_subcategory.png")
    plt.close(fig)

    samp = df.sample(min(len(df), 5000), random_state=42)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(samp["discount"], samp["margin"].clip(-2, 1), s=8, alpha=0.3)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Discount")
    ax.set_ylabel("Line margin (clipped to -200%..100%)")
    ax.set_title("Discount vs line-item margin")
    fig.tight_layout()
    fig.savefig(FIG / "04_discount_vs_margin_scatter.png")
    plt.close(fig)


def main():
    orders, returns = load_raw()
    print(f"Raw shape: {orders.shape}")
    df = clean(orders, returns)
    print(f"Clean shape: {df.shape}")
    print("\nNull counts (non-zero only):")
    nulls = df.isna().sum()
    print(nulls[nulls > 0].to_string() if (nulls > 0).any() else "none")
    print("\nDescribe:")
    print(df[["sales", "profit", "discount", "quantity", "margin"]].describe().round(2).to_string())

    # ---- Exports
    df.to_csv(PROC / "orders_clean.csv", index=False)

    sql_cols = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode", "customer_id",
        "customer_name", "segment", "country", "city", "state", "postal_code", "region",
        "product_id", "category", "sub_category", "product_name", "sales", "quantity",
        "discount", "profit",
    ]
    present = [c for c in sql_cols if c in df.columns]
    sql_df = df[present].copy()
    sql_df["order_date"] = sql_df["order_date"].dt.strftime("%Y-%m-%d")
    sql_df["ship_date"] = sql_df["ship_date"].dt.strftime("%Y-%m-%d")
    sql_df.to_csv(PROC / "orders_for_sql.csv", index=False)

    if returns is not None:
        (returns[["order_id"]].drop_duplicates()
         .to_csv(PROC / "returns_for_sql.csv", index=False))
    else:  # keep the SQL loader working; the returns table will simply be empty
        pd.DataFrame({"order_id": []}).to_csv(PROC / "returns_for_sql.csv", index=False)

    # ---- Aggregates (also feed Power BI)
    monthly = summarise(df, "order_month")
    monthly["rev_growth_pct"] = 100 * monthly["revenue"].pct_change()
    monthly["profit_growth_pct"] = 100 * monthly["profit"].pct_change()
    monthly.to_csv(PROC / "monthly_kpis.csv", index=False)

    yearly = summarise(df, "order_year")
    yearly["rev_growth_pct"] = 100 * yearly["revenue"].pct_change()
    yearly["profit_growth_pct"] = 100 * yearly["profit"].pct_change()
    yearly.to_csv(PROC / "yearly_kpis.csv", index=False)

    cat = summarise(df, "category")
    sub = summarise(df, ["category", "sub_category"])
    bands = summarise(df, "discount_band")
    bands["discount_band"] = pd.Categorical(bands["discount_band"], DISCOUNT_LABELS, ordered=True)
    bands = bands.sort_values("discount_band")
    region = summarise(df, "region")
    state = summarise(df, ["region", "state"]).sort_values("profit")

    cat.to_csv(PROC / "category_profit.csv", index=False)
    sub.to_csv(PROC / "subcategory_profit.csv", index=False)
    bands.to_csv(PROC / "discount_band_profit.csv", index=False)
    region.to_csv(PROC / "region_profit.csv", index=False)
    state.to_csv(PROC / "state_profit.csv", index=False)

    make_charts(df, monthly, sub, bands)

    print("\nYearly KPIs:")
    print(yearly[["order_year", "revenue", "profit", "margin_pct", "rev_growth_pct", "profit_growth_pct"]]
          .round(2).to_string(index=False))
    print("\nMargin by discount band:")
    print(bands[["discount_band", "lines", "revenue", "profit", "margin_pct"]].round(2).to_string(index=False))
    print(f"\nSaved cleaned data and charts. Next: python python/02_rfm_segmentation.py")


if __name__ == "__main__":
    main()
