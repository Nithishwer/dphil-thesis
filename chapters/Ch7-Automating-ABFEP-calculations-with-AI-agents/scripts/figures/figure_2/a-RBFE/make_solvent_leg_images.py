"""Render the two solvated ligands with PyMOL using the supplied camera view."""

from pathlib import Path

import pymol2

CHAPTER = Path(__file__).resolve().parents[4]
HERE = CHAPTER / "figures/figure_2/a-RBFE"
ROOT = CHAPTER / "data/figures/figure_2/a-RBFE"
IMAGE_WIDTH = 4800
IMAGE_HEIGHT = 3600
FOG_START = 0.35
SCAFFOLD_COLOR = (79 / 255, 193 / 255, 232 / 255)  # #4FC1E8
ADDED_GROUP_COLOR = (255 / 255, 206 / 255, 84 / 255)  # #FFCE54
WATER_OXYGEN_COLOR = (237 / 255, 85 / 255, 100 / 255)  # #ED5564
VIEW = (
    0.970534861,
    0.064346656,
    -0.232213423,
    -0.240845695,
    0.228878543,
    -0.943190157,
    -0.007544111,
    0.971325219,
    0.237631872,
    -0.000006892,
    -0.000045098,
    -50.657875061,
    16.439970016,
    18.834005356,
    17.575885773,
    11.819276810,
    89.484252930,
    -20.000000000,
)


def main():
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
        cmd.set("antialias", 2)
        cmd.set("ray_shadows", 0)
        # Fade distant geometry toward the white background, including in PNGs.
        cmd.set("depth_cue", 1)
        cmd.set("ray_trace_fog", 1)
        cmd.set("fog_start", FOG_START)
        # Soft diffuse lighting gives the ligand a matte, chalk-like finish.
        cmd.set("specular", 0)
        cmd.set("spec_reflect", 0)
        cmd.set("shininess", 0)
        cmd.set("ambient", 0.6)
        cmd.set("direct", 0.4)
        cmd.set("reflect", 0.15)
        cmd.set("stick_quality", 24)
        cmd.set_color("scaffold", SCAFFOLD_COLOR)
        cmd.set_color("added_group", ADDED_GROUP_COLOR)
        cmd.set_color("water_oxygen", WATER_OXYGEN_COLOR)

        for name in ("11b", "13b"):
            cmd.delete("all")
            cmd.load(str(ROOT / f"{name}_solvent.pdb"), "system")
            cmd.remove("resn UNL and hydro")
            cmd.hide("everything", "all")
            cmd.select("ligand", "resn UNL")
            cmd.select("waters", "resn SOL")
            cmd.show("sticks", "ligand or waters")
            cmd.color("scaffold", "ligand")
            cmd.color("water_oxygen", "waters and elem O")
            cmd.color("white", "waters and elem H")
            cmd.set("stick_radius", 0.23, "ligand")
            cmd.set("stick_radius", 0.015, "waters")

            # These four PDB atom names identify the N-butyl group added in 13b.
            if name == "13b":
                cmd.color("added_group", "ligand and name C13+C14+C15+C16")

            cmd.deselect()
            cmd.set_view(VIEW)
            output = HERE / f"{name}_solvent.png"
            cmd.png(str(output), width=IMAGE_WIDTH, height=IMAGE_HEIGHT, dpi=600, ray=1)
            print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
