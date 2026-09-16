"""Redraw the README charts from the exported marts in exports/.

    uv run --with matplotlib python docs/charts.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
RAMP = ["#86b6ef", "#5598e7", "#3987e5", "#2a78d6", "#1c5cab", "#184f95", "#104281"]
plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.linewidth": 1, "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "grid.linewidth": 1, "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.labelcolor": INK2,
    "axes.titlelocation": "left", "axes.titleweight": "bold", "axes.titlesize": 13, "axes.titlecolor": INK,
    "font.size": 10, "legend.frameon": False,
})


def title(fig, text, sub=None):
    fig.text(0.04, 0.95, text, fontsize=14, fontweight="bold", color=INK, va="top")
    if sub:
        fig.text(0.04, 0.895, sub, fontsize=10, color=INK2, va="top")


def read(name):
    with open(ROOT / "exports" / name, newline="") as f:
        return list(csv.DictReader(f))


rate = read("mart_reply_rate_by_message_type.csv")
weekly = read("mart_weekly_funnel.csv")
sends = sum(int(r["sends"]) for r in rate)
bounced = sum(int(r["bounced"]) for r in rate)
delivered = sum(int(r["delivered"]) for r in rate)
human = sum(int(r["human_replies"]) for r in rate)
inbound = human + sum(int(r["machine_responses"]) for r in weekly)
leads = sum(int(r["leads_first_contacted"]) for r in weekly)

# 487 and 167 are the source grain (listings, addresses); the rest come from the marts above.
stages = [
    ("Shopify app listings scraped", 487),
    ("Contact addresses in tier A", 167),
    ("Leads sent a first email", leads),
    ("Emails sent", sends),
    ("Delivered (not bounced)", delivered),
    ("Inbound messages of any kind", inbound),
    ("Human replies", human),
]
fig, ax = plt.subplots(figsize=(11, 5.2))
fig.subplots_adjust(top=0.8, bottom=0.08, left=0.27, right=0.96)
title(fig, "487 listings in, 1 human reply out",
      "The Signet cold outreach campaign, 2026-08-13 to 2026-09-09, as the warehouse counts it.")
ys = list(range(len(stages)))[::-1]
vals = [v for _, v in stages]
ax.barh(ys, vals, height=0.5, color=RAMP)
for y, (label, v) in zip(ys, stages):
    ax.text(v + 6, y, f"{v:,}", va="center", fontsize=10, color=INK)
ax.set_yticks(ys, [s for s, _ in stages])
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.set_xlim(0, 560)
fig.savefig(OUT / "funnel.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4.8))
fig.subplots_adjust(top=0.78, bottom=0.14, left=0.06, right=0.98)
title(fig, "Emails sent per week, and the week the one human reply came back",
      "mart_weekly_funnel, one row per ISO week. Weeks with no sends would show as zero.")
x = list(range(len(weekly)))
d = [int(r["delivered"]) for r in weekly]
b = [int(r["bounced"]) for r in weekly]
ax.bar(x, d, 0.42, color=BLUE, label="delivered")
ax.bar(x, b, 0.42, bottom=[v + 0.25 for v in d], color=ORANGE, label="bounced")
for xi, dv, bv in zip(x, d, b):
    ax.text(xi, dv + bv + 1.0, f"{dv + bv}", ha="center", fontsize=9, color=INK)
for xi, r in zip(x, weekly):
    if int(r["human_replies"]):
        ax.annotate(f"{r['human_replies']} human reply", (xi, int(r["delivered"]) + int(r["bounced"]) + 3.2),
                    ha="center", fontsize=9, color=INK2)
ax.set_xticks(x, [f"{r['iso_week_label']}\nw/c {r['week_start']}" for r in weekly])
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_ylim(0, 32)
ax.legend(loc="upper right")
fig.savefig(OUT / "weekly.png", dpi=150)
plt.close(fig)
print("stages", stages)
