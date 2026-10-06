"""
Step 3: Customer lifetime value, repeat purchase behaviour and cohort retention.

Outputs:
  data/processed/customer_summary.csv      CLV, repeat flag, first-order discount, deciles
  data/processed/cohort_retention_monthly.csv   (long format, for Power BI)
  data/processed/cohort_retention_annual.csv    (long format, for Power BI)
  data/processed/repeat_gap_days.csv       days between consecutive orders
  images/06_cohort_retention_monthly.png, 07_cohort_retention_annual.png

Run:  python python/03_cohort_retention.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from config import FIG, PROC


def customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    # One row per order first, so order-level stats are not inflated by line count
    orders = (df.groupby(["customer_id", "order_id"])
                .agg(order_date=("order_date", "min"),
                     sales=("sales", "sum"),
                     profit=("profit", "sum"),
                     discount=("discount", "mean"))
                .reset_index()
                .sort_values(["customer_id", "order_date"]))

    first_order = orders.groupby("customer_id").head(1).set_index("customer_id")

    cust = orders.groupby("customer_id").agg(
        first_order=("order_date", "min"),
        last_order=("order_date", "max"),
        orders=("order_id", "nunique"),
        revenue=("sales", "sum"),
        profit=("profit", "sum"),
        avg_discount=("discount", "mean"),
    )
    cust["first_order_discount"] = first_order["discount"]
    cust["first_order_profit"] = first_order["profit"]
    cust["lifespan_days"] = (cust["last_order"] - cust["first_order"]).dt.days
    cust["customer_type"] = np.where(cust["orders"] > 1, "Repeat", "One-time")
    cust["margin_pct"] = 100 * cust["profit"] / cust["revenue"]
    cust["avg_order_value"] = cust["revenue"] / cust["orders"]
    cust["profit_decile"] = pd.qcut(cust["profit"].rank(method="first", ascending=False),
                                    10, labels=range(1, 11)).astype(int)
    cust["acquisition_year"] = cust["first_order"].dt.year
    return cust.reset_index()


def repeat_gaps(df: pd.DataFrame) -> pd.DataFrame:
    o = (df.groupby(["customer_id", "order_id"])["order_date"].min()
           .reset_index().sort_values(["customer_id", "order_date"]))
    o["days_since_prev"] = o.groupby("customer_id")["order_date"].diff().dt.days
    return o.dropna(subset=["days_since_prev"])


def monthly_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    d = df[["customer_id", "order_date"]].copy()
    d["order_month"] = d["order_date"].dt.to_period("M")
    d["cohort"] = d.groupby("customer_id")["order_date"].transform("min").dt.to_period("M")
    d["period"] = (d["order_month"] - d["cohort"]).apply(lambda x: x.n)
    counts = d.groupby(["cohort", "period"])["customer_id"].nunique().unstack(fill_value=0)
    retention = counts.divide(counts[0], axis=0)
    return counts, retention


def annual_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    d = df[["customer_id", "order_date"]].copy()
    d["year"] = d["order_date"].dt.year
    d["cohort_year"] = d.groupby("customer_id")["year"].transform("min")
    d["years_since"] = d["year"] - d["cohort_year"]
    counts = d.groupby(["cohort_year", "years_since"])["customer_id"].nunique().unstack(fill_value=0)
    retention = counts.divide(counts[0], axis=0)
    return counts, retention


def to_long(counts, retention, cohort_name):
    long = (retention.stack().rename("retention").reset_index())
    long["customers"] = counts.stack().values
    long["cohort_size"] = long[cohort_name].map(counts[0])
    long.columns = [cohort_name, "period", "retention", "customers", "cohort_size"]
    long[cohort_name] = long[cohort_name].astype(str)
    return long


def main():
    df = pd.read_csv(PROC / "orders_clean.csv", parse_dates=["order_date"])

    cust = customer_summary(df)
    cust.to_csv(PROC / "customer_summary.csv", index=False)
    repeat_gaps(df).to_csv(PROC / "repeat_gap_days.csv", index=False)

    print("Customers:", len(cust))
    print(cust.groupby("customer_type").agg(
        customers=("customer_id", "count"),
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        avg_first_order_discount=("first_order_discount", "mean"),
    ).round(2).to_string())

    mc, mr = monthly_cohorts(df)
    to_long(mc, mr, "cohort").to_csv(PROC / "cohort_retention_monthly.csv", index=False)
    ac, ar = annual_cohorts(df)
    to_long(ac, ar, "cohort_year").to_csv(PROC / "cohort_retention_annual.csv", index=False)

    # Monthly heatmap (first 12 periods keeps it readable)
    show = mr.iloc[:, :13]
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(show, annot=True, fmt=".0%", cmap="Blues", vmin=0, vmax=1,
                cbar_kws={"label": "Retention"}, ax=ax, annot_kws={"size": 6})
    ax.set_title("Monthly cohort retention (customers active in month N after first order)")
    ax.set_xlabel("Months since first order")
    ax.set_ylabel("Cohort (first order month)")
    fig.tight_layout()
    fig.savefig(FIG / "06_cohort_retention_monthly.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(ar, annot=True, fmt=".0%", cmap="Blues", vmin=0, vmax=1, ax=ax)
    ax.set_title("Annual cohort retention (share active N years after acquisition year)")
    ax.set_xlabel("Years since acquisition year")
    ax.set_ylabel("Acquisition year")
    fig.tight_layout()
    fig.savefig(FIG / "07_cohort_retention_annual.png", dpi=130)
    plt.close(fig)

    print("\nAnnual cohort retention:")
    print(ar.round(3).to_string())
    print("\nNext: python python/04_profit_drivers.py")


if __name__ == "__main__":
    main()
