"""08: uji dashboard dengan Streamlit AppTest (semua halaman dan filter; tidak ada exception)."""
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit" / "app.py"
at = AppTest.from_file(str(APP), default_timeout=120).run()
assert not at.exception, at.exception
assert [m.label for m in at.metric] == ["Pelanggan unik", "Retensi bulan 1 (tertimbang)", "Repeat purchase rate", "Revenue per pelanggan"]
assert "5.852" in at.metric[0].value.replace(",", ".") or "5.852" in at.metric[0].value

at.sidebar.radio[0].set_value("Retensi Kohort").run()
assert not at.exception and len(at.get("plotly_chart")) == 1

at.sidebar.radio[0].set_value("Segmen RFM").run()
assert not at.exception and len(at.get("plotly_chart")) == 1
at.sidebar.selectbox[0].set_value("Luar Inggris").run()
assert not at.exception
print("AppTest: semua halaman dan filter lulus; metric:", [m.value for m in at.metric])
