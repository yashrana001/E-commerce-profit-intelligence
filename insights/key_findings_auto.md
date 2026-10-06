# Key findings (auto-generated)

Every number below was computed by `python/04_profit_drivers.py` from your data.
Use them to fill in `insights/why_profit_lags_revenue.md`.

## 1. Revenue vs profit by year

| Year | Revenue | Profit | Margin | Revenue growth | Profit growth |
|---|---|---|---|---|---|
| 2011 | $179,068 | $19,020 | 10.6% |  |  |
| 2012 | $163,954 | $19,708 | 12.0% | -8.4% | 3.6% |
| 2013 | $261,514 | $43,667 | 16.7% | 59.5% | 121.6% |
| 2014 | $280,924 | $27,953 | 10.0% | 7.4% | -36.0% |

## 2. Profit bridge (growth effect vs margin effect)

| Period | Δ Revenue | Δ Profit | Growth effect | Margin effect |
|---|---|---|---|---|
| 2011→2012 | -$15,114 | $688 | -$2,379 | $3,067 |
| 2012→2013 | $97,560 | $23,959 | $15,383 | $8,576 |
| 2013→2014 | $19,409 | -$15,714 | -$1,139 | -$14,575 |

Biggest margin erosion in the latest year (2014), by sub-category:

- **Machines**: margin effect -$6,775 on revenue change of $2,033
- **Tables**: margin effect -$3,802 on revenue change of $5,022
- **Bookcases**: margin effect -$1,386 on revenue change of -$2,940
- **Phones**: margin effect -$919 on revenue change of -$2,627
- **Chairs**: margin effect -$897 on revenue change of $4,022

## 3. Discount erosion

- Loss-making line items: **18.6%** of all lines, destroying **$61,764** of profit.
- Overall margin: **12.5%**. Excluding loss-making lines it would be **24.3%**.

| Discount band | Lines | Revenue | Profit | Margin |
|---|---|---|---|---|
| 0% | 1,874 | $418,534 | $125,677 | 30.0% |
| 1-20% | 1,557 | $336,836 | $38,924 | 11.6% |
| 21-40% | 172 | $84,330 | -$13,951 | -16.5% |
| 40%+ | 371 | $45,760 | -$40,303 | -88.1% |

- Lines discounted above 20% are **14.7%** of revenue but contribute **-$54,254** of profit (margin -41.7%).

Share of revenue sold at >20% discount, by year: 2011: 18.6%, 2012: 12.5%, 2013: 11.0%, 2014: 16.9%

## 4. Product mix

Bottom 5 sub-categories by total profit:

- **Tables** (Furniture): profit -$6,253, margin -7.0%, avg discount 25.2%
- **Bookcases** (Furniture): profit -$1,215, margin -2.9%, avg discount 21.5%
- **Supplies** (Office Supplies): profit -$959, margin -7.5%, avg discount 10.2%
- **Fasteners** (Office Supplies): profit $298, margin 25.0%, avg discount 8.9%
- **Envelopes** (Office Supplies): profit $2,267, margin 41.4%, avg discount 8.3%

Top 5 sub-categories by total profit:

- **Copiers** (Technology): profit $23,795, margin 38.9%
- **Accessories** (Technology): profit $17,529, margin 25.8%
- **Phones** (Technology): profit $16,572, margin 12.9%
- **Paper** (Office Supplies): profit $12,892, margin 43.6%
- **Chairs** (Furniture): profit $11,694, margin 9.7%

Category share of revenue by year (mix shift check):

| Year | Furniture | Office Supplies | Technology |
|---|---|---|---|
| 2011 | 35.7% | 29.9% | 34.4% |
| 2012 | 36.9% | 27.5% | 35.6% |
| 2013 | 29.4% | 26.0% | 44.6% |
| 2014 | 30.4% | 32.7% | 37.0% |

## 5. Returns

No Returns sheet found in the raw file, so returns analysis was skipped.

## 6. Regional drag

- **9** of 47 states are loss-making, losing **$40,488** in total.

Five worst states:

- **Texas** (Central): revenue $77,075, profit -$12,948, avg discount 36.8%
- **Illinois** (Central): revenue $25,906, profit -$9,089, avg discount 38.9%
- **Pennsylvania** (East): revenue $39,214, profit -$5,797, avg discount 32.2%
- **North Carolina** (South): revenue $30,622, profit -$4,512, avg discount 29.5%
- **Tennessee** (South): revenue $7,616, profit -$2,517, avg discount 31.0%

## 7. Customer quality

- **One-time** customers: 160 (21.9%), profit $9,947 (9.0% of total), avg first-order discount 15.6%
- **Repeat** customers: 569 (78.1%), profit $100,401 (91.0% of total), avg first-order discount 15.4%
- Top 10% of customers by profit generate **71.7%** of total profit.
- Bottom 10% of customers by profit (decile 10) total **-$33,394**.

RFM segments:

| Segment | Customers | Revenue share | Profit share | Margin |
|---|---|---|---|---|
| Champions | 176 | 37.9% | 36.1% | 11.9% |
| Loyal | 140 | 17.5% | 13.3% | 9.5% |
| New | 61 | 4.1% | 4.4% | 13.2% |
| Needs Attention | 60 | 5.4% | 5.9% | 13.6% |
| At Risk | 121 | 24.1% | 30.4% | 15.8% |
| Lost | 171 | 11.0% | 9.9% | 11.2% |
