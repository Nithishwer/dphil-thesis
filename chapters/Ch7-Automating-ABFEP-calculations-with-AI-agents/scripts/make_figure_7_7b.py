"""Render the selected PepT2 views and assemble thesis Figure 7.7B."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pymol2
from matplotlib.patches import ConnectionPatch, Rectangle
from PIL import Image

CHAPTER = Path(__file__).resolve().parents[1]
WORKING = CHAPTER / "scripts/intermediates/figure_7_7b"
OUTPUT = CHAPTER / "figures/figure_7_7b"
SOURCE = WORKING / "renders/task29_full_membrane.pse"
SESSION = WORKING / "renders/task29_selected_views.pse"

# Camera values supplied by the user from the full-membrane session.
OVERVIEW = (
    -0.889423370,
    0.001803395,
    0.457077265,
    -0.010883234,
    0.999623716,
    -0.025119983,
    -0.456951797,
    -0.027316937,
    -0.889070511,
    -0.000009716,
    -0.000005826,
    -203.307907104,
    -10.084425926,
    0.062387943,
    12.644667625,
    73.308189392,
    333.308135986,
    20.000000000,
)
CLOSEUP = (
    0.915257514,
    0.372350633,
    0.153794929,
    -0.402832538,
    0.850579798,
    0.337996483,
    -0.004962791,
    -0.371308088,
    0.928490877,
    0.000006897,
    0.000005122,
    -39.656139374,
    -1.527552366,
    0.290421039,
    1.423612475,
    23.497169495,
    55.814117432,
    20.000000000,
)
# Helices 290-317 and 642-664 obscure AMP702; include their short end transitions.
FOREGROUND = "protein and resi 288-319+640-666"
FIRST = "ligand_AMP702 and name C6"
SECOND = "clashing_lipid_POPE808 and name C316"
WIDTH_MM, HEIGHT_MM = 69.6, 30.0


def project(coordinates, view, aspect):
    """Project onto the orthographic image using PyMOL's column-major rotation."""
    view = np.array(view)
    rotated = (np.asarray(coordinates) - view[12:15]) @ view[:9].reshape(3, 3)
    height = -2 * view[11] * np.tan(np.deg2rad(abs(view[17]) / 2))
    return 0.5 + (rotated[..., :2] + view[9:11]) / [height * aspect, height]


def render_views():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.load(str(SOURCE))
        atom_count = cmd.count_atoms("not clash_atoms")
        cmd.scene("full_system", "clear")
        cmd.select("foreground_helices", FOREGROUND)
        cmd.deselect()
        cmd.set("scene_buttons", 1)
        cmd.set("label_size", 22)
        endpoints = np.array([cmd.get_atom_coords(FIRST), cmd.get_atom_coords(SECOND)])
        ligand = cmd.get_coords("ligand_AMP702 and not elem H")
        for name, view, dimensions in [
            ("overview", OVERVIEW, (1800, 1200)),
            ("closeup", CLOSEUP, (1200, 1200)),
        ]:
            cmd.show("cartoon", "protein")
            if name == "closeup":
                cmd.hide("cartoon", "foreground_helices")
            cmd.enable("clash_distance")
            cmd.viewport(*dimensions)
            cmd.set_view(view)
            cmd.scene(name, "store")
            # The publication panel adds a clean vector distance annotation.
            cmd.disable("clash_distance")
            print(f"Rendering {name}", flush=True)
            cmd.png(str(OUTPUT / f"{name}.png"), *dimensions, dpi=600, ray=1)
        cmd.scene("overview", "recall", animate=0)
        cmd.viewport(1200, 800)
        cmd.save(str(SESSION))

    # Check both scene cameras and visibility after reopening the delivered session.
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.load(str(SESSION))
        for name, view in [("overview", OVERVIEW), ("closeup", CLOSEUP)]:
            cmd.scene(name, "recall", animate=0)
            assert np.allclose(cmd.get_view(), view, atol=1e-5, rtol=0)
            assert cmd.count_atoms("not clash_atoms") == atom_count == 47256
            assert abs(cmd.get_distance(FIRST, SECOND) - 1.368612436) < 1e-5
            visible = cmd.count_atoms("foreground_helices and rep cartoon")
            if name == "overview":
                assert visible > 0
            else:
                assert visible == 0
    return {"endpoints": endpoints, "ligand": ligand}


