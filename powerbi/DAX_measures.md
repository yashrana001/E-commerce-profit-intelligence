# DAX: date table, calculated tables and measures

Load these files from `data/processed/` (Get Data → Text/CSV):

| Power BI table name | File |
|---|---|
| `Fact_Orders` | `orders_clean.csv` |
| `Dim_Customer` | `dim_customer.csv` |
| `Cohort_Monthly` | `cohort_retention_monthly.csv` |
| `Cohort_Annual` | `cohort_retention_annual.csv` |
| `Bridge` | `profit_bridge_subcategory.csv` |

Set data types: `order_date`, `ship_date`, `order_month` (Fact_Orders) and `first_order`, `last_order` (Dim_Customer) = **Date**. `discount`, `margin`, `retention` = **Decimal**. `returned`, `loss_making` = **True/False**.

---

## 1. Date table (Modeling → New table)

```dax
Dim_Date =
ADDCOLUMNS (
    CALENDAR (
        DATE ( YEAR ( MIN ( Fact_Orders[order_date] ) ), 1, 1 ),
        DATE ( YEAR ( MAX ( Fact_Orders[order_date] ) ), 12, 31 )
    ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Month Num", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year-Month", FORMAT ( [Date], "YYYY-MM" )
)
```
Then: Table tools → **Mark as date table** → `Date`. Sort `Month` by `Month Num`.

## 2. Helper tables for the profit-bridge waterfall

```dax
Bridge Steps =
DATATABLE (
    "Step", STRING,
    "Step Order", INTEGER,
    {
        { "Prior-year profit", 1 },
        { "Growth effect", 2 },
        { "Margin effect", 3 },
        { "Current-year profit", 4 }
    }
)
```
Sort `Step` by `Step Order`.

---

## 3. Core KPI measures

```dax
Total Sales   = SUM ( Fact_Orders[sales] )
Total Profit  = SUM ( Fact_Orders[profit] )
Margin %      = DIVIDE ( [Total Profit], [Total Sales] )
Orders        = DISTINCTCOUNT ( Fact_Orders[order_id] )
Customers     = DISTINCTCOUNT ( Fact_Orders[customer_id] )
Avg Discount  = AVERAGE ( Fact_Orders[discount] )
Avg Order Value = DIVIDE ( [Total Sales], [Orders] )
```

## 4. Time intelligence (the "revenue vs profit" story)

```dax
Sales PY   = CALCULATE ( [Total Sales],  SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
Profit PY  = CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
Margin PY  = DIVIDE ( [Profit PY], [Sales PY] )

Sales YoY %  = DIVIDE ( [Total Sales]  - [Sales PY],  [Sales PY] )
Profit YoY % = DIVIDE ( [Total Profit] - [Profit PY], ABS ( [Profit PY] ) )
Margin Change (pts) = ( [Margin %] - [Margin PY] ) * 100

-- Positive = revenue is outgrowing profit. This is THE headline KPI of the project.
Growth Gap (pts) = ( [Sales YoY %] - [Profit YoY %] ) * 100

Sales YTD  = TOTALYTD ( [Total Sales],  Dim_Date[Date] )
Profit YTD = TOTALYTD ( [Total Profit], Dim_Date[Date] )
```

## 5. Discount and loss measures

```dax
Loss-making Sales   = CALCULATE ( [Total Sales],  Fact_Orders[profit] < 0 )
Profit Lost on Loss Lines = CALCULATE ( [Total Profit], Fact_Orders[profit] < 0 )
Loss Lines %        = DIVIDE ( CALCULATE ( COUNTROWS ( Fact_Orders ), Fact_Orders[profit] < 0 ), COUNTROWS ( Fact_Orders ) )

High-discount Sales = CALCULATE ( [Total Sales], Fact_Orders[discount] > 0.2 )
High-discount Share % = DIVIDE ( [High-discount Sales], [Total Sales] )
High-discount Margin % =
DIVIDE (
    CALCULATE ( [Total Profit], Fact_Orders[discount] > 0.2 ),
    [High-discount Sales]
)
```

## 6. Returns

```dax
Returned Orders = CALCULATE ( DISTINCTCOUNT ( Fact_Orders[order_id] ), Fact_Orders[returned] = TRUE () )
Return Rate     = DIVIDE ( [Returned Orders], [Orders] )
Returned Revenue = CALCULATE ( [Total Sales], Fact_Orders[returned] = TRUE () )
Returned Revenue % = DIVIDE ( [Returned Revenue], [Total Sales] )
```

## 7. Customer measures

```dax
Customer Count = DISTINCTCOUNT ( Dim_Customer[customer_id] )
Repeat Customers =
CALCULATE ( [Customer Count], Dim_Customer[customer_type] = "Repeat" )
Repeat Rate % = DIVIDE ( [Repeat Customers], [Customer Count] )

Avg CLV (profit) = AVERAGE ( Dim_Customer[profit] )
Avg CLV (revenue) = AVERAGE ( Dim_Customer[revenue] )

Profit per Customer = DIVIDE ( SUM ( Dim_Customer[profit] ), [Customer Count] )
Profit Share % =
DIVIDE ( SUM ( Dim_Customer[profit] ), CALCULATE ( SUM ( Dim_Customer[profit] ), ALL ( Dim_Customer ) ) )

-- Needs the INACTIVE relationship Dim_Date[Date] -> Dim_Customer[first_order] (see data_model.md)
New Customers =
CALCULATE ( COUNTROWS ( Dim_Customer ), USERELATIONSHIP ( Dim_Date[Date], Dim_Customer[first_order] ) )

Avg First-order Discount = AVERAGE ( Dim_Customer[first_order_discount] )
```

## 8. Cohort measure

```dax
Retention % = AVERAGE ( Cohort_Annual[retention] )     -- for the annual matrix
Retention % (Monthly) = AVERAGE ( Cohort_Monthly[retention] )
```

## 9. Profit bridge

```dax
Bridge Value =
SWITCH (
    SELECTEDVALUE ( 'Bridge Steps'[Step] ),
    "Prior-year profit",   SUM ( Bridge[profit_prev] ),
    "Growth effect",       SUM ( Bridge[growth_effect] ),
    "Margin effect",       SUM ( Bridge[margin_effect] ),
    "Current-year profit", SUM ( Bridge[profit_cur] )
)
```
Use a **single-select slicer on `Bridge[year_to]`** so one year transition shows at a time.

## 10. Dynamic titles (nice touch for drill-downs)

```dax
Title - Profit Trend =
"Revenue vs profit, "
    & IF ( ISFILTERED ( Fact_Orders[region] ), SELECTEDVALUE ( Fact_Orders[region], "multiple regions" ), "all regions" )

Insight - Growth Gap =
VAR gap = [Growth Gap (pts)]
RETURN
    IF (
        ISBLANK ( gap ), "Select a year to compare",
        IF ( gap > 0,
            "Revenue grew " & FORMAT ( gap, "0.0" ) & " pts faster than profit",
            "Profit grew " & FORMAT ( -gap, "0.0" ) & " pts faster than revenue" )
    )
```
