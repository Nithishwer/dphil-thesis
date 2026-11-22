#!/usr/bin/env python3
"""Draw a synthetic alchemical-metadynamics free-energy schematic.

Run with Python, NumPy, and Matplotlib:
    python make_figure_2d.py

Transparent PNG and PDF files are saved in the chapter figures folder. The surface and
coordinates are illustrative; no simulation data or physical energy scale is used.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, Normalize

CHAPTER = Path(__file__).resolve().parents[4]
HERE = CHAPTER / "figures/figure_2/d-AlchMetad"
OUTPUT_STEM = HERE / "figure_2d"
FIGURE_SIZE = (6.8, 5.4)
DPI = 600
GRID_POINTS = 151
ELEVATION = 33
AZIMUTH = -30
COLORMAP = "viridis"


def free_energy(alchemical_cv: np.ndarray, metad_cv: np.ndarray) -> np.ndarray:
    """Recreate the reference's left valley, front trough, and centre-right hill.

    The rear corner is highest. A broad shallow valley sweeps down the left,
    beside a rounded hill, into a deeper trough near the front corner.
    """
    x = 2 * alchemical_cv - 1

    # The curved background rises steeply toward the rear corner.
    energy = 0.55 * (x - 1.05) ** 2 + 0.28 * (metad_cv + 0.75) ** 2

    # A tall central hill divides the shallow left valley from the deep front trough.
    energy += 3.60 * np.exp(
        -0.5 * (((x - 0.32) / 0.63) ** 2 + ((metad_cv - 0.05) / 0.55) ** 2)
    )

    # Lift the left rim and back-right corner while retaining the low front trough.
    energy += 1.10 * np.exp(-0.5 * ((x + 1.00) / 0.35) ** 2)
    energy += 2.40 * np.exp(
        -0.5 * (((x - 1.00) / 0.45) ** 2 + ((metad_cv - 1.00) / 0.50) ** 2)
    )

    # Cut a deep trough between the two high rear corners.
    energy -= 2.50 * np.exp(-0.5 * ((x / 0.38) ** 2 + ((metad_cv - 0.95) / 0.42) ** 2))
    energy -= 1.55 * np.exp(
        -0.5 * (((x + 0.40) / 0.40) ** 2 + ((metad_cv + 0.38) / 0.52) ** 2)
    )
    energy -= 0.80 * np.exp(
        -0.5 * (((x - 0.78) / 0.50) ** 2 + ((metad_cv + 0.88) / 0.38) ** 2)
    )
    return energy - energy.min()


def configure_style() -> None:
    """Use the same typography for the final panel and shape comparisons."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "text.color": "#27343b",
            "axes.labelcolor": "#27343b",
            "pdf.fonttype": 42,
        }
    )


def draw_surface(
    ax,
    alchemical_cv: np.ndarray,
    metad_cv: np.ndarray,
    energy: np.ndarray,
) -> None:
    """Draw one landscape with the shared camera, colours, axes, and contours."""
    energy = energy - energy.min()
    energy_range = energy.max()
    floor = -0.28 * energy_range
    colour_scale = Normalize(vmin=0, vmax=energy_range)
    cmap = plt.get_cmap(COLORMAP)

    ax.view_init(elev=ELEVATION, azim=AZIMUTH)
    ax.set_box_aspect((1.0, 1.0, 1.10))

    # Project the same energy contours onto a plane below the surface.
    ax.contour(
        alchemical_cv,
        metad_cv,
        energy,
        levels=np.linspace(0.08, 0.96, 11) * energy_range,
        zdir="z",
        offset=floor,
        cmap=cmap,
        norm=colour_scale,
        linewidths=0.8,
        alpha=0.65,
    )

    # Soft lighting and a fine mesh reveal the slopes, as in the reference.
    face_colours = LightSource(azdeg=315, altdeg=48).shade(
        energy,
        cmap=cmap,
        norm=colour_scale,
        vert_exag=0.35,
        dx=1 / (GRID_POINTS - 1),
        dy=2 / (GRID_POINTS - 1),
        blend_mode="soft",
    )
    ax.plot_surface(
        alchemical_cv,
        metad_cv,
        energy,
        facecolors=face_colours,
        rstride=3,
        cstride=3,
        edgecolor=(0.13, 0.19, 0.24, 0.32),
        linewidth=0.28,
        antialiased=True,
        shade=False,
        rasterized=True,
    )

    ax.set(xlim=(0, 1), ylim=(-1, 1), zlim=(floor, energy_range * 1.04))
    ax.set_xlabel(r"Alchemical CV, $\lambda$", labelpad=9)
    ax.set_ylabel(r"Metadynamics CV, $s$", labelpad=9)
    ax.set_zlabel("Free energy", labelpad=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.grid(False)

    # Keep only the axis lines; omit numerical scales for arbitrary CV/energy units.
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((1, 1, 1, 0))
        axis.line.set_color("#809097")
        axis.line.set_linewidth(0.8)


def main() -> None:
    configure_style()
    alchemical_cv, metad_cv = np.meshgrid(
        np.linspace(0, 1, GRID_POINTS), np.linspace(-1, 1, GRID_POINTS)
    )
    figure = plt.figure(figsize=FIGURE_SIZE)
    ax = figure.add_subplot(projection="3d", proj_type="ortho")
    draw_surface(ax, alchemical_cv, metad_cv, free_energy(alchemical_cv, metad_cv))
    figure.subplots_adjust(left=0.03, right=0.88, bottom=0.09, top=0.99)
    for extension in ("png", "pdf"):
        output = OUTPUT_STEM.with_suffix(f".{extension}")
        figure.savefig(
            output, dpi=DPI, bbox_inches="tight", pad_inches=0.12, transparent=True
        )
        print(f"Saved {output}")
    plt.close(figure)


if __name__ == "__main__":
    main()
