"""Plot available Deflorian OX2 set 1 results with and without sodium."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data" / "figure_3_5"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts" / "intermediates" / "figure_3_5"
FIGURE_DIR = CHAPTER_DIR / "figures" / "figure_3_5"
CONDITIONS = {"without_na": "Without Na+", "with_na": "With Na+"}


def summarize(repeats, method):
    """Average available repeats, keeping wholly missing compounds in the table."""
    return (
        repeats.groupby(["Condition", "Compound"], sort=False)
        .agg(
            Experimental_G=("Experimental_G", "first"),
            Experimental_Error=("Experimental_Error", "first"),
            Predicted_G=(method, "mean"),
            Predicted_Error=(method, "std"),
            N_repeats=(method, "count"),
        )
        .reset_index()
    )


def statistics(points):
    x = points["Experimental_G"].to_numpy()
    y = points["Predicted_G"].to_numpy()
    result = {
        "N_compounds": len(points),
        "MUE": np.nan,
        "RMSE": np.nan,
        "Pearson_R": np.nan,
        "Spearman_rho": np.nan,
    }
    if len(points):
        result.update(MUE=np.mean(np.abs(y - x)), RMSE=np.sqrt(np.mean((y - x) ** 2)))
    if len(points) > 1 and np.ptp(x) > 0 and np.ptp(y) > 0:
        result.update(
            Pearson_R=pearsonr(x, y).statistic, Spearman_rho=spearmanr(x, y).statistic
        )
    return result


def plot_panel(axis, points, label, limits, stats):
    xs = np.linspace(*limits, 500)
    for width, alpha in zip((1, 2, 3, 5), np.linspace(0.28, 0.07, 4)):
        axis.fill_between(
            xs, xs - width, xs + width, color="#f55f74", alpha=alpha, zorder=0
        )
    axis.plot(xs, xs, color="gray", linestyle="--", linewidth=1)
    axis.errorbar(
        points["Experimental_G"],
        points["Predicted_G"],
        xerr=points["Experimental_Error"],
        fmt="none",
        ecolor="grey",
        alpha=0.5,
        elinewidth=1.2,
        zorder=1,
    )
    # A single repeat has no sample SD, but its mean still belongs on the plot.
    repeated = points.dropna(subset=["Predicted_Error"])
    axis.errorbar(
        repeated["Experimental_G"],
        repeated["Predicted_G"],
        yerr=repeated["Predicted_Error"],
        fmt="none",
        ecolor="grey",
        alpha=0.5,
        elinewidth=1.2,
        zorder=1,
    )
    axis.scatter(
        points["Experimental_G"], points["Predicted_G"], color="#3594cc", s=30, zorder=2
    )
    if len(points):
        lines = []
        for name, key in (
            ("MUE", "MUE"),
            ("RMSE", "RMSE"),
            ("Pearson R", "Pearson_R"),
            ("Spearman ρ", "Spearman_rho"),
        ):
            value = stats[key]
            lines.append(
                f"{name} = {value:.2f}" if np.isfinite(value) else f"{name} = NA"
            )
        axis.text(
            0.05,
            0.95,
            "\n".join(lines),
            transform=axis.transAxes,
            va="top",
            fontsize=12,
            alpha=0.8,
        )
    else:
        axis.text(
            0.5, 0.5, "No results available", transform=axis.transAxes, ha="center"
        )
    axis.text(
        0.95,
        0.05,
        label,
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=14,
        alpha=0.8,
    )
    axis.set(
        xlim=limits,
        ylim=limits,
        aspect="equal",
        xlabel="Experimental ΔG (kcal/mol)",
        ylabel="Predicted ΔG (kcal/mol)",
    )
    ticks = np.arange(limits[0], limits[1] + 0.1, 2)
    axis.set_xticks(ticks)
    axis.set_yticks(ticks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("MBAR", "BAR", "TI"), default="MBAR")
    args = parser.parse_args()
    repeats = pd.read_csv(DATA_DIR / "deflorian_set1_repeats.csv")
    summary = summarize(repeats, args.method)
    available = summary.dropna(subset=["Experimental_G", "Predicted_G"])

    # Share limits across panels and include the full extent of available error bars.
    limits = [-20, -3]
    if len(available):
        x, y = available["Experimental_G"], available["Predicted_G"]
        xerr = available["Experimental_Error"]
        yerr = available["Predicted_Error"].fillna(0)
        limits = [
            min(-20, 2 * np.floor(min((x - xerr).min(), (y - yerr).min()) / 2)),
            max(-3, 2 * np.ceil(max((x + xerr).max(), (y + yerr).max()) / 2)),
        ]

    # Preserve Roboto outlines in SVGs, matching the other chapter plots.
    plt.rcParams.update(
        {"font.family": "Roboto", "font.size": 12, "svg.fonttype": "path"}
    )
    figure, axes = plt.subplots(1, 2, figsize=(9, 4.8), layout="constrained")
    stats_rows = []
    for letter, axis, (condition, label) in zip("ab", axes, CONDITIONS.items()):
        points = available[available["Condition"] == condition]
        stats = statistics(points)
        stats_rows.append({"Condition": condition, "Method": args.method, **stats})
        plot_panel(axis, points, label, limits, stats)
        axis.text(-0.2, 1.06, f"{letter}.", transform=axis.transAxes, fontsize=22)

    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(
        INTERMEDIATE_DIR / f"deflorian_set1_{args.method}_w_stats.csv",
        index=False,
        na_rep="NA",
    )
    pd.DataFrame(stats_rows).to_csv(
        INTERMEDIATE_DIR / f"statistics_{args.method}.csv", index=False, na_rep="NA"
    )
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for extension in ("svg", "pdf"):
        output = FIGURE_DIR / f"figure_3_5_{args.method}.{extension}"
        figure.savefig(output, dpi=600)
        print(output)
    plt.close(figure)


if __name__ == "__main__":
    main()
