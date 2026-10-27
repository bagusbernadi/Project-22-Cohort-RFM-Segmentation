"""07: siapkan CSV untuk dashboard (dibaca app Streamlit; tidak perlu database saat deploy)."""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import RES_ANALYSIS, RES_PRESENT  # noqa: E402

ret = pd.read_csv(RES_ANALYSIS / "cohort_retention.csv", parse_dates=["cohort_month"])
ret = ret[ret.month_index <= 12].copy()
ret["cohort"] = ret.cohort_month.dt.strftime("%Y-%m")
ret[["cohort", "cohort_month", "month_index", "cohort_size", "active_customers", "retention_rate"]] \
    .to_csv(RES_PRESENT / "dashboard_retention.csv", index=False)

cust = pd.read_csv(RES_ANALYSIS / "customers_rfm.csv")
flags = pd.read_csv(RES_ANALYSIS / "customers_flags.csv")[["customer_id", "grup_negara"]]
cust = cust.merge(flags, on="customer_id", how="left")
assert cust.grup_negara.notna().all()
cust.to_csv(RES_PRESENT / "dashboard_customers.csv", index=False)

seg = pd.read_csv(RES_ANALYSIS / "q4_q5_segments.csv")
seg.to_csv(RES_PRESENT / "dashboard_segments.csv", index=False)

kpi = pd.read_csv(RES_ANALYSIS / "kpi.csv")
kpi.to_csv(RES_PRESENT / "dashboard_kpi.csv", index=False)

hyp = pd.read_csv(RES_ANALYSIS / "hypotheses.csv")
hyp.to_csv(RES_PRESENT / "dashboard_hypotheses.csv", index=False)
print("dashboard csv:", sorted(p.name for p in RES_PRESENT.glob("dashboard_*.csv")))
