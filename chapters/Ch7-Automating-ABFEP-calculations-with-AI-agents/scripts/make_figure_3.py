#!/usr/bin/env python3
"""Figure 3 - strict-pass@1 over time and frontier-model reward scores.

Panel (a) reads strict-pass scores and 95% task-bootstrap intervals from the sibling
data/headline.csv. Panels (b) and (c) show mean correctness and process scores for
Opus-5.5, GPT-6.1 Sol, GPT-6 Astra, Gemini 4 Argon, and GLM-5.2, with the saved 95%
task-bootstrap intervals from data/metrics/. Colours identify OpenAI, Anthropic,
Google, and one shared openweight group; shapes in (a) use the user-defined model
classes. Each point is labelled, with colour and class legends inside the top left.
Horizontal reward bars are stacked to the right of (a), with (b) above (c).
The empty interval between the July 2025 Qwen releases and DeepSeek's December
2025 release is omitted; the date windows use the same scale and share one y-axis.

Release dates are frozen below with source URLs. OpenAI dates use the API
release changelog: GPT-5.5 became available in the API on 24 April, and GPT-5.6
launched on 9 July after its limited June preview. Gemini 4 Argon uses its
13 October developer launch after limited September access. Dates describe model
releases, not benchmark execution times. Fable has no score and is not plotted.
Daggers identify the six v0.1.0 runs, which have one attempt per task and different
task definitions and grading from the later runs with three attempts per task.
Superscript stars identify the seven v0.2 configurations.

Run from any directory with the MDArena analysis Python environment:
    python make_figure_3.py

Edit LABEL_OFFSETS below to position each model's text relative to its dot,
then rerun this script to update the figure.

Writes figure_3.png (600 dpi) and figure_3.pdf into the chapter figures folder.
"""

from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.transforms import Bbox
from benchmark_versions import marked_name

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_3"

HEADLINE_CSV = CHAPTER / "data/headline.csv"
METRICS_DIR = CHAPTER / "data/metrics"
OUT_STEM = HERE / "figure_3"
EARLY_MODELS = {"qwen3-coder-480b", "qwen3-235b-a22b-instruct-2507"}

# (CSV label, display name, colour group, class, release date).
MODELS = [
    ("gpt-5.5-medium", "GPT-5.5 Medium", "OpenAI", "sol_opus", "2026-04-24"),
    ("gpt-5.5-xhigh", "GPT-5.5 XHigh", "OpenAI", "sol_opus", "2026-04-24"),
    ("gpt-5.6-terra", "GPT-5.6 Terra", "OpenAI", "terra_sonnet", "2026-07-09"),
    ("gpt-5.6-sol", "GPT-5.6 Sol", "OpenAI", "sol_opus", "2026-07-09"),
    ("gpt-6.1-sol", "GPT-6.1 Sol", "OpenAI", "sol_opus", "2026-09-29"),
    ("gpt-6-astra", "GPT-6 Astra", "OpenAI", "astra_fable", "2026-09-03"),
    ("sonnet-5", "Claude Sonnet-5", "Anthropic", "terra_sonnet", "2026-06-30"),
    ("opus-5", "Claude Opus-5", "Anthropic", "sol_opus", "2026-07-24"),
    ("opus-5.5", "Claude Opus-5.5", "Anthropic", "sol_opus", "2026-09-22"),
    ("gemini-3.7-flash", "Gemini 3.7 Flash", "Google", "terra_sonnet", "2026-08-13"),
    ("gemini-4-argon", "Gemini 4\nArgon", "Google", "sol_opus", "2026-10-13"),
    ("gemini-3.5-flash", "Gemini 3.5 Flash", "Google", "terra_sonnet", "2026-05-19"),
    (
        "gemini-3.1-pro-preview",
        "Gemini 3.1 Pro\nPreview",
        "Google",
        "sol_opus",
        "2026-02-19",
    ),
    ("glm-5.2", "GLM-5.2", "Openweight", "sol_opus", "2026-06-16"),
    ("deepseek-v3.2", "DeepSeek-V3.2", "Openweight", "sol_opus", "2025-12-01"),
    (
        "deepseek-v4",
        "DeepSeek-V4.1 Flash",
        "Openweight",
        "sol_opus",
        "2026-09-10",
    ),
    (
        "qwen3-coder-480b",
        "Qwen3 Coder\n480B A35B",
        "Openweight",
        "sol_opus",
        "2025-07-22",
    ),
    (
        "qwen3-235b-a22b-instruct-2507",
        "Qwen3 Instruct\n235B A22B (2507)",
        "Openweight",
        "sol_opus",
        "2025-07-21",
    ),
]