def add_image(fig, name, x, y, width):
    with Image.open(OUTPUT / f"{name}.png") as image:
        height = width * image.height / image.width
        pixels = np.array(image)
    ax = fig.add_axes(
        [x / WIDTH_MM, y / HEIGHT_MM, width / WIDTH_MM, height / HEIGHT_MM]
    )
    ax.imshow(pixels, extent=(0, 1, 0, 1), interpolation="none", aspect="auto")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.set_axis_off()
    return ax


def assemble_panel(coordinates):
    plt.rcParams.update({"font.family": "Liberation Sans", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4))
    label_backdrop = {
        "boxstyle": "round,pad=0.12,rounding_size=0.12",
        "facecolor": (1, 1, 1, 0.80),
        "edgecolor": "none",
        "linewidth": 0,
    }
    overview = add_image(fig, "overview", 0, 1.5, 40.5)
    closeup = add_image(fig, "closeup", 42.1, 1.5, 27.0)
    closeup.add_patch(Rectangle((0, 0), 1, 1, fill=False, ec="#AAAAAA", lw=0.5))
    overview.text(
        0.49,
        0.25,
        "PEPT2",
        fontsize=6.0,
        color="#3B7A3D",
        ha="center",
        va="center",
        bbox=label_backdrop,
    )

    ligand = project(coordinates["ligand"], OVERVIEW, 1.5)
    low, high = ligand.min(axis=0) - 0.025, ligand.max(axis=0) + 0.025
    overview.add_patch(Rectangle(low, *(high - low), fill=False, ec="#777777", lw=0.5))
    fig.add_artist(
        ConnectionPatch(
            (high[0], (low[1] + high[1]) / 2),
            (0, 0.5),
            coordsA=overview.transData,
            coordsB=closeup.transData,
            color="#888888",
            lw=0.45,
        )
    )
    points = project(coordinates["endpoints"], CLOSEUP, 1)
    closeup.plot(*points.T, color="#333333", lw=0.6, ls=(0, (2, 1.5)))
    closeup.scatter(*points.T, s=5, color="#333333", zorder=5)
    midpoint = points.mean(axis=0)
    closeup.text(
        midpoint[0] - 0.18,
        midpoint[1] + 0.055,
        "1.37 Å",
        fontsize=7.5,
        ha="center",
        va="center",
        bbox=label_backdrop,
    )
    ligand_center = project(coordinates["ligand"].mean(axis=0), CLOSEUP, 1)
    for label, anchor, offset, color in [
        ("AMP702", ligand_center, (0.20, -0.18), "#2D9FBA"),
        ("POPE808", points[1], (0.19, 0.20), "#9F792F"),
    ]:
        closeup.text(
            *(anchor + offset),
            label,
            fontsize=6.0,
            ha="center",
            va="center",
            color=color,
            bbox=label_backdrop,
        )
    fig.savefig(OUTPUT / "figure_7_7b.pdf")
    fig.savefig(OUTPUT / "figure_7_7b.png", dpi=600)
    plt.close(fig)


def main():
    coordinates = render_views()
    assemble_panel(coordinates)
    record = {
        "source_session": str(SOURCE.relative_to(CHAPTER)),
        "session": str(SESSION.relative_to(CHAPTER)),
        "overview_view": list(OVERVIEW),
        "closeup_view": list(CLOSEUP),
        "closeup_hidden_cartoon": FOREGROUND,
        "overview_cartoon": "All protein residues displayed",
        "contact_distance_A": float(
            np.linalg.norm(np.diff(coordinates["endpoints"], axis=0))
        ),
        "session_reopened_and_verified": True,
    }
    (WORKING / "task29_selected_views.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(f"Saved {SESSION} and {OUTPUT / 'figure_7_7b.pdf'}", flush=True)


if __name__ == "__main__":
    main()
