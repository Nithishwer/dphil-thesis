"""Illustrate the prepared PepT2 cluster's prescribed proton-transfer scan.

Run with Python, PyMOL, NumPy and Pillow:
    python render_proton_transfer.py
    python render_proton_transfer.py --no-labels

Read qm_cluster.xyz, atom_map.tsv and orca.inp from outputs/ or job_output/.
These are preparation artifacts, not completed QM calculations. Only the
transferring proton is interpolated along its initial vector toward the
acceptor, satisfying each prescribed O-H distance. All other atoms stay fixed.

Save three representative PNGs, proton_transfer_steps.png (600 dpi), and
proton_transfer.pse with all ten illustrative states. The full capped cluster
is retained; Tyr188, Asn192, their caps and nonpolar hydrogens are hidden.
The --no-labels option saves separate *_no_labels files without any text.
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pymol2
from PIL import Image, ImageDraw, ImageFont

CHAPTER = Path(__file__).resolve().parents[4]
HERE = CHAPTER / "figures/figure_2/b-QMMM"
ROOT = CHAPTER / "data/figures/figure_2/b-QMMM"
INPUT_DIR = ROOT / "outputs"
if not INPUT_DIR.is_dir():
    INPUT_DIR = ROOT / "job_output"

IMAGE_SIZE = 1600
DPI = 600
PROTEIN_COLOR = (160 / 255, 213 / 255, 104 / 255)  # #A0D568
LIGAND_COLOR = (79 / 255, 193 / 255, 232 / 255)  # #4FC1E8
ELEMENT_COLORS = {
    "N": (0.20, 0.35, 0.90),
    "O": (0.93, 0.33, 0.39),
    "S": (1, 0.81, 0.33),
}


def read_scan():
    """Read atom identities and the scan definition from the prepared job."""
    with (INPUT_DIR / "atom_map.tsv").open() as handle:
        atoms = list(csv.DictReader(handle, delimiter="\t"))
    lines = (INPUT_DIR / "qm_cluster.xyz").read_text().splitlines()
    xyz_atoms = [line.split() for line in lines[2:] if line.strip()]
    if len(atoms) != int(lines[0]) or len(xyz_atoms) != len(atoms):
        raise ValueError("XYZ atom count and atom map disagree.")
    for index, (atom, xyz_atom) in enumerate(zip(atoms, xyz_atoms)):
        if int(atom["index_0based"]) != index or atom["element"] != xyz_atom[0]:
            raise ValueError(f"Atom map does not match XYZ atom {index}.")
    coordinates = np.array(
        [[float(value) for value in atom[1:4]] for atom in xyz_atoms]
    )

    scan = re.search(
        r"\bB\s+(\d+)\s+(\d+)\s*=\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*(\d+)",
        (INPUT_DIR / "orca.inp").read_text(),
    )
    if scan is None:
        raise ValueError("No ORCA bond scan was found.")
    proton, acceptor = (int(value) for value in scan.group(1, 2))
    if atoms[proton]["element"] != "H" or atoms[acceptor]["element"] != "O":
        raise ValueError("Expected an H-to-O distance scan.")
    distances = np.linspace(float(scan[3]), float(scan[4]), int(scan[5]))
    direction = coordinates[proton] - coordinates[acceptor]
    if not np.isclose(np.linalg.norm(direction), distances[0], atol=1e-6):
        raise ValueError("Initial XYZ geometry does not match the ORCA scan distance.")

    # Find the proton's original donor within the same residue.
    candidates = [
        index
        for index, atom in enumerate(atoms)
        if atom["element"] in {"N", "O"}
        and (atom["resname"], atom["resid"])
        == (atoms[proton]["resname"], atoms[proton]["resid"])
    ]
    donor = min(
        candidates,
        key=lambda index: np.linalg.norm(coordinates[index] - coordinates[proton]),
    )
    if np.linalg.norm(coordinates[donor] - coordinates[proton]) > 1.25:
        raise ValueError("Could not identify the original proton donor.")
    positions = coordinates[acceptor] + distances[:, None] * direction / np.linalg.norm(
        direction
    )
    return atoms, coordinates, proton, donor, acceptor, positions


def restore_ligand_bonds(cmd):
    """Use reference heavy-atom bonds while retaining the job's protonation."""
    cmd.load(str(ROOT / "ligand.sdf"), "reference")
    reference = cmd.get_model("reference and not hydro")
    cmd.delete("reference")
    counts = Counter()
    names = []
    for atom in reference.atom:
        counts[atom.symbol] += 1
        names.append(f"{atom.symbol}{counts[atom.symbol]}x")
    if set(names) != {atom.name for atom in cmd.get_model("ligand and not hydro").atom}:
        raise ValueError("SDF heavy atoms do not match the cluster ligand.")
    cmd.unbond("ligand and not hydro", "ligand and not hydro")
    for bond in reference.bond:
        first, second = (names[index] for index in bond.index)
        cmd.bond(f"ligand and name {first}", f"ligand and name {second}", bond.order)


