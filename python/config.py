
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "images"
INSIGHTS = ROOT / "insights"

for p in (RAW, PROC, FIG, INSIGHTS):
    p.mkdir(parents=True, exist_ok=True)

# Discount bands used everywhere (Python, SQL and Power BI use the same cut-offs)
DISCOUNT_BINS = [-0.001, 0.0, 0.20, 0.40, 1.0]
DISCOUNT_LABELS = ["0%", "1-20%", "21-40%", "40%+"]


def find_raw_file() -> Path:
    """Return the first xlsx/xls/csv found in data/raw/."""
    for pattern in ("*.xlsx", "*.xls", "*.csv"):
        files = sorted(RAW.glob(pattern))
        if files:
            return files[0]
    raise FileNotFoundError(
        f"No dataset found in {RAW}. See data/README.md for download instructions."
    )
