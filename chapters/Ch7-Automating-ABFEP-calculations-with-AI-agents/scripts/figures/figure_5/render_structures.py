"""Render coordinate-faithful PyMOL candidates and save every camera setting.

These full-frame renders and their cameras are retained in Figure 5. The
assembly script crops existing pixels and derives each placement's height from
its pixel ratio; it never changes the coordinates or this camera.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pymol2

CHAPTER = Path(__file__).resolve().parents[3]
HERE = CHAPTER / "data/figures/figure_5"
OUTPUT = CHAPTER / "figures/figure_5"
DERIVED = HERE / "derived"
RENDERS = OUTPUT / "renders"
PALETTE = {
    "protein": [0.73, 0.86, 0.57],
    "cyan": [0.22, 0.72, 0.85],
    "gold": [0.85, 0.67, 0.32],
    "oxygen": [0.91, 0.28, 0.36],
    "nitrogen": [0.21, 0.29, 0.91],
    "sulfur": [0.95, 0.77, 0.25],
    "halogen": [0.51, 0.78, 0.34],
}


def unit(vector):
    return vector / np.linalg.norm(vector)


def basis_from_axes(right, up):
    right = unit(np.array(right, dtype=float))
    up = unit(np.array(up, dtype=float) - np.dot(up, right) * right)
    return np.column_stack([right, up, np.cross(right, up)])


def axis_rotation(axis, degrees):
    x, y, z = unit(np.array(axis, dtype=float))
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    angle = np.deg2rad(degrees)
    return np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * (skew @ skew)


def load_scene(cmd, task, stage, basis):
    cmd.reinitialize()
    cmd.bg_color("white")
    cmd.set("orthoscopic", 1)
    cmd.set("ray_opaque_background", 1)
    cmd.set("ray_trace_mode", 0)
    cmd.set("ray_trace_color", [0.37, 0.43, 0.33])
    cmd.set("ray_trace_gain", 0.035)
    cmd.set("antialias", 2)
    cmd.set("ray_shadows", 0)
    cmd.set("ambient", 0.5)
    cmd.set("direct", 0.55)
    cmd.set("specular", 0.12)
    cmd.set("shininess", 18)
    cmd.set("depth_cue", 0)
    cmd.set("cartoon_fancy_helices", 1)
    cmd.set("cartoon_flat_sheets", 1)
    cmd.set("cartoon_loop_radius", 0.18)
    cmd.set("cartoon_oval_width", 0.18)
    cmd.set("cartoon_oval_length", 0.85)
    cmd.set("stick_radius", 0.17)
    cmd.set("stick_quality", 20)
    cmd.set("sphere_quality", 3)
    cmd.set("valence", 0)
    for name, color in PALETTE.items():
        cmd.set_color(name, color)
    prefix = f"task25_{stage}" if task == 25 else "task29"
    names = ["protein", "ligand"] + (["lipid"] if task == 29 else [])
    for name in names:
        cmd.load(str(DERIVED / f"{prefix}_{name}.pdb"), name)
        coordinates = cmd.get_coords(name)
        cmd.load_coords(coordinates @ basis, name)
    cmd.hide("everything", "all")
    cmd.color("protein", "protein")
    cmd.show("cartoon", "protein")
    cmd.dss("protein")
    cmd.set("cartoon_transparency", 0.12, "protein")
    cmd.color("cyan", "ligand")
    cmd.show("sticks", "ligand and not elem H")
    for elem, color in [
        ("O", "oxygen"),
        ("N", "nitrogen"),
        ("S", "sulfur"),
        ("F+Cl+Br", "halogen"),
    ]:
        cmd.color(color, f"ligand and elem {elem}")
    if task == 25 and stage == "submitted":
        # The audited nearest atom is a hydrogen. Keep that exact side chain and H visible.
        cmd.show("sticks", "protein and resi 117 and (not elem H or name HZ2)")
        cmd.set("stick_radius", 0.13, "protein")
        cmd.color("nitrogen", "protein and resi 117 and elem N")
        cmd.color("white", "protein and resi 117 and elem H")
    if task == 29:
        cmd.color("gold", "lipid")
        cmd.show("sticks", "lipid and not elem H")
        for elem, color in [("O", "oxygen"), ("N", "nitrogen"), ("P", "sulfur")]:
            cmd.color(color, f"lipid and elem {elem}")
        cmd.hide("cartoon", "protein")
        cmd.show("cartoon", "byres (protein within 12 of ligand)")
        cmd.set("cartoon_transparency", 0.82, "protein")
        cmd.create("contact_spheres", "(ligand and name C6) or (lipid and name C316)")
        cmd.hide("everything", "contact_spheres")
        cmd.show("spheres", "contact_spheres")
        cmd.set("sphere_scale", 1, "contact_spheres")
        cmd.set("sphere_transparency", 0.67, "contact_spheres")
        # Prevent any proximity-derived AMP--POPE bond: these are distinct covalent objects.
        assert (
            cmd.count_atoms("ligand and name C6")
            == cmd.count_atoms("lipid and name C316")
            == 1
        )
    return names


def set_camera(cmd, center, height_A, aspect):
    distance = height_A / (2 * np.tan(np.deg2rad(10)))
    view = (
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        -distance,
        *center,
        distance - 130,
        distance + 130,
        20.0,
    )
    cmd.set_view(view)
    return {
        "view": list(cmd.get_view()),
        "center_A": [float(x) for x in center],
        "height_A": float(height_A),
        "width_A": float(height_A * aspect),
        "orthoscopic": True,
        "field_of_view_degrees": 20,
    }


def projected(point, basis, camera):
    point = np.array(point) @ basis - camera["center_A"]
    return [
        float(0.5 + point[0] / camera["width_A"]),
        float(0.5 + point[1] / camera["height_A"]),
    ]


def render(cmd, destination, width, height):
    print(f"Rendering {destination.name}", flush=True)
    cmd.png(str(destination), width=width, height=height, dpi=600, ray=1, quiet=0)


def task25(cmd, geometry, index, yaw, tilt, final):
    displacement = np.array(geometry["task25"]["display_ligand_center_A"])
    right = unit(np.array([displacement[0], displacement[1], 0.0]))
    base = basis_from_axes(right, [0, 0, 1])
    basis = axis_rotation([0, 0, 1], yaw) @ base @ axis_rotation([1, 0, 0], tilt)
    names = load_scene(cmd, 25, "submitted", basis)
    points = np.concatenate([cmd.get_coords(name) for name in names])
    extent_min, extent_max = points.min(axis=0), points.max(axis=0)
    center = (extent_min + extent_max) / 2
    # A common camera span and center for both states preserves receptor orientation and scale.
    aspect = 0.78
    span = max(
        (extent_max[1] - extent_min[1]) + 10,
        ((extent_max[0] - extent_min[0]) + 10) / aspect,
    )
    camera = set_camera(cmd, center, span, aspect)
    camera.update(basis=basis.tolist(), task=25, candidate=index, yaw=yaw, tilt=tilt)
    camera["contact_endpoints_fraction"] = [
        projected(p, basis, camera) for p in geometry["task25"]["display_endpoints_A"]
    ]
    width = 1404 if final else 624
    height = 1800 if final else 800
    out = RENDERS if final else RENDERS / "candidates"
    for stage in ["submitted", "intermediate"]:
        load_scene(cmd, 25, stage, basis)
        cmd.set_view(camera["view"])
        render(cmd, out / f"task25_{stage}_{index}.png", width, height)
        if final:
            cmd.save(str(RENDERS / f"task25_{stage}.pse"))
    # A separate magnified view shows actual pocket contacts in the intermediate only.
    load_scene(cmd, 25, "intermediate", basis)
    cmd.set("cartoon_transparency", 0.55, "protein")
    center_pocket = cmd.get_coords("ligand and not elem H").mean(axis=0)
    inset_camera = set_camera(cmd, center_pocket, 21.0, 1.25)
    render(
        cmd,
        out / f"task25_pocket_{index}.png",
        1250 if final else 625,
        1000 if final else 500,
    )
    camera["pocket_camera"] = inset_camera
    return camera


def task29(cmd, geometry, index, tilt, roll, final):
    endpoints = np.array(geometry["task29"]["display_endpoints_A"])
    from prepare_figure_5 import load_atoms

    lipid, _ = load_atoms(DERIVED / "task29_lipid.pdb")
    head = np.array(next(a["xyz"] for a in lipid if a["name"] == "P"))
    base = basis_from_axes(endpoints[1] - endpoints[0], head)
    # Rotating about the contact axis keeps the measured separation in the image plane.
    basis = base @ axis_rotation([1, 0, 0], tilt) @ axis_rotation([0, 0, 1], roll)
    load_scene(cmd, 29, "submitted", basis)
    coordinates = np.concatenate(
        [cmd.get_coords(n + " and not elem H") for n in ["ligand", "lipid"]]
    )
    extent_min, extent_max = coordinates.min(axis=0), coordinates.max(axis=0)
    center = (extent_min + extent_max) / 2
    aspect = 1.0
    span = max(
        (extent_max[1] - extent_min[1]) + 7,
        ((extent_max[0] - extent_min[0]) + 7) / aspect,
    )
    camera = set_camera(cmd, center, span, aspect)
    camera.update(basis=basis.tolist(), task=29, candidate=index, tilt=tilt, roll=roll)
    camera["contact_endpoints_fraction"] = [
        projected(p, basis, camera) for p in endpoints
    ]
    camera["ligand_center_fraction"] = projected(
        np.array([a["xyz"] for a in load_atoms(DERIVED / "task29_ligand.pdb")[0]]).mean(
            axis=0
        ),
        basis,
        camera,
    )
    camera["lipid_head_fraction"] = projected(head, basis, camera)
    out = RENDERS if final else RENDERS / "candidates"
    render(
        cmd,
        out / f"task29_submitted_{index}.png",
        1800 if final else 900,
        1800 if final else 900,
    )
    if final:
        cmd.save(str(RENDERS / "task29_submitted.pse"))
    # True 1.7 Å carbon radii, transparency only; no change to atom coordinates.
    cmd.hide("cartoon", "protein")
    inset_camera = set_camera(cmd, [0, 0, 0], 9.5, 1.5)
    render(
        cmd,
        out / f"task29_contact_{index}.png",
        1650 if final else 825,
        1100 if final else 550,
    )
    inset_camera["contact_endpoints_fraction"] = [
        projected(p, basis, inset_camera) for p in endpoints
    ]
    camera["contact_camera"] = inset_camera
    return camera


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--final",
        action="store_true",
        help="Render the selected angles at >=600 dpi for final placement",
    )
    args = parser.parse_args()
    RENDERS.mkdir(exist_ok=True)
    (RENDERS / "candidates").mkdir(exist_ok=True)
    geometry = json.loads((HERE / "verified_geometry.json").read_text())
    cameras = {}
    with pymol2.PyMOL() as p:
        if args.final:
            cameras["task25"] = task25(p.cmd, geometry, "selected", -25, 12, True)
            cameras["task29"] = task29(p.cmd, geometry, "selected", 30, -12, True)
        else:
            for index, (yaw, tilt) in enumerate([(0, 0), (-25, 12), (25, -12)], 1):
                cameras[f"task25_{index}"] = task25(
                    p.cmd, geometry, str(index), yaw, tilt, False
                )
            for index, (tilt, roll) in enumerate([(0, 0), (30, -12), (-30, 12)], 1):
                cameras[f"task29_{index}"] = task29(
                    p.cmd, geometry, str(index), tilt, roll, False
                )
    filename = "camera_settings.json" if args.final else "candidate_cameras.json"
    (HERE / filename).write_text(json.dumps(cameras, indent=2) + "\n")
    print(
        f"Rendered {'selected scenes' if args.final else 'three candidate angles per example'} with PyMOL."
    )


if __name__ == "__main__":
    main()
