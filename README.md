# E-Commerce Profit & Customer Intelligence

**Business question:** *Revenue is increasing, but why isn't profit increasing at the same rate?*

An end-to-end analysis on the Superstore dataset using **SQL (PostgreSQL)**, **Python (pandas)** and **Power BI**.
It tests five hypotheses about where margin is leaking and ends with quantified recommendations.

> 📌 **Headline result:** Revenue grew 57% from 2011 to 2014 but profit grew only 47%. Sales discounted above 20% are just 14.7% of revenue, yet they lose $54,254, about half of total profit.
> Full write-up: [`insights/why_profit_lags_revenue.md`](insights/why_profit_lags_revenue.md)

## Dashboard preview
*(add screenshots after building the report in Power BI)*

| Executive KPIs | Product profitability |
|---|---|
| ![p1](images/dashboard_page1.png) | ![p2](images/dashboard_page2.png) |
| **Customer intelligence** | **Regions & returns** |
| ![p3](images/dashboard_page3.png) | ![p4](images/dashboard_page4.png) |

## Hypotheses tested

| # | Hypothesis | Where it's tested |
|---|---|---|
| 1 | **Discount erosion:** higher discounts push line items into negative profit | `sql/02`, `python/01`, `python/04` |
| 2 | **Mix shift:** growth comes from low-margin categories/sub-categories | `sql/03`, `python/04` (profit bridge) |
| 3 | **Returns:** some products/regions have return rates that eat margin | `sql/05` |
| 4 | **Regional drag:** some regions/states grow revenue but lose money | `sql/05` |
| 5 | **Customer quality:** new customers come in at deep discounts and don't repeat; a small repeat segment drives most profit | `sql/04`, `python/02`, `python/03` |

## What's in the analysis

- **Revenue & profit trends**: monthly/yearly growth, rolling margin, growth gap
- **Profit bridge**: splits each year's profit change into a *growth effect* and a *margin effect* by sub-category
- **Product/category profitability**: ranking, Pareto, products that sell well but lose money
- **Discount vs profit**: band analysis, break-even discount, high-discount revenue share over time
- **Customer lifetime value**, **RFM segmentation** (profit per segment, not just revenue), **repeat purchase gaps**
- **Returns** by category/region/discount band; **regional performance** and loss-making states
- **Cohort retention**: monthly and annual

## Tech used

| Layer | Skills shown |
|---|---|
| **SQL** | CTEs, multi-table joins, window functions (`RANK`, `NTILE`, `LAG`, `FIRST_VALUE`, running totals, rolling frames), conditional aggregation (`FILTER`), customer-level aggregation, cohort index maths |
| **Python** | pandas cleaning, EDA, feature engineering, RFM, cohort analysis, profit-bridge decomposition, matplotlib/seaborn |
| **Power BI** | Star-ish data model, DAX time intelligence, KPI dashboard, drill-through, waterfall, cohort matrix, dynamic titles |

## Repo structure

```
├── data/
│   ├── raw/                  # put Superstore file here (not committed)
│   └── processed/            # generated CSVs (loaded by SQL and Power BI)
├── sql/                      # PostgreSQL scripts 00–05
├── python/                   # pipeline scripts 01–05 + run_all.py
├── notebooks/                # walkthrough notebook
├── powerbi/                  # DAX, data model, build guide, theme
├── insights/                 # auto-generated findings + final write-up
├── images/                   # charts and dashboard screenshots
├── tests/                    # synthetic data generator for smoke tests
└── requirements.txt
```

## How to run

**1. Get the data.** See [`data/README.md`](data/README.md) and place the file in `data/raw/`.

**2. Python pipeline**
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python python/run_all.py
```
**key findings 
This writes cleaned data and aggregates to `data/processed/`, charts to `images/`, and the numbers for your
1. **Discounts are the biggest leak.** Margin is 30.0% with no discount, -16.5% at 21-40% discount and -88.1% at 40%+. Lines above 20% discount lose $54,254.
2. **Growth came from lower-margin products.** In 2014 revenue rose $19,409 but profit fell $15,714. Tables, Bookcases and Supplies lose money overall.
3. **A few states and customers matter most.** 9 of 47 states lose $40,488 in total (Texas, Illinois and Pennsylvania worst), and the top 10% of customers generate 71.7% of profit.

**3. SQL (PostgreSQL 13+)**
```bash
createdb superstore
psql -d superstore -f sql/00_schema_and_load.sql      # run from repo root
psql -d superstore -f sql/01_revenue_profit_trends.sql
# ... 02 to 05
```
`00` loads `orders_for_sql.csv` and `returns_for_sql.csv` (created by Python step 1), so run Python first.

**4. Power BI.** Follow [`powerbi/dashboard_build_guide.md`](powerbi/dashboard_build_guide.md) and paste measures from
[`powerbi/DAX_measures.md`](powerbi/DAX_measures.md).

**5. Write-up.** Fill [`insights/why_profit_lags_revenue.md`](insights/why_profit_lags_revenue.md) using the auto-generated numbers.

## Smoke test without the real dataset
```bash
python tests/generate_synthetic_data.py     # writes data/raw/synthetic_superstore.xlsx (fake data)
python python/run_all.py
```
Delete the synthetic file before using the real one. The synthetic data exists only to verify the code runs.

## Key findings
*(fill in from `insights/key_findings_auto.md`)*

1. ...
2. ...
3. ...

## Recommendations
1. Cap discounts at 20% and require approval above that.
2. Reprice or drop Tables, Bookcases and Supplies, and review Machines pricing.
3. Fix pricing in Texas, Illinois, Pennsylvania, North Carolina and Tennessee.
4. Win back "At Risk" customers (24.1% of revenue but 30.4% of profit) and protect the top 10% of customers.

## Limitations
- Superstore is a sample dataset with no cost breakdown, so "profit" is taken as recorded.
- Four years of data gives sparse monthly cohorts; the annual cohort view is easier to read.
- RFM thresholds are quintile-based and the segment rules are a judgement call.

## License
MIT
