#!/usr/bin/env python3
"""Figure 7.9: cohort medians and failure counts for five coding agents.

Medians are transcribed from the supplied excerpt; dispersion is not inferred.
Failure counts come from the chapter's per-trial tables, using Figure A1's
classification. Panel c excludes full passes and stacks the remaining outcomes.

Inputs: ../../data/trials/<model>.csv, relative to this figure folder.
Outputs: figure_7_9.{pdf,png,svg}, alongside this script.

Run with the thesis plotting environment: python /path/to/make_figure_7_9.py
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHAPTER = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent / "figure_7_9"
PASS_THRESHOLD = 0.999

# Each row contains the data label, model name, median calls and median minutes.
MODELS = [
    ("gpt-6-astra", "GPT-6 Astra", 12.5, 4.1),
    ("gpt-6.1-sol", "GPT-6.1 Sol", 14, 3.9),
    ("opus-5.5", "Claude Opus 5.5", 11, 2.0),
    ("gemini-4-argon", "Gemini 4 Argon", 53, 18.5),
    ("glm-5.2", "GLM-5.2", 35, 17.5),
]

ERROR_COLOURS = {
    "Failed evaluation": "#2a9d8f",  # Verdigris
    "Agent timeout": "#e9c46a",  # Jasmine
    "Other runtime error": "#e76f51",  # Burnt Peach
}


def failure_counts(label: str) -> Counter[str]:
    """Use the same mutually exclusive failure categories as Figure A1."""
    with (CHAPTER / "data/trials" / f"{label}.csv").open(newline="") as handle:
        trials = list(csv.DictReader(handle))
    if len(trials) != 150:
        raise ValueError(f"Expected 150 trials for {label}, found {len(trials)}")

    counts = Counter()
    for trial in trials:
        # A runtime error remains a failed delivery even if its artifacts score well.
        if trial["status"] == "error":
            outcome = (
                "Agent timeout"
                if trial["exception_type"] == "AgentTimeoutError"
                else "Other runtime error"
            )
            counts[outcome] += 1
        elif (
            float(trial["correctness"] or 0) < PASS_THRESHOLD
            or float(trial["process"] or 0) < PASS_THRESHOLD
        ):
            counts["Failed evaluation"] += 1
    return counts


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 8,
            "ytick.labelsize": 9,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    # Give panel C room for its legend while keeping the model rows aligned.
    fig, axes = plt.subplots(
        1, 3, sharey=True, figsize=(7.2, 3.0), width_ratios=[1, 1, 1.35]
    )
    fig.subplots_adjust(left=0.21, right=0.97, bottom=0.24, top=0.90, wspace=0.30)
    panels = [
        ("A", "Median tool calls\nper trial", 65, [0, 20, 40, 60]),
        ("B", "Median execution\ntime (min)", 24, [0, 10, 20]),
        ("C", "Failed trials\n(out of 150)", 150, [0, 50, 100, 150]),
    ]

    for ax, (letter, xlabel, maximum, ticks) in zip(axes, panels):
        ax.set(xlim=(0, maximum), ylim=(4.5, -0.5), xticks=ticks, xlabel=xlabel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#666666")
        ax.grid(False)
        ax.tick_params(axis="x", width=0.6, length=3, pad=4)
        ax.tick_params(axis="y", length=0, pad=9)
        ax.annotate(
            letter,
            xy=(0, 1),
            xycoords="axes fraction",
            xytext=(0, 8),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            va="bottom",
        )

    for ax, column in zip(axes[:2], [2, 3]):
        for row, model in enumerate(MODELS):
            value = model[column]
            ax.plot([0, value], [row, row], color="#999999", linewidth=1.1)
            ax.scatter(value, row, s=23, color="#333333", zorder=3)
            label = f"{value:g}" if column == 2 else f"{value:.1f}"
            ax.annotate(
                label,
                (value, row),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8.5,
                va="center",
            )

    counts = [failure_counts(model[0]) for model in MODELS]

    left = [0] * len(MODELS)
    for outcome, colour in ERROR_COLOURS.items():
        values = [count[outcome] for count in counts]
        axes[2].barh(
            range(len(MODELS)),
            values,
            left=left,
            height=0.5,
            color=colour,
            edgecolor="white",
            linewidth=0.4,
            label=outcome,
            zorder=3,
        )
        left = [base + value for base, value in zip(left, values)]

    for row, total in enumerate(left):
        axes[2].annotate(
            str(total),
            (total, row),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=8.5,
            va="center",
        )

    axes[2].legend(
        labels=["Evaluation", "Timeout", "Runtime error"],
        loc="upper right",
        frameon=False,
        fontsize=8,
        labelcolor="black",
        handlelength=1.2,
        handletextpad=0.5,
        borderaxespad=0.4,
        labelspacing=0.45,
    )
    axes[0].set_yticks(range(len(MODELS)), labels=[model[1] for model in MODELS])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "pdf", "svg"]:
        path = OUTPUT.with_suffix(f".{extension}")
        fig.savefig(path, dpi=600, facecolor="white")
        if extension == "svg":
            # Remove trailing spaces emitted by Matplotlib's SVG backend.
            path.write_text(
                "\n".join(line.rstrip() for line in path.read_text().splitlines())
                + "\n"
            )
    plt.close(fig)
    for model, count in zip(MODELS, counts):
        print(model[1], {outcome: count[outcome] for outcome in ERROR_COLOURS})
    print(f"Saved {OUTPUT}.{{png,pdf,svg}}")


if __name__ == "__main__":
    main()