# Keep the same frontier-model order in both reward panels.
FRONTIER_MODELS = [
    ("opus-5.5", "Claude Opus-5.5", "Anthropic"),
    ("gpt-6-astra", "GPT-6 Astra", "OpenAI"),
    ("gpt-6.1-sol", "GPT-6.1 Sol", "OpenAI"),
    ("gemini-4-argon", "Gemini 4 Argon", "Google"),
    ("glm-5.2", "GLM-5.2", "Openweight"),
]

# Size-based plotting convention: GLM-5.2 is about 753B parameters and Qwen is
# 480B total / 35B active. This does not establish parameter matching to Terra/Sol.
# https://huggingface.co/zai-org/GLM-5.2
# https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct
# Pro, DeepSeek, and both Qwen models use the Sol/Opus circle convention.
# GPT-5.5 Medium and XHigh are reasoning settings of the same model, so both
# retain that class rather than implying a model-size difference.

RELEASE_SOURCES = {
    "OpenAI models": "https://developers.openai.com/api/docs/changelog",
    "Claude Sonnet-5": "https://www.anthropic.com/news/claude-sonnet-5",
    "Claude Opus-5": "https://www.anthropic.com/news/claude-opus-5",
    "Claude Opus-5.5": "https://www.anthropic.com/claude-opus-5-5",
    "Gemini 3.7 Flash": (
        "https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/"
    ),
    "Gemini 4 Argon": "https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-4-argon/",
    "Gemini 3.5 Flash": "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5/",
    "Gemini 3.1 Pro Preview": (
        "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/"
    ),
    "GLM-5.2": "https://www.nist.gov/news-events/news/2026/07/caisi-assessment-zais-glm-52",
    "DeepSeek-V3.2": "https://api-docs.deepseek.com/news/news251201/",
    "DeepSeek-V4.1 Flash": "https://api-docs.deepseek.com/news/news260910/",
    "Qwen3 Coder 480B A35B": "https://qwenlm.github.io/blog/qwen3-coder/",
    "Qwen3 Instruct 235B A22B (2507)": "https://github.com/QwenLM/Qwen3#news",
}

GROUP_COLOURS = {
    "OpenAI": "#43AA8B",
    "Anthropic": "#F3722C",
    "Google": "#F9C74F",
    "Openweight": "#577590",
}
CLASS_MARKERS = {
    "terra_sonnet": "s",
    "sol_opus": "o",
    "astra_fable": "*",
}
CLASS_LABELS = {
    "terra_sonnet": "Tier 1",
    "sol_opus": "Tier 2",
    "astra_fable": "Tier 3",
}

