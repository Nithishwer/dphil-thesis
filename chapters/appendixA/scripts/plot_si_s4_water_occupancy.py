#!/usr/bin/env python3
"""Plot VDW-window binding-pocket resolvation from the generated CSV files."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s4"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s4/regenerated"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


ROOT = CHAPTER_DIR
OUT_DIR = FIGURE_DIR
SUMMARY_CSV = DATA_DIR / "all_datasets_vdw_water_occupancy_summary.csv"
APO_CSV = DATA_DIR / "all_datasets_apo_reference_means.csv"


def natural_key(value: object) -> list[object]:
    return [
        int(bit) if bit.isdigit() else bit for bit in re.split(r"(\d+)", str(value))
    ]


def setup_style() -> None:
    try:
        font_path = fm.findfont("Roboto")
        roboto_font = fm.FontProperties(fname=font_path)
        mpl.rcParams["font.family"] = roboto_font.get_name()
    except Exception:
        pass

    mpl.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 10,
            "axes.labelsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 8,
            "legend.title_fontsize": 5,
        }
    )


def expand_apo(summary: pd.DataFrame, apo: pd.DataFrame) -> pd.DataFrame:
    windows = (
        summary[["window", "window_index"]]
        .drop_duplicates()
        .sort_values("window_index")
    )
    rows = []
    for apo_row in apo.itertuples(index=False):
        for window in windows.itertuples(index=False):
            rows.append(
                {
                    "Compound": "apo",
                    "Repeat": str(apo_row.Repeat),
                    "window": window.window,
                    "window_index": int(window.window_index),
                    "occupancy": apo_row.occupancy,
                }
            )
    return pd.DataFrame(rows)


def apo_label_positions(
    apo: pd.DataFrame, ymax: float
) -> tuple[dict[str, float], float]:
    positions = {}
    gap = max(1.2, ymax * 0.055)
    last_y = -float("inf")
    for apo_row in sorted(apo.itertuples(index=False), key=lambda row: row.occupancy):
        y = max(apo_row.occupancy + ymax * 0.012, last_y + gap)
        positions[apo_row.apo_run] = y
        last_y = y
    return positions, max(ymax, last_y + gap)


def plot_dataset(
    summary: pd.DataFrame,
    apo: pd.DataFrame,
    output_stem: Path,
    title: str | None = None,
    show_legend: bool = True,
) -> None:
    plot_df = pd.concat([summary, expand_apo(summary, apo)], ignore_index=True)
    compounds = sorted(
        [compound for compound in plot_df["Compound"].unique() if compound != "apo"],
        key=natural_key,
    )
    palette = dict(zip(compounds, sns.color_palette("tab20", n_colors=len(compounds))))
    palette["apo"] = "gray"

    fig, ax = plt.subplots(figsize=(5, 5))
    sns.lineplot(
        data=plot_df.sort_values(["Compound", "Repeat", "window_index"]),
        x="window_index",
        y="occupancy",
        hue="Compound",
        style="Repeat",
        hue_order=compounds + ["apo"],
        palette=palette,
        estimator=None,
        linewidth=1.2,
        ax=ax,
        legend=show_legend,
    )

    ymax = max(14, plot_df["occupancy"].max() * 1.08)
    label_positions, ymax = apo_label_positions(apo, ymax)
    for apo_row in apo.itertuples(index=False):
        ax.text(
            0,
            label_positions[apo_row.apo_run],
            "Apo mean",
            color="gray",
            fontsize=8,
            ha="left",
            va="bottom",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.2},
        )

    if title:
        ax.set_title(title)
    ax.set_box_aspect(1)
    ax.set_xlabel("ABFE Window")
    ax.set_ylabel("Average Number of Binding Pocket Waters")
    ax.set_ylim(5, ymax)
    windows = (
        summary[["window", "window_index"]]
        .drop_duplicates()
        .sort_values("window_index")
    )
    ax.set_xticks(windows["window_index"])
    ax.set_xticklabels(windows["window"], rotation=90)

    if show_legend:
        ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1), frameon=False)

    fig.tight_layout()
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    fig.savefig(output_stem.with_suffix(".svg"))
    plt.close(fig)


def plot_all_datasets(
    loaded: list[tuple[str, str, pd.DataFrame, pd.DataFrame]],
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    for ax, (_, label, summary, apo) in zip(axes.flat, loaded):
        plot_df = pd.concat([summary, expand_apo(summary, apo)], ignore_index=True)
        compounds = sorted(
            [
                compound
                for compound in plot_df["Compound"].unique()
                if compound != "apo"
            ],
            key=natural_key,
        )
        palette = dict(
            zip(compounds, sns.color_palette("tab20", n_colors=len(compounds)))
        )
        palette["apo"] = "gray"
        sns.lineplot(
            data=plot_df.sort_values(["Compound", "Repeat", "window_index"]),
            x="window_index",
            y="occupancy",
            hue="Compound",
            style="Repeat",
            hue_order=compounds + ["apo"],
            palette=palette,
            estimator=None,
            linewidth=1.0,
            ax=ax,
            legend=False,
        )
        ymax = max(14, plot_df["occupancy"].max() * 1.08)
        label_positions, ymax = apo_label_positions(apo, ymax)
        for apo_row in apo.itertuples(index=False):
            ax.text(
                0,
                label_positions[apo_row.apo_run],
                "Apo mean",
                color="gray",
                fontsize=7,
                bbox={
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.85,
                    "pad": 0.2,
                },
            )
        windows = (
            summary[["window", "window_index"]]
            .drop_duplicates()
            .sort_values("window_index")
        )
        ax.set_title(label)
        ax.set_box_aspect(1)
        ax.set_xlabel("ABFE Window")
        ax.set_ylabel("Average Number of Binding Pocket Waters")
        ax.set_ylim(5, ymax)
        ax.set_xticks(windows["window_index"])
        ax.set_xticklabels(windows["window"], rotation=90)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "si_fig9_vdw_solvation_for_all_datasets.png", dpi=300)
    fig.savefig(OUT_DIR / "si_fig9_vdw_solvation_for_all_datasets.svg")
    plt.close(fig)


def main() -> None:
    setup_style()
    summary = pd.read_csv(SUMMARY_CSV)
    apo = pd.read_csv(APO_CSV)
    summary[["Compound", "Repeat", "dataset", "dataset_label"]] = summary[
        ["Compound", "Repeat", "dataset", "dataset_label"]
    ].astype(str)
    apo[["Repeat", "dataset", "dataset_label"]] = apo[
        ["Repeat", "dataset", "dataset_label"]
    ].astype(str)
    a2a_apo = apo[apo["dataset"] == "a2a_apo"]

    loaded = []
    for dataset, label in (
        summary[["dataset", "dataset_label"]].drop_duplicates().itertuples(index=False)
    ):
        dataset_summary = summary[summary["dataset"] == dataset]
        dataset_apo = (
            a2a_apo if label.endswith("A2A") else apo[apo["dataset"] == dataset]
        )
        loaded.append((dataset, label, dataset_summary, dataset_apo))
        plot_dataset(
            dataset_summary,
            dataset_apo,
            OUT_DIR / f"{dataset}_vdw_solvation_all_cmp",
            show_legend=True,
        )

    plot_all_datasets(loaded)


if __name__ == "__main__":
    main()
