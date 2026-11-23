from pathlib import Path

import logging
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import matplotlib as mpl

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = REPO_DIR / "chapters/Ch4-Binding-pocket-resolvation/data/water_occupancy"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s3/panels"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s3"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    """Main function to run the analysis"""

    # ==============================
    # ✅ GLOBAL FONT CONFIGURATION
    # ==============================

    BASE_FONT_SIZE = 10  # Controls EVERYTHING
    TITLE_FONT_SIZE = 10
    LABEL_FONT_SIZE = 10
    TICK_FONT_SIZE = 10
    LEGEND_FONT_SIZE = 8
    LEGEND_TITLE_FONT_SIZE = 5

    # ---- Load Roboto Font (make sure it's installed) ----
    try:
        font_path = fm.findfont("Roboto")
        roboto_font = fm.FontProperties(fname=font_path)
        mpl.rcParams["font.family"] = roboto_font.get_name()
    except Exception:
        print("⚠️ Roboto not found. Falling back to default font.")

    # ---- Apply global font scaling ----
    mpl.rcParams.update(
        {
            "font.size": BASE_FONT_SIZE,
            "axes.titlesize": TITLE_FONT_SIZE,
            "axes.labelsize": LABEL_FONT_SIZE,
            "xtick.labelsize": TICK_FONT_SIZE,
            "ytick.labelsize": TICK_FONT_SIZE,
            "legend.fontsize": LEGEND_FONT_SIZE,
            "legend.title_fontsize": LEGEND_TITLE_FONT_SIZE,
        }
    )

    # ==============================
    # DATA LOADING
    # ==============================

    cumulative_df = pd.read_csv(
        DATA_DIR / "cumulative_water_occupancy_all_cmp_solvated.csv"
    )
    cumulative_df["Repeat"] = cumulative_df["van"]
    cumulative_df["Compound"] = cumulative_df["cmp"]

    # Subset compounds not in 6, 9, 13
    cumulative_df = cumulative_df[~cumulative_df["Compound"].isin([6, 9, 13])]

    # Arrange compounds in order of solvation in vdw.19
    vdw_19_df = cumulative_df[cumulative_df["window"] == "vdw.19"]
    vdw_19_df = vdw_19_df.sort_values(by="occupancy", ascending=False)
    max_cmp = vdw_19_df.iloc[0]["Compound"]
    min_cmp = vdw_19_df.iloc[-1]["Compound"]
    median_cmp = vdw_19_df.iloc[int(len(vdw_19_df) / 2)]["Compound"]
    print(max_cmp, min_cmp, median_cmp)

    def window_sort_key(w):
        w = str(w).lower()
        if w.startswith("rest"):
            return (0, w)
        elif w.startswith("coul"):
            return (1, w)
        elif w.startswith("vdw"):
            return (2, w)
        else:
            return (3, w)  # anything unexpected goes last

    # Get sorted unique window order
    sorted_windows = sorted(
        cumulative_df["window"].dropna().unique(), key=window_sort_key
    )

    # Apply categorical ordering
    cumulative_df["window"] = pd.Categorical(
        cumulative_df["window"], categories=sorted_windows, ordered=True
    )

    # Save cumulative df
    cumulative_df.to_csv(
        INTERMEDIATE_DIR / "cumulative_water_occupancy_all_cmp_subset.csv", index=False
    )

    # Read apo occupancy ranges
    apo_range_df = pd.read_csv(DATA_DIR / "apo_occupancy_ranges.csv")

    # Make empty df with rows id,van,occupancy,window,cmp,Repeat,Compound

    apo_cumulative_df = pd.DataFrame(
        columns=["id", "van", "occupancy", "window", "cmp", "Repeat", "Compound"]
    )

    # id suffixed
    id_suffixes = (
        [""]
        + [f"_coul.{i:02d}" for i in range(11)]
        + [f"_rest.{i:02d}" for i in range(12)]
        + [f"_vdw.{i:02d}" for i in range(21)]
    )

    apo_rows = []

    for row in apo_range_df.itertuples(index=False):
        for suffix in id_suffixes:
            window = (
                suffix[1:] if suffix else ""
            )  # "" -> blank, "_coul.00" -> "coul.00"

            apo_rows.append(
                {
                    "id": f"{row.apo_run}{suffix}",
                    "van": row.apo_run,
                    "occupancy": row.apo_mean_occupancy,
                    "window": window,
                    "cmp": "apo",
                    "Repeat": int(row.apo_run.split("_")[-1]),
                    "Compound": "apo",
                }
            )

    apo_cumulative_df = pd.DataFrame(apo_rows)

    # Now append the cumulative df to the apo cumulative df
    cumulative_df = pd.concat([cumulative_df, apo_cumulative_df], ignore_index=True)

    # ==============================
    # PLOTTING
    # ==============================

    palette_3 = sns.color_palette("colorblind")
    compound_palette = {
        "7": palette_3[0],
        "8": palette_3[1],
        "10": palette_3[2],
        "11": palette_3[3],
        "12": palette_3[4],
        "14": palette_3[5],
        "15": palette_3[6],
        "16": palette_3[7],
        "17": palette_3[8],
        "apo": "gray",
    }

    # Make hue values consistent
    cumulative_df["Compound"] = cumulative_df["Compound"].astype(str)

    plt.figure(figsize=(5, 4))

    sns.lineplot(
        data=cumulative_df,
        x="window",
        y="occupancy",
        hue="Compound",
        style="Repeat",
        palette=compound_palette,
        hue_order=["7", "8", "10", "11", "12", "14", "15", "16", "17", "apo"],
    )

    # Add lines for min and max apo occupancy
    # x = cumulative_df["window"].unique()
    # x = x[~pd.isna(x)]

    # apo_range_df = pd.read_csv(DATA_DIR / "apo_occupancy_ranges.csv")

    # apo_linestyles = {
    #     "1": "solid",
    #     "2": "dashed",
    #     "3": "dotted",
    # }

    # x = cumulative_df["window"].cat.categories

    # for row in apo_range_df.itertuples():
    #     mean = row.apo_mean_occupancy
    #     run_id = str(row.apo_run.split("_")[-1])
    #     linestyle = apo_linestyles.get(run_id, "-.")

    #     plt.plot(
    #         x,
    #         np.full(len(x), mean, dtype=float),
    #         linestyle=linestyle,
    #         color="gray",
    #         alpha=0.7,
    #         linewidth=2,
    #         zorder=10,
    #         label=f"Apo run {run_id}",
    #     )

    # ==============================
    # ✅ TITLES & LABELS (AUTO-SCALED)
    # ==============================

    # plt.title(
    #     "Average Water Occupancy Across Windows for All Compounds",
    #     fontweight="bold"
    # )
    plt.xlabel("ABFE Window")
    plt.ylabel("Average Number of Binding Pocket Waters")
    plt.title("After Solvation")

    plt.legend(loc="upper left", bbox_to_anchor=(1.05, 1), frameon=False)

    # ✅ FULLY VERTICAL X-TICKS (AUTO FONT SIZE)
    ax = plt.gca()
    ticks = ax.get_xticks()
    labels = [t.get_text() for t in ax.get_xticklabels()]

    # ✅ Keep every other tick
    ax.set_xticks(ticks[::2])
    ax.set_xticklabels(labels[::2], rotation=90)
    plt.yticks()

    plt.tight_layout()
    plt.savefig(
        FIGURE_DIR / "Water_occupancy_across_windows_all_cmp_solvated_v1.png",
        dpi=300,
    )
    plt.close()


if __name__ == "__main__":
    main()
