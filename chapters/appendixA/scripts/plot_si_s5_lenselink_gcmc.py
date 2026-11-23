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
DATA_DIR = CHAPTER_DIR / "data/si_s5"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s5/regenerated"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s5"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


def plot_exp_vs_pred(
    df,
    err_color="black",
    err_alpha=0.8,
    err_linewidth=1.2,
    marker_color="black",
    marker_alpha=1.0,
    marker_size=30,
    cap_size=0,
    shading_dGs=None,
    shading_color="orange",
    save_name="exp_vs_pred_with_dg_shading.png",
    min=None,
    max=None,
    axis_fontsize=12,
    tick_fontsize=12,
    plot_stats=True,
    label=None,
):
    """
    Plot Experimental vs Predicted Delta G with the same shaded-band style used
    for the main exp-vs-ABFE figures.
    """

    rcParams["font.family"] = "Roboto"

    if shading_dGs is None:
        shading_dGs = [1, 2, 5]
    shading_dGs = sorted(shading_dGs)

    x = df["Experimental_G"].values
    y = df["Predicted_G"].values

    plt.figure(figsize=(4, 4))

    if min is not None and max is not None:
        min_val = min
        max_val = max
    else:
        min_val = min(min(x), min(y))
        max_val = max(max(x), max(y))
        pad = max(3.0, df["Experimental_Error"].max(), df["Predicted_Error"].max())
        min_val -= pad
        max_val += pad

    xs = np.linspace(min_val, max_val, 500)
    alphas = np.linspace(0.28, 0.07, len(shading_dGs))

    for dg, alpha in zip(shading_dGs, alphas):
        plt.fill_between(
            xs, xs - dg, xs + dg, color=shading_color, alpha=alpha, zorder=0
        )

    plt.plot(xs, xs, color="gray", linestyle="--", linewidth=1)

    plt.errorbar(
        x,
        y,
        xerr=df["Experimental_Error"],
        yerr=df["Predicted_Error"],
        fmt="none",
        ecolor=err_color,
        alpha=err_alpha,
        elinewidth=err_linewidth,
        capsize=cap_size,
        zorder=1,
    )

    plt.scatter(x, y, color=marker_color, alpha=marker_alpha, s=marker_size, zorder=2)

    if plot_stats:
        mue = mean_absolute_error(x, y)
        rmse = np.sqrt(mean_squared_error(x, y))
        r2 = r2_score(x, y)
        pearson_r, _ = pearsonr(x, y)
        spearman_r, _ = spearmanr(x, y)
        kendall_tau, _ = kendalltau(x, y)

        stats_text = (
            f"MUE = {mue:.2f}\n"
            f"RMSE = {rmse:.2f}\n"
            f"Pearson R = {pearson_r:.2f}\n"
            f"Spearman rho = {spearman_r:.2f}"
        )
        plt.text(
            0.05,
            0.95,
            stats_text,
            transform=plt.gca().transAxes,
            fontsize=12,
            verticalalignment="top",
            color="black",
            alpha=0.8,
        )

        stats_df = pd.DataFrame(
            [
                {
                    "MUE": mue,
                    "RMSE": rmse,
                    "R2": r2,
                    "Pearson_R": pearson_r,
                    "Spearman_rho": spearman_r,
                    "Kendall_tau": kendall_tau,
                    "n_ligands": len(df),
                    "n_replicates_used": int(df["n_replicates_used"].sum()),
                }
            ]
        )
        stats_df.to_csv(
            INTERMEDIATE_DIR / "lenselink_gcmc_exploratory_exp_vs_abfe_stats.csv",
            index=False,
        )

    plt.xlabel("Experimental Delta G (kcal/mol)", fontsize=axis_fontsize)
    plt.ylabel("Predicted Delta G (kcal/mol)", fontsize=axis_fontsize)

    if label is not None:
        plt.text(
            0.95,
            0.05,
            label,
            transform=plt.gca().transAxes,
            fontsize=14,
            horizontalalignment="right",
            verticalalignment="bottom",
            color="black",
            alpha=0.8,
        )

    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)

    tick_values = np.arange(np.floor(min_val), np.ceil(max_val) + 1, 2)
    plt.xticks(tick_values, fontsize=tick_fontsize)
    plt.yticks(tick_values, fontsize=tick_fontsize)

    plt.tight_layout()
    plt.savefig(save_name, dpi=600)
    plt.close()


def main():
    csv_path = DATA_DIR / "lenselink_gcmc_exploratory_w_stats.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} does not exist. Run s0_make_lenselink_gcmc_exp_v_abfe_df_w_stats.py first."
        )

    df = pd.read_csv(csv_path)
    plot_exp_vs_pred(
        df,
        err_color="grey",
        err_alpha=0.5,
        marker_color="#3594cc",
        marker_alpha=1.0,
        shading_dGs=[1, 2, 3, 5],
        shading_color="#f55f74",
        save_name=FIGURE_DIR
        / "exp_vs_pred_with_dg_shading_blue_lenselink_gcmc_exploratory_wstat_v3_label.svg",
        min=-17,
        max=-6,
        label="GCMC",
    )


if __name__ == "__main__":
    main()
