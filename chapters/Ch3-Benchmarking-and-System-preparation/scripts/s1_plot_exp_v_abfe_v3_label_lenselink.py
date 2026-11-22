from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.stats import kendalltau, pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data" / "allosteric_sodium"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts" / "intermediates" / "allosteric_sodium"
FIGURE_DIR = CHAPTER_DIR / "figures" / "allosteric_sodium"


def plot_exp_vs_pred(
    df,
    err_color="black",
    err_alpha=0.8,
    err_lidewidth=1.2,
    marker_color="black",
    marker_alpha=1.0,
    marker_size=30,
    cap_size=0,
    shading_dGs=None,
    shading_color="orange",
    save_name="exp_vs_pred_with_dg_shading.png",
    min=None,
    max=None,
    title_fontsize=12,
    axis_fontsize=12,
    tick_fontsize=12,
    plot_stats: bool = True,
    label: str = None,  # ✅ NEW
):
    """
    Plots Experimental vs Predicted ΔG with:
    - error bars
    - diagonal shaded regions for ΔG thresholds
    - optional statistics overlay if plot_stats=True
    """

    # Set Roboto font globally
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

    base_alpha = 0.28
    alphas = np.linspace(base_alpha, 0.07, len(shading_dGs))

    # Shading
    for dg, alpha in zip(shading_dGs, alphas):
        upper = xs + dg
        lower = xs - dg
        plt.fill_between(xs, lower, upper, color=shading_color, alpha=alpha, zorder=0)

    # Identity line
    plt.plot(xs, xs, color="gray", linestyle="--", linewidth=1)

    # Error bars
    plt.errorbar(
        x,
        y,
        xerr=df["Experimental_Error"],
        yerr=df["Predicted_Error"],
        fmt="none",
        ecolor=err_color,
        alpha=err_alpha,
        elinewidth=err_lidewidth,
        capsize=cap_size,
        zorder=1,
    )

    # Scatter points: dataset colored
    if marker_color == "Dataset":
        datasets = df["Dataset"].unique()
        cmap = plt.get_cmap("tab10")
        color_map = {ds: cmap(i % 10) for i, ds in enumerate(datasets)}

        for ds in datasets:
            subset = df[df["Dataset"] == ds]
            plt.scatter(
                subset["Experimental_G"],
                subset["Predicted_G"],
                color=color_map[ds],
                alpha=marker_alpha,
                s=marker_size,
                label=ds,
                zorder=2,
            )

        plt.legend(title="Dataset", bbox_to_anchor=(1.05, 1), loc="upper left")

    else:
        plt.scatter(
            x, y, color=marker_color, alpha=marker_alpha, s=marker_size, zorder=2
        )

    # ✅ COMPUTE + PLOT STATS
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
            # f"R² = {r2:.2f}\n"
            f"Pearson R = {pearson_r:.2f}\n"
            f"Spearman ρ = {spearman_r:.2f}\n"
            # f"Kendall τ = {kendall_tau:.2f}"
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
            # bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
        )

    # Axis labels + title with fontsize
    plt.xlabel("Experimental ΔG (kcal/mol)", fontsize=axis_fontsize)
    plt.ylabel("Predicted ΔG (kcal/mol)", fontsize=axis_fontsize)
    # plt.title(
    #     "Experimental vs Predicted affinities",
    #     fontsize=title_fontsize,
    # )
    # ✅ LOWER-RIGHT LABEL
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
    # Set axis limits first
    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)

    # ✅ Define 1 kcal/mol tick spacing from the minimum value
    tick_values = np.arange(np.floor(min_val), np.ceil(max_val) + 1, 2)

    plt.xticks(tick_values, fontsize=tick_fontsize)
    plt.yticks(tick_values, fontsize=tick_fontsize)

    plt.tight_layout()
    plt.savefig(save_name, dpi=600)
    plt.show()


def main():
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path_dict = {
        "lenselink_with_na": DATA_DIR / "lenselink_exp_v_abfe_df_na.csv",
        "lenselink_without_na": DATA_DIR / "lenselink_exp_v_abfe_df.csv",
    }

    label_dict = {
        "lenselink_without_na": "Without Na+",
        "lenselink_with_na": "With Na+",
    }

    stats_dict = {
        "Sampling": [],
        "MUE": [],
        "RMSE": [],
        "R2": [],
        "Pearson_R": [],
        "Spearman_rho": [],
        "Kendall_tau": [],
    }

    for name, csv_path in csv_path_dict.items():
        df_exp_v_abfe_w_stat = pd.read_csv(DATA_DIR / f"{name}_w_stats.csv")

        plot_exp_vs_pred(
            df_exp_v_abfe_w_stat,
            err_color="grey",
            err_alpha=0.5,
            marker_color="#3594cc",
            marker_alpha=1.0,
            shading_dGs=[1, 2, 3, 5],
            shading_color="#f55f74",
            save_name=FIGURE_DIR
            / f"exp_vs_pred_with_dg_shading_blue_{name}_wstat_v3_label.svg",
            min=-17,
            max=-6,
            label=label_dict[name],
        )

        # Calculate stats
        mue = mean_absolute_error(
            df_exp_v_abfe_w_stat["Experimental_G"], df_exp_v_abfe_w_stat["Predicted_G"]
        )
        rmse = np.sqrt(
            mean_squared_error(
                df_exp_v_abfe_w_stat["Experimental_G"],
                df_exp_v_abfe_w_stat["Predicted_G"],
            )
        )
        r2 = r2_score(
            df_exp_v_abfe_w_stat["Experimental_G"], df_exp_v_abfe_w_stat["Predicted_G"]
        )
        pearson_r, _ = pearsonr(
            df_exp_v_abfe_w_stat["Experimental_G"], df_exp_v_abfe_w_stat["Predicted_G"]
        )
        spearman_r, _ = spearmanr(
            df_exp_v_abfe_w_stat["Experimental_G"], df_exp_v_abfe_w_stat["Predicted_G"]
        )
        kendall_tau, _ = kendalltau(
            df_exp_v_abfe_w_stat["Experimental_G"], df_exp_v_abfe_w_stat["Predicted_G"]
        )

        # Save stats to a df
        stats_dict["Sampling"].append(name)
        stats_dict["MUE"].append(mue)
        stats_dict["RMSE"].append(rmse)
        stats_dict["R2"].append(r2)
        stats_dict["Pearson_R"].append(pearson_r)
        stats_dict["Spearman_rho"].append(spearman_r)
        stats_dict["Kendall_tau"].append(kendall_tau)

    # Save stats df to csv
    stats_df = pd.DataFrame(stats_dict)
    stats_df.to_csv(
        INTERMEDIATE_DIR / "exp_vs_abfe_stats_summary_lenselink.csv", index=False
    )


if __name__ == "__main__":
    main()
