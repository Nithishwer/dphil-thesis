"""Make an editable PyMOL session with PepT2 and the complete submitted bilayer."""

import json
from collections import Counter
from itertools import groupby
from pathlib import Path

import numpy as np
import pymol2
from chempy import Atom, Bond
from chempy.models import Indexed
from prepare_figure_5 import AMINO_ACIDS, element, load_atoms, sha256
from render_figure_5_structures import PALETTE, set_camera

CHAPTER = Path(__file__).resolve().parents[1]
DATA = CHAPTER / "data/figures/figure_7_7b"
WORKING = CHAPTER / "scripts/intermediates/figure_7_7b"
SESSION = WORKING / "renders/task29_full_membrane.pse"
PREVIEW = CHAPTER / "figures/figure_7_7b/full_membrane.png"


def read_topology(path):
    """Read explicit atom order and bonds, including protein residue boundaries."""
    names, bonds, section = [], [], ""
    for line in path.read_text().splitlines():
        line = line.split(";")[0].strip()
        if line.startswith("["):
            section = line.strip("[] ")
        elif line and not line.startswith("#"):
            fields = line.split()
            if section == "atoms":
                assert int(fields[0]) == len(names) + 1
                names.append(fields[4])
            elif section == "bonds":
                bonds.append((int(fields[0]) - 1, int(fields[1]) - 1))
    return names, bonds


def make_model(molecules, topology, translation, basis):
    """Keep each molecule's saved geometry and its topology-defined connectivity."""
    names, bonds = topology
    model = Indexed()
    for molecule in molecules:
        assert [atom["name"] for atom in molecule] == names
        offset = len(model.atom)
        for record in molecule:
            atom = Atom()
            atom.name = record["name"]
            atom.resn = record["resname"]
            atom.resi = str(record["resid"])
            atom.chain = "A"
            atom.id = record["row"]
            atom.symbol = element(record["name"])
            atom.hetatm = int(record["resname"] not in AMINO_ACIDS)
            atom.coord = ((np.array(record["xyz"]) + translation) @ basis).tolist()
            model.atom.append(atom)
        # Explicit bonds prevent false bonds between overlapping lipid molecules.
        for first, second in bonds:
            bond = Bond()
            bond.index = [offset + first, offset + second]
            bond.order = 1
            model.bond.append(bond)
    return model


