from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/deflorian_pca/full"
FIGURE_DIR = CHAPTER_DIR / "figures/si_s10/panels"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s10"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


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
CLUSTER_MAP = {
    "g": 3,
    "j": 3,
    "k": 3,
    "l": 3,
    "m": 2,
    "q": 2,
    "r": 2,
    "n": 4,
    "i": 4,
    "h": 4,
}

CLUSTER_COLORS = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#D55E00",
    "#56B4E9",
]


def assign_ensemble_type(df):
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

    return df


def add_clusters(df, cmp_label, random_state=0):
    """
    Cluster using PC1, PC2, PC3 with predefined cluster numbers.
    """
    # Extract letter (e.g. "4g" -> "g")
    cmp_letter = cmp_label[-1].lower()
    n_clusters = CLUSTER_MAP.get(cmp_letter, 3)  # default fallback

    X = df[["PC1", "PC2", "PC3"]].to_numpy()
    X_scaled = StandardScaler().fit_transform(X)

    # Safety: cannot have more clusters than samples
    n_clusters = min(n_clusters, len(df))

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    df["cluster"] = model.fit_predict(X_scaled)
    df["n_clusters"] = n_clusters

    return df, n_clusters


def plot_pca_by_cluster(df, cmp_label, outdir, n_clusters):
    fig, ax = plt.subplots(figsize=(4, 4))

    for cluster_id in sorted(df["cluster"].unique()):
        group = df[df["cluster"] == cluster_id]
        ax.scatter(
            group["PC1"],
            group["PC2"],
            label=f"Cluster {cluster_id + 1}",
            s=8,
            alpha=0.85,
            edgecolors="none",
            color=CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)],
        )

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(f"Compound {cmp_label} (k={n_clusters})")
    ax.legend(frameon=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    outpath = outdir / f"pc1_vs_pc2_clusters_{cmp_label}.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)

    return outpath


def process_cmp(csv_path, cmp_label, outroot):
    df = pd.read_csv(csv_path)
    df = assign_ensemble_type(df)

    df, n_clusters = add_clusters(df, cmp_label)

    outdir = Path(outroot) / cmp_label
    outdir.mkdir(parents=True, exist_ok=True)

    clustered_csv = outdir / f"pca_projection_df_clustered_{cmp_label}.csv"
    df.to_csv(clustered_csv, index=False)

    plot_path = plot_pca_by_cluster(df, cmp_label, FIGURE_DIR / cmp_label, n_clusters)

    return clustered_csv, plot_path, n_clusters


# ---- Run ----
output_root = INTERMEDIATE_DIR
output_files = []

for cmp_label in CMPS:
    csv_path = BASE_DIR / f"cmp_{cmp_label}" / "pca_projection_df.csv"
    clustered_csv, plot_path, k = process_cmp(
        csv_path,
        cmp_label,
        output_root,
    )
    output_files.append((clustered_csv, plot_path, k))

print("Saved files:")
for clustered_csv, plot_path, k in output_files:
    print(f"{clustered_csv}  | k={k}")
    print(plot_path)
