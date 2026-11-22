"""Check saved coordinates, PDF resolution, source preservation and review copies."""

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
import PIL
import pymol2
import scipy
from PIL import Image
from prepare_figure_5 import (
    AMINO_ACIDS,
    HERE,
    OUTPUT,
    REPO,
    load_atoms,
    positions,
    read_csv,
    sha256,
)


def main():
    sources = json.loads((HERE / "source_manifest.json").read_text())
    geometry = json.loads((HERE / "verified_geometry.json").read_text())
    cameras = json.loads((HERE / "camera_settings.json").read_text())
    revision = json.loads((HERE / "layout_revision_manifest.json").read_text())
    layout = json.loads((HERE / "layout.json").read_text())
    selection = json.loads((HERE / "selection_manifest.json").read_text())
    palette_approval = selection.get("palette_revisions", [selection])[-1]
    assert all(sha256(Path(p["path"])) == p["sha256"] for p in sources["inputs"])
    assert (
        sha256(HERE / "source_manifest.json")
        == revision["original_source_manifest_sha256"]
    )
    assert all(
        sha256(REPO / path) == digest
        for path, digest in revision["protected_local_files"].items()
    )
    assert len(read_csv(HERE / "task_success.csv")) == 50
    shared = [
        r
        for r in read_csv(HERE / "task_success.csv")
        if r["shared_top_three"] == "True"
    ]
    assert len(shared) == geometry["shared_tasks"] == 42
    assert (
        sum(r["difficulty"] == "hard" for r in shared)
        == geometry["shared_hard_tasks"]
        == 12
    )

    # Check that every rendered atom derives from the recorded whole-structure transform.
    final, _ = load_atoms(Path(geometry["task25"]["final_artifact"]))
    intermediate, _ = load_atoms(Path(geometry["task25"]["intermediate_artifact"]))
    g25 = geometry["task25"]
    R, t = np.array(g25["row_vector_rotation"]), np.array(g25["final_translation_A"])
    shift = np.array(g25["final_ligand_whole_molecule_translation_A"])
    max_rounding_error = 0.0
    for stage, atoms in [("intermediate", intermediate), ("submitted", final)]:
        for name in ["protein", "ligand"]:
            selected = (
                [a for a in atoms if a["resname"] in AMINO_ACIDS]
                if name == "protein"
                else [a for a in atoms if a["resname"] == "LIG"]
            )
            coordinates = positions(selected)
            if stage == "submitted":
                coordinates = (coordinates + (shift if name == "ligand" else 0)) @ R + t
            else:
                coordinates += g25["intermediate_translation_A"]
            copied, _ = load_atoms(HERE / f"derived/task25_{stage}_{name}.pdb")
            assert [(a["name"], a["resid"]) for a in copied] == [
                (a["name"], a["resid"]) for a in selected
            ]
            error = float(np.linalg.norm(positions(copied) - coordinates, axis=1).max())
            max_rounding_error = max(max_rounding_error, error)
            assert error <= 0.000867
    atoms29, _ = load_atoms(Path(geometry["task29"]["artifact"]))
    for name in ["protein", "ligand", "lipid"]:
        chosen = (
            [a for a in atoms29 if a["resname"] in AMINO_ACIDS]
            if name == "protein"
            else [a for a in atoms29 if a["resname"] == "AMP"]
            if name == "ligand"
            else [a for a in atoms29 if (a["resname"], a["resid"]) == ("POPE", 808)]
        )
        derived, _ = load_atoms(HERE / f"derived/task29_{name}.pdb")
        error = float(
            np.linalg.norm(
                positions(derived)
                - positions(chosen)
                - geometry["task29"]["global_translation_A"],
                axis=1,
            ).max()
        )
        max_rounding_error = max(max_rounding_error, error)
        assert error <= 0.000867
    # Preserve the distinction between this clash and the atom actually named in the log.
    log = (
        Path(geometry["task29"]["artifact"]).with_name("em_test_mdrun.log").read_text()
    )
    assert re.search(r"Maximum force\s*=\s*inf on atom 44170", log)
    other_overlap = float(
        np.linalg.norm(np.array(atoms29[44169]["xyz"]) - atoms29[31013]["xyz"])
    )
    assert abs(other_overlap - 0.05477225575050815) < 1e-8

    # Inspect the saved sessions, including the actual contact atom centers after camera rotation.
    with pymol2.PyMOL() as p:
        p.cmd.load(str(OUTPUT / "renders/task25_submitted.pse"))
        a = p.cmd.get_atom_coords("ligand and name CL")
        b = p.cmd.get_atom_coords("protein and resi 117 and name HZ2")
        rendered25 = float(np.linalg.norm(np.array(a) - b))
        assert abs(rendered25 - g25["final_nearest_pair"]["distance_A"]) < 0.0018
        p.cmd.reinitialize()
        p.cmd.load(str(OUTPUT / "renders/task29_submitted.pse"))
        a = p.cmd.get_atom_coords("ligand and name C6")
        b = p.cmd.get_atom_coords("lipid and name C316")
        rendered29 = float(np.linalg.norm(np.array(a) - b))
        assert (
            abs(rendered29 - geometry["task29"]["carbon_pair"]["distance_A"]) < 0.0018
        )
        assert p.cmd.count_atoms("contact_spheres") == 2
        radii = [atom.vdw for atom in p.cmd.get_model("contact_spheres").atom]
        assert np.allclose(radii, 1.7)
        pymol_version = p.cmd.get_version()[0]
    assert (
        abs(
            (
                np.array(geometry["task29"]["display_endpoints_A"])[1]
                - geometry["task29"]["display_endpoints_A"][0]
            )
            @ np.array(cameras["task29"]["basis"])[:, 2]
        )
        < 1e-9
    )
    for camera in cameras.values():
        basis = np.array(camera["basis"])
        assert (
            np.allclose(basis.T @ basis, np.eye(3)) and np.linalg.det(basis) > 0.999999
        )
    # Image height follows its cropped pixel ratio; the two receptors share exactly the same scale.
    placements = layout["placements"]
    assert len(placements) == 5 and set(layout["panels"]) == {"A", "B", "C"}
    rows = read_csv(HERE / "task_success.csv")
    assert layout["heatmap"]["task_order"] == [row["task_id"] for row in rows]
    assert layout["heatmap"]["source_sha256"] == sha256(HERE / "task_success.csv")
    heatmap = layout["heatmap"]
    assert heatmap["difficulty_labels"] == [
        row["difficulty"][0].upper() for row in rows
    ]
    assert heatmap["task_names"] == [row["short_description"] for row in rows]
    assert heatmap["models"] == selection["models"]
    assert heatmap["task_order"] == selection["task_order"]
    assert heatmap["colors"] == palette_approval["colors"]
    assert heatmap["colors"][:3] == selection["colors"][:3]
    assert heatmap["orientation"] == "configurations_rows_tasks_columns"
    assert heatmap["matrix_shape"] == [5, 50] and heatmap["single_continuous_matrix"]
    assert (
        heatmap["type_label_rotation_degrees"] == 0 and heatmap["cell_annotations"] == 0
    )
    assert heatmap["label_spacing"]["minimum_task_label_gap_mm"] > 0
    assert heatmap["label_spacing"]["minimum_index_gap_mm"] > 0
    assert heatmap["label_spacing"]["task_type_labels_do_not_overlap"]
    labels = read_csv(HERE / "task_labels_and_values.csv")
    assert [row["display_label"] for row in labels] == heatmap["display_task_names"]
    assert len(labels) == 50
    for original, displayed in zip(rows, labels):
        assert all(
            original[key] == displayed[key] for key in original if key in displayed
        )
    bands = layout["right_panel_bands_mm"]
    assert bands["B"][0] == bands["C"][1]
    assert np.isclose(bands["B"][1] - bands["B"][0], bands["C"][1] - bands["C"][0])
    for index, placement in enumerate(placements):
        low, high = bands["B" if index < 3 else "C"]
        assert low <= placement["placement_mm"][1]
        assert placement["placement_mm"][1] + placement["placement_mm"][3] <= high
    assert all(
        "-\n" not in label for label in layout["heatmap"]["group_labels"].values()
    )
    for placement in placements:
        path = OUTPUT / placement["source"]
        assert sha256(path) == placement["source_sha256"]
        width_px, height_px = placement["cropped_pixels"]
        x, y, width_mm, height_mm = placement["placement_mm"]
        assert abs(width_mm / height_mm - width_px / height_px) < 1e-12
        assert (
            x >= 0
            and y >= 0
            and x + width_mm <= layout["width_mm"]
            and y + height_mm <= layout["height_mm"]
        )
    assert placements[0]["crop_pixels"] == placements[1]["crop_pixels"]
    assert placements[0]["placement_mm"][1:] == placements[1]["placement_mm"][1:]

    # Ensure complete receptors/ligands and the full offending lipid stay inside the main crops.
    scenes = [
        ("task25_intermediate", "task25", placements[0], ["protein", "ligand"]),
        ("task25_submitted", "task25", placements[1], ["protein", "ligand"]),
        ("task29", "task29", placements[3], ["ligand", "lipid"]),
    ]
    for prefix, key, placement, names in scenes:
        camera = cameras[key]
        left, right, bottom, top = placement["original_fraction_extent"]
        for name in names:
            atoms, _ = load_atoms(HERE / f"derived/{prefix}_{name}.pdb")
            if name == "protein":
                atoms = [a for a in atoms if a["name"] == "CA"]
            coords = positions(atoms) @ np.array(camera["basis"]) - camera["center_A"]
            uv = 0.5 + coords[:, :2] / [camera["width_A"], camera["height_A"]]
            assert (uv[:, 0] >= left).all() and (uv[:, 0] <= right).all()
            assert (uv[:, 1] >= bottom).all() and (uv[:, 1] <= top).all()
    overview, inset = placements[3], placements[4]
    left, right, bottom, top = overview["original_fraction_extent"]
    x, y, width, height = overview["placement_mm"]
    inset_x, inset_y, inset_width, inset_height = inset["placement_mm"]
    for u, v in cameras["task29"]["contact_endpoints_fraction"]:
        px, py = (
            x + (u - left) / (right - left) * width,
            y + (v - bottom) / (top - bottom) * height,
        )
        assert not (
            inset_x <= px <= inset_x + inset_width
            and inset_y <= py <= inset_y + inset_height
        )

    copy_record = json.loads(
        (REPO / "figures/figure_S2/copy_manifest.json").read_text()
    )
    for record in copy_record["copies"]:
        source, target = REPO / record["source"], REPO / record["destination"]
        assert (
            source.read_bytes() == target.read_bytes()
            and sha256(target) == record["sha256"]
        )
    # Embedded molecular resolution is checked at the actual PDF placement, not its PNG metadata.
    image_info = subprocess.check_output(
        ["pdfimages", "-list", str(OUTPUT / "figure_5.pdf")], text=True
    )
    embedded = []
    for line in image_info.splitlines():
        fields = line.split()
        if len(fields) > 14 and fields[0].isdigit() and fields[2] == "image":
            embedded.append(
                {
                    "width_px": int(fields[3]),
                    "height_px": int(fields[4]),
                    "x_dpi": int(fields[12]),
                    "y_dpi": int(fields[13]),
                }
            )
    assert len(embedded) == 5 and all(
        min(r["x_dpi"], r["y_dpi"]) >= 600 for r in embedded
    )
    page_info = subprocess.check_output(
        ["pdfinfo", str(OUTPUT / "figure_5.pdf")], text=True
    )
    assert "Pages:           1" in page_info
    template_info = subprocess.check_output(
        [
            "pdfinfo",
            str(
                REPO
                / "data/source/Royal_Society_of_Chemistry_communication_template.pdf"
            ),
        ],
        text=True,
    )
    template_size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", template_info)
    full_text_width_mm = float(template_size.group(1)) * 25.4 / 72 - 30
    assert "left=1.5cm, right=1.5cm" in (REPO / "data/source/main.tex").read_text()
    assert abs(full_text_width_mm - layout["width_mm"]) < 0.001
    size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", page_info)
    assert np.allclose(
        [float(v) * 25.4 / 72 for v in size.groups()],
        [layout["width_mm"], layout["height_mm"]],
        atol=0.001,
    )
    fonts = subprocess.check_output(
        ["pdffonts", str(OUTPUT / "figure_5.pdf")], text=True
    )
    assert "LiberationSans" in fonts
    with Image.open(OUTPUT / "figure_5.png") as image:
        png_size = list(image.size)
        assert abs(image.width - layout["width_mm"] / 25.4 * 600) < 1
        assert abs(image.height - layout["height_mm"] / 25.4 * 600) < 1
        rgba = image.convert("RGBA")
        assert (
            hashlib.sha256(rgba.tobytes()).hexdigest()
            == palette_approval["approved_RGBA_sha256"]
        )
        x = selection["B_C_region_left_pixel"]
        assert (
            hashlib.sha256(
                rgba.crop((x, 0, image.width, image.height)).tobytes()
            ).hexdigest()
            == selection["approved_B_C_RGBA_sha256"]
        )
    figure3_info = subprocess.check_output(
        ["pdfinfo", str(OUTPUT.parent / "figure_3/figure_3.pdf")], text=True
    )
    figure3_size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", figure3_info)
    figure3_width, figure3_height = [float(value) for value in figure3_size.groups()]
    figure3_scaled_height = figure3_height / figure3_width * layout["width_mm"]
    assert abs(figure3_scaled_height - layout["height_mm"]) < 0.02
    text = subprocess.check_output(
        ["pdftotext", "-layout", str(OUTPUT / "figure_5.pdf"), "-"], text=True
    )
    raw_text = subprocess.check_output(
        ["pdftotext", "-raw", str(OUTPUT / "figure_5.pdf"), "-"], text=True
    )
    normal = " ".join(raw_text.split())
    assert all(
        " ".join(name.split()) in normal for name in heatmap["display_task_names"]
    )
    assert all(
        label in normal
        for label in [
            "37.8",
            "1.37",
            "AMP702",
            "POPE808",
            "C316",
            "Correctness:",
            "Process:",
            "Parameterization",
            "Diagnostics",
            "Difficulty",
        ]
    )
    assert all(
        label not in normal
        for label in [
            "42 tasks",
            "12 hard",
            "Matched receptor",
            "→",
            "Task-level strict success",
            "Binding-pose loss",
            "Ligand–lipid clash",
        ]
    )
    assert all(
        sha256(REPO / path) == digest
        for path, digest in revision["protected_local_files"].items()
    )
    result = {
        "manuscript_commit": sources["manuscript_commit"],
        "layout_revision_commit": revision["baseline_commit"],
        "Figure5_dimensions_mm": [layout["width_mm"], layout["height_mm"]],
        "full_text_width_basis": "Letter paper in the supplied RSC template, minus the current 15 mm side margins",
        "full_text_width_mm": full_text_width_mm,
        "panels": ["A: five-configuration heatmap", "B: Task 25", "C: Task 29"],
        "heatmap_task_difficulty_labels_verified": 50,
        "vector_heatmap": True,
        "selected_option": selection["selected_option"],
        "pixel_identical_to_approved_option": palette_approval["approved_RGBA_sha256"]
        == selection["approved_RGBA_sha256"],
        "pixel_identical_to_current_palette_approval": True,
        "palette_revisions": selection.get("palette_revisions", []),
        "B_C_pixel_identical_to_approved_option": True,
        "Figure3_height_at_same_width_mm": figure3_scaled_height,
        "right_panel_bands_mm": bands,
        "retained_original_analysis_shared_tasks": 42,
        "retained_original_analysis_shared_hard_tasks": 12,
        "task25_distance_A": g25["final_nearest_pair"]["distance_A"],
        "task29_distance_A": geometry["task29"]["carbon_pair"]["distance_A"],
        "task25_CA_rmsd_A": g25["protein_CA_rmsd_A"],
        "max_derived_PDB_rounding_error_A": max_rounding_error,
        "rendered_task25_pair_A": rendered25,
        "rendered_task29_pair_A": rendered29,
        "separate_log_atom_overlap_A": other_overlap,
        "carbon_sphere_radii_A": radii,
        "protected_local_files_unchanged": len(revision["protected_local_files"]),
        "source_files_rehashed_unchanged": len(sources["inputs"]),
        "tex_scores_original_artifacts_unchanged": True,
        "original_coordinates_cameras_renders_provenance_unchanged": True,
        "vector_annotations": True,
        "image_aspect_ratios_preserved": True,
        "complete_main_molecules_inside_crops": True,
        "main_clash_not_obscured_by_inset": True,
        "S2_copy": copy_record,
        "molecular_images_embedded_in_PDF": embedded,
        "PNG_size_px": png_size,
        "PDF_page_info": page_info,
        "PDF_font_info": fonts,
        "PDF_image_info": image_info,
        "PDF_text": text,
        "software": {
            "PyMOL": pymol_version,
            "NumPy": np.__version__,
            "SciPy": scipy.__version__,
            "Matplotlib": matplotlib.__version__,
            "Pillow": PIL.__version__,
        },
        "scripts_sha256": {
            p.name: sha256(p) for p in Path(__file__).resolve().parent.glob("*.py")
        },
    }
    (HERE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    inventory = [
        {
            "path": str(p.relative_to(REPO)),
            "size_bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in sorted([*HERE.rglob("*"), *(REPO / "figures/figure_S2").rglob("*")])
        if p.is_file() and p.name != "created_files.csv"
    ]
    with (HERE / "created_files.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, ["path", "size_bytes", "sha256"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(inventory)
    print(
        f"Verified approved Figure 5: all 50 task difficulties/names, identical data and source geometry; {rendered25:.6f} and {rendered29:.6f} Å in saved sessions; S2 unchanged."
    )


if __name__ == "__main__":
    main()
