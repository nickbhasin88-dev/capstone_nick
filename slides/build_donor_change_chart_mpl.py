"""
Change in health aid by donor, 2023 to 2030, in Computer Modern (matplotlib), sized for the right-hand chart area of
the deck slide "Health aid falls about 25% by 2030" (5.7 x 3.1 in). Same values as build_donor_change_chart.py.

Font: the requested settings (serif Computer Modern, 18 pt, usetex). When LaTeX is not installed, matplotlib's bundled
Computer Modern fonts (cmr10, with the 'cm' math fontset) are used instead: same typeface, no LaTeX needed.

    python slides/build_donor_change_chart_mpl.py  -> slides/render/donor_change_chart_cm.png and .pdf
"""
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import rc  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "render" / "donor_change_chart_cm"
DATA = [("United States", -66), ("Germany", -41), ("France", -34), ("United Kingdom", -32), ("Netherlands", -32),
        ("Japan", -15), ("Canada", 2), ("Gates Foundation", 22)]
NAVY, LIGHT, GRID, INK, MUTED = "#1C3073", "#8FA8E0", "#D5DCEA", "#1F2937", "#595959"
SIZE = 18
W, H = 5.7, 3.1

if shutil.which("latex"):
    rc("font", **{"family": "serif", "serif": ["Computer Modern"], "size": SIZE})
    rc("text", usetex=True)
else:
    rc("font", **{"family": "serif", "serif": ["cmr10"], "size": SIZE})
    rc("mathtext", fontset="cm")
    rc("axes", unicode_minus=False)
    rc("axes.formatter", use_mathtext=True)


def pct(v, bold=False):
    s = f"{'+' if v > 0 else '-' if v < 0 else ''}{abs(v):.0f}\\%"
    return f"$\\mathbf{{{s}}}$" if bold else f"${s}$"


fig, ax = plt.subplots(figsize=(W, H))
names = [d for d, _ in DATA]
vals = [v for _, v in DATA]
ys = range(len(DATA))
ax.barh(ys, vals, height=0.72, color=[NAVY if v < 0 else LIGHT for v in vals], zorder=2)
ax.invert_yaxis()                                         # United States on top
ax.set_yticks(list(ys), names, fontsize=SIZE * 0.78, color=INK)
ax.tick_params(axis="y", length=0, pad=6)

ax.set_xlim(-86, 38)
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v)))
ax.tick_params(axis="x", length=0, labelsize=SIZE * 0.6, colors=MUTED, pad=4)
ax.grid(axis="x", color=GRID, linewidth=0.75, zorder=0)
ax.axvline(0, color=INK, linewidth=1.3, zorder=3)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.set_xlabel("Change in health aid, 2023 to 2030", fontsize=SIZE * 0.6, color=MUTED, labelpad=4)

for y, v in zip(ys, vals):
    ax.text(v + (1.5 if v > 0 else -1.5), y, pct(v, True), va="center", ha="left" if v > 0 else "right",
            color=INK, fontsize=SIZE * 0.72, zorder=4)

fig.subplots_adjust(left=0.325, right=0.985, top=0.98, bottom=0.20)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}.{ext}", dpi=300, transparent=(ext == "png"))
print("wrote", f"{OUT}.png", f"{OUT}.pdf", "| usetex" if shutil.which("latex") else "| bundled Computer Modern (no LaTeX)")
