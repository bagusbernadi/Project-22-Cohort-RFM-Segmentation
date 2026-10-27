"""Helper format angka Indonesia (1.234,5) dan escaping HTML untuk Report."""
import html
import math


def num(x, d=0):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, d=1):
    """x dalam proporsi 0..1."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return num(100 * x, d) + "%"


def pct_raw(x, d=1):
    """x sudah dalam persen (0..100)."""
    return num(x, d) + "%"


def esc(t):
    return html.escape(str(t), quote=True)


def pill(label, kind=""):
    cls = "pill" + (f" {kind}" if kind else "")
    return f'<span class="{cls}">{esc(label)}</span>'


def table(headers, rows, cls=""):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    c = f' class="{cls}"' if cls else ""
    return f'<div class="scroll"><table{c}><tr>{th}</tr>{body}</table></div>'