# Edit these values to move each model's label relative to its dot, then rerun.
# Each tuple is (x_offset, y_offset, horizontal_alignment, vertical_alignment).
# Offsets are in points (1 point = 1/72 inch), independent of the axis scales:
#   x_offset: positive moves right; negative moves left.
#   y_offset: positive moves up; negative moves down.
# Alignment chooses the text edge placed at that offset:
#   horizontal: "left", "center", "right"; vertical: "top", "center", "bottom".
# Example: (15, -10, "left", "top") places the label's top-left corner
# 15 points right and 10 points below its dot. Only the text moves.
LABEL_OFFSETS = {
    "gpt-5.5-medium": (-15, -40, "center", "top"),
    "gpt-5.5-xhigh": (-12, 24, "right", "bottom"),
    "gpt-5.6-terra": (-20, 20, "right", "bottom"),
    "gpt-5.6-sol": (-30, 12, "right", "bottom"),
    "gpt-6.1-sol": (20, 20, "left", "top"),
    "gpt-6-astra": (-12, 38, "right", "bottom"),
    "sonnet-5": (8, -28, "left", "top"),
    "opus-5": (20, 40, "right", "bottom"),
    "opus-5.5": (-20, 24, "left", "bottom"),
    "gemini-3.7-flash": (10, -12, "left", "top"),
    "gemini-4-argon": (10, 5, "left", "bottom"),
    "gemini-3.5-flash": (10, -14, "left", "top"),
    "gemini-3.1-pro-preview": (-14, 12, "right", "bottom"),
    "glm-5.2": (-10, -8, "right", "top"),
    "deepseek-v3.2": (10, 16, "left", "bottom"),
    "deepseek-v4": (-10, -22, "right", "top"),
    "qwen3-coder-480b": (0, 20, "center", "bottom"),
    "qwen3-235b-a22b-instruct-2507": (20, 82, "center", "bottom"),
}

BAR_EDGE = "#7A7A7A"
BAR_EDGE_WIDTH = 0.7
LABEL_SIZE = 11


def read_headline() -> dict[str, dict[str, str]]:
    if not HEADLINE_CSV.is_file():
        sys.exit(f"No headline CSV at {HEADLINE_CSV}.")
    with HEADLINE_CSV.open() as stream:
        records = list(csv.DictReader(stream))
    rows = {row["model"]: row for row in records}
    if len(rows) != len(records):
        sys.exit(f"Duplicate model rows in {HEADLINE_CSV}.")
    expected = {model[0] for model in MODELS}
    if set(rows) != expected:
        sys.exit(
            "Headline models and release-date metadata differ. "
            f"Missing scores: {sorted(expected - set(rows))}; "
            f"missing release metadata: {sorted(set(rows) - expected)}."
        )
    for label, row in rows.items():
        score, low, high = (
            float(row[column])
            for column in ("strict_pass_at_1", "strict_ci_low", "strict_ci_high")
        )
        if not 0 <= low <= score <= high <= 1:
            sys.exit(f"{label}: invalid strict-pass score or confidence interval.")
    return rows


def read_reward_metrics() -> dict[str, dict[str, tuple[float, float, float]]]:
    """Read saved task means and bootstrap intervals for the frontier models."""
    metrics = {}
    for label, _, _ in FRONTIER_MODELS:
        path = METRICS_DIR / f"{label}.csv"
        with path.open() as stream:
            rows = {row["metric"]: row for row in csv.DictReader(stream)}
        metrics[label] = {}
        for metric in ("mean correctness", "mean process"):
            row = rows[metric]
            score, low, high = (
                float(row[column]) for column in ("value", "ci_low", "ci_high")
            )
            if not 0 <= low <= score <= high <= 1:
                sys.exit(f"{label}: invalid {metric} score or confidence interval.")
            metrics[label][metric] = (score, low, high)
    return metrics


