
import importlib

for name in ("01_clean_eda", "02_rfm_segmentation", "03_cohort_retention", "04_profit_drivers", "05_export_powerbi"):
    print(f"\n{'=' * 70}\nRunning {name}\n{'=' * 70}")
    importlib.import_module(name).main()