def main():
    geometry = json.loads((DATA / "geometry.json").read_text())
    source = DATA / "system.gro"
    atoms, box = load_atoms(source)
    protein = [atom for atom in atoms if atom["resname"] in AMINO_ACIDS]
    alpha_carbon_count = sum(atom["name"] == "CA" for atom in protein)
    ligand = [atom for atom in atoms if atom["resname"] == "AMP"]
    lipids = [
        list(group)
        for _, group in groupby(
            (atom for atom in atoms if atom["resname"] in {"POPE", "POPG"}),
            key=lambda atom: (atom["resname"], atom["resid"]),
        )
    ]
    clashing = [
        molecule
        for molecule in lipids
        if (molecule[0]["resname"], molecule[0]["resid"]) == ("POPE", 808)
    ]
    assert len(clashing) == 1
    counts = Counter(molecule[0]["resname"] for molecule in lipids)
    assert counts == {"POPE": 237, "POPG": 79}
    assert {atom["resid"] for atom in ligand} == {702}

    objects = {
        "protein": ([protein], "protein.itp"),
        "ligand_AMP702": ([ligand], "AMP.itp"),
        "clashing_lipid_POPE808": (clashing, "POPE.itp"),
        "other_POPE": (
            [m for m in lipids if m[0]["resname"] == "POPE" and m[0]["resid"] != 808],
            "POPE.itp",
        ),
        "other_POPG": ([m for m in lipids if m[0]["resname"] == "POPG"], "POPG.itp"),
    }
    translation = np.array(geometry["global_translation_A"])
    # Use a side view with the membrane normal vertical; the user will choose the final view.
    basis = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    topologies = {
        filename: read_topology(source.parent / filename)
        for _, filename in objects.values()
    }
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.bg_color("white")
        for name, color in PALETTE.items():
            cmd.set_color(name, color)
        cmd.set_color("membrane_grey", [0.65, 0.68, 0.70])
        for name, (molecules, filename) in objects.items():
            model = make_model(molecules, topologies[filename], translation, basis)
            cmd.load_model(model, name)
            assert cmd.count_atoms(name) == sum(len(m) for m in molecules)
        cmd.hide("everything", "all")
        cmd.dss("protein")
        cmd.color("protein", "protein")
        cmd.show("cartoon", "protein")
        cmd.set("cartoon_transparency", 0.30, "protein")
        cmd.set("cartoon_fancy_helices", 1)
        cmd.set("cartoon_loop_radius", 0.18)

        for name in ["other_POPE", "other_POPG"]:
            cmd.color("membrane_grey", name)
            cmd.show("sticks", f"{name} and not elem H")
            cmd.set("stick_radius", 0.10, name)
            cmd.set("stick_transparency", 0.85, name)
        for name, carbon_color in [
            ("ligand_AMP702", "cyan"),
            ("clashing_lipid_POPE808", "gold"),
        ]:
            cmd.show("sticks", f"{name} and not elem H")
            cmd.color(carbon_color, name)
            for symbol, color in [
                ("O", "oxygen"),
                ("N", "nitrogen"),
                ("S+P", "sulfur"),
            ]:
                cmd.color(color, f"{name} and elem {symbol}")
            cmd.set("stick_radius", 0.23, name)

        first = "ligand_AMP702 and name C6"
        second = "clashing_lipid_POPE808 and name C316"
        distance = cmd.get_distance(first, second)
        assert abs(distance - geometry["carbon_pair"]["distance_A"]) < 1e-4
        cmd.create("clash_atoms", f"({first}) or ({second})")
        cmd.hide("everything", "clash_atoms")
        cmd.show("spheres", "clash_atoms")
        cmd.set("sphere_transparency", 0.65, "clash_atoms")
        cmd.distance("clash_distance", first, second)
        cmd.set("dash_color", "black", "clash_distance")
        cmd.set("dash_radius", 0.05, "clash_distance")
        cmd.set("label_distance_digits", 2)
        cmd.set("label_color", "black", "clash_distance")
        cmd.set("label_size", 18)

        cmd.set("orthoscopic", 1)
        cmd.set("depth_cue", 0)
        cmd.set("ray_shadows", 0)
        cmd.set("ambient", 0.5)
        cmd.set("direct", 0.55)
        cmd.set("specular", 0.12)
        cmd.set("antialias", 2)
        cmd.set("ray_opaque_background", 1)
        cmd.set("valence", 0)
        width, height = 1200, 900
        cmd.viewport(width, height)
        coordinates = cmd.get_coords("not elem H and not clash_atoms")
        low, high = coordinates.min(axis=0), coordinates.max(axis=0)
        span = max(high[1] - low[1], (high[0] - low[0]) * height / width) + 12
        camera = set_camera(cmd, (low + high) / 2, span, width / height)
        cmd.scene("full_system", "store")
        cmd.deselect()
        cmd.save(str(SESSION))
        print(f"Saved {SESSION}", flush=True)
        cmd.png(str(PREVIEW), width=width, height=height, dpi=150, ray=1)

    # Reopen the delivered session to verify completeness and the highlighted contact.
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.load(str(SESSION))
        expected = len(protein) + len(ligand) + sum(len(m) for m in lipids)
        actual = cmd.count_atoms("not clash_atoms")
        assert actual == expected
        assert cmd.count_atoms("protein and name CA") == alpha_carbon_count
        assert (
            cmd.count_atoms("protein and name CA and rep cartoon") == alpha_carbon_count
        )
        assert abs(cmd.get_distance(first, second) - distance) < 1e-5
        for name in ["other_POPE", "other_POPG"]:
            assert abs(cmd.get_setting_float("stick_transparency", name) - 0.85) < 1e-5

    report = {
        "source": str(source.relative_to(CHAPTER)),
        "source_sha256": sha256(source),
        "topology_sha256": {
            filename: sha256(source.parent / filename) for filename in topologies
        },
        "box_A": box.tolist(),
        "protein_atoms": len(protein),
        "protein_alpha_carbons": alpha_carbon_count,
        "lipid_counts": dict(counts),
        "total_atoms_excluding_contact_copies": actual,
        "highlighted_lipid": "POPE808",
        "contact_distance_A": distance,
        "global_translation_A": translation.tolist(),
        "global_rotation": basis.tolist(),
        "coordinates": "One shared rigid transform; no imaging or geometry changes.",
        "camera": camera,
        "session": str(SESSION.relative_to(CHAPTER)),
        "session_sha256": sha256(SESSION),
        "preview": str(PREVIEW.relative_to(CHAPTER)),
        "session_reopened_and_verified": True,
    }
    (WORKING / "task29_full_membrane.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        f"Verified {actual} atoms, {sum(counts.values())} lipids, {distance:.5f} A contact."
    )


if __name__ == "__main__":
    main()
