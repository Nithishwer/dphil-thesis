#!/usr/bin/env python3
"""Figure A2 - performance by task category.

Three panels sharing a category axis, one bar per model:

    left    Strict-Pass@1
    middle  average correctness score
    right   average process score

This was two figures - a strict-rate figure in the main text and a partial-credit
one in the appendix. They shared an axis, an ordering and a legend, and the whole
point is the gap between them, which is easier to see side by side than eleven
pages apart. Merged, and the pair moved to the appendix so the main text carries
three figures.

Scores are the adjusted ones, meaning a crashed trial counts as zero rather than
being dropped. That is the same convention as every other results figure, and it
is why a model with many crashes sits lower here than its graded work alone would
suggest.

No error bars. Category sizes run from 13 tasks down to 1, and a bar drawn from a
single task has no interval to show; the task count in each row label is the
honest signal of how much weight a row carries.

Data comes from `mdarena analyze --manifest`, copied into `data/`:

    data/category_summary/<label>.csv   one row per category with the two
                                        adjusted-score quantities
    data/task_summary/<label>.csv       task-to-category mapping
    data/trials/<label>.csv             trial scores used to calculate strict
                                        pass at task and category level

Usage:
    python make_figure_A2.py
"""

from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

CHAPTER = Path(__file__).resolve().parents[3]
HERE = CHAPTER / "figures/figure_A2"
DATA = CHAPTER / "data"
CATEGORY_DIR = DATA / "category_summary"
TASK_SUMMARY_DIR = DATA / "task_summary"
TRIALS_DIR = DATA / "trials"
OUT_STEM = HERE / "figure_A2"
PASS_THRESHOLD = 0.999

# Same order and palette as Figures 2 and 3.
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

BAR_EDGE = "#7A7A7A"
BAR_EDGE_WIDTH = 0.5

LABELS = {
    "analysis": "Analysis",
    "system_preparation": "System preparation",
    "free_energy": "Free energy",
    "enhanced_sampling": "Enhanced sampling",
    "parameterization": "Parameterization",
    "diagnostics": "Diagnostics",
    "quantum_chemistry": "Quantum chemistry",
}

PANELS = [
    ("strict_pass_at_1", "Average strict-pass@1 rate"),
    ("mean_correctness_adj", "Average correctness score"),
    ("mean_process_adj", "Average process score"),
]

# Fraction of a category's row taken up by its ten bars; the remainder is the
# gap to the next category. At 0.84 the clusters nearly touched and the figure
# read as one block of bars rather than seven groups. The height
# below grows with it so the bars keep their thickness rather than being
# squeezed to pay for the gap.
BAR_WIDTH_TOTAL = 0.60
FIGURE_HEIGHT = 11.5
LABEL_SIZE = 11

LEGEND_TOP = 0.085
AXES_BOTTOM = 0.10
LAYOUT_PAD = 0.4


def label(value: str) -> str:
    return LABELS.get(value, value.replace("_", " ").capitalize())


def read_category_summary(name: str) -> dict[str, dict[str, str]]:
    path = CATEGORY_DIR / f"{name}.csv"
    if not path.is_file():
        sys.exit(
            f"No per-category table at {path}.\n"
            "Produce one with:\n"
            "    mdarena analyze --manifest <runs.toml> --output-dir <dir>\n"
            f"then copy <dir>/{name}/tables/category_summary.csv to {path}."
        )
    return {r["category"]: r for r in csv.DictReader(path.open())}


def read_rows(directory: Path, name: str, description: str) -> list[dict[str, str]]:
    path = directory / f"{name}.csv"
    if not path.is_file():
        sys.exit(f"No {description} table at {path}.")
    return list(csv.DictReader(path.open()))


