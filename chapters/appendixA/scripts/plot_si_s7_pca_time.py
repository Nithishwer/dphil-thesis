from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/deflorian_pca/full"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s7/panels"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


# ---- Global publication settings ----
plt.rcParams.update(
    {
        "font.family": "Roboto",
        "font.sans-serif": ["Roboto"],
        "font.size": 12,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "legend.fontsize": 12,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "figure.dpi": 300,
        "savefig.dpi": 600,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

BASE_DIR = DATA_DIR

CMPS = ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4r", "4q"]

# ---- Cluster rules ----
# ---- Cluster rules ----


def plot_pca_colored_by_time(csv_path, cmp_label, outdir):
    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(4, 4))
    sc = ax.scatter(
        df["PC1"],
        df["PC2"],
        c=df["timestep"],
        s=8,
        alpha=0.85,
        edgecolors="none",
        cmap="viridis",
    )

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(f"Compound {cmp_label}")
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("Timestep")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    outpath = outdir / f"pc1_vs_pc2_time_{cmp_label}.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)

    return outpath


# ---- Run ----
output_files = []

for cmp_label in CMPS:
    csv_path = BASE_DIR / f"cmp_{cmp_label}" / "pca_projection_df.csv"
    plot_path = plot_pca_colored_by_time(csv_path, cmp_label, FIGURE_DIR)
    output_files.append((plot_path))

print("Saved files:")
for plot_path in output_files:
    print(plot_path)
