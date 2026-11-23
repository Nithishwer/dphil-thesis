from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/deflorian_pca/full"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s6/panels"
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

# Colorblind-friendly palette (Okabe-Ito)
COLORS = {
    "ABFE": "#0072B2",  # blue
    "Apo": "#E69F00",  # orange
    "Holo": "#009E73",  # green
}

BASE_DIR = DATA_DIR

CMPS = ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4r", "4q"]


def plot_pca_by_ensemble(csv_path, cmp_label, outdir=None):
    """
    Read a PCA projection CSV, assign ensemble_type, and plot PC1 vs PC2.
    Saves a publication-quality PNG.
    """
    df = pd.read_csv(csv_path)

    # --- Create ensemble_type ---
    ensemble_lower = df["ensemble"].astype(str).str.lower()

    df["ensemble_type"] = "Holo"
    df.loc[
        ensemble_lower.str.contains("coul|vdw|rest", regex=True, na=False),
        "ensemble_type",
    ] = "ABFE"
    df.loc[
        ensemble_lower.str.contains("apo", regex=True, na=False),
        "ensemble_type",
    ] = "Apo"

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(4, 4))

    order = ["ABFE", "Apo", "Holo"]
    for etype in order:
        group = df[df["ensemble_type"] == etype]
        if group.empty:
            continue
        ax.scatter(
            group["PC1"],
            group["PC2"],
            label=etype,
            s=8,
            alpha=0.85,
            edgecolors="none",
            color=COLORS[etype],
        )

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(f"Compound {cmp_label}")

    ax.legend(frameon=False, title=None)

    # Clean look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    if outdir is None:
        outdir = Path.cwd()
    else:
        outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    outpath = outdir / f"pc1_vs_pc2_cmp_{cmp_label}.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)

    return outpath


# ---- Loop over all cmp values ----
output_files = []
for cmp_label in CMPS:
    csv_path = BASE_DIR / f"cmp_{cmp_label}" / "pca_projection_df.csv"
    outpath = plot_pca_by_ensemble(csv_path, cmp_label, outdir=FIGURE_DIR)
    output_files.append(outpath)

print("Saved figures:")
for path in output_files:
    print(path)
