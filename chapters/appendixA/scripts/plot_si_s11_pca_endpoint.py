from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/deflorian_pca/subset"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s11/panels"
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
    "vdw.20": "#0072B2",  # blue
    "apo": "#E69F00",  # orange
    "other": "#009E73",  # green, unused in plot
}


CMPS = ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4r", "4q"]


def assign_ensemble_type(df):
    ensemble_lower = df["ensemble"].astype(str).str.lower()

    df["ensemble_type"] = "other"
    df.loc[
        ensemble_lower.str.contains("vdw\\.20", regex=True, na=False), "ensemble_type"
    ] = "vdw.20"
    df.loc[
        ensemble_lower.str.contains("apo", regex=True, na=False), "ensemble_type"
    ] = "apo"

    return df


def plot_pca_by_ensemble(csv_path, cmp_label, outdir=None):
    """
    Read a PCA projection CSV, assign ensemble_type, and plot PC1 vs PC2.
    Only plots vdw.20 and apo.
    """
    df = pd.read_csv(csv_path)
    df = assign_ensemble_type(df)

    # Keep only the two groups we want to show
    df = df[df["ensemble_type"].isin(["vdw.20", "apo"])].copy()

    fig, ax = plt.subplots(figsize=(4, 4))

    order = ["vdw.20", "apo"]
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


source_dict = {
    compound: DATA_DIR / compound / "subset_pca_projection_df.csv" for compound in CMPS
}

# ---- Loop over all cmp values ----
output_files = []
for cmp_label in CMPS:
    csv_path = source_dict[cmp_label]
    outpath = plot_pca_by_ensemble(
        csv_path,
        cmp_label,
        outdir=FIGURE_DIR,
    )
    output_files.append(outpath)

print("Saved figures:")
for path in output_files:
    print(path)