def draw_reward_panel(ax, metrics, metric: str, xlabel: str) -> None:
    """Plot one bar per frontier model, using the provider colours from (a)."""
    bar_spacing = 0.65
    for index, (label, display, group) in enumerate(FRONTIER_MODELS):
        position = index * bar_spacing
        score, low, high = metrics[label][metric]
        ax.barh(
            position,
            score,
            height=0.42,
            color=GROUP_COLOURS[group],
            edgecolor=BAR_EDGE,
            linewidth=BAR_EDGE_WIDTH,
            xerr=[[score - low], [high - score]],
            capsize=3,
            error_kw={"ecolor": "#222222", "elinewidth": 0.9},
        )
        ax.text(
            0.025,
            position,
            marked_name(label, display),
            ha="left",
            va="center",
            fontsize=9,
            color="white" if label == "glm-5.2" else "black",
        )
        ax.text(
            high + 0.02, position, f"{score:.3f}", ha="left", va="center", fontsize=8
        )
    ax.set_yticks([])
    ax.set_ylim((len(FRONTIER_MODELS) - 1) * bar_spacing + 0.4, -0.4)
    ax.set_xlim(0, 1.18)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel(xlabel, fontsize=LABEL_SIZE)
    ax.set_ylabel("Models", fontsize=LABEL_SIZE)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def main() -> int:
    headline = read_headline()
    reward_metrics = read_reward_metrics()
    # Embed TrueType fonts so the PDF retains scalable, editable text.
    plt.rcParams["pdf.fonttype"] = 42
    release_dates = {
        label: date.fromisoformat(released) for label, _, _, _, released in MODELS
    }
    qwen_dates = [release_dates[label] for label in EARLY_MODELS]
    recent_dates = [
        released
        for label, released in release_dates.items()
        if label not in EARLY_MODELS
    ]
    date_windows = [
        (min(qwen_dates) - timedelta(days=35), max(qwen_dates) + timedelta(days=35)),
        (
            min(recent_dates) - timedelta(days=20),
            max(recent_dates) + timedelta(days=45),
        ),
    ]
    # Stack the horizontal reward panels to the right of the broken-axis plot.
    fig = plt.figure(figsize=(14, 5.5))
    panels = fig.add_gridspec(
        1,
        2,
        width_ratios=[2, 0.7],
        wspace=0.12,
        left=0.055,
        right=0.99,
        top=0.92,
        bottom=0.19,
    )
    release_panels = panels[0].subgridspec(
        1,
        2,
        wspace=0.06,
        width_ratios=[(end - start).days for start, end in date_windows],
    )
    qwen_ax = fig.add_subplot(release_panels[0])
    recent_ax = fig.add_subplot(release_panels[1], sharey=qwen_ax)
    reward_panels = panels[1].subgridspec(2, 1, hspace=0.65)
    correctness_ax = fig.add_subplot(reward_panels[0])
    process_ax = fig.add_subplot(reward_panels[1])
    # Match Figure 1's panel letters and fixed offsets in points.
    for ax, letter in ((qwen_ax, "A"), (correctness_ax, "B"), (process_ax, "C")):
        ax.annotate(
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

    draw_reward_panel(
        correctness_ax, reward_metrics, "mean correctness", "Average correctness score"
    )
    draw_reward_panel(
        process_ax, reward_metrics, "mean process", "Average process score"
    )

    for label, display, group, model_class, released in MODELS:
        released = release_dates[label]
        ax = qwen_ax if label in EARLY_MODELS else recent_ax
        row = headline[label]
        score = float(row["strict_pass_at_1"])
        low, high = float(row["strict_ci_low"]), float(row["strict_ci_high"])
        colour = GROUP_COLOURS[group]
        marker = CLASS_MARKERS[model_class]
        ax.errorbar(
            released,
            score,
            yerr=[[score - low], [high - score]],
            fmt="none",
            ecolor=colour,
            elinewidth=0.9,
            capsize=3,
            alpha=0.65,
            zorder=2,
        )
        ax.scatter(
            [released],
            [score],
            s=145 if marker == "*" else 85,
            marker=marker,
            color=colour,
            edgecolor=BAR_EDGE,
            linewidth=BAR_EDGE_WIDTH,
            zorder=3,
        )
        dx, dy, horizontal, vertical = LABEL_OFFSETS[label]
        ax.annotate(
            marked_name(label, display),
            xy=(mdates.date2num(released), score),
            xytext=(dx, dy),
            textcoords="offset points",
            ha=horizontal,
            va=vertical,
            fontsize=9,
            color="#222222",
            arrowprops={
                "arrowstyle": "-",
                "color": BAR_EDGE,
                "lw": 0.6,
                # Route the longer Qwen leader around the other Qwen label.
                "connectionstyle": (
                    "arc3,rad=-0.9"
                    if label == "qwen3-235b-a22b-instruct-2507"
                    else "arc3"
                ),
            },
        )

    for ax, limits in zip((qwen_ax, recent_ax), date_windows):
        ax.set_xlim(*limits)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
        ax.set_ylim(0, 1.1)
        ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.tick_params(axis="both", labelsize=9)
        ax.grid(axis="y", alpha=0.25, linewidth=0.6)
        ax.set_axisbelow(True)
    qwen_ax.set_xticks([min(qwen_dates)])
    recent_ax.xaxis.set_major_locator(mdates.MonthLocator())
    qwen_ax.set_ylabel("Average strict-pass@1 rate", fontsize=LABEL_SIZE)
    recent_ax.tick_params(axis="y", left=False, labelleft=False)
    qwen_ax.spines["right"].set_visible(False)
    recent_ax.spines["left"].set_visible(False)
    release_bounds = panels[0].get_position(fig)
    fig.text(
        (release_bounds.x0 + release_bounds.x1) / 2,
        0.04,
        "Model release date",
        ha="center",
        fontsize=LABEL_SIZE,
    )

    # Diagonal marks make the omitted date interval explicit. Marker sizes are
    # in points, so the slashes match despite the unequal panel widths.
    for ax, edge in ((qwen_ax, 1), (recent_ax, 0)):
        ax.plot(
            [edge, edge],
            [0, 1],
            transform=ax.transAxes,
            linestyle="none",
            marker=[(-1, -0.6), (1, 0.6)],
            markersize=10,
            color=BAR_EDGE,
            markeredgewidth=1,
            clip_on=False,
        )

    model_legend = fig.legend(
        handles=[
            Patch(
                facecolor=colour,
                edgecolor=BAR_EDGE,
                linewidth=BAR_EDGE_WIDTH,
                label=group,
            )
            for group, colour in GROUP_COLOURS.items()
        ],
        title="Model group\n",
        loc="upper left",
        bbox_to_anchor=(0.08, 0.97),
        bbox_transform=qwen_ax.transAxes,
        ncol=1,
        frameon=False,
        fontsize=9.5,
        title_fontsize=9.5,
        handlelength=1.1,
        handletextpad=0.5,
    )
    class_legend = fig.legend(
        handles=[
            Line2D(
                [],
                [],
                marker=marker,
                linestyle="none",
                markersize=8,
                markerfacecolor="#777777",
                markeredgecolor=BAR_EDGE,
                label=CLASS_LABELS[model_class],
            )
            for model_class, marker in CLASS_MARKERS.items()
        ],
        title="Class\n",
        loc="upper left",
        bbox_to_anchor=(1.26, 0.97),
        bbox_transform=qwen_ax.transAxes,
        ncol=1,
        frameon=False,
        fontsize=9.5,
        title_fontsize=9.5,
        handlelength=1.1,
        handletextpad=0.5,
    )

    for legend in (model_legend, class_legend):
        legend.get_title().set_linespacing(0.8)

    # Put one padded, opaque background beneath both legend columns.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend_bounds = Bbox.union(
        [
            model_legend.get_window_extent(renderer),
            class_legend.get_window_extent(renderer),
        ]
    ).padded(renderer.points_to_pixels(3))
    legend_bounds = legend_bounds.transformed(fig.transFigure.inverted())
    fig.add_artist(
        Rectangle(
            (legend_bounds.x0, legend_bounds.y0),
            legend_bounds.width,
            legend_bounds.height,
            transform=fig.transFigure,
            facecolor="white",
            edgecolor="#D3D3D3",
            linewidth=0.8,
            zorder=4,
        )
    )
    fig.savefig(f"{OUT_STEM}.png", dpi=600, bbox_inches="tight", transparent=True)
    fig.savefig(f"{OUT_STEM}.pdf", bbox_inches="tight", transparent=True)

    print(f"Read {len(MODELS)} models from {HEADLINE_CSV}")
    for label, display, group, model_class, released in MODELS:
        display = display.replace("\n", " ")
        print(
            f"  {display:<24} {released}  strict={float(headline[label]['strict_pass_at_1']):.1%}"
            f"  {group}; {CLASS_LABELS[model_class]}"
        )
    print(f"Wrote {OUT_STEM}.png and {OUT_STEM}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
