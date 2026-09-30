"""Regression check for generate_report.py chart axes.

    python3 scripts/check_report_axes.py skills/social-media-report/scripts/generate_report.py

Builds the chart shapes that broke in the Sep 2026 output evals (narrow rate
range, counts in the low thousands, a single data point, 31 daily labels)
and fails on duplicate y tick labels or a crowded flat x axis.
"""
import importlib.util, sys, tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("gr", sys.argv[1]); gr = importlib.util.module_from_spec(spec); spec.loader.exec_module(gr)
captured = []
real_close = gr.plt.close
gr.plt.close = lambda fig=None: captured.append(fig)
days = [f"08-{d:02d}" for d in range(1, 32)]
cases = {
  "narrow rate trend (1.83-1.96)": {"type": "trend", "labels": ["Jun", "Jul", "Aug"], "series": [{"name": "ER", "values": [1.83, 1.83, 1.96]}]},
  "counts in thousands (2.9K-4.1K)": {"type": "trend", "labels": ["Jan","Feb","Mar","May","Jun","Aug"], "series": [{"name": "I", "values": [4050, 3950, 3450, 2900, 3700, 2850]}]},
  "single data point (1.18M)": {"type": "trend", "labels": ["Aug"], "series": [{"name": "V", "values": [1177342]}]},
  "31 daily labels": {"type": "trend", "labels": days, "series": [{"name": "V", "values": [300000 + 7000 * (i % 9) for i in range(31)]}]},
  "narrow benchmark (4.77 vs 4.2)": {"type": "benchmark", "account_value": 4.77, "benchmark_value": 4.2},
}
bad = 0
for name, c in cases.items():
    c.setdefault("id", "x"); c.setdefault("title", "t"); c.setdefault("takeaway", "")
    gr.build_chart(c, Path(tempfile.mkdtemp()) / "c.png")
    fig = captured.pop(); ax = fig.axes[0]
    ylab = [t.get_text() for t in ax.get_yticklabels() if t.get_text()]
    xt = [t for t in ax.get_xticklabels() if t.get_text() and t.get_visible()]
    problems = []
    if len(set(ylab)) < len(ylab): problems.append(f"duplicate y labels {ylab}")
    if len(xt) > 16 and all(t.get_rotation() == 0 for t in xt): problems.append(f"{len(xt)} flat x labels")
    print(("FAIL " if problems else "ok   ") + name + ": " + ("; ".join(problems) or str(ylab)))
    bad += bool(problems)
    real_close(fig)
sys.exit(1 if bad else 0)
