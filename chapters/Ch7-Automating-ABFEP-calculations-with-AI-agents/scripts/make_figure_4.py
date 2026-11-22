#!/usr/bin/env python3
"""Figure 4 - performance and cost across task difficulty.

Three panels, the same triptych as the v1 figure:

    left    strict-pass@1 by difficulty, grouped bars
    middle  mean cost per trial by difficulty, grouped bars
    right   strict-pass@1 against mean cost per trial, one marker per model

Data comes from `mdarena analyze --manifest`, copied into `data/`:

    data/task_summary/<label>.csv   one row per task: `mean_cost_usd` and the
                                    task -> difficulty map
    data/trials/<label>.csv         one row per trial; used to calculate strict
                                    pass and estimate costs for GLM and DeepSeek
    data/headline.csv              overall strict-pass@1 and recorded costs

Per-task tables are used rather than `difficulty_summary.csv` because the
summary carries no dispersion for either quantity, and the error bars need it.
Aggregating here keeps one definition of "mean over tasks" for the bar and its
interval, instead of taking the bar from one file and inventing the interval
from another.

Error bars are 95% confidence intervals, the same kind Figure 2 shows and
computed the same way - see `mean_and_ci` below for the method and why it
resamples tasks rather than trials.

Usage:
    python make_figure_4.py
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
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from benchmark_versions import marked_name

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_4"

DATA = CHAPTER / "data"
TASK_SUMMARY_DIR = DATA / "task_summary"
TRIALS_DIR = DATA / "trials"
HEADLINE_CSV = DATA / "headline.csv"
OUT_STEM = HERE / "figure_4"

# Left to right: (csv label, display name, scatter and legend marker).
MODELS = [
    ("gpt-5.6-sol", "GPT-5.6 Sol", "o"),
    ("gpt-6.1-sol", "GPT-6.1 Sol", "^"),
    ("gpt-6-astra", "GPT-6 Astra", "*"),
    ("opus-5", "Claude Opus-5", "o"),
    ("opus-5.5", "Claude Opus-5.5", "^"),
    ("gemini-3.7-flash", "Gemini 3.7 Flash", "o"),
    ("gemini-4-argon", "Gemini 4 Argon", "^"),
    ("glm-5.2", "GLM-5.2", "o"),
    ("deepseek-v4", "DeepSeek V4.1 Flash", "o"),
]

# Use one hue per legend group and distinct shades for the models.
MODEL_COLOURS = [
    "#88C8B2",  # GPT-5.6 Sol
    "#3D997B",  # GPT-6.1 Sol
    "#12614F",  # GPT-6 Astra
    "#E88E70",  # Claude Opus-5
    "#B84D35",  # Claude Opus-5.5
    "#F2D46F",  # Gemini 3.7 Flash
    "#BD8B13",  # Gemini 4 Argon
    "#849DB7",  # GLM-5.2
    "#3C5773",  # DeepSeek V4.1 Flash
]

BAR_EDGE = "#7A7A7A"
BAR_EDGE_WIDTH = 0.7
ERROR_COLOUR = "#222222"

# ---------------------------------------------------------------------------
# GLM and Qwen's supplied means are in GBP. Allocate them across tasks using
# relative token prices, then scale to the supplied mean across all trials.
# Source: MDArena_NeurIPS_2026/figures/figure_3/make_figure_3.py, lines 83-110.
# The historical exchange rate is a plotting assumption, not a billing record.
GBP_TO_USD = 1.36
FLAT_COST_GBP = {"glm-5.2": 1.38, "qwen3-coder-480b": 0.14}
TOKEN_PRICE_WEIGHTS = (1.0, 0.1, 4.0)

# Vertex AI list prices in USD per million uncached input, cached input, and output
# tokens. The DeepSeek runs took place after the free preview ended.
# https://cloud.google.com/model-garden/partner-models/pricing
TOKEN_PRICES_USD_PER_MILLION = {"deepseek-v4": (0.30, 0.03, 1.20)}

# Hatch bars derived from token counts.
FLAT_HATCH = "///"

DIFFICULTIES = ["easy", "medium", "hard"]
DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}

BAR_WIDTH_TOTAL = 0.82
LABEL_SIZE = 11

# Linear cost axis on the right panel. Log spacing would separate the cheap
# models better, but it also makes a doubling in price look like a small step,
# which is the opposite of what a cost panel is for.
COST_LOG_SCALE = False
COST_TICKS = [0.2, 0.5, 1.0, 2.0]

LEGEND_TOP = 0.18
AXES_BOTTOM = 0.20
LAYOUT_PAD = 0.4


STRICT_COLUMN = "strict_pass_at_1"
PASS_THRESHOLD = 0.999


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


def read_task_summary(label: str) -> list[dict[str, str]]:
    path = TASK_SUMMARY_DIR / f"{label}.csv"
    if not path.is_file():
        sys.exit(
            f"No per-task table at {path}.\n"
            "Produce one with:\n"
            "    mdarena analyze --manifest <runs.toml> --output-dir <dir>\n"
            f"then copy <dir>/{label}/tables/task_summary.csv to {path}."
        )
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


def estimated_costs(
    trials: list[dict[str, str]],
    token_prices: tuple[float, float, float],
    flat_cost_usd: float | None,
) -> tuple[dict[str, float], float]:
    """Return estimated costs by task and the mean across all trials."""
    input_price, cache_price, output_price = token_prices
    costs: dict[str, list[float]] = collections.defaultdict(list)
    for row in trials:
        total_input = float(row["n_input_tokens"] or 0.0)
        cached = float(row["n_cache_tokens"] or 0.0)
        output = float(row["n_output_tokens"] or 0.0)
        # OpenCode's exported input total includes cache hits.
        costs[row["task_id"]].append(
            max(0.0, total_input - cached) * input_price
            + cached * cache_price
            + output * output_price
        )
    mean = statistics.fmean(
        cost for trial_costs in costs.values() for cost in trial_costs
    )
    scale = 1 / 1_000_000 if flat_cost_usd is None else flat_cost_usd / mean
    return (
        {
            task: statistics.fmean(trial_costs) * scale
            for task, trial_costs in costs.items()
        },
        mean * scale,
    )


def read_headline() -> dict[str, dict[str, str]]:
    if not HEADLINE_CSV.is_file():
        sys.exit(
            f"No headline table at {HEADLINE_CSV}; see make_figure_2.py for how to produce it."
        )
    return {r["model"]: r for r in csv.DictReader(HEADLINE_CSV.open())}


# --- 95% confidence intervals -----------------------------------------------
# The same interval Figure 2 shows, computed the same way, so all three results
# figures mean the same thing by an error bar. Earlier drafts of Figures 3 and 4
# used a standard error instead, purely because no interval was pre-computed per
# difficulty or per category; that left one paper showing two different kinds of
# bar with no way for a reader to tell them apart.
#
# The method: treat each TASK as one observation, draw 2000 random samples of
# the tasks in the bin (with replacement), take the mean of each sample, and
# report the 2.5th and 97.5th percentiles of those 2000 means. Resampling tasks
# rather than trials matters because three attempts at one task are far more
# alike than three at different tasks; treating them as independent would make
# the bars roughly a third too short.
#
# The interval is not symmetric about the bar, so the two halves differ. A bin
# holding one task has nothing to resample and gets no bar at all.
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 0


def mean_and_ci(values: list[float]) -> tuple[float, float, float]:
    """(mean over tasks, distance down to the interval, distance up to it)."""
    if not values:
        return float("nan"), 0.0, 0.0
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, 0.0, 0.0
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.asarray(values)[
        rng.integers(0, len(values), size=(N_BOOTSTRAP, len(values)))
    ]
    low, high = np.percentile(draws.mean(axis=1), [2.5, 97.5])
    return mean, max(0.0, mean - low), max(0.0, high - mean)


def by_difficulty(
    rows: list[dict[str, str]], column: str
) -> dict[str, tuple[float, float, float]]:
    """{difficulty: (mean over tasks, down, up)} for one numeric column."""
    out = {}
    for level in DIFFICULTIES:
        values = [
            float(r[column])
            for r in rows
            if r["difficulty"] == level and r.get(column) not in (None, "")
        ]
        out[level] = mean_and_ci(values)
    return out


def grouped_bars(ax, series, colours, ylabel: str, hatched: set[str], names) -> None:
    """One cluster of model bars per difficulty level.

    `series` is {label: {difficulty: (value, se)}}; a NaN value is skipped so a
    model with no data in a bin leaves a gap rather than a zero-height bar,
    which would read as a measured zero.
    """
    n = len(names)
    width = BAR_WIDTH_TOTAL / n
    x = np.arange(len(DIFFICULTIES))
    for i, label in enumerate(names):
        offset = (i - (n - 1) / 2) * width
        values = [series[label][d][0] for d in DIFFICULTIES]
        errors = np.array(
            [
                [series[label][d][1] for d in DIFFICULTIES],
                [series[label][d][2] for d in DIFFICULTIES],
            ]
        )
        ax.bar(
            x + offset,
            values,
            width,
            color=colours[i],
            edgecolor=BAR_EDGE,
            linewidth=BAR_EDGE_WIDTH,
            hatch=FLAT_HATCH if label in hatched else None,
            hatchcolor="#D9D9D9",
            yerr=errors,
            capsize=2,
            error_kw={"ecolor": ERROR_COLOUR, "elinewidth": 0.8, "capthick": 0.8},
        )
    ax.set_xticks(x)
    ax.set_xticklabels([DIFFICULTY_LABELS[d] for d in DIFFICULTIES])
    ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def main(
    models=MODELS,
    colours=MODEL_COLOURS,
    out_stem=OUT_STEM,
    legend_columns=4,
) -> int:
    """Render Figure 3 or S1 with identical estimators and plotting styles."""
    headline = read_headline()
    names = [label for label, _, _ in models]

    pass_by_diff, cost_by_diff = {}, {}
    estimated_mean_costs = {}
    flat_cost_usd = {k: v * GBP_TO_USD for k, v in FLAT_COST_GBP.items()}
    for label, _, _ in models:
        rows = read_task_summary(label)
        trials = read_trials(label)
        strict = strict_pass_by_task(trials)
        summary_tasks = {row["task_id"] for row in rows}
        if set(strict) != summary_tasks:
            sys.exit(f"{label}: trial and task-summary tables cover different tasks.")
        for row in rows:
            row[STRICT_COLUMN] = str(strict[row["task_id"]])
        reported = float(headline[label][STRICT_COLUMN])
        calculated = statistics.fmean(strict.values())
        if abs(calculated - reported) > 1e-12:
            sys.exit(
                f"{label}: calculated strict-pass@1 {calculated} does not match headline.csv {reported}."
            )
        pass_by_diff[label] = by_difficulty(rows, STRICT_COLUMN)
        if label in flat_cost_usd or label in TOKEN_PRICES_USD_PER_MILLION:
            prices = TOKEN_PRICES_USD_PER_MILLION.get(label, TOKEN_PRICE_WEIGHTS)
            estimated, estimated_mean_costs[label] = estimated_costs(
                trials, prices, flat_cost_usd.get(label)
            )
            for row in rows:
                row["estimated_cost_usd"] = str(estimated[row["task_id"]])
            cost_by_diff[label] = by_difficulty(rows, "estimated_cost_usd")
        else:
            cost_by_diff[label] = by_difficulty(rows, "mean_cost_usd")

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6))

    grouped_bars(
        axes[0], pass_by_diff, colours, "Average strict-pass@1 rate", set(), names
    )
    axes[0].set_ylim(0, 1.05)
    axes[0].set_yticks(np.arange(0, 1.01, 0.2))

    grouped_bars(
        axes[1],
        cost_by_diff,
        colours,
        "Average cost per trial (USD)",
        set(estimated_mean_costs),
        names,
    )
    axes[1].set_ylim(bottom=0)

    ax = axes[2]
    for (label, _, marker), colour in zip(models, colours):
        cost = estimated_mean_costs.get(label)
        if cost is None:
            raw = headline[label]["mean_cost_usd"]
            cost = float(raw) if raw else None
        if cost is None:
            continue
        ax.scatter(
            [cost],
            [float(headline[label]["strict_pass_at_1"])],
            marker=marker,
            s=110,
            color=colour,
            edgecolor=BAR_EDGE,
            linewidth=BAR_EDGE_WIDTH,
            zorder=3,
        )
    if COST_LOG_SCALE:
        ax.set_xscale("log")
        ax.set_xticks(COST_TICKS)
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.get_xaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Average cost per trial (USD)", fontsize=LABEL_SIZE)
    ax.set_ylabel("Average strict-pass@1 rate", fontsize=LABEL_SIZE)
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)

    # Match Figures 1 and 2's panel letters and fixed offsets in points.
    for axis, letter in zip(axes, "ABC"):
        axis.annotate(
            letter,
            xy=(0, 1),
            xycoords="axes fraction",
            xytext=(-22, 12),
            textcoords="offset points",
            fontsize=14,
            fontweight="bold",
            va="bottom",
            ha="left",
        )

    # Keep each model's marker, colour, and benchmark annotation together.
    handles = [
        Line2D(
            [],
            [],
            marker=marker,
            linestyle="none",
            markersize=8,
            markerfacecolor=colour,
            markeredgecolor=BAR_EDGE,
            markeredgewidth=BAR_EDGE_WIDTH,
            label=marked_name(label, name),
        )
        for colour, (label, name, marker) in zip(colours, models)
    ]
    if estimated_mean_costs:
        axes[1].legend(
            handles=[
                Patch(
                    facecolor="white",
                    edgecolor=BAR_EDGE,
                    linewidth=BAR_EDGE_WIDTH,
                    hatch=FLAT_HATCH,
                    label="Cost estimated from token counts",
                )
            ],
            loc="upper left",
            frameon=False,
            fontsize=8.5,
        )
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.10, LEGEND_TOP, 0.80, 0)
        if legend_columns == 3
        else (0.16, LEGEND_TOP, 0.68, 0),
        mode="expand",
        frameon=False,
        fontsize=8.5,
        ncols=legend_columns,
        handlelength=1.1,
        handletextpad=0.5,
        labelspacing=0.4,
        borderpad=0.0,
    )
    fig.tight_layout(rect=(0, AXES_BOTTOM, 1, 1), pad=LAYOUT_PAD)

    fig.savefig(f"{out_stem}.png", dpi=600, bbox_inches="tight", transparent=True)
    fig.savefig(f"{out_stem}.pdf", bbox_inches="tight", transparent=True)

    print(f"Read per-task tables for {len(models)} models from {TASK_SUMMARY_DIR}")
    for label, name, _ in models:
        cells = "  ".join(
            f"{DIFFICULTY_LABELS[d]} {pass_by_diff[label][d][0]:.2f}/{cost_by_diff[label][d][0]:.2f}"
            for d in DIFFICULTIES
        )
        print(f"  {name:<24} pass/cost  {cells}")
    for label, mean_cost in estimated_mean_costs.items():
        print(f"  {label}: mean estimated cost per trial USD {mean_cost:.3f}")
    print(f"Wrote {out_stem}.png and {out_stem}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
