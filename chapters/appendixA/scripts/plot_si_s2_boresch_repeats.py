from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s2"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s2/regenerated"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


# Load data
df = pd.read_csv(DATA_DIR / "exp_v_abfe_df_van_reps_all.csv")


# Rename cells in Vanilla properly
df["Vanilla"] = df["Vanilla"].replace(
    {"van1": "EQ run 1", "van2": "EQ run 2", "van3": "EQ run 3"}
)

# Combine Vanilla + Rep
df["van_rep"] = df["Vanilla"] + "_" + df["Rep"]


# Sort for consistent ordering
df = df.sort_values(["Lig_Name", "Vanilla", "Rep"])

# Unique identifiers
ligands = df["Lig_Name"].unique()
van_reps = df["van_rep"].unique()

# Bar layout
n_ligands = len(ligands)
n_sub = len(van_reps)
bar_width = 0.8 / n_sub
x = np.arange(n_ligands)

# User-specified color palette
vanilla_colors = {
    "EQ run 1": "#f55f74",
    "EQ run 2": "#b279cb",
    "EQ run 3": "#3594cc",
}

# ---- Statistics (unchanged, correct) ----

# SD over repeats for each compound–vanilla
repeat_sd = (
    df.groupby(["Lig_Name", "Vanilla"])["TI"].std().reset_index(name="repeat_sd")
)
avg_repeat_error = repeat_sd["repeat_sd"].mean()
std_repeat_error = repeat_sd["repeat_sd"].std()


# First average repeats → one value per compound–vanilla
cv_mean = df.groupby(["Lig_Name", "Vanilla"])["TI"].mean().reset_index()


# SD over vanillas for each compound
vanilla_sd = cv_mean.groupby("Lig_Name")["TI"].std().reset_index(name="vanilla_sd")

avg_vanilla_error = vanilla_sd["vanilla_sd"].mean()
std_vanilla_error = vanilla_sd["vanilla_sd"].std()


# ---- Plot ----
plt.figure(figsize=(8, 4))

plt.rcParams.update(
    {
        "font.size": 12,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "legend.fontsize": 12,
        "legend.title_fontsize": 12,
        "font.family": "Roboto",
    }
)

used_labels = set()

for i, vr in enumerate(van_reps):
    subset = df[df["van_rep"] == vr]
    subset = subset.set_index("Lig_Name").reindex(ligands)

    vanilla = vr.split("_")[0]
    label = vanilla if vanilla not in used_labels else None
    used_labels.add(vanilla)

    plt.bar(
        x + i * bar_width,
        subset["TI"],
        width=bar_width,
        color=vanilla_colors[vanilla],
        label=label,
        edgecolor="black",
        linewidth=0.5,
    )

# ---- Axis formatting ----
compound_labels = [lig.split("_")[-1] for lig in ligands]
tick_positions = x + bar_width * (n_sub - 1) / 2

plt.ylim(-20.5, 0)
plt.xticks(tick_positions, compound_labels, ha="center")
plt.ylabel("Predicted ΔG (kcal/mol)")
plt.xlabel("Compound")
plt.title("TI Values by Compound and Vanilla/Replica")

plt.gca().invert_yaxis()

plt.legend(title="Structure-Boresch", frameon=False)

# ---- Stats annotation ----
stats_text = f"Avg. Repeat SD: {avg_repeat_error:.2f} kcal/mol\nAvg. Structure-Boresch SD: {avg_vanilla_error:.2f} kcal/mol"

plt.text(
    0.99,
    0.95,
    stats_text,
    transform=plt.gca().transAxes,
    fontsize=12,
    va="top",
    ha="right",
    bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.3"),
)


plt.tight_layout()
plt.savefig(FIGURE_DIR / "si_fig1_bar_plot.svg", dpi=600)
plt.close()
