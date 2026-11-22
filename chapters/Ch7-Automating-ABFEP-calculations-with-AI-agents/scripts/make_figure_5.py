"""Assemble the approved horizontal-header Figure 5 and its underlying display table."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import ConnectionPatch, Rectangle
from PIL import Image
from prepare_figure_5 import load_atoms, positions, sha256

CHAPTER = Path(__file__).resolve().parents[1]
DATA = CHAPTER / "data/figures/figure_5"
HERE = CHAPTER / "scripts/intermediates/figure_5"
OUTPUT = CHAPTER / "figures/figure_5"
# The supplied RSC template is letter paper, with 15 mm left/right margins.
WIDTH_MM, HEIGHT_MM = 185.9, 73.3
MODELS = ["opus-5.5", "gpt-6.1-sol", "gpt-6-astra", "gemini-4-argon", "glm-5.2"]
NAMES = ["Claude Opus-5.5", "GPT-6.1 Sol", "GPT-6 Astra", "Gemini 4 Argon", "GLM-5.2"]
COLORS = ["#F0E4DC", "#D7AD73", "#7BB5BC", "#418D84"]
GROUPS = {
    "analysis": "Analysis",
    "system_preparation": "System preparation",
    "free_energy": "Free energy",
    "enhanced_sampling": "Enhanced\nsampling",
    "parameterization": "Parameterization",
    "diagnostics": "Diagnostics",
    "quantum_chemistry": "QM",
}
CYAN, GOLD = "#2D9FBA", "#9F792F"
TASK25_CROP = (
    0.04,
    0.045,
    0.96,
    0.95,
)  # left, bottom, right, top in the unchanged saved render.
TASK29_CROP = (0.055, 0.055, 0.955, 0.90)


DETAIL_FONT_SIZE = 5.5
FONT_FAMILY = "Liberation Sans"
HEATMAP_BOTTOM_MM, HEATMAP_HEIGHT_MM = 44, 12

DISPLAY_NAMES = {
    1: "Solvated ligand from SMILES",
    2: "Reject incompatible trajectories",
    3: "Binding-pocket residues",
    4: "Side-chain distance",
    5: "Protein–ligand H bonds",
    6: "THR106 rotamers",
    7: "TYK2 equilibration",
    8: "TYK2 clashes",
    9: "mGlu5 holo-to-apo",
    10: "Mg coordination",
    11: "Glycoinsulin AMBER–GROMACS",
    12: "ICL1 water transfer",
    13: "Oxymyoglobin altloc cleanup",
    14: "Ligand pose / conform. RMSD",
    15: "MenG thermostat / COM",
    16: "Ala–Phe GAFF parameters",
    17: "ICL2 interaction ranking",
    18: "Ion-charge scaling / water–decane",
    19: "Most-open TPC2 frame",
    20: "A2A ABFE dhdl analysis",
    21: "OX2R water transfer",
    22: "PepT2 PCA CV suitability",
    23: "A2A–ZM241385 POPC",
    24: "SMIRNOFF ligand parameters",
    25: "mGlu5–51D POPC",
    26: "D3 POPC membrane",
    27: "A2A–AZD4635 POPC",
    28: "PepT2 PCA umbrella setup",
    29: "PepT2–ampicillin membrane",
    30: "CAM-ion pore umbrellas",
    31: "Na+ permeation / conductance",
    32: "DHODH OpenFE RBFE",
    33: "D3 OpenFE RBFE",
    34: "OX2R OpenFE RBFE",
    35: "D3 OpenFE ABFE",
    36: "mGlu5 OpenFE ABFE",
    37: "A2A OpenFE ABFE",
    38: "PepT2–amoxicillin QM cluster",
    39: "D3 charged ABFE / GROMACS",
    40: "MenG–SAM RMSD / PBC",
    41: "Argon hydration / REXEE",
    42: "Fixed-weight expanded ensemble",
    43: "CB7–10 Wang–Landau",
    44: "ATP8B1 helix RMSD / mapping",
    45: "ATP8B1 insertion depth",
    46: "CHARMM topology / FF repair",
    47: "Phosphoaspartate parameters",
    48: "CB7–10 alchemical MetaD",
    49: "SLCO2A1 kinetic energy",
    50: "Glycoinsulin β-sheet propensity",
}


def display_name(row):
    return DISPLAY_NAMES[int(row["number"])]


def image_axes(
    fig,
    path,
    x_mm,
    y_mm,
    width_mm,
    placements,
    crop=(0, 0, 1, 1),
    frame=False,
    canvas_mm=None,
):
    """Crop pixels, then derive physical height from their aspect ratio exactly."""
    with Image.open(path) as source:
        full_width, full_height = source.size
        left, bottom, right, top = crop
        bounds = (
            round(left * full_width),
            round((1 - top) * full_height),
            round(right * full_width),
            round((1 - bottom) * full_height),
        )
        image = source.crop(bounds)
    left, upper, right, lower = bounds
    extent = (
        left / full_width,
        right / full_width,
        1 - lower / full_height,
        1 - upper / full_height,
    )
    height_mm = width_mm * image.height / image.width
    canvas_width, canvas_height = canvas_mm or (WIDTH_MM, HEIGHT_MM)
    ax = fig.add_axes(
        [
            x_mm / canvas_width,
            y_mm / canvas_height,
            width_mm / canvas_width,
            height_mm / canvas_height,
        ]
    )
    ax.imshow(image, extent=extent, aspect="auto", interpolation="none")
    ax.set(xlim=extent[:2], ylim=extent[2:])
    ax.set_axis_off()
    if frame:
        ax.add_patch(
            Rectangle(
                (0, 0),
                1,
                1,
                fill=False,
                edgecolor="#AAAAAA",
                lw=0.45,
                transform=ax.transAxes,
                clip_on=False,
            )
        )
    placements.append(
        {
            "source": str(path.relative_to(OUTPUT)),
            "source_sha256": sha256(path),
            "source_pixels": [full_width, full_height],
            "crop_pixels": list(bounds),
            "cropped_pixels": list(image.size),
            "original_fraction_extent": list(extent),
            "placement_mm": [x_mm, y_mm, width_mm, height_mm],
            "effective_dpi": image.width / (width_mm / 25.4),
        }
    )
    return ax


def distance_marker(ax, points, label, offset=(0, 0)):
    first, second = np.array(points)
    ax.plot(
        [first[0], second[0]],
        [first[1], second[1]],
        color="#333333",
        lw=0.65,
        ls=(0, (2, 1.6)),
        zorder=8,
    )
    ax.scatter(
        [first[0], second[0]],
        [first[1], second[1]],
        s=3.3,
        color="#333333",
        zorder=9,
        linewidths=0,
    )
    ax.text(
        *((first + second) / 2 + offset),
        label,
        ha="center",
        va="center",
        fontsize=7.8,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.1},
        zorder=10,
    )


def add_image(fig, name, x, y, width, placements, crop=(0, 0, 1, 1), frame=False):
    return image_axes(
        fig,
        OUTPUT / f"renders/{name}.png",
        x,
        y,
        width,
        placements,
        crop,
        frame,
        canvas_mm=(WIDTH_MM, HEIGHT_MM),
    )


def panel_label(fig, x, y, letter, details=None):
    label = fig.text(
        x / WIDTH_MM,
        y / HEIGHT_MM,
        letter,
        fontsize=8.5,
        fontweight="bold",
        fontfamily=FONT_FAMILY,
        va="center",
    )
    if details:
        label_top_mm = (
            label.get_window_extent(fig.canvas.get_renderer()).y1 * 25.4 / fig.dpi
        )
        fig.text(
            (x + 4) / WIDTH_MM,
            (label_top_mm - 0.2) / HEIGHT_MM,
            "\n".join(details),
            fontsize=DETAIL_FONT_SIZE,
            va="top",
            linespacing=1.35,
        )


def protein_center_x(stage, camera, placement):
    """Center each state label on the projected protein, excluding the displaced ligand."""
    atoms, _ = load_atoms(HERE / f"derived/task25_{stage}_protein.pdb")
    alpha_carbons = positions([atom for atom in atoms if atom["name"] == "CA"])
    projected = alpha_carbons @ np.array(camera["basis"]) - camera["center_A"]
    horizontal = 0.5 + projected[:, 0] / camera["width_A"]
    center = (horizontal.min() + horizontal.max()) / 2
    left, right, _, _ = placement["original_fraction_extent"]
    x, _, width, _ = placement["placement_mm"]
    return float(x + (center - left) / (right - left) * width)


def heatmap(fig, rows):
    panel_label(fig, 1, 70.3, "A")
    ax = fig.add_axes(
        [
            24 / WIDTH_MM,
            HEATMAP_BOTTOM_MM / HEIGHT_MM,
            108 / WIDTH_MM,
            HEATMAP_HEIGHT_MM / HEIGHT_MM,
        ]
    )
    # Keep one heatmap, with a narrow blank gutter between the seven scientific task types.
    group_gap = 0.4
    column_lefts = np.array(
        [
            i + group_gap * list(GROUPS).index(row["category"])
            for i, row in enumerate(rows)
        ]
    )
    column_centers = column_lefts + 0.5
    values = np.array([[int(row[model]) for row in rows] for model in MODELS])
    for category in GROUPS:
        columns = [i for i, row in enumerate(rows) if row["category"] == category]
        edges = np.r_[column_lefts[columns], column_lefts[columns[-1]] + 1]
        ax.pcolormesh(
            edges,
            np.arange(6),
            values[:, columns],
            cmap=ListedColormap(COLORS),
            norm=BoundaryNorm(np.arange(-0.5, 4), 4),
            edgecolors="white",
            linewidth=0.18,
            rasterized=False,
        )
    ax.set(xlim=(0, column_lefts[-1] + 1), ylim=(5, 0))
    ax.set_yticks(np.arange(5) + 0.5, NAMES, fontsize=6.2)
    labels = [display_name(row) for row in rows]
    ax.set_xticks(
        column_centers, labels, fontsize=5.6, rotation=90, ha="center", va="top"
    )
    ax.tick_params(axis="y", length=0, pad=2)
    ax.tick_params(axis="x", length=0, pad=15.9)
    # Align the indices directly beneath the data; rotating them leaves clear space between columns.
    index_labels = [
        ax.text(
            center,
            -1.5 / HEATMAP_HEIGHT_MM,
            f"{int(row['number']):02d}",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="center",
            rotation=90,
            fontsize=5.4,
            fontweight="bold",
        )
        for center, row in zip(column_centers, rows)
    ]
    for spine in ax.spines.values():
        spine.set_visible(False)
    for column, row in enumerate(rows):
        shared = all(int(row[model]) == 3 for model in MODELS[:3])
        ax.add_patch(
            Rectangle(
                (column_lefts[column], 1 + 0.8 / HEATMAP_HEIGHT_MM),
                1,
                0.9 / HEATMAP_HEIGHT_MM,
                transform=ax.get_xaxis_transform(),
                facecolor="#344F48" if shared else "#F4F4F4",
                edgecolor="white",
                lw=0.25,
                clip_on=False,
            )
        )
    ax.text(
        -0.4,
        1 + 1.25 / HEATMAP_HEIGHT_MM,
        "Shared by top 3",
        transform=ax.get_xaxis_transform(),
        ha="right",
        va="center",
        fontsize=5.5,
    )
    titles = []
    for type_index, (category, label) in enumerate(GROUPS.items()):
        indices = [i for i, row in enumerate(rows) if row["category"] == category]
        left, right = column_lefts[min(indices)], column_lefts[max(indices)] + 1
        # Two horizontal levels keep full task-type words legible without overlap.
        label = label.replace("System preparation", "System\npreparation")
        header_y_mm = 60 if type_index % 2 == 0 else 64
        height = 1 + (header_y_mm - 56) / HEATMAP_HEIGHT_MM
        titles.append(
            ax.text(
                (left + right) / 2,
                height,
                label,
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=5.8,
                rotation=0,
            )
        )
        ax.plot(
            [left + 0.08, right - 0.08],
            [1 + 1.9 / HEATMAP_HEIGHT_MM] * 2,
            transform=ax.get_xaxis_transform(),
            color="#BBBBBB",
            lw=0.45,
            clip_on=False,
        )
        if type_index % 2:
            ax.plot(
                [(left + right) / 2] * 2,
                [
                    1 + 1.9 / HEATMAP_HEIGHT_MM,
                    1 + (header_y_mm - 56 - 0.6) / HEATMAP_HEIGHT_MM,
                ],
                transform=ax.get_xaxis_transform(),
                color="#BBBBBB",
                lw=0.35,
                clip_on=False,
            )
    for center, row in zip(column_centers, rows):
        ax.text(
            center,
            (40.0 - HEATMAP_BOTTOM_MM) / HEATMAP_HEIGHT_MM,
            row["difficulty"][0].upper(),
            transform=ax.get_xaxis_transform(),
            fontsize=5.2,
            ha="center",
            va="center",
        )
    for y, label in [(42.5, "Task ID"), (40.0, "Difficulty")]:
        ax.text(
            -0.5,
            (y - HEATMAP_BOTTOM_MM) / HEATMAP_HEIGHT_MM,
            label,
            transform=ax.get_xaxis_transform(),
            ha="right",
            va="center",
            fontsize=5.0,
        )
    for row, label, index in zip(rows, ax.get_xticklabels(), index_labels):
        if int(row["number"]) in [25, 29]:
            label.set_color("#8E542C")
            index.set_color("#8E542C")
    fig.text(
        26 / WIDTH_MM,
        1.5 / HEIGHT_MM,
        "Strict passes out of 3",
        fontsize=6.2,
        va="center",
    )
    for value, color in enumerate(COLORS):
        x = 61 + 7 * value
        fig.add_artist(
            Rectangle(
                (x / WIDTH_MM, 0.8 / HEIGHT_MM),
                3 / WIDTH_MM,
                1.5 / HEIGHT_MM,
                transform=fig.transFigure,
                facecolor=color,
                edgecolor="none",
            )
        )
        fig.text(
            (x + 3.7) / WIDTH_MM, 1.5 / HEIGHT_MM, str(value), fontsize=6.2, va="center"
        )
    fig.text(
        93 / WIDTH_MM,
        1.5 / HEIGHT_MM,
        "E/M/H: easy/medium/hard",
        fontsize=5.6,
        va="center",
    )
    return list(ax.get_xticklabels()), titles, index_labels


def label_spacing(fig, labels):
    """Check all task names and type headings at their actual print size."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    scale = 25.4 / fig.dpi
    names, titles, indices = labels
    boxes = [label.get_window_extent(renderer) for label in names]
    bounds = []
    for box in boxes:
        x, y, width, height = np.array(box.bounds) * scale
        assert x >= 0 and y >= 0 and x + width <= WIDTH_MM and y + height <= HEIGHT_MM
        bounds.append([float(v) for v in [x, y, width, height]])
    gaps = [(right.x0 - left.x1) * scale for left, right in zip(boxes, boxes[1:])]
    assert min(gaps) > 0, "Task names collide"
    boxes = [label.get_window_extent(renderer) for label in titles]
    assert not any(
        a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i + 1 :]
    ), "Task-type headings collide"
    for box in boxes:
        assert (
            box.x0 >= 0
            and box.y0 >= 0
            and box.x1 <= fig.bbox.width
            and box.y1 <= fig.bbox.height
        )
    boxes = [label.get_window_extent(renderer) for label in indices]
    index_gap = min(
        (right.x0 - left.x1) * scale for left, right in zip(boxes, boxes[1:])
    )
    assert index_gap > 0, "Task indices collide"
    return {
        "minimum_task_label_gap_mm": float(min(gaps)),
        "task_type_labels_do_not_overlap": True,
        "minimum_index_gap_mm": float(index_gap),
        "task_indices_on_one_baseline": True,
        "task_label_bounds_mm": bounds,
    }


