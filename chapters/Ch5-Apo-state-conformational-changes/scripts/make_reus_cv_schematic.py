from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CHAPTER_DIR = Path(__file__).resolve().parents[1]
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/reus_schematic/cv"
FIGURE_DIR = CHAPTER_DIR / "figures/reus_schematic/regenerated"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def generate_gaussian_points(
    center=(0, 0),
    n_points=1000,
    spread=1.0,
    random_state=None,
    simulation="abfe",
    cluster="0",
):
    """
    Generate a DataFrame of 2D Gaussian-distributed points around a center.

    Parameters:
        center (tuple): (x, y) coordinates of the center point.
        n_points (int): Number of points to generate.
        spread (float or tuple): Standard deviation.
                                 If float, same spread for x and y.
                                 If tuple, interpreted as (spread_x, spread_y).
        random_state (int, optional): Seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame with columns ['x', 'y'].
    """

    if random_state is not None:
        np.random.seed(random_state)

    cx, cy = center

    # Handle isotropic or anisotropic spread
    if isinstance(spread, (int, float)):
        spread_x = spread_y = spread
    else:
        spread_x, spread_y = spread

    x = np.random.normal(loc=cx, scale=spread_x, size=n_points)
    y = np.random.normal(loc=cy, scale=spread_y, size=n_points)

    df = pd.DataFrame({"x": x, "y": y})
    df["simulation"] = simulation
    df["cluster"] = cluster

    return df


def plot_points_from_csv(
    csv_path,
    color_by=None,
    palette=None,
    xlim=None,
    ylim=None,
    point_size=10,
    figsize=(6, 6),
    save_path=None,
    dpi=300,
    title=None,
    pad_inches=0.05,  # small padding so nothing gets clipped
    right_margin=0.98,  # useful if right side is tight
):
    matplotlib.rcParams["font.family"] = "Roboto"

    df = pd.read_csv(csv_path)
    if color_by is not None:
        df[color_by] = df[color_by].astype(str)

    fig, ax = plt.subplots(figsize=figsize)

    if color_by is None:
        ax.scatter(df["x"], df["y"], s=point_size)
    else:
        if color_by not in df.columns:
            raise ValueError(f"{color_by} column not found in CSV.")
        categories = df[color_by].unique()
        for cat in categories:
            subset = df[df[color_by] == cat]
            if palette is not None:
                if cat not in palette:
                    raise ValueError(
                        f"No color provided for category {cat} in palette."
                    )
                color = palette[cat]
                ax.scatter(subset["x"], subset["y"], s=point_size, c=color)
            else:
                ax.scatter(subset["x"], subset["y"], s=point_size)

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("PC1", fontsize=14)
    ax.set_ylabel("PC2", fontsize=14)
    if title is not None:
        ax.set_title(title, fontsize=16, pad=10)

    # remove ticks but keep labels
    ax.set_xticks([])
    ax.set_yticks([])

    # tiny data margin so markers on the edge are not clipped
    ax.margins(0.01)

    # nudge subplot parameters (in case right margin still tight)
    fig.subplots_adjust(right=right_margin)

    # let matplotlib layout elements, then save with a small padding
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight", pad_inches=pad_inches)

    plt.close()


# Example usage
if __name__ == "__main__":
    sim_palette = {"vdw.20": "#FF595E", "apo": "#FFCA3A"}

    df_vdw20 = generate_gaussian_points(
        center=(5, 10),
        n_points=200,
        spread=1,
        random_state=42,
        simulation="vdw.20",
        cluster="0",
    )
    df_apo = generate_gaussian_points(
        center=(15, 10),
        n_points=1000,
        spread=1.5,
        random_state=42,
        simulation="apo",
        cluster="1",
    )
    df = pd.concat(
        [
            df_vdw20,
            df_apo,
        ]
    )

    df.to_csv(INTERMEDIATE_DIR / "points.csv", index=False)

    plot_points_from_csv(
        INTERMEDIATE_DIR / "points.csv",
        color_by="simulation",
        xlim=(0, 20),
        ylim=(0, 20),
        palette=sim_palette,
        point_size=2,
        figsize=(4, 4),
        save_path=FIGURE_DIR / "2_cv_clusters.png",
        dpi=600,
        title="PCA of Clusters of Interest",
    )
