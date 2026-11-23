from pathlib import Path
import logging

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/water_occupancy"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/water_occupancy/initial"
FIGURE_DIR = CHAPTER_DIR / "figures/water_occupancy"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

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
        matplotlib.rcParams["font.family"] = roboto_font.get_name()
    except Exception:
        print("⚠️ Roboto not found. Falling back to default font.")

    # ---- Apply global font scaling ----
    matplotlib.rcParams.update(
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
        DATA_DIR / "cumulative_water_occupancy_all_cmp_initial.csv"
    )
    cumulative_df["Repeat"] = cumulative_df["van"]
    cumulative_df["Compound"] = cumulative_df["cmp"]

    # Subset compounds 6, 9, 13
    cumulative_df = cumulative_df[cumulative_df["Compound"].isin([6, 9, 13])]

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
        "6": palette_3[0],
        "9": palette_3[1],
        "13": palette_3[2],
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
        hue_order=["6", "9", "13", "apo"],
    )

    # Add lines for min and max apo occupancy
    # x = cumulative_df["window"].unique()
    # x = x[~pd.isna(x)]

    # apo_range_df = pd.read_csv(DATA_DIR / "apo_occupancy_ranges.csv")

    # Add lines for apo occupancy + labels

    # Position label above the coul.00 column
    coul_pos = "coul.00"
    print(coul_pos)

    for row in apo_range_df.itertuples():
        mean = row.apo_mean_occupancy
        run_id = str(row.apo_run.split("_")[-1])

        plt.text(
            coul_pos,  # x position for the coul.00 column
            mean + 0.05,  # lift text slightly above the line
            f"Apo repeat {run_id}",
            color="gray",
            fontsize=LEGEND_FONT_SIZE,
            ha="left",
            va="bottom",
        )
    # ==============================
    # ✅ TITLES & LABELS (AUTO-SCALED)
    # ==============================

    # plt.title(
    #     "Average Water Occupancy Across Windows for All Compounds",
    #     fontweight="bold"
    # )
    plt.xlabel("ABFE Window")
    plt.ylabel("Average Number of Binding Pocket Waters")
    plt.ylim(0, 14)

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
        FIGURE_DIR / "Water_occupancy_across_windows_all_cmp_initial_v6_apo_text.png",
        dpi=300,
    )
    plt.close()


if __name__ == "__main__":
    main()
