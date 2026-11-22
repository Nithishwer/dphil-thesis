"""Compare angled task-type headings with wider gaps between task types."""

import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from make_figure_5 import (
    DATA,
    FONT_FAMILY,
    OUTPUT,
    WIDTH_MM,
    heatmap,
    label_spacing,
)


def main():
    output = OUTPUT / "variants"
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "font.size": 7,
            "pdf.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    with (DATA / "task_success.csv").open() as stream:
        rows = list(csv.DictReader(stream))

    for name, rotation, gap in [("angled", 55, 0.4), ("wider_gaps", 0, 3.0)]:
        # Extra height accommodates the full angled names without clipping.
        fig = plt.figure(figsize=(WIDTH_MM / 25.4, 80 / 25.4), dpi=300)
        labels = heatmap(fig, rows, header_rotation=rotation, group_gap=gap)
        # These standalone comparisons do not need the composite's panel letter.
        for text in list(fig.texts):
            if text.get_text() == "A":
                text.remove()
        label_spacing(fig, labels)
        for suffix in ["pdf", "png"]:
            path = output / f"task_success_{name}.{suffix}"
            fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
        print(f"Saved {name}: {rotation} degree headings, {gap} column gap.")


if __name__ == "__main__":
    main()
