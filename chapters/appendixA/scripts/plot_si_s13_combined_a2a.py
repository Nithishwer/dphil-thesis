#!/usr/bin/env python3
"""Pool A2A ABFE results and plot experimental vs predicted dG."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rcParams
from scipy.stats import kendalltau, pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s13"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s13/regenerated"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s13"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


HERE = Path(__file__).resolve().parent
PROJECT = DATA_DIR

INPUTS = {
    "Deflorian": DATA_DIR / "deflorian_w_stats.csv",
    "Lenselink": DATA_DIR / "lenselink_w_stats.csv",
    "Minetti": DATA_DIR / "minetti_w_stats.csv",
}
REQUIRED_COLUMNS = {
    "Lig_Name",
    "Experimental_G",
    "Predicted_G",
    "Predicted_Error",
    "Experimental_Error",
    "Dataset",
}
COLORS = {
    "Deflorian": "#0B62A4",
    "Lenselink": "#0F8B7A",
    "Minetti": "#5C3B8E",
}

COMBINED_CSV = INTERMEDIATE_DIR / "A2A_combined_with_na_w_stats.csv"
STATS_CSV = INTERMEDIATE_DIR / "A2A_combined_exp_vs_abfe_stats_summary.csv"
PLOT_SVG = FIGURE_DIR / "A2A_combined_exp_vs_pred_with_dg_shading.svg"
PLOT_PNG = FIGURE_DIR / "A2A_combined_exp_vs_pred_with_dg_shading.png"


def read_source(label: str, path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    df = df.copy()
    df["Source"] = label
    return df


def combined_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    x = df["Experimental_G"]
    y = df["Predicted_G"]
    return {
        "N": len(df),
        "MUE": mean_absolute_error(x, y),
        "RMSE": np.sqrt(mean_squared_error(x, y)),
        "R2": r2_score(x, y),
        "Pearson_R": pearsonr(x, y)[0],
        "Spearman_rho": spearmanr(x, y)[0],
        "Kendall_tau": kendalltau(x, y)[0],
    }


def plot_exp_vs_pred(df: pd.DataFrame, metrics: dict[str, float | int]) -> None:
    rcParams["font.family"] = "Roboto"

    fig, ax = plt.subplots(figsize=(4, 4))
    min_val, max_val = -18, -6
    xs = np.linspace(min_val, max_val, 500)

    for dg, alpha in zip([1, 2, 3, 5], np.linspace(0.28, 0.07, 4)):
        ax.fill_between(xs, xs - dg, xs + dg, color="#f55f74", alpha=alpha, zorder=0)

    ax.plot(xs, xs, color="gray", linestyle="--", linewidth=1)
    ax.errorbar(
        df["Experimental_G"],
        df["Predicted_G"],
        xerr=df["Experimental_Error"],
        yerr=df["Predicted_Error"],
        fmt="none",
        ecolor="grey",
        alpha=0.5,
        elinewidth=1.2,
        capsize=0,
        zorder=1,
    )

    for source, group in df.groupby("Source", sort=False):
        ax.scatter(
            group["Experimental_G"],
            group["Predicted_G"],
            color=COLORS[source],
            alpha=1.0,
            s=30,
            label=source,
            zorder=2,
        )

    stats_text = (
        f"MUE = {metrics['MUE']:.2f}\n"
        f"RMSE = {metrics['RMSE']:.2f}\n"
        f"Pearson R = {metrics['Pearson_R']:.2f}\n"
        f"Spearman rho = {metrics['Spearman_rho']:.2f}\n"
        f"Kendall tau = {metrics['Kendall_tau']:.2f}"
    )
    ax.text(
        0.05,
        0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        color="black",
        alpha=0.8,
    )
    ax.text(
        0.95,
        0.05,
        "A2A combined",
        transform=ax.transAxes,
        fontsize=14,
        horizontalalignment="right",
        verticalalignment="bottom",
        color="black",
        alpha=0.8,
    )

    ax.set_xlabel("Experimental ΔG (kcal/mol)", fontsize=12)
    ax.set_ylabel("Predicted ΔG (kcal/mol)", fontsize=12)
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ticks = np.arange(np.floor(min_val), np.ceil(max_val) + 1, 2)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(title="Dataset", loc="lower left", frameon=True)

    fig.tight_layout()
    fig.savefig(PLOT_SVG, dpi=600)
    fig.savefig(PLOT_PNG, dpi=600)
    plt.close(fig)


def main() -> None:
    combined = pd.concat(
        [read_source(label, path) for label, path in INPUTS.items()],
        ignore_index=True,
    )
    counts = combined["Source"].value_counts().to_dict()
    expected_counts = {"Deflorian": 10, "Lenselink": 7, "Minetti": 9}
    if counts != expected_counts or len(combined) != 26:
        raise ValueError(
            f"Unexpected A2A combined counts: {counts}, total={len(combined)}"
        )

    metrics = combined_metrics(combined)
    combined.to_csv(COMBINED_CSV, index=False)
    pd.DataFrame([metrics]).to_csv(STATS_CSV, index=False)
    plot_exp_vs_pred(combined, metrics)

    print(f"Wrote {COMBINED_CSV}")
    print(f"Wrote {STATS_CSV}")
    print(f"Wrote {PLOT_SVG}")


if __name__ == "__main__":
    main()
