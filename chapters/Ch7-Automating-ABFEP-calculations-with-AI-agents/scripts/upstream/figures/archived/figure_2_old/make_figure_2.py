#!/usr/bin/env python3
"""Figure 2 - overall agent performance on MDArena.

Three panels, the same triptych as the v1 figure:

    (a) Success       Strict-Pass@1, one bar per model
    (b) Correctness   mean correctness reward
    (c) Process       mean process reward

Data comes from `mdarena analyze --manifest`, copied into `data/`:

    data/headline.csv          the comparison table: one row per model, holding
                               every point estimate and the strict pass@1 CI
    data/metrics/<label>.csv   each run's own metrics table, which is the only
                               place the correctness and process intervals are
                               written

Two files rather than one because `headline.csv` carries `strict_ci_low` /
`strict_ci_high` but no interval for the two reward means - `compare.py` does not
copy those across, though `aggregate.py` computes them. Rather than recomputing
them here from the trial data (which would put a second, drifting definition of
the interval in the repository), the per-run tables are read for those two
panels. If `data/metrics/` is absent the figure still draws, without error bars
on (b) and (c), and says so loudly on stdout.

All three intervals are 95% task-clustered bootstrap CIs, resampling *tasks*
rather than trials: three attempts at one task are far more alike than three at
different tasks (ICC ~0.8 on v0.2), so resampling trials would treat correlated
observations as independent and understate the interval by about half again.

This differs from the v1 figure, whose caption said "standard errors across
tasks, using binomial standard errors for pass/fail success rates". The bars are
asymmetric here because a percentile interval need not be symmetric about the
estimate, and the caption has to say "95% task-clustered CI" rather than
"standard error". They are not interchangeable and the figure is wrong if the
caption is not updated with it.

Usage:
    python make_figure_2.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "data"
HEADLINE_CSV = DATA / "headline.csv"
METRICS_DIR = DATA / "metrics"
OUT_STEM = HERE / "figure_2"

# Presentation order, fixed by hand rather than sorted by score. Grouping the
# GPT configurations, then the Claude ones, lets a reader compare within a
# family without hunting across the axis; sorting by score would interleave them
# and make the within-family comparison the hardest one to read.
#
# Left to right: (csv label, display name).
MODELS = [
    ("gpt-5.6-terra", "GPT-5.6 Terra"),
    ("gpt-5.6-sol", "GPT-5.6 Sol"),
    ("gpt-6.1-sol", "GPT-6.1 Sol"),
    ("gpt-6-astra", "GPT-6 Astra"),
    ("sonnet-5", "Claude Sonnet-5"),
    ("opus-5", "Claude Opus-5"),
    ("opus-5.5", "Claude Opus-5.5"),
    ("gemini-3.7-flash", "Gemini 3.7 Flash"),
    ("glm-5.2", "GLM-5.2"),
    ("qwen3-coder-480b", "Qwen3 Coder 480B A35B"),
]

# Fixed model palette, in the same order as MODELS above.
MODEL_COLOURS = [
    "#90BE6D",  # GPT-5.6 Terra
    "#43AA8B",  # GPT-5.6 Sol
    "#277DA8",  # GPT-6.1 Sol
    "#9B5DE5",  # GPT-6 Astra
    "#F8961E",  # Claude Sonnet-5
    "#F3722C",  # Claude Opus-5
    "#D65F8D",  # Claude Opus-5.5
    "#F9C74F",  # Gemini 3.7 Flash
    "#F94144",  # GLM-5.2
    "#577590",  # Qwen3 Coder 480B A35B
]

# These fills are pale by design (Figure 1 lightened them to a lightness floor so
# nothing reads as heavy). Pale fills on white need an outline or the bar edge
# disappears; a mid grey is enough to define it without competing with the fill.
BAR_EDGE = "#7A7A7A"
BAR_EDGE_WIDTH = 0.7

# Error bars sit on top of a pale fill, so they are drawn in near-black: a
# lighter colour would be lost against the bar it overlays.
ERROR_COLOUR = "#222222"

BAR_WIDTH = 0.72
Y_MAX = 1.05
LABEL_SIZE = 11

# Where the legend's top edge sits, and where the axes' bottom edge sits, both as
# fractions of figure height. The gap between them is the whole of the space
# under the panels, so the two move together: raising LEGEND_TOP without raising
# AXES_BOTTOM by as much closes the gap, and past about 0.01 apart the legend
# collides with the y tick labels of the leftmost panel.
#
# `bbox_inches="tight"` crops whitespace at the figure's outer edge but not
# between two pieces of content, so this gap is what actually reaches the page.
LEGEND_TOP = 0.15
AXES_BOTTOM = 0.20

# Padding `tight_layout` leaves around the axes, in font-size units. The default
# of 1.08 is most of the space under the panels once the panel captions are gone,
# so it is tightened here rather than by moving the two fractions above: those
# set where the blocks sit, this sets how much air each one keeps around itself.
LAYOUT_PAD = 0.4

# Which row of each metrics.csv holds each panel's interval. The `metric` column
# is free text written by `aggregate.py`, so these are matched exactly and a
# miss is reported rather than silently skipped.
METRIC_ROWS = {
    "correctness": "mean correctness",
    "process": "mean process",
}

# (csv column, y-axis label, metrics.csv key). There is no panel caption: each
# y-axis label now names its own quantity in full, so an "(a) Success" underneath
# would only repeat it. Panels are referred to left-to-right in the text.
PANELS = [
    ("strict_pass_at_1", "Average strict-pass@1 rate", None),
    ("mean_correctness_adj", "Average correctness score", "correctness"),
    ("mean_process_adj", "Average process score", "process"),
]


def read_headline() -> dict[str, dict[str, str]]:
    if not HEADLINE_CSV.is_file():
        sys.exit(
            f"No headline table at {HEADLINE_CSV}.\n"
            "Produce one with:\n"
            "    mdarena analyze --manifest <runs.toml> --output-dir <dir>\n"
            f"then copy <dir>/tables/headline.csv to {HEADLINE_CSV}."
        )
    rows = {r["model"]: r for r in csv.DictReader(HEADLINE_CSV.open())}
    missing = [label for label, _ in MODELS if label not in rows]
    if missing:
        sys.exit(
            f"{HEADLINE_CSV} has no row for: {', '.join(missing)}.\n"
            f"It contains: {', '.join(sorted(rows))}.\n"
            "Either the manifest labels changed or the wrong table was copied."
        )
    return rows


def read_metrics() -> dict[str, dict[str, tuple[float, float]]]:
    """Per-model {metric key: (ci_low, ci_high)}, or {} if the directory is absent.

    Returning empty rather than exiting keeps the figure buildable from
    `headline.csv` alone, which is the file most likely to have been copied on
    its own. The caller announces the degradation.
    """
    if not METRICS_DIR.is_dir():
        return {}
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for label, _ in MODELS:
        path = METRICS_DIR / f"{label}.csv"
        if not path.is_file():
            continue
        by_metric = {r["metric"]: r for r in csv.DictReader(path.open())}
        found = {}
        for key, row_name in METRIC_ROWS.items():
            row = by_metric.get(row_name)
            if row:
                found[key] = (float(row["ci_low"]), float(row["ci_high"]))
        if found:
            out[label] = found
    return out


def error_bars(values: list[float], bounds: list[tuple[float, float] | None]) -> np.ndarray | None:
    """Asymmetric yerr as matplotlib wants it: a 2xN array of (down, up) lengths.

    A percentile bootstrap interval is not symmetric about the estimate, so the
    two halves are computed separately from the interval rather than from a
    single half-width. Clamped at zero: a stored interval that does not bracket
    its own estimate would otherwise draw a bar pointing the wrong way, which
    reads as a plotting bug rather than as the data problem it is.
    """
    if not any(b is not None for b in bounds):
        return None
    lo, hi = [], []
    for value, bound in zip(values, bounds):
        if bound is None:
            lo.append(0.0)
            hi.append(0.0)
        else:
            lo.append(max(0.0, value - bound[0]))
            hi.append(max(0.0, bound[1] - value))
    return np.array([lo, hi])


def draw_panel(ax, values, bounds, ylabel: str, colours) -> None:
    x = np.arange(len(values))
    ax.bar(
        x,
        values,
        BAR_WIDTH,
        color=colours,
        edgecolor=BAR_EDGE,
        linewidth=BAR_EDGE_WIDTH,
        yerr=error_bars(values, bounds),
        capsize=3,
        error_kw={"ecolor": ERROR_COLOUR, "elinewidth": 1.0, "capthick": 1.0},
    )
    ax.set_xticks(x)
    # The bars are identified by the shared legend, not by the axis: ten model
    # names under each of three panels would be unreadable at this width and
    # would repeat the same list three times.
    ax.set_xticklabels([])
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.7, len(values) - 0.3)
    ax.set_ylim(0, Y_MAX)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def main() -> int:
    headline = read_headline()
    metrics = read_metrics()

    colours = MODEL_COLOURS

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6))
    for ax, (column, ylabel, metric_key) in zip(axes, PANELS):
        values = [float(headline[label][column]) for label, _ in MODELS]
        if metric_key is None:  # panel (a): the interval is in headline.csv itself
            bounds = [
                (float(headline[label]["strict_ci_low"]), float(headline[label]["strict_ci_high"]))
                for label, _ in MODELS
            ]
        else:
            bounds = [metrics.get(label, {}).get(metric_key) for label, _ in MODELS]
        draw_panel(ax, values, bounds, ylabel, colours)

    fig.legend(
        handles=[
            Patch(facecolor=c, edgecolor=BAR_EDGE, linewidth=BAR_EDGE_WIDTH, label=name)
            for c, (_, name) in zip(colours, MODELS)
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, LEGEND_TOP),
        frameon=False,
        fontsize=9.5,
        ncol=5,
        columnspacing=1.2,
        handlelength=1.1,
        handletextpad=0.5,
        labelspacing=0.4,
        borderpad=0.0,
    )
    fig.tight_layout(rect=(0, AXES_BOTTOM, 1, 1), pad=LAYOUT_PAD)

    fig.savefig(f"{OUT_STEM}.png", dpi=600, bbox_inches="tight", transparent=True)
    fig.savefig(f"{OUT_STEM}.pdf", bbox_inches="tight", transparent=True)

    # Print what was plotted. A figure regenerated against refreshed tables
    # should announce the change rather than quietly look different.
    print(f"Read {len(MODELS)} models from {HEADLINE_CSV}")
    for label, name in MODELS:
        row = headline[label]
        lo, hi = float(row["strict_ci_low"]), float(row["strict_ci_high"])
        print(
            f"  {name:<24} strict={float(row['strict_pass_at_1']):.1%} [{lo:.1%}, {hi:.1%}]"
            f"  correctness={float(row['mean_correctness_adj']):.3f}"
            f"  process={float(row['mean_process_adj']):.3f}"
        )
    if not metrics:
        print(
            f"\n  WARNING: no {METRICS_DIR} - panels (b) and (c) were drawn WITHOUT error bars.\n"
            "  Copy each run's tables/metrics.csv there as <label>.csv to restore them."
        )
    else:
        no_ci = [name for label, name in MODELS if label not in metrics]
        if no_ci:
            print(f"\n  WARNING: no metrics.csv for {', '.join(no_ci)} - those bars have no (b)/(c) interval.")
    print(f"Wrote {OUT_STEM}.png and {OUT_STEM}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
