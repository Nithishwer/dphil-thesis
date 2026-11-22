"""Render the full supplied PepT2 protein and bound amoxicillin for Figure 2b.

Run with a Python environment containing PyMOL:
    python render_pept2.py

Inputs were copied unchanged from MDArena-dev task
38_pept2_qm_cluster_orca/environment/inputs. The PDB supplies the bound
coordinates; ligand.sdf supplies connectivity, not its separate ligand pose.
Outputs: pept2_complex.png (600 dpi) and editable pept2_complex.pse.
"""

from collections import Counter
from pathlib import Path

import pymol2

CHAPTER = Path(__file__).resolve().parents[4]
HERE = CHAPTER / "figures/figure_2/b-QMMM"
ROOT = CHAPTER / "data/figures/figure_2/b-QMMM"
IMAGE_WIDTH = 4800
IMAGE_HEIGHT = 3600
PROTEIN_COLOR = (160 / 255, 213 / 255, 104 / 255)  # #A0D568, Figure 2a
LIGAND_COLOR = (79 / 255, 193 / 255, 232 / 255)  # #4FC1E8, Figure 2a
VIEW = (
    -0.542038262,
    0.316666096,
    -0.778405845,
    -0.836530805,
    -0.115071520,
    0.535700500,
    0.080064312,
    0.941531122,
    0.327274144,
    -0.000045215,
    0.000082701,
    -271.100677490,
    61.972198486,
    61.217018127,
    52.801055908,
    185.595352173,
    356.609619141,
    -20.000000000,
)


def main():
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.load(str(ROOT / "structure.pdb"), "system")
        cmd.create("protein", "system and polymer.protein and not hydro")
        cmd.create("ligand", "system and resn unk and resi 915 and not hydro")
        cmd.delete("system")

        # Match SDF heavy atoms to the PDB's element-number names (C1x, O1x, ...).
        # Explicit connectivity avoids a spurious C1x-C5x bond inferred from the PDB.
        cmd.load(str(ROOT / "ligand.sdf"), "ligand_reference")
        reference = cmd.get_model("ligand_reference and not hydro")
        cmd.delete("ligand_reference")
        element_counts = Counter()
        atom_names = []
        for atom in reference.atom:
            element_counts[atom.symbol] += 1
            atom_names.append(f"{atom.symbol}{element_counts[atom.symbol]}x")
        bound_names = {atom.name for atom in cmd.get_model("ligand").atom}
        if set(atom_names) != bound_names:
            raise ValueError(
                "SDF heavy atoms do not match the bound ligand atom names."
            )
        cmd.unbond("ligand", "ligand")
        for bond in reference.bond:
            first, second = (atom_names[index] for index in bond.index)
            cmd.bond(
                f"ligand and name {first}", f"ligand and name {second}", bond.order
            )

        cmd.hide("everything", "all")
        cmd.dss("protein")
        cmd.set_color("protein_green", PROTEIN_COLOR)
        cmd.set_color("ligand_blue", LIGAND_COLOR)
        cmd.show("cartoon", "protein")
        cmd.color("protein_green", "protein")
        cmd.set("cartoon_transparency", 0, "protein")
        cmd.show("sticks", "ligand")
        cmd.color("ligand_blue", "ligand")
        cmd.set("stick_radius", 0.23, "ligand")
        cmd.set("valence", 0)

        # Match Figure 2a's white background and matte lighting, without distance haze.
        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
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
        cmd.viewport(IMAGE_WIDTH, IMAGE_HEIGHT)

        cmd.set_view(VIEW)
        cmd.deselect()

        output = HERE / "pept2_complex.png"
        cmd.png(str(output), width=IMAGE_WIDTH, height=IMAGE_HEIGHT, dpi=600, ray=1)
        cmd.save(str(HERE / "pept2_complex.pse"))
        print(f"Saved {output}", flush=True)
        print(f"Saved {HERE / 'pept2_complex.pse'}", flush=True)


if __name__ == "__main__":
    main()
