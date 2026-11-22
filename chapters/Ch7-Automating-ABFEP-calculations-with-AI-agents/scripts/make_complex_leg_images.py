"""Render edited protein complexes with selected side chains and a dedicated view."""

from pathlib import Path

import pymol2
from make_solvent_leg_images import (
    ADDED_GROUP_COLOR,
    FOG_START,
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    SCAFFOLD_COLOR,
    WATER_OXYGEN_COLOR,
)

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_2/a-RBFE"
ROOT = CHAPTER / "scripts/intermediates/figure_2/a-RBFE"
PROTEIN_COLOR = (160 / 255, 213 / 255, 104 / 255)  # #A0D568
# User-selected residues, identical in both ligand panels.
BINDING_SITE_RESIDUES = (86, 89, 106, 107, 110, 183, 188, 192, 196)
VIEW = (
    0.960162342,
    0.048414592,
    0.275203198,
    0.231334567,
    0.414688170,
    -0.880064189,
    -0.156734183,
    0.908668578,
    0.386971772,
    -0.000077319,
    -0.000122864,
    -36.614292145,
    16.162557602,
    18.423006058,
    16.067035675,
    -0.848967791,
    74.076538086,
    -20.000000000,
)


def main():
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
        cmd.set("antialias", 2)
        cmd.set("ray_shadows", 0)
        cmd.set("depth_cue", 1)
        cmd.set("ray_trace_fog", 1.5)
        cmd.set("fog_start", FOG_START)
        # Match the solvent-leg images' matte, chalk-like finish.
        cmd.set("specular", 0)
        cmd.set("spec_reflect", 0)
        cmd.set("shininess", 0)
        cmd.set("ambient", 0.6)
        cmd.set("direct", 0.4)
        cmd.set("reflect", 0.15)
        cmd.set("stick_quality", 24)
        cmd.set("stick_radius", 0.23)
        # Anchor side chains to the cartoon while hiding backbone sticks inside it.
        cmd.set("cartoon_side_chain_helper", 1)
        # Leave missing protein segments disconnected instead of drawing dashes.
        cmd.set("cartoon_gap_cutoff", 0)
        # Match the single-stick bonds shown in the solvent PDBs.
        cmd.set("valence", 0)
        cmd.set_color("scaffold", SCAFFOLD_COLOR)
        cmd.set_color("added_group", ADDED_GROUP_COLOR)
        cmd.set_color("protein_green", PROTEIN_COLOR)
        cmd.set_color("oxygen_red", WATER_OXYGEN_COLOR)

        for name in ("11b", "13b"):
            cmd.delete("all")
            cmd.load(str(ROOT / f"{name}_complex_edited.pdb"), "system")
            cmd.remove("hydro")
            cmd.hide("everything", "all")
            cmd.select("ligand", "system and resn UNL")
            cmd.select("receptor", "system and chain A")
            cmd.dss("receptor")
            cmd.show("cartoon", "receptor")
            cmd.color("protein_green", "receptor")
            cmd.set("cartoon_transparency", 0, "receptor")

            residue_selection = "+".join(str(resi) for resi in BINDING_SITE_RESIDUES)
            cmd.select("pocket_residues", f"receptor and resi {residue_selection}")
            if cmd.count_atoms("pocket_residues and name CA") != len(
                BINDING_SITE_RESIDUES
            ):
                raise ValueError(f"{name}: a required binding-site residue is missing.")
            cmd.select("pocket_sidechains", "pocket_residues and not name N+C+O+OXT")
            cmd.show("sticks", "pocket_sidechains")
            cmd.color("protein_green", "pocket_sidechains and elem C")
            cmd.color("blue", "pocket_sidechains and elem N")
            cmd.color("oxygen_red", "pocket_sidechains and elem O")
            cmd.color("yellow", "pocket_sidechains and elem S")
            residue_names = ", ".join(
                f"{atom.resn}{atom.resi}"
                for atom in cmd.get_model("pocket_residues and name CA").atom
            )
            print(f"{name}: binding-site residues: {residue_names}", flush=True)

            cmd.show("sticks", "ligand")
            cmd.color("scaffold", "ligand")

            if name == "13b":
                cmd.color("added_group", "ligand and name C13+C14+C15+C16")

            cmd.deselect()
            cmd.set_view(VIEW)
            output = HERE / f"{name}_complex.png"
            cmd.png(str(output), width=IMAGE_WIDTH, height=IMAGE_HEIGHT, dpi=600, ray=1)
            print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
