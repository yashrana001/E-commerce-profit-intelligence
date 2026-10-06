
import pandas as pd

from config import PROC


def main():
    cust = pd.read_csv(PROC / "customer_summary.csv")
    rfm = pd.read_csv(PROC / "rfm_segments.csv")[
        ["customer_id", "recency", "frequency", "monetary", "R", "F", "M", "rfm_score", "segment"]
    ].rename(columns={"recency": "recency_days", "segment": "rfm_segment"})
    dim = cust.merge(rfm, on="customer_id", how="left")

    names = (pd.read_csv(PROC / "orders_clean.csv", usecols=["customer_id", "customer_name", "segment"])
               .drop_duplicates("customer_id"))
    dim = dim.merge(names, on="customer_id", how="left").rename(columns={"segment": "customer_segment"})
    dim.to_csv(PROC / "dim_customer.csv", index=False)
    print(f"dim_customer.csv: {len(dim)} customers, {dim.shape[1]} columns")

    print("\nLoad these into Power BI:")
    for f in ["orders_clean.csv", "dim_customer.csv", "cohort_retention_monthly.csv",
              "cohort_retention_annual.csv", "profit_bridge_subcategory.csv",
              "rfm_segment_summary.csv"]:
        print("  -", f)


if __name__ == "__main__":
    main()
