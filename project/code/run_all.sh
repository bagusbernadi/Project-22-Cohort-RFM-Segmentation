#!/usr/bin/env bash
# Jalankan seluruh pipeline dari nol (urutan = nomor skrip). Jalankan dari folder project/.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 code/1-data-preparation/python/01_prepare_raw.py
python3 code/1-data-preparation/python/02_clean_and_load.py
python3 code/2-analysis/python/03_run_analysis_sql.py
python3 code/2-analysis/python/04_crosscheck.py
python3 code/2-analysis/python/05_analysis.py
python3 code/2-analysis/python/06_sensitivity.py
python3 code/3-presentation/python/07_dashboard_data.py
python3 code/3-presentation/python/08_test_dashboard.py
cd ..
python3 design-and-report/src/build_report.py