def structures(fig, cameras, placements):
    camera = cameras["task25"]
    panel_label(
        fig,
        135,
        70.3,
        "B",
        (
            "Task 25 · Claude Opus-5.5 · replicate 3",
            "Correctness: 1.000; Process: 0.875",
        ),
    )
    before = add_image(
        fig, "task25_intermediate_selected", 135.5, 37.0, 23.4, placements, TASK25_CROP
    )
    after = add_image(
        fig, "task25_submitted_selected", 160.4, 37.0, 23.4, placements, TASK25_CROP
    )
    state_centers = {}
    for stage, title, placement in zip(
        ["intermediate", "submitted"], ["Intermediate", "Submitted"], placements[:2]
    ):
        x = protein_center_x(stage, camera, placement)
        state_centers[stage] = x
        fig.text(
            x / WIDTH_MM,
            43.6 / HEIGHT_MM,
            title,
            fontsize=DETAIL_FONT_SIZE,
            ha="center",
            va="top",
        )
    distance_marker(
        after, camera["contact_endpoints_fraction"], "37.8 Å", offset=(0.02, 0.05)
    )
    after.texts[-1].set_fontsize(6.4)
    chlorine, hydrogen = camera["contact_endpoints_fraction"]
    after.annotate(
        "Cl",
        chlorine,
        xytext=(4, 3),
        textcoords="offset points",
        fontsize=DETAIL_FONT_SIZE,
        color="#436832",
    )
    after.annotate(
        "Lys117 HZ2",
        hydrogen,
        xytext=(-24, 8),
        ha="right",
        va="bottom",
        arrowprops={"arrowstyle": "-", "lw": 0.4},
        textcoords="offset points",
        fontsize=DETAIL_FONT_SIZE,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
    )
    pocket = add_image(
        fig, "task25_pocket_selected", 148.0, 52.9, 12.0, placements, frame=True
    )
    pocket.text(
        0.5,
        1.05,
        "Pocket",
        transform=pocket.transAxes,
        ha="center",
        fontsize=DETAIL_FONT_SIZE,
    )
    center = np.array(camera["pocket_camera"]["center_A"])
    bound = [
        0.5 + (center[0] - camera["center_A"][0]) / camera["width_A"],
        0.5 + (center[1] - camera["center_A"][1]) / camera["height_A"],
    ]
    before.add_patch(
        Rectangle(
            (bound[0] - 0.07, bound[1] - 0.045),
            0.14,
            0.09,
            fill=False,
            edgecolor="#777777",
            lw=0.45,
        )
    )
    fig.add_artist(
        ConnectionPatch(
            (bound[0] + 0.07, bound[1]),
            (0, 0.5),
            coordsA=before.transData,
            coordsB=pocket.transAxes,
            color="#888888",
            lw=0.45,
        )
    )

    # A quiet separator makes the two equally sized case panels distinct.
    fig.add_artist(
        plt.Line2D(
            [135 / WIDTH_MM, 184 / WIDTH_MM],
            [36.65 / HEIGHT_MM] * 2,
            transform=fig.transFigure,
            color="#BBBBBB",
            lw=0.35,
        )
    )
    camera = cameras["task29"]
    # B and C each occupy a separate 36.65 mm band; neither panel crosses the boundary.
    panel_label(
        fig,
        135,
        33.65,
        "C",
        (
            "Task 29 · Claude Opus-5.5 · replicate 2",
            "Correctness: 1.000; Process: 0.9375",
        ),
    )
    overview = add_image(
        fig, "task29_submitted_selected", 137, 3.0, 28.0, placements, TASK29_CROP
    )
    center = np.array(camera["contact_endpoints_fraction"]).mean(axis=0)
    overview.add_patch(
        Rectangle(
            (center[0] - 0.06, center[1] - 0.06),
            0.12,
            0.12,
            fill=False,
            edgecolor="#777777",
            lw=0.5,
        )
    )
    overview.annotate(
        "AMP702",
        camera["ligand_center_fraction"],
        xytext=(0.13, -0.005),
        textcoords="axes fraction",
        fontsize=DETAIL_FONT_SIZE,
        color=CYAN,
        ha="center",
        va="top",
        arrowprops={"arrowstyle": "-", "lw": 0.45, "color": CYAN},
    )
    # A colored label below the molecule avoids adding whitespace above C.
    overview.text(
        0.62,
        -0.005,
        "POPE808",
        transform=overview.transAxes,
        fontsize=DETAIL_FONT_SIZE,
        color=GOLD,
        ha="center",
        va="top",
    )
    detail = add_image(
        fig, "task29_contact_selected", 160.8, 4.55, 23.0, placements, frame=True
    )
    detail.text(
        0.5,
        1.04,
        "Clash detail",
        transform=detail.transAxes,
        ha="center",
        fontsize=DETAIL_FONT_SIZE,
    )
    points = camera["contact_camera"]["contact_endpoints_fraction"]
    distance_marker(detail, points, "1.37 Å", offset=(0, 0.30))
    detail.texts[-1].set_fontsize(6.4)
    for label, point, textpos, color in [
        ("C6", points[0], (0.18, -0.11), CYAN),
        ("C316", points[1], (0.8, -0.11), GOLD),
    ]:
        detail.annotate(
            label,
            point,
            xytext=textpos,
            textcoords="axes fraction",
            fontsize=DETAIL_FONT_SIZE,
            ha="center",
            va="top",
            color=color,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
            arrowprops={"arrowstyle": "-", "color": color, "lw": 0.45},
        )
    fig.add_artist(
        ConnectionPatch(
            (center[0] + 0.06, center[1]),
            (0, 0.5),
            coordsA=overview.transData,
            coordsB=detail.transAxes,
            color="#888888",
            lw=0.45,
        )
    )

    return state_centers


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 7,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    with (DATA / "task_success.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    cameras = json.loads((DATA / "camera_settings.json").read_text())
    fig = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), dpi=300)
    placements = []
    label_artists = heatmap(fig, rows)
    state_centers = structures(fig, cameras, placements)
    spacing = label_spacing(fig, label_artists)
    fig.savefig(OUTPUT / "figure_5.pdf", dpi=600)
    for ax in fig.axes:
        for image in ax.images:
            image.set_interpolation("hanning")
    fig.savefig(OUTPUT / "figure_5.png", dpi=600)
    with Image.open(OUTPUT / "figure_5.png") as image:
        image.resize(
            (round(WIDTH_MM / 25.4 * 150), round(HEIGHT_MM / 25.4 * 150)),
            Image.Resampling.LANCZOS,
        ).save(OUTPUT / "preview_at_manuscript_width.png", dpi=(150, 150))
    plt.close(fig)
    layout = {
        "width_mm": WIDTH_MM,
        "height_mm": HEIGHT_MM,
        "arrangement": "A left, one continuous 5-row by 50-column heatmap; B/C stacked right",
        "panels": {
            "A": "Named task heatmap",
            "B": "Task 25 binding-pose loss",
            "C": "Task 29 ligand–lipid clash",
        },
        "right_panel_bands_mm": {"B": [36.65, 73.3], "C": [0, 36.65]},
        "heatmap": {
            "orientation": "configurations_rows_tasks_columns",
            "matrix_shape": [5, 50],
            "single_continuous_matrix": True,
            "label_rotation_degrees": 90,
            "task_index_font_weight": "bold",
            "cell_annotations": 0,
            "colors": COLORS,
            "group_labels": {
                key: value.replace("System preparation", "System\npreparation")
                for key, value in GROUPS.items()
            },
            "difficulty_labels": [row["difficulty"][0].upper() for row in rows],
            "task_indices_position": "separate aligned row below heatmap",
            "type_label_rotation_degrees": 0,
            "cell_size_mm": [108 / 52.4, HEATMAP_HEIGHT_MM / 5],
            "task_type_gutter_mm": 108 / 52.4 * 0.4,
            "label_spacing": spacing,
            "models": MODELS,
            "task_order": [row["task_id"] for row in rows],
            "task_names": [row["short_description"] for row in rows],
            "display_task_names": [display_name(row) for row in rows],
            "source_sha256": sha256(DATA / "task_success.csv"),
        },
        "typography": {
            "panel_letter_size_pt": 8.5,
            "panel_titles": False,
            "case_details_position": "two lines beside panel letter, below its top",
            "state_labels_position": "below protein representations, centered on projected CA bounds",
            "state_label_centers_x_mm": state_centers,
            "font_family": FONT_FAMILY,
            "B_C_task_scores_state_size_pt": DETAIL_FONT_SIZE,
            "replicate_labels": "replicate 2/3",
            "POPE808_label": "below molecule",
        },
        "camera_settings_sha256": sha256(DATA / "camera_settings.json"),
        "placements": placements,
    }
    (HERE / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")
    with (HERE / "task_labels_and_values.csv").open("w", newline="") as stream:
        fields = [
            "task_id",
            "number",
            "category",
            "difficulty",
            "short_description",
            "display_label",
            *MODELS,
        ]
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{key: row[key] for key in fields if key != "display_label"},
                    "display_label": display_name(row),
                }
            )
    print(
        f"Assembled Figure 5: {WIDTH_MM} × {HEIGHT_MM} mm; approved horizontal headers and all 50 task names."
    )


if __name__ == "__main__":
    main()
