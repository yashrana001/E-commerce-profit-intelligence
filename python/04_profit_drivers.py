
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import FIG, INSIGHTS, PROC


def bridge(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby(["order_year", "category", "sub_category"])
           .agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index())
    g["margin"] = g["profit"] / g["sales"]
    years = sorted(g["order_year"].unique())
    rows = []
    for prev, cur in zip(years[:-1], years[1:]):
        a = g[g["order_year"] == prev].set_index(["category", "sub_category"])
        b = g[g["order_year"] == cur].set_index(["category", "sub_category"])
        j = a.join(b, how="outer", lsuffix="_prev", rsuffix="_cur").fillna(0)
        # If a sub-category had no sales in the prior year, treat its prior margin as the current one
        prior_margin = j["margin_prev"].where(j["sales_prev"] != 0, j["margin_cur"])
        j["growth_effect"] = (j["sales_cur"] - j["sales_prev"]) * prior_margin
        j["margin_effect"] = j["profit_cur"] - j["profit_prev"] - j["growth_effect"]
        j["delta_profit"] = j["profit_cur"] - j["profit_prev"]
        j["delta_sales"] = j["sales_cur"] - j["sales_prev"]
        j["year_from"], j["year_to"] = prev, cur
        rows.append(j.reset_index())
    out = pd.concat(rows, ignore_index=True)
    return out[["year_from", "year_to", "category", "sub_category", "sales_prev", "sales_cur",
                "profit_prev", "profit_cur", "delta_sales", "delta_profit",
                "growth_effect", "margin_effect"]]


