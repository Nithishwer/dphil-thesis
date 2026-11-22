#!/usr/bin/env python3
"""Render task-47 pAsp in the matte-stick style of Figures 2a and 2b.

Run with Python, PyMOL, NumPy and Matplotlib:
    python make_figure_2c.py

Coordinates come from the run's peptide.gro, retaining all five residues with
a rigid camera rotation only. Connectivity and torsion assignments use topol.top.
Outputs: transparent PNG/PDF/SVG, clean/marked PyMOL PNGs, and a PyMOL session.
See README.md for provenance and the meaning of the torsion labels.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pymol2
from pymol.cgo import BEGIN, COLOR, CYLINDER, END, LINE_STRIP, LINEWIDTH, VERTEX

CHAPTER = Path(__file__).resolve().parents[4]
HERE = CHAPTER / "figures/figure_2/c-pAsp"
DPI = 600
IMAGE_WIDTH = 3200
IMAGE_HEIGHT = 2400
# Exact get_view supplied by the user, applied to the existing peptide orientation.
VIEW = (
    0.907946587,
    -0.341594070,
    0.242769778,
    0.417559355,
    0.786648631,
    -0.454782754,
    -0.035627462,
    0.514292955,
    0.856863022,
    -0.000008493,
    -0.000003103,
    -70.000198364,
    -0.348471344,
    1.441730380,
    1.778938055,
    50.0,
    90.0,
    -20.0,
)
CAMERA_DISTANCE = -VIEW[11]
FIELD_OF_VIEW = abs(VIEW[17])
CAMERA_ROLL = 40.0  # Degrees around the long CA-to-P axis.
PLOT_LIMITS = ((-5.0, 8.0), (-9.6, 11.6))
INHERITED_COLOR = "#83939c"
TORSION_COLORS = {"tau1": "#248caa", "tau2": "#d49a25"}
PROTEIN_COLOR = "#a0d568"  # Match the peptide/protein carbons in Figures 2a/2b.
SIDECHAIN_COLOR = "#4fc1e8"  # Match the scaffold/ligand cyan in Figures 2a/2b.
ELEMENT_COLORS = {"N": "#3333ff", "O": "#ed5564", "P": "#ffce54"}
TORSION_LABEL_POSITIONS = {
    "omega_minus": (-4.2, 1.9),
    "phi": (-4.2, 0.4),
    "psi": (7.2, 0.1),
    "omega_plus": (7.2, -2.0),
    "chi1": (-4.2, -0.9),
    "chi2": (-4.2, -2.2),
    "tau1": (-4.2, -3.5),
    "tau2": (-4.2, -4.8),
}

# Mark the central pAsp torsions within the complete pentapeptide.
TORSION_BONDS = {
    "omega_minus": ((578, "C"), (579, "N")),
    "phi": ((579, "N"), (579, "CA")),
    "psi": ((579, "CA"), (579, "C")),
    "omega_plus": ((579, "C"), (580, "N")),
    "chi1": ((579, "CA"), (579, "CB")),
    "chi2": ((579, "CB"), (579, "CG")),
    "tau1": ((579, "CG"), (579, "OD2")),
    "tau2": ((579, "OD2"), (579, "P")),
}
TORSION_LABELS = {
    "omega_minus": r"$\omega_{-}$",
    "phi": r"$\phi$",
    "psi": r"$\psi$",
    "omega_plus": r"$\omega_{+}$",
    "chi1": r"$\chi_1$",
    "chi2": r"$\chi_2$",
    "tau1": r"$\tau_1$",
    "tau2": r"$\tau_2$",
}


def read_section(path, section_name):
    """Read GROMACS rows, including repeated dihedral sections."""
    section = ""
    rows = []
    for line in path.read_text().splitlines():
        line = line.split(";", 1)[0].strip()
        if line.startswith("["):
            section = line.strip("[] ")
        elif line and not line.startswith("#") and section == section_name:
            rows.append(line.split())
    return rows


def read_topology():
    """Check that the drawing covers all five added proper torsions."""
    path = CHAPTER / "data/figures/figure_2/c-pAsp/topol.top"
    atoms = {
        int(row[0]): (int(row[2]), row[4], row[1])
        for row in read_section(path, "atoms")
    }
    charge = sum(
        float(row[6]) for row in read_section(path, "atoms") if row[3] == "D2P"
    )
    if not np.isclose(charge, -2):
        raise ValueError(f"Expected dianionic D2P; found charge {charge}.")
    parameters = read_section(
        CHAPTER / "data/figures/figure_2/c-pAsp/phosphoasp.itp", "dihedraltypes"
    )
    added = set()
    for row in read_section(path, "dihedrals"):
        if row[4] != "9":
            continue
        quartet = [atoms[int(index)] for index in row[:4]]
        if not all(atom[0] == 579 for atom in quartet):
            continue
        types = [atom[2] for atom in quartet]
        for term in parameters:
            for ordering in (types, types[::-1]):
                if all(
                    want == "X" or want == got for want, got in zip(term[:4], ordering)
                ):
                    added.add(tuple(atom[1] for atom in quartet))
    expected = {
        ("CB", "CG", "OD2", "P"),
        ("OD1", "CG", "OD2", "P"),
        *(("CG", "OD2", "P", atom) for atom in ("OP1", "OP2", "OP3")),
    }
    if added != expected:
        raise ValueError(f"Added torsions differ from the five displayed: {added}.")
    bonds = [
        (atoms[int(row[0])][:2], atoms[int(row[1])][:2])
        for row in read_section(path, "bonds")
    ]
    for first, second in TORSION_BONDS.values():
        if (first, second) not in bonds and (second, first) not in bonds:
            raise ValueError(f"Torsion axis is not bonded: {first}, {second}.")
    return bonds


def camera_coordinates(coordinates):
    """Point CA-to-P downward while keeping the backbone spread horizontally."""
    origin = (coordinates[579, "CA"] + coordinates[579, "P"]) / 2
    up = coordinates[579, "CA"] - coordinates[579, "P"]
    up /= np.linalg.norm(up)
    right = coordinates[579, "C"] - coordinates[579, "N"]
    right -= np.dot(right, up) * up
    right /= np.linalg.norm(right)
    depth = np.cross(right, up)
    angle = np.deg2rad(CAMERA_ROLL)
    rotated_right = np.cos(angle) * right + np.sin(angle) * depth
    rotated_depth = np.cross(rotated_right, up)
    rotation = np.array([rotated_right, up, rotated_depth])
    return {key: rotation @ (xyz - origin) for key, xyz in coordinates.items()}


def project_point(point):
    """Match the perspective projection selected by the user's get_view."""
    # PyMOL stores the view rotation in OpenGL column-major order.
    rotation = np.array(VIEW[:9]).reshape(3, 3).T
    camera = rotation @ (point - np.array(VIEW[12:15])) + np.array(VIEW[9:12])
    return camera[:2] * CAMERA_DISTANCE / -camera[2]


