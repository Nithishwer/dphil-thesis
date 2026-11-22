#!/usr/bin/env python3
"""Render the CB7-10 host-guest complex with headless PyMOL.

Run using a Python environment containing PyMOL:
    python render_cb7_10.py

The original complex.gro is copied from MDArena-dev task
48_cb7_10_alchemical_metadynamics/environment/inputs. The accompanying
cb7_10.pdb retains its HOS/MOL coordinates and topology-defined connectivity,
with coordinates converted from nanometres to angstroms.

Outputs: a transparent cb7_10.png and an editable cb7_10.pse session.
"""

from pathlib import Path

import pymol2

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_2/d-AlchMetad"
WORK = CHAPTER / "scripts/intermediates/figure_2/d-AlchMetad"
IMAGE_SIZE = 1800
DPI = 600
HOST_COLOUR = (160 / 255, 213 / 255, 104 / 255)  # #A0D568
GUEST_COLOUR = (255 / 255, 206 / 255, 84 / 255)  # #FFCE54
NITROGEN_COLOUR = (79 / 255, 193 / 255, 232 / 255)  # #4FC1E8
OXYGEN_COLOUR = (237 / 255, 85 / 255, 100 / 255)  # #ED5564
VIEW = (
    0.728066921,
    0.678287446,
    -0.099245235,
    -0.637174189,
    0.616199851,
    -0.462935507,
    -0.252848476,
    0.400281638,
    0.880819619,
    0.000000000,
    0.000000000,
    -39.088825226,
    36.118770599,
    15.162414551,
    22.879604340,
    30.817928314,
    47.359722137,
    -20.000000000,
)


def main() -> None:
    with pymol2.PyMOL() as pymol:
        cmd = pymol.cmd
        cmd.load(
            str(CHAPTER / "data/figures/figure_2/d-AlchMetad/cb7_10.pdb"), "cb7_10"
        )
        cmd.select("host", "resn HOS and not hydro")
        cmd.select("guest", "resn MOL and not hydro")
        cmd.hide("everything", "all")

        cmd.set_color("host_carbon", HOST_COLOUR)
        cmd.set_color("guest_carbon", GUEST_COLOUR)
        cmd.set_color("nitrogen", NITROGEN_COLOUR)
        cmd.set_color("oxygen", OXYGEN_COLOUR)
        cmd.color("host_carbon", "host")
        cmd.color("nitrogen", "host and elem N")
        cmd.color("oxygen", "host and elem O")
        cmd.color("guest_carbon", "resn MOL")
        cmd.show("sticks", "host or guest")
        cmd.set("stick_radius", 0.16, "host or guest")

        cmd.deselect()

        cmd.bg_color("white")
        cmd.set("orthoscopic", 1)
        cmd.set("antialias", 2)
        cmd.set("ray_shadows", 0)
        # Fade distant atoms toward the background in both the viewer and ray trace.
        cmd.set("depth_cue", 1)
        cmd.set("ray_trace_fog", 1)
        cmd.set("fog_start", 0.25)
        cmd.set("fog", 0.65)
        # Match the soft matte finish used by the a-RBFE rendering scripts.
        cmd.set("specular", 0)
        cmd.set("spec_reflect", 0)
        cmd.set("shininess", 0)
        cmd.set("ambient", 0.6)
        cmd.set("direct", 0.4)
        cmd.set("reflect", 0.15)
        cmd.set("stick_quality", 24)
        cmd.set("ray_opaque_background", 0)
        cmd.set("opaque_background", 0)
        cmd.set("max_threads", 4)
        cmd.viewport(IMAGE_SIZE, IMAGE_SIZE)
        cmd.set_view(VIEW)

        image_path = HERE / "cb7_10.png"
        cmd.png(str(image_path), width=IMAGE_SIZE, height=IMAGE_SIZE, dpi=DPI, ray=1)
        WORK.mkdir(parents=True, exist_ok=True)
        cmd.save(str(WORK / "cb7_10.pse"))
        print(f"Saved {image_path}")
        print(f"Saved {WORK / 'cb7_10.pse'}")


if __name__ == "__main__":
    main()
