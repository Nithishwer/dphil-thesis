#!/usr/bin/env python3
"""Figure A1 - how every trial ended, by model.

One stacked bar per model, splitting all 150 of its trials into four outcomes:

    Full pass            both rewards full - the strict pass@1 numerator
    Failed evaluation    finished and was graded, but did not pass
    Agent timeout        ran out of its wall-clock budget
    Other runtime error  crashed some other way (usually a non-zero exit)

The point of the figure is that the last two are not the same kind of failure as
the second. A model can score badly because its work was wrong, or because it
never delivered work at all, and the headline rate cannot tell them apart.

Trials, not tasks. The v1 caption said "percentage of MDArena tasks", but a task
has three attempts that can end differently, so there is no single outcome to
assign it. Everything here is a percentage of that model's 150 trials.
The regraded runs use the qualifying trials selected for the DD analysis.

Data comes from `mdarena analyze --manifest`, copied into `data/`:

    data/trials/<label>.csv   one row per trial, with status, exception type and
                              both rewards

Usage:
    python make_figure_A1.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_A1"
DATA = CHAPTER / "data"
TRIALS_DIR = DATA / "trials"
OUT_STEM = HERE / "figure_A1"

MODELS = [
    ("gpt-5.6-terra", "GPT-5.6\nTerra"),
    ("gpt-5.6-sol", "GPT-5.6\nSol"),
    ("gpt-6.1-sol", "GPT-6.1\nSol"),
    ("gpt-6-astra", "GPT-6\nAstra"),
    ("sonnet-5", "Claude\nSonnet-5"),
    ("opus-5", "Claude\nOpus-5"),
    ("opus-5.5", "Claude\nOpus-5.5"),
    ("gemini-3.7-flash", "Gemini\n3.7 Flash"),
    ("glm-5.2", "GLM-5.2"),
    ("qwen3-coder-480b", "Qwen3 Coder\n480B A35B"),
]

# These colours encode outcomes rather than model identity.
OUTCOME_COLOURS = {
    "Full pass": "#90BE6D",
    "Failed evaluation": "#F8961E",
    "Agent timeout": "#F9C74F",
    "Other runtime error": "#F94144",
}
OUTCOMES = list(OUTCOME_COLOURS)

BAR_EDGE = "#7A7A7A"
BAR_EDGE_WIDTH = 0.7
LABEL_SIZE = 11
BAR_WIDTH = 0.62

# A segment thinner than this (per cent) gets no inline number; below it the
# text collides with the segment boundaries. The value is still in the printed
# summary and in the stack itself.
SEGMENT_LABEL_MIN = 6.0

PASS_THRESHOLD = 0.999
TIMEOUT_EXCEPTION = "AgentTimeoutError"

LEGEND_TOP = 0.10
AXES_BOTTOM = 0.11
LAYOUT_PAD = 0.4


def read_trials(name: str) -> list[dict[str, str]]:
    path = TRIALS_DIR / f"{name}.csv"
    if not path.is_file():
        sys.exit(
            f"No per-trial table at {path}.\n"
            "Produce one with:\n"
            "    mdarena analyze --manifest <runs.toml> --output-dir <dir>\n"
            f"then copy <dir>/{name}/tables/trials.csv to {path}."
        )
    return list(csv.DictReader(path.open()))


def classify(row: dict[str, str]) -> str:
    """One trial's outcome. Errors are checked first, deliberately.

    Harbor grades whatever the agent left behind, so a crashed trial can still
    carry full rewards. It is still a failed delivery and belongs in an error
    bucket - which is the same rule the strict pass@1 rate applies, so the green
    segment here is exactly that rate.
    """
    if row["status"] == "error":
        return (
            "Agent timeout"
            if row["exception_type"] == TIMEOUT_EXCEPTION
            else "Other runtime error"
        )
    correctness = float(row["correctness"] or 0.0)
    process = float(row["process"] or 0.0)
    if correctness >= PASS_THRESHOLD and process >= PASS_THRESHOLD:
        return "Full pass"
    return "Failed evaluation"


def main() -> int:
    shares, counts = {}, {}
    for label, _ in MODELS:
        rows = read_trials(label)
        tally = {outcome: 0 for outcome in OUTCOMES}
        for row in rows:
            tally[classify(row)] += 1
        counts[label] = tally
        shares[label] = {k: 100.0 * v / len(rows) for k, v in tally.items()}

    fig, ax = plt.subplots(figsize=(12.5, 4.2))
    x = np.arange(len(MODELS))
    bottom = np.zeros(len(MODELS))
    for outcome in OUTCOMES:
        values = np.array([shares[label][outcome] for label, _ in MODELS])
        ax.bar(
            x,
            values,
            BAR_WIDTH,
            bottom=bottom,
            color=OUTCOME_COLOURS[outcome],
            edgecolor=BAR_EDGE,
            linewidth=BAR_EDGE_WIDTH,
            label=outcome,
        )
        for xi, (value, base) in enumerate(zip(values, bottom)):
            if value >= SEGMENT_LABEL_MIN:
                ax.text(
                    xi,
                    base + value / 2,
                    f"{value:.0f}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                )
        bottom += values

    ax.set_xticks(x)
    ax.set_xticklabels([name for _, name in MODELS], fontsize=9.5)
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_ylabel("Trials (%)", fontsize=LABEL_SIZE)
    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)

    fig.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, LEGEND_TOP),
        frameon=False,
        fontsize=9.5,
        ncol=4,
        columnspacing=1.6,
        handlelength=1.1,
        handletextpad=0.5,
        borderpad=0.0,
    )
    fig.tight_layout(rect=(0, AXES_BOTTOM, 1, 1), pad=LAYOUT_PAD)

    fig.savefig(f"{OUT_STEM}.png", dpi=600, bbox_inches="tight", transparent=True)
    fig.savefig(f"{OUT_STEM}.pdf", bbox_inches="tight", transparent=True)

    print(f"Read per-trial tables for {len(MODELS)} models from {TRIALS_DIR}")
    for label, name in MODELS:
        cells = "  ".join(f"{o}={counts[label][o]:>3}" for o in OUTCOMES)
        print(f"  {name.replace(chr(10), ' '):<22} {cells}")
    print(f"Wrote {OUT_STEM}.png and {OUT_STEM}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
