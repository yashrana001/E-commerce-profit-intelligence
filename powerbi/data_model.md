# Data model

```
Dim_Date ──(1:*, active)──────────► Fact_Orders[order_date]
Dim_Date ──(1:*, INACTIVE)────────► Dim_Customer[first_order]     (used by [New Customers])
Dim_Customer ──(1:*)──────────────► Fact_Orders[customer_id]
```
`Cohort_Monthly`, `Cohort_Annual` and `Bridge` are standalone (no relationships). They are already
aggregated, so they use their own slicers.

## Relationships to create (Model view)

| From (one side) | To (many side) | Cardinality | Cross-filter | Active |
|---|---|---|---|---|
| `Dim_Date[Date]` | `Fact_Orders[order_date]` | One to many | Single | Yes |
| `Dim_Customer[customer_id]` | `Fact_Orders[customer_id]` | One to many | Single | Yes |
| `Dim_Date[Date]` | `Dim_Customer[first_order]` | One to many | Single | **No** (inactive) |

## Power Query tips
- Use **Get Data → Text/CSV** with the default delimiter, then **Transform** only to fix types.
- Don't pivot or merge in Power Query. The Python step already did the shaping.
- Hide `Row ID`, `Postal Code`, `ship_days` and the helper columns in Report view.

## Column notes

| Column | Meaning |
|---|---|
| `Fact_Orders[discount_band]` | `0%`, `1-20%`, `21-40%`, `40%+` (same cut-offs as Python and SQL). Sort by creating a sort column or use *Sort by column*. |
| `Fact_Orders[margin]` | Line-level profit / sales |
| `Fact_Orders[loss_making]` | `profit < 0` |
| `Fact_Orders[returned]` | Order appears in the Returns sheet |
| `Dim_Customer[customer_type]` | `Repeat` (more than 1 order) or `One-time` |
| `Dim_Customer[rfm_segment]` | Champions, Loyal, New, Needs Attention, At Risk, Lost |
| `Dim_Customer[profit_decile]` | 1 = most profitable 10% of customers |
| `Bridge[growth_effect]` | Extra revenue earned at last year's margin |
| `Bridge[margin_effect]` | Change in profit caused by margin moving |
