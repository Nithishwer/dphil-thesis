"""Export the updated binding-pose panel for thesis Figure 7.7."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from make_figure_5 import (
    CHAPTER,
    DATA,
    FONT_FAMILY,
    HEIGHT_MM,
    WIDTH_MM,
    binding_pose_panel,
)
from matplotlib.transforms import Bbox

OUTPUT = CHAPTER / "figures/figure_7_7"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {"font.family": FONT_FAMILY, "font.size": 7, "pdf.fonttype": 42}
    )
    cameras = json.loads((DATA / "camera_settings.json").read_text())
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=300)
    binding_pose_panel(fig, cameras["task25"], [], thesis=True)
    # Retain the original molecular scale and crop away the unused canvas.
    bounds = Bbox.from_extents(135 / 25.4, 34.5 / 25.4, 185.9 / 25.4, 70.2 / 25.4)
    fig.savefig(OUTPUT / "figure_7_7_A.pdf", bbox_inches=bounds, dpi=600)
    for ax in fig.axes:
        for image in ax.images:
            image.set_interpolation("hanning")
    fig.savefig(OUTPUT / "figure_7_7_A.png", bbox_inches=bounds, dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