def strict_pass_by_task(trials: list[dict[str, str]]) -> dict[str, float]:
    """Return strict pass rates, counting incomplete trials as failures."""
    scores: dict[str, list[float]] = collections.defaultdict(list)
    for row in trials:
        passed = (
            row["status"] == "completed"
            and float(row["correctness"] or 0.0) >= PASS_THRESHOLD
            and float(row["process"] or 0.0) >= PASS_THRESHOLD
        )
        scores[row["task_id"]].append(float(passed))
    return {task: statistics.fmean(values) for task, values in scores.items()}


def main() -> int:
    per_model = {name: read_category_summary(name) for name, _ in MODELS}

    for name, _ in MODELS:
        tasks = {
            row["task_id"]: row for row in read_rows(TASK_SUMMARY_DIR, name, "per-task")
        }
        strict = strict_pass_by_task(read_rows(TRIALS_DIR, name, "per-trial"))
        if set(strict) != set(tasks):
            sys.exit(f"{name}: trial and task-summary tables cover different tasks.")
        strict_by_category: dict[str, list[float]] = collections.defaultdict(list)
        for task_id, rate in strict.items():
            strict_by_category[tasks[task_id]["category"]].append(rate)
        for category, values in strict_by_category.items():
            if category not in per_model[name]:
                sys.exit(
                    f"{name}: category {category!r} is missing from category_summary.csv."
                )
            expected = int(per_model[name][category]["n_tasks"])
            if len(values) != expected:
                sys.exit(
                    f"{name}: category {category!r} contains {len(values)} tasks, "
                    f"but category_summary.csv reports {expected}."
                )
            per_model[name][category]["strict_pass_at_1"] = str(
                statistics.fmean(values)
            )

    first = next(iter(per_model.values()))
    counts = {c: int(r["n_tasks"]) for c, r in first.items()}
    for name, rows in per_model.items():
        if {c: int(r["n_tasks"]) for c, r in rows.items()} != counts:
            sys.exit(
                f"{name} covers a different task set; all runs in one figure must match."
            )

    # Largest category first; `barh` numbers upward, so reverse to put it on top.
    categories = sorted(counts, key=lambda c: counts[c])

    colours = MODEL_COLOURS
    n = len(MODELS)
    height = BAR_WIDTH_TOTAL / n
    y = np.arange(len(categories))

    fig, axes = plt.subplots(1, len(PANELS), figsize=(14.5, FIGURE_HEIGHT), sharey=True)
    for ax, (column, xlabel) in zip(axes, PANELS):
        for i, (name, _) in enumerate(MODELS):
            # Negated so the first model sits at the TOP of each cluster, the
            # order the legend lists them in.
            offset = ((n - 1) / 2 - i) * height
            values = [float(per_model[name][c][column]) for c in categories]
            ax.barh(
                y + offset,
                values,
                height,
                color=colours[i],
                edgecolor=BAR_EDGE,
                linewidth=BAR_EDGE_WIDTH,
            )
        ax.set_xlim(0, 1.02)
        ax.set_xticks(np.arange(0, 1.01, 0.2))
        ax.set_xlabel(xlabel, fontsize=LABEL_SIZE)
        ax.tick_params(axis="both", labelsize=9.5)
        ax.grid(axis="x", alpha=0.25, linewidth=0.6)
        ax.set_axisbelow(True)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels([f"{label(c)} (n={counts[c]})" for c in categories])
    axes[0].set_ylim(-0.6, len(categories) - 0.4)

    fig.legend(
        handles=[
            Patch(
                facecolor=c, edgecolor=BAR_EDGE, linewidth=BAR_EDGE_WIDTH, label=display
            )
            for c, (_, display) in zip(colours, MODELS)
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

    print(f"Read per-category tables for {len(MODELS)} models from {CATEGORY_DIR}")
    for c in reversed(categories):
        cells = "  ".join(
            f"{name}="
            + "/".join(
                f"{float(per_model[name][c][column]):.2f}" for column, _ in PANELS
            )
            for name, _ in MODELS
        )
        print(
            f"  {label(c):<20} (n={counts[c]:>2})  strict/correctness/process  {cells}"
        )
    print(f"Wrote {OUT_STEM}.png and {OUT_STEM}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
