#!/usr/bin/env python3
"""Plot published SI Figure S8: PCA overlap across four datasets."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s8"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s8/regenerated"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s8"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


OUT = FIGURE_DIR
DATASETS = [
    ("lenselink", "Lenselink A2A"),
    ("kumar", "Kumar D3"),
    ("christopher", "Christopher mGlu5"),
    ("minetti", "Minetti A2A"),
]
STATE_ORDER = ["apo", "vdw.20", "holo"]
HIST_BINS = 60
PSEUDOCOUNT = 1e-12
COLORS = {
    "apo": "#E69F00",
    "vdw.20": "#0072B2",
    "holo": "#009E73",
}
LABEL_OFFSETS = {
    "apo": (0, -14),
    "vdw.20": (0, 14),
    "holo": (18, 0),
}


def load_projection(dataset: str) -> pd.DataFrame:
    path = DATA_DIR / f"{dataset}_pca_projection.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing projection CSV: {path}")
    table = pd.read_csv(path)
    if table.empty:
        raise ValueError(f"{path} is empty")
    missing = set(STATE_ORDER) - set(table["state"])
    if missing:
        raise ValueError(f"{dataset} is missing states: {sorted(missing)}")
    return table


def probability(points: np.ndarray, ranges: list[tuple[float, float]]) -> np.ndarray:
    hist, _, _ = np.histogram2d(
        points[:, 0], points[:, 1], bins=HIST_BINS, range=ranges
    )
    prob = hist.ravel()
    return prob / prob.sum()


def jensen_shannon_divergence(first: np.ndarray, second: np.ndarray) -> float:
    first = first + PSEUDOCOUNT
    second = second + PSEUDOCOUNT
    first = first / first.sum()
    second = second / second.sum()
    midpoint = 0.5 * (first + second)
    return float(
        0.5
        * (
            np.sum(first * np.log2(first / midpoint))
            + np.sum(second * np.log2(second / midpoint))
        )
    )


def vdw20_apo_not_holo_metrics(table: pd.DataFrame) -> dict[str, float]:
    apo = table.loc[table["state"] == "apo", ["PC1", "PC2"]].to_numpy()
    holo = table.loc[table["state"] == "holo", ["PC1", "PC2"]].to_numpy()
    vdw20 = table.loc[table["state"] == "vdw.20", ["PC1", "PC2"]].to_numpy()
    combined = np.vstack([apo, holo, vdw20])
    ranges = []
    for column in range(2):
        low = float(combined[:, column].min())
        high = float(combined[:, column].max())
        if low == high:
            low -= 0.5
            high += 0.5
        ranges.append((low, high))

    apo_prob = probability(apo, ranges)
    holo_prob = probability(holo, ranges)
    vdw_prob = probability(vdw20, ranges)
    apo_not_holo = np.clip(apo_prob - holo_prob, 0, None)
    apo_not_holo_mass = apo_not_holo.sum()
    if apo_not_holo_mass <= 0:
        raise ValueError("No apo density remains after subtracting holo overlap")

    apo_not_holo_prob = apo_not_holo / apo_not_holo_mass
    jsd = jensen_shannon_divergence(vdw_prob, apo_not_holo_prob)
    overlap = np.minimum(vdw_prob, apo_not_holo).sum() * 100
    return {
        "jsd": float(jsd),
        "overlap_percent": float(overlap),
        "apo_not_holo_percent": float(apo_not_holo_mass * 100),
        "n_apo": int(len(apo)),
        "n_holo": int(len(holo)),
        "n_vdw20": int(len(vdw20)),
    }


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 7.4))
    axes = axes.ravel()

    legend_handles = {}
    metrics_rows = []
    for ax, (dataset, title) in zip(axes, DATASETS):
        table = load_projection(dataset)
        metrics = vdw20_apo_not_holo_metrics(table)
        metrics_rows.append({"dataset": dataset, "title": title, **metrics})

        for state in STATE_ORDER:
            group = table[table["state"] == state]
            scatter = ax.scatter(
                group["PC1"],
                group["PC2"],
                s=10,
                alpha=0.75,
                linewidths=0,
                color=COLORS[state],
                label=state,
                rasterized=True,
            )
            legend_handles[state] = scatter
            ax.annotate(
                state,
                xy=(group["PC1"].median(), group["PC2"].median()),
                xytext=LABEL_OFFSETS[state],
                textcoords="offset points",
                color=COLORS[state],
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=5,
                bbox={
                    "boxstyle": "round,pad=0.18",
                    "facecolor": "white",
                    "edgecolor": COLORS[state],
                    "alpha": 0.85,
                    "linewidth": 0.8,
                },
            )

        ax.text(
            0.02,
            0.98,
            "vdw.20 vs apo\n"
            f"JSD={metrics['jsd']:.2f}\n"
            f"Overlap={metrics['overlap_percent']:.0f}%",
            transform=ax.transAxes,
            fontsize=8,
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "0.35",
                "alpha": 0.85,
                "linewidth": 0.6,
            },
        )
        ax.set_title(f"{title}", fontsize=11)
        ax.set_xlabel("PC1", fontsize=10)
        ax.set_ylabel("PC2", fontsize=10)
        ax.tick_params(labelsize=8)

    fig.subplots_adjust(
        left=0.08, right=0.98, top=0.95, bottom=0.09, hspace=0.34, wspace=0.22
    )
    fig.legend(
        [legend_handles[state] for state in STATE_ORDER],
        STATE_ORDER,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=3,
        frameon=False,
    )
    pd.DataFrame(metrics_rows).to_csv(
        INTERMEDIATE_DIR / "si_fig12_apo_vdw20_overlap_metrics.csv", index=False
    )
    fig.savefig(OUT / "si_fig12_pca_apo_vdw20_holo.png", dpi=300)
    fig.savefig(OUT / "si_fig12_pca_apo_vdw20_holo.pdf")
    print(f"wrote {OUT / 'si_fig12_apo_vdw20_overlap_metrics.csv'}")
    print(f"wrote {OUT / 'si_fig12_pca_apo_vdw20_holo.png'}")
    print(f"wrote {OUT / 'si_fig12_pca_apo_vdw20_holo.pdf'}")


if __name__ == "__main__":
    main()