def label_coordinates(position):
    """Place a screen annotation on a plane in front of the peptide."""
    rotation = np.array(VIEW[:9]).reshape(3, 3).T
    depth = CAMERA_DISTANCE - 15.0
    camera = np.array([*np.asarray(position) * depth / CAMERA_DISTANCE, -depth])
    return np.linalg.solve(rotation, camera - np.array(VIEW[9:12])) + np.array(
        VIEW[12:15]
    )


def torsion_arc(first, second, color):
    """Draw a small 3D rotation arc perpendicular to the actual bond axis."""
    axis = second - first
    axis /= np.linalg.norm(axis)
    horizontal = np.cross(axis, [0.0, 0.0, 1.0])
    if np.linalg.norm(horizontal) < 0.1:
        horizontal = np.cross(axis, [0.0, 1.0, 0.0])
    horizontal /= np.linalg.norm(horizontal)
    vertical = np.cross(axis, horizontal)
    center = (first + second) / 2
    angles = np.linspace(0.15, 1.8 * np.pi, 75)
    points = center + 0.34 * (
        np.cos(angles)[:, None] * horizontal + np.sin(angles)[:, None] * vertical
    )
    rgb = matplotlib.colors.to_rgb(color)
    drawing = [LINEWIDTH, 3.0, BEGIN, LINE_STRIP, COLOR, *rgb]
    for point in points:
        drawing.extend([VERTEX, *point])
    drawing.append(END)
    return drawing


def add_pymol_labels(cmd, coordinates):
    """Keep the markers and labels editable in the saved PyMOL session."""
    leaders = []
    for name, (first, second) in TORSION_BONDS.items():
        color = TORSION_COLORS.get(name, INHERITED_COLOR)
        rgb = matplotlib.colors.to_rgb(color)
        center = (coordinates[first] + coordinates[second]) / 2
        position = label_coordinates(TORSION_LABEL_POSITIONS[name])
        # Stop the leader before its text, as in the publication overlay.
        start = position + 0.18 * (center - position)
        leaders.extend([CYLINDER, *start, *center, 0.012, *rgb, *rgb])
        label = name.replace("omega_minus", "omega-").replace("omega_plus", "omega+")
        cmd.pseudoatom(f"label_{name}", pos=position.tolist(), label=label)
        cmd.set_color(f"label_color_{name}", rgb)
        cmd.set("label_color", f"label_color_{name}", f"label_{name}")
    cmd.load_cgo(leaders, "torsion_leaders")
    cmd.hide("nonbonded", "label_*")
    cmd.set("label_font_id", 7)
    cmd.set("label_size", 24)
    cmd.set("label_outline_color", "white")
    cmd.group("torsion_annotations", "label_* torsion_leaders")
    cmd.deselect()


