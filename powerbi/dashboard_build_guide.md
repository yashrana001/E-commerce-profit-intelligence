# Power BI build guide (4 pages)

A `.pbix` file can't be generated from code, so this is a click-by-click spec. Budget about 3 to 4 hours.
Import the theme first: **View → Themes → Browse for themes → `powerbi/theme.json`**.

Global rules: 16:9 canvas, one question per page, a dynamic title on every page, slicers synced across pages
(**View → Sync slicers**) for Year, Region and Category.

---

## Page 1: Executive KPIs ("Why isn't profit growing with revenue?")

**Slicers:** Year (tile), Region (dropdown), Category (tile)

| Visual | Fields |
|---|---|
| 6 KPI cards | `[Total Sales]`, `[Total Profit]`, `[Margin %]`, `[Sales YoY %]`, `[Profit YoY %]`, `[Growth Gap (pts)]` |
| Second card row | `[Return Rate]`, `[Avg Discount]`, `[Loss Lines %]` |
| Line + clustered column | X: `Dim_Date[Year-Month]`. Columns: `[Total Sales]`. Line (secondary axis): `[Margin %]` |
| **Profit bridge waterfall** | Category: `'Bridge Steps'[Step]`. Y: `[Bridge Value]`. Slicer on `Bridge[year_to]` (single select). Format → Waterfall → mark *Current-year profit* as total |
| Smart narrative or card | `[Insight - Growth Gap]` |

Callout: put `[Growth Gap (pts)]` first and large. It is the answer to the business question.

## Page 2: Product profitability

**Slicers:** Year, Category, Discount band

| Visual | Fields |
|---|---|
| Matrix | Rows: `category` → `sub_category`. Values: `[Total Sales]`, `[Total Profit]`, `[Margin %]`, `[Avg Discount]`. Conditional-format `[Margin %]` (red below 0, green above) |
| Scatter | X: `[Avg Discount]`. Y: `[Margin %]`. Details: `sub_category`. Size: `[Total Sales]` |
| Column chart | X: `discount_band`. Y: `[Margin %]` (the single clearest chart in the project) |
| Top N and Bottom N bars | `product_name` filtered Top 10 / Bottom 10 by `[Total Profit]` |
| Stacked 100% column | X: Year. Legend: `category`. Value: `[Total Sales]` (mix-shift check) |

**Drill-through page:** create a hidden page with `sub_category` as the drill-through field showing its monthly trend, top loss-making products, and discount distribution. Right-click any sub-category on Page 2 → Drill through.

## Page 3: Customer intelligence

**Slicers:** Acquisition year (`Dim_Customer[acquisition_year]`), Customer type, RFM segment

| Visual | Fields |
|---|---|
| Treemap | Group: `rfm_segment`. Values: `Customer Count` |
| Clustered bars | Axis: `rfm_segment`. Values: `[Profit Share %]` and revenue share (add `% of grand total` to Sales) |
| Histogram-style column | Axis: `profit_decile`. Values: `SUM(Dim_Customer[profit])` (profit concentration) |
| Line | X: `Dim_Date[Year]`. Values: `[New Customers]`, `[Repeat Customers]` |
| Cards | `[Repeat Rate %]`, `[Avg CLV (profit)]`, `[Avg First-order Discount]` |
| Matrix: cohort retention | Rows: `Cohort_Annual[cohort_year]`. Columns: `Cohort_Annual[period]`. Values: `[Retention %]`. Format → Cell elements → Background color → gradient (white to dark blue, min 0, max 1) |

Duplicate the matrix using `Cohort_Monthly` on a tooltip or bookmark ("Monthly view") if you want finer detail.

## Page 4: Regions and returns

**Slicers:** Year, Category

| Visual | Fields |
|---|---|
| Filled map | Location: `state`. Color saturation: `[Total Profit]` with diverging colors (red/green, centre at 0) |
| Table | `state`, `region`, `[Total Sales]`, `[Total Profit]`, `[Margin %]`, `[Avg Discount]`. Conditional formatting on profit |
| Column chart | X: `category`. Y: `[Return Rate]`. Legend or small multiples: `region` |
| Scatter | X: `[Return Rate]`. Y: `[Margin %]`. Details: `sub_category` |

---

## Interactivity checklist
- [ ] Slicers synced across pages
- [ ] Drill-through from sub-category
- [ ] Hierarchy drill (category → sub-category → product) on Page 2 matrix
- [ ] Tooltips pages on the main line chart (margin, discount, loss-line share)
- [ ] Bookmarks: "All years" and "Latest year" buttons
- [ ] Page navigator

## Export for GitHub
1. File → Export → PDF to `powerbi/dashboard.pdf`
2. Screenshot each page into `images/dashboard_page1.png` … `dashboard_page4.png`
3. Save the report as `powerbi/Profit_Intelligence.pbix` (keep it under 100 MB; the Superstore data is tiny)