def pct(x, d=1):
    return f"{x:.{d}f}%"


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def main():
    df = pd.read_csv(PROC / "orders_clean.csv", parse_dates=["order_date"])
    br = bridge(df)
    br.to_csv(PROC / "profit_bridge_subcategory.csv", index=False)

    tot = br.groupby(["year_from", "year_to"]).agg(
        delta_sales=("delta_sales", "sum"),
        delta_profit=("delta_profit", "sum"),
        growth_effect=("growth_effect", "sum"),
        margin_effect=("margin_effect", "sum"),
    ).reset_index()
    tot.to_csv(PROC / "profit_bridge_total.csv", index=False)

    # ---- Chart: stacked growth vs margin effect per year transition
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = [f"{a}→{b}" for a, b in zip(tot["year_from"], tot["year_to"])]
    x = range(len(labels))
    w = 0.38
    ax.bar([i - w / 2 for i in x], tot["growth_effect"], w,
           label="Growth effect (extra revenue at old margin)", color="#2ca02c")
    ax.bar([i + w / 2 for i in x], tot["margin_effect"], w,
           label="Margin effect (change in margin)", color="#d62728")
    ax.plot(list(x), tot["delta_profit"], "ko-", label="Net change in profit")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("Profit bridge: why profit moves differently from revenue")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "08_profit_bridge.png", dpi=130)
    plt.close(fig)

    # ---- Key findings (all numbers computed from the data)
    L = ["# Key findings (auto-generated)", "",
         "Every number below was computed by `python/04_profit_drivers.py` from your data.",
         "Use them to fill in `insights/why_profit_lags_revenue.md`.", ""]

    yearly = pd.read_csv(PROC / "yearly_kpis.csv")
    L += ["## 1. Revenue vs profit by year", "",
          "| Year | Revenue | Profit | Margin | Revenue growth | Profit growth |", "|---|---|---|---|---|---|"]
    for _, r in yearly.iterrows():
        rg = "" if pd.isna(r["rev_growth_pct"]) else pct(r["rev_growth_pct"])
        pg = "" if pd.isna(r["profit_growth_pct"]) else pct(r["profit_growth_pct"])
        L.append(f"| {int(r['order_year'])} | {money(r['revenue'])} | {money(r['profit'])} | "
                 f"{pct(r['margin_pct'])} | {rg} | {pg} |")
    L.append("")

    L += ["## 2. Profit bridge (growth effect vs margin effect)", "",
          "| Period | Δ Revenue | Δ Profit | Growth effect | Margin effect |", "|---|---|---|---|---|"]
    for _, r in tot.iterrows():
        L.append(f"| {int(r['year_from'])}→{int(r['year_to'])} | {money(r['delta_sales'])} | "
                 f"{money(r['delta_profit'])} | {money(r['growth_effect'])} | {money(r['margin_effect'])} |")
    L.append("")
    last = br[br["year_to"] == br["year_to"].max()]
    worst = last.nsmallest(5, "margin_effect")[["sub_category", "margin_effect", "delta_sales"]]
    L += [f"Biggest margin erosion in the latest year ({int(br['year_to'].max())}), by sub-category:", ""]
    for _, r in worst.iterrows():
        L.append(f"- **{r['sub_category']}**: margin effect {money(r['margin_effect'])} "
                 f"on revenue change of {money(r['delta_sales'])}")
    L.append("")

    # Discount erosion
    total_sales, total_profit = df["sales"].sum(), df["profit"].sum()
    loss = df[df["loss_making"]]
    L += ["## 3. Discount erosion", "",
          f"- Loss-making line items: **{pct(100 * len(loss) / len(df))}** of all lines, "
          f"destroying **{money(-loss['profit'].sum())}** of profit.",
          f"- Overall margin: **{pct(100 * total_profit / total_sales)}**. "
          f"Excluding loss-making lines it would be **{pct(100 * (total_profit - loss['profit'].sum()) / (total_sales - loss['sales'].sum()))}**.", ""]
    bands = pd.read_csv(PROC / "discount_band_profit.csv")
    L += ["| Discount band | Lines | Revenue | Profit | Margin |", "|---|---|---|---|---|"]
    for _, r in bands.iterrows():
        L.append(f"| {r['discount_band']} | {int(r['lines']):,} | {money(r['revenue'])} | "
                 f"{money(r['profit'])} | {pct(r['margin_pct'])} |")
    hi = df[df["discount"] > 0.20]
    L += ["", f"- Lines discounted above 20% are **{pct(100 * hi['sales'].sum() / total_sales)}** of revenue "
              f"but contribute **{money(hi['profit'].sum())}** of profit "
              f"(margin {pct(100 * hi['profit'].sum() / hi['sales'].sum())}).", ""]
    hi_sales = df.loc[df["discount"] > 0.20].groupby("order_year")["sales"].sum()
    share_by_year = (100 * hi_sales / df.groupby("order_year")["sales"].sum()).fillna(0)
    L.append("Share of revenue sold at >20% discount, by year: " +
             ", ".join(f"{int(y)}: {pct(v)}" for y, v in share_by_year.items()))
    L.append("")

    # Mix shift
    sub = pd.read_csv(PROC / "subcategory_profit.csv").sort_values("profit")
    L += ["## 4. Product mix", "", "Bottom 5 sub-categories by total profit:", ""]
    for _, r in sub.head(5).iterrows():
        L.append(f"- **{r['sub_category']}** ({r['category']}): profit {money(r['profit'])}, "
                 f"margin {pct(r['margin_pct'])}, avg discount {pct(100 * r['avg_discount'])}")
    L += ["", "Top 5 sub-categories by total profit:", ""]
    for _, r in sub.tail(5).iloc[::-1].iterrows():
        L.append(f"- **{r['sub_category']}** ({r['category']}): profit {money(r['profit'])}, "
                 f"margin {pct(r['margin_pct'])}")
    cat_share = (df.groupby(["order_year", "category"])["sales"].sum()
                   .groupby(level=0).transform(lambda s: 100 * s / s.sum()).unstack())
    L += ["", "Category share of revenue by year (mix shift check):", "",
          "| Year | " + " | ".join(cat_share.columns) + " |",
          "|---|" + "---|" * len(cat_share.columns)]
    for y, r in cat_share.iterrows():
        L.append(f"| {int(y)} | " + " | ".join(pct(v) for v in r) + " |")
    L.append("")

    # Returns
    L += ["## 5. Returns", ""]
    if df["returned"].any():
        order_lvl = df.groupby(["order_id", "category"]).agg(
            returned=("returned", "max"), sales=("sales", "sum")).reset_index()
        rr = order_lvl.groupby("category").agg(
            orders=("order_id", "nunique"), returned=("returned", "sum"),
            returned_revenue=("sales", lambda s: s[order_lvl.loc[s.index, "returned"]].sum()))
        rr["return_rate_pct"] = 100 * rr["returned"] / rr["orders"]
        overall = 100 * df.drop_duplicates("order_id")["returned"].mean()
        L.append(f"- Overall order return rate: **{pct(overall)}**.")
        for cat, r in rr.sort_values("return_rate_pct", ascending=False).iterrows():
            L.append(f"- {cat}: {pct(r['return_rate_pct'])} of orders returned, "
                     f"{money(r['returned_revenue'])} of revenue returned")
    else:
        L.append("No Returns sheet found in the raw file, so returns analysis was skipped.")
    L.append("")

    # Regions
    state = pd.read_csv(PROC / "state_profit.csv")
    neg = state[state["profit"] < 0]
    L += ["## 6. Regional drag", "",
          f"- **{len(neg)}** of {len(state)} states are loss-making, losing **{money(abs(neg['profit'].sum()))}** in total.",
          "", "Five worst states:", ""]
    for _, r in state.head(5).iterrows():
        L.append(f"- **{r['state']}** ({r['region']}): revenue {money(r['revenue'])}, profit "
                 f"{money(r['profit'])}, avg discount {pct(100 * r['avg_discount'])}")
    L.append("")

    # Customers
    cust = pd.read_csv(PROC / "customer_summary.csv")
    seg = pd.read_csv(PROC / "rfm_segment_summary.csv")
    rep = cust.groupby("customer_type").agg(
        customers=("customer_id", "count"), profit=("profit", "sum"),
        revenue=("revenue", "sum"), first_disc=("first_order_discount", "mean"))
    top10 = cust[cust["profit_decile"] == 1]["profit"].sum()
    L += ["## 7. Customer quality", ""]
    for t, r in rep.iterrows():
        L.append(f"- **{t}** customers: {int(r['customers'])} ({pct(100 * r['customers'] / len(cust))}), "
                 f"profit {money(r['profit'])} ({pct(100 * r['profit'] / cust['profit'].sum())} of total), "
                 f"avg first-order discount {pct(100 * r['first_disc'])}")
    L += [f"- Top 10% of customers by profit generate **{pct(100 * top10 / cust['profit'].sum())}** of total profit.",
          f"- Bottom 10% of customers by profit (decile 10) total **{money(cust[cust['profit_decile'] == 10]['profit'].sum())}**.",
          "", "RFM segments:", "",
          "| Segment | Customers | Revenue share | Profit share | Margin |", "|---|---|---|---|---|"]
    for _, r in seg.iterrows():
        L.append(f"| {r['segment']} | {int(r['customers'])} | {pct(r['revenue_share_pct'])} | "
                 f"{pct(r['profit_share_pct'])} | {pct(r['margin_pct'])} |")
    L.append("")

    (INSIGHTS / "key_findings_auto.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {INSIGHTS / 'key_findings_auto.md'}")


if __name__ == "__main__":
    main()