def render_molecule(bonds):
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        # PyMOL reads GRO coordinates in nm and converts them to angstroms.
        cmd.load(str(CHAPTER / "data/figures/figure_2/c-pAsp/peptide.gro"), "pasp")
        if cmd.count_atoms("pasp") != 86:
            raise ValueError("Expected the complete 86-atom task-47 pentapeptide.")
        cmd.remove("pasp and hydro")
        model = cmd.get_model("pasp")
        residues = {(atom.resi, atom.resn) for atom in model.atom}
        expected_residues = {
            ("577", "PHE"),
            ("578", "SER"),
            ("579", "D2P"),
            ("580", "LYS"),
            ("581", "THR"),
        }
        if residues != expected_residues or len(model.atom) != 46:
            raise ValueError(
                "The drawing must retain all five residues and 46 heavy atoms."
            )
        coordinates = {
            (int(atom.resi), atom.name): np.array(atom.coord) for atom in model.atom
        }
        coordinates = camera_coordinates(coordinates)
        selections = {
            key: f"pasp and resi {key[0]} and name {key[1]}" for key in coordinates
        }
        cmd.unbond("pasp", "pasp")
        for first, second in bonds:
            if first in selections and second in selections:
                cmd.bond(selections[first], selections[second])
        # Replace coordinates with a rigid rotation; no geometry is optimized.
        model = cmd.get_model("pasp")
        cmd.load_coords(
            np.array([coordinates[int(atom.resi), atom.name] for atom in model.atom]),
            "pasp",
        )
        cmd.hide("everything")
        cmd.show("sticks", "pasp")
        cmd.set_color("protein_green", matplotlib.colors.to_rgb(PROTEIN_COLOR))
        cmd.set_color("sidechain_cyan", matplotlib.colors.to_rgb(SIDECHAIN_COLOR))
        cmd.color("protein_green", "pasp")
        cmd.color("sidechain_cyan", "pasp and resi 579 and name CB+CG")
        for element, color in ELEMENT_COLORS.items():
            cmd.set_color(f"element_{element}", matplotlib.colors.to_rgb(color))
            cmd.color(f"element_{element}", f"pasp and elem {element}")
        cmd.set("stick_radius", 0.23)
        cmd.set("valence", 0)
        cmd.bg_color("white")
        for name, value in {
            "auto_zoom": 0,  # Keep the camera fixed when adding markers and labels.
            "field_of_view": FIELD_OF_VIEW,
            "antialias": 2,
            "ray_shadows": 0,
            "depth_cue": 0,
            "ray_trace_fog": 0,
            "specular": 0,
            "spec_reflect": 0,
            "shininess": 0,
            "ambient": 0.6,
            "direct": 0.4,
            "reflect": 0.15,
            "stick_quality": 24,
            "ray_opaque_background": 0,
            "opaque_background": 0,
            "max_threads": 4,
        }.items():
            cmd.set(name, value)
        cmd.viewport(IMAGE_WIDTH, IMAGE_HEIGHT)
        cmd.set_view(VIEW)
        cmd.deselect()
        cmd.png(
            str(HERE / "pasp_clean.png"),
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            dpi=DPI,
            ray=1,
        )
        for name, (first, second) in TORSION_BONDS.items():
            color = TORSION_COLORS.get(name, INHERITED_COLOR)
            cmd.load_cgo(
                torsion_arc(coordinates[first], coordinates[second], color), name
            )
        cmd.group("torsion_markers", " ".join(TORSION_BONDS))
        cmd.png(
            str(HERE / "pasp.png"),
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            dpi=DPI,
            ray=1,
        )
        add_pymol_labels(cmd, coordinates)
        cmd.save(str(HERE / "pasp.pse"))
    return coordinates


def make_panel(coordinates):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    figure = plt.figure(figsize=(5.8, 8.8))
    ax = figure.add_axes((0.02, 0.02, 0.96, 0.96))
    half_height = CAMERA_DISTANCE * np.tan(np.deg2rad(FIELD_OF_VIEW / 2))
    half_width = half_height * IMAGE_WIDTH / IMAGE_HEIGHT
    ax.imshow(
        plt.imread(HERE / "pasp.png"),
        extent=(-half_width, half_width, -half_height, half_height),
    )
    ax.set(xlim=PLOT_LIMITS[0], ylim=PLOT_LIMITS[1])
    ax.axis("off")

    # Project the annotations with the same perspective as the PyMOL rendering.
    for name, (first, second) in TORSION_BONDS.items():
        center = project_point((coordinates[first] + coordinates[second]) / 2)
        color = TORSION_COLORS.get(name, INHERITED_COLOR)
        ax.annotate(
            TORSION_LABELS[name],
            xy=center,
            xytext=TORSION_LABEL_POSITIONS[name],
            color=color,
            fontsize=16,
            ha="center",
            va="center",
            arrowprops={
                "arrowstyle": "-",
                "color": color,
                "linewidth": 1.0,
                "shrinkA": 8,
                "shrinkB": 6,
            },
        )

    for extension in ("png", "pdf", "svg"):
        output = HERE / f"figure_2c.{extension}"
        figure.savefig(output, dpi=DPI, transparent=True)
        print(f"Saved {output}")
    plt.close(figure)


def main():
    bonds = read_topology()
    coordinates = render_molecule(bonds)
    make_panel(coordinates)
    print(
        "Validated all five residues, 46 heavy atoms, D2P charge, and five added torsions."
    )


if __name__ == "__main__":
    main()
