# Data

## Dataset: Superstore (Orders, Returns, People)

The raw file is **not** committed to this repo. Download it yourself and drop it in `data/raw/`.

**Where to get it**
- Tableau's "Sample - Superstore" workbook (`.xls`/`.xlsx` with 3 sheets: Orders, Returns, People), or
- The Kaggle "Superstore Dataset" (usually a single CSV, Orders only).

**What the pipeline expects**

| File type | Behaviour |
|---|---|
| `.xlsx` / `.xls` with sheets `Orders`, `Returns`, `People` | Full pipeline, including the returns analysis |
| `.csv` (Orders only) | Works, but the returns analysis is skipped (no Returns sheet) |

The loader picks the first `.xlsx`, `.xls` or `.csv` it finds in `data/raw/`.

**Orders columns used:** Row ID, Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Customer Name, Segment, Country, City, State, Postal Code, Region, Product ID, Category, Sub-Category, Product Name, Sales, Quantity, Discount, Profit.

**Returns columns used:** Returned, Order ID.

`data/processed/` is created by the Python scripts. It holds the cleaned tables and the CSVs that Power BI and PostgreSQL load.