def set_cluster_view(cmd, atoms, coordinates, donor, acceptor):
    """Place the donor on the left and acceptor on the right in every frame."""
    horizontal = coordinates[acceptor] - coordinates[donor]
    horizontal /= np.linalg.norm(horizontal)
    tyrosine_oxygen = next(
        index
        for index, atom in enumerate(atoms)
        if atom["resname"] == "TYR" and atom["atom_name"] == "OH"
    )
    vertical = coordinates[tyrosine_oxygen] - coordinates[donor]
    vertical -= np.dot(vertical, horizontal) * horizontal
    vertical /= np.linalg.norm(vertical)
    rotation = np.array([horizontal, vertical, np.cross(horizontal, vertical)])
    center = coordinates.mean(axis=0)
    cmd.set_view((*rotation.T.ravel(), 0, 0, -60, *center, 10, 110, -20))
    cmd.turn("x", -30)
    cmd.zoom("displayed_cluster", buffer=1, complete=1)


def make_strip(frames, show_labels):
    """Combine representative states, optionally including explanatory text."""
    extra_height = 330 if show_labels else 0
    top_margin = 100 if show_labels else 0
    strip = Image.new("RGB", (3 * IMAGE_SIZE, IMAGE_SIZE + extra_height), "white")
    draw = ImageDraw.Draw(strip)
    heading_font = ImageFont.truetype("DejaVuSans.ttf", 52)
    text_font = ImageFont.truetype("DejaVuSans.ttf", 39)
    for panel, (step, image_path, donor_distance, acceptor_distance) in enumerate(
        frames
    ):
        left = panel * IMAGE_SIZE
        with Image.open(image_path) as frame:
            strip.paste(frame.convert("RGB"), (left, top_margin))
        if not show_labels:
            continue
        center = left + IMAGE_SIZE // 2
        draw.text(
            (center, 50),
            f"Scan step {step}",
            font=heading_font,
            fill="#27343b",
            anchor="mm",
        )
        draw.text(
            (center, IMAGE_SIZE + 140),
            f"N–H: {donor_distance:.2f} Å    O–H: {acceptor_distance:.2f} Å",
            font=text_font,
            fill="#27343b",
            anchor="mm",
        )
    if show_labels:
        draw.text(
            (strip.width // 2, strip.height - 85),
            "Amoxicillin N3x → H⁺ → Glu412 OE1 (biological E622)",
            font=text_font,
            fill="#27343b",
            anchor="mm",
        )
        draw.text(
            (strip.width // 2, strip.height - 30),
            "Illustrative scan positions; no QM optimization was performed.",
            font=text_font,
            fill="#27343b",
            anchor="mm",
        )
    suffix = "" if show_labels else "_no_labels"
    output = HERE / f"proton_transfer_steps{suffix}.png"
    strip.save(output, dpi=(DPI, DPI))
    print(f"Saved {output}", flush=True)


def main(show_labels=True):
    atoms, coordinates, proton, donor, acceptor, positions = read_scan()
    frames = []
    selected_steps = (0, (len(positions) - 1) // 2, len(positions) - 1)
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.set("retain_order", 1)
        cmd.load(str(INPUT_DIR / "qm_cluster.xyz"), "raw_cluster")
        model = cmd.get_model("raw_cluster")
        cmd.delete("raw_cluster")
        for index, (atom, identity) in enumerate(zip(model.atom, atoms)):
            atom.id = index + 1
            atom.name = identity["atom_name"]
            atom.resn = identity["resname"]
            atom.resi = identity["resid"]
            atom.chain = identity["chain"]
        for state, position in enumerate(positions, start=1):
            model.atom[proton].coord = position.tolist()
            cmd.load_model(model, "qm_cluster", state=state)

        # XYZ serial IDs are zero-based; use explicit one-based IDs for selections.
        cmd.alter("qm_cluster", "ID = index")

        cmd.select("ligand", "qm_cluster and resn unk")
        cmd.select("displayed_cluster", "qm_cluster and not resi 188+192")
        cmd.select("transferring_proton", f"qm_cluster and id {proton + 1}")
        cmd.select("donor", f"qm_cluster and id {donor + 1}")
        cmd.select("acceptor", f"qm_cluster and id {acceptor + 1}")
        restore_ligand_bonds(cmd)
        # Show the proton independently so no fixed bond implies the wrong attachment.
        cmd.unbond("transferring_proton", "qm_cluster")
        cmd.hide("everything", "all")
        cmd.show("sticks", "displayed_cluster and (not hydro or neighbor (elem N+O))")
        cmd.show("spheres", "transferring_proton")
        cmd.set("sphere_scale", 0.25, "transferring_proton")
        cmd.set("stick_radius", 0.16)
        cmd.set("valence", 0)
        cmd.set_color("protein_green", PROTEIN_COLOR)
        cmd.set_color("ligand_blue", LIGAND_COLOR)
        cmd.color("protein_green", "qm_cluster and elem C")
        cmd.color("ligand_blue", "ligand and elem C")
        cmd.color("white", "qm_cluster and elem H")
        for element, color in ELEMENT_COLORS.items():
            cmd.set_color(f"element_{element}", color)
            cmd.color(f"element_{element}", f"qm_cluster and elem {element}")
        for name, endpoint in (
            ("donor_distance", "donor"),
            ("acceptor_distance", "acceptor"),
        ):
            cmd.distance(name, endpoint, "transferring_proton", state=0)
            cmd.hide("labels", name)
        cmd.set("dash_color", "gray50")
        cmd.set("dash_radius", 0.035)
        cmd.set("dash_gap", 0.12)
        for residue, number, label_position in (
            ("ASN", 348, (-3, 1, 5)),
            ("GLU", 412, (2, 2.5, 5)),
        ):
            selection = f"qm_cluster and resn {residue} and resi {number} and name CA"
            cmd.label(selection, repr(f"{residue.title()}{number}"))
            cmd.set("label_position", label_position, selection)
        cmd.label("ligand and name C16x", repr("Amoxicillin"))
        cmd.set("label_position", (-3, -3, 5), "ligand and name C16x")
        cmd.label("transferring_proton", repr("H+"))
        cmd.set("label_position", (0, 1, 5), "transferring_proton")
        cmd.label("donor", repr("N3x"))
        cmd.set("label_position", (-1, -1.2, 5), "donor")
        cmd.label("acceptor", repr("OE1"))
        cmd.set("label_position", (1, -1.2, 5), "acceptor")
        cmd.set("label_color", "gray20")
        cmd.set("label_outline_color", "white")
        cmd.set("float_labels", 1)
        cmd.set("label_size", 34)

        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
        cmd.set("orthoscopic", 1)
        cmd.set("antialias", 2)
        cmd.set("ray_shadows", 0)
        cmd.set("depth_cue", 0)
        cmd.set("ray_trace_fog", 0)
        cmd.set("specular", 0)
        cmd.set("spec_reflect", 0)
        cmd.set("shininess", 0)
        cmd.set("ambient", 0.6)
        cmd.set("direct", 0.4)
        cmd.set("reflect", 0.15)
        cmd.set("stick_quality", 24)
        cmd.set("max_threads", 4)
        cmd.viewport(IMAGE_SIZE, IMAGE_SIZE)
        set_cluster_view(cmd, atoms, coordinates, donor, acceptor)
        cmd.deselect()
        if not show_labels:
            cmd.label("all", "''")
            cmd.hide("labels", "all")
        suffix = "" if show_labels else "_no_labels"

        for step in selected_steps:
            cmd.frame(step + 1)
            output = HERE / f"proton_transfer_step_{step + 1:02d}{suffix}.png"
            cmd.png(str(output), width=IMAGE_SIZE, height=IMAGE_SIZE, dpi=DPI, ray=1)
            donor_distance = np.linalg.norm(positions[step] - coordinates[donor])
            acceptor_distance = np.linalg.norm(positions[step] - coordinates[acceptor])
            frames.append((step + 1, output, donor_distance, acceptor_distance))
            print(f"Saved {output}", flush=True)
        cmd.frame(1)
        session_path = HERE / f"proton_transfer{suffix}.pse"
        cmd.save(str(session_path))
        print(f"Saved {session_path}", flush=True)
    make_strip(frames, show_labels)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Save separate versions without labels, headings or captions.",
    )
    args = parser.parse_args()
    main(show_labels=not args.no_labels)
