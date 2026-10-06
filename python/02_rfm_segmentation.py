
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import FIG, PROC

SEGMENT_ORDER = ["Champions", "Loyal", "New", "Needs Attention", "At Risk", "Lost"]


def score(series: pd.Series, labels, ascending_rank=True) -> pd.Series:
    """Quintile score using rank(method='first') so ties never break qcut."""
    ranked = series.rank(method="first", ascending=ascending_rank)
    return pd.qcut(ranked, 5, labels=labels).astype(int)


def segment(row) -> str:
    r, f = row["R"], row["F"]
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "New"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2:
        return "Lost"
    return "Needs Attention"


def main():
    df = pd.read_csv(PROC / "orders_clean.csv", parse_dates=["order_date"])
    snapshot = df["order_date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_id").agg(
        recency=("order_date", lambda x: (snapshot - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("sales", "sum"),
        profit=("profit", "sum"),
        avg_discount=("discount", "mean"),
    )

    # Recency: lower days = better, so rank descending to give the best score 5
    rfm["R"] = score(rfm["recency"], [5, 4, 3, 2, 1])
    rfm["F"] = score(rfm["frequency"], [1, 2, 3, 4, 5])
    rfm["M"] = score(rfm["monetary"], [1, 2, 3, 4, 5])
    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    rfm["segment"] = rfm.apply(segment, axis=1)
    rfm = rfm.reset_index()
    rfm.to_csv(PROC / "rfm_segments.csv", index=False)

    summary = rfm.groupby("segment").agg(
        customers=("customer_id", "count"),
        revenue=("monetary", "sum"),
        profit=("profit", "sum"),
        avg_orders=("frequency", "mean"),
        avg_recency_days=("recency", "mean"),
        avg_discount=("avg_discount", "mean"),
    )
    summary["margin_pct"] = 100 * summary["profit"] / summary["revenue"]
    summary["customer_share_pct"] = 100 * summary["customers"] / summary["customers"].sum()
    summary["revenue_share_pct"] = 100 * summary["revenue"] / summary["revenue"].sum()
    summary["profit_share_pct"] = 100 * summary["profit"] / summary["profit"].sum()
    summary["profit_per_customer"] = summary["profit"] / summary["customers"]
    summary = summary.reindex([s for s in SEGMENT_ORDER if s in summary.index]).reset_index()
    summary.to_csv(PROC / "rfm_segment_summary.csv", index=False)

    print(summary.round(2).to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = range(len(summary))
    w = 0.38
    ax.bar([i - w / 2 for i in x], summary["revenue_share_pct"], w, label="Revenue share %", color="#1f77b4")
    ax.bar([i + w / 2 for i in x], summary["profit_share_pct"], w, label="Profit share %", color="#2ca02c")
    ax.set_xticks(list(x))
    ax.set_xticklabels(summary["segment"], rotation=20)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("RFM segments: share of revenue vs share of profit")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "05_rfm_segment_profit.png", dpi=130)
    plt.close(fig)
    print("\nNext: python python/03_cohort_retention.py")


if __name__ == "__main__":
    main()
