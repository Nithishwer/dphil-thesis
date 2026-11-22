"""Verify the selected results and make coordinate-preserving visualization copies."""

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

CHAPTER = Path(__file__).resolve().parents[1]
DATA = CHAPTER / "data/figures/figure_5"
HERE = CHAPTER / "scripts/intermediates/figure_5"
OUTPUT = CHAPTER / "figures/figure_5"
REPO = CHAPTER
CURRENT = REPO / "data/analysis/task39_policy_b_2026-11-20/current"
AUDIT = REPO / "data/analysis/section3_review_2026-11-20"
MODELS = ["opus-5.5", "gpt-6.1-sol", "gpt-6-astra", "gemini-4-argon", "glm-5.2"]
AMINO_ACIDS = set(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL HID HIE HIP CYX CYM ASH GLH LYN ACE NME".split()
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def element(name):
    name = name.lstrip("0123456789")
    return (
        "Cl"
        if name.upper() == "CL"
        else "Br"
        if name.upper() == "BR"
        else name[0].upper()
    )


def load_atoms(path):
    lines = path.read_text().splitlines()
    atoms = []
    if path.suffix == ".gro":
        count = int(lines[1])
        box = np.array([float(x) for x in lines[count + 2].split()])
        assert len(box) == 3 or (len(box) == 9 and np.allclose(box[3:], 0))
        for row, line in enumerate(lines[2 : count + 2], 1):
            dots = [m.start() for m in re.finditer(r"\.", line[20:])]
            width = dots[1] - dots[0]
            atoms.append(
                {
                    "row": row,
                    "name": line[10:15].strip(),
                    "resname": line[5:10].strip(),
                    "resid": int(line[:5]),
                    "xyz": [
                        float(line[20 + i * width : 20 + (i + 1) * width]) * 10
                        for i in range(3)
                    ],
                }
            )
        return atoms, box[:3] * 10
    for line in lines:
        if line.startswith(("ATOM  ", "HETATM")):
            atoms.append(
                {
                    "row": len(atoms) + 1,
                    "name": line[12:16].strip(),
                    "resname": line[17:20].strip(),
                    "resid": int(line[22:26]),
                    "xyz": [float(line[30:38]), float(line[38:46]), float(line[46:54])],
                }
            )
    return atoms, None


def positions(atoms):
    return np.array([a["xyz"] for a in atoms])


def nearest(first, second, box=None):
    """Independent periodic KD-tree check, followed by an exact pair displacement."""
    a, b = positions(first), positions(second)
    tree = cKDTree(np.mod(b, box), boxsize=box) if box is not None else cKDTree(b)
    distances, indices = tree.query(np.mod(a, box) if box is not None else a)
    i = int(distances.argmin())
    j = int(indices[i])
    shift = (
        np.rint((b[j] - a[i]) / box).astype(int)
        if box is not None
        else np.zeros(3, dtype=int)
    )
    delta = a[i] + shift * box - b[j] if box is not None else a[i] - b[j]
    assert abs(np.linalg.norm(delta) - distances[i]) < 1e-9
    return {
        "distance_A": float(np.linalg.norm(delta)),
        "first": first[i],
        "second": second[j],
        "first_whole_molecule_image_shift_lattice": shift.tolist(),
    }


def topology(path):
    """Read saved atom identities and covalent bonds; never infer bonds across objects."""
    names, bonds, section = {}, [], ""
    for line in path.read_text().splitlines():
        line = line.split(";")[0].strip()
        if line.startswith("["):
            section = line.strip("[] ")
        elif line and not line.startswith("#"):
            fields = line.split()
            if section == "atoms":
                names[int(fields[0])] = fields[4]
            elif section == "bonds":
                bonds.append((names[int(fields[0])], names[int(fields[1])]))
    return bonds


def write_pdb(path, atoms, bonds=(), protein=False):
    # Each ligand/lipid is a separate object, with bonds from its saved topology.
    lines, indices = [], {}
    for i, atom in enumerate(atoms, 1):
        name = atom["name"]
        indices[name] = i
        x, y, z = atom["xyz"]
        label = name.rjust(4) if len(name) == 4 else (" " + name).ljust(4)
        resname = atom["resname"][:3]
        if atom["resname"] == "POPE":
            resname = "PPE"
        lines.append(
            f"{'ATOM  ' if protein else 'HETATM'}{i:5d} {label} {resname:>3} A{atom['resid']:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {element(name):>2}  "
        )
    for a, b in bonds:
        if a in indices and b in indices:
            lines.append(f"CONECT{indices[a]:5d}{indices[b]:5d}")
    path.write_text("\n".join(lines) + "\nEND\n")


def transform(atoms, rotation, translation):
    xyz = positions(atoms) @ rotation + translation
    return [dict(atom, xyz=point.tolist()) for atom, point in zip(atoms, xyz)]


def main():
    derived = HERE / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    tracked = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO)
        .decode()
        .split("\0")
    )
    protected = {
        p: sha256(REPO / p)
        for p in tracked
        if p
        and (REPO / p).is_file()
        and not p.startswith(("figures/figure_5/", "scripts/intermediates/figure_5/"))
        and REPO / p != DATA / "task_success.csv"
    }
    inputs = [
        CURRENT / "tables/task_success_matrix.csv",
        CURRENT / "tables/task_metadata.csv",
        AUDIT / "evidence/case_evidence.json",
        AUDIT / "deterministic_checks/artifact_results.json",
    ]

    matrix = read_csv(inputs[0])
    assert len(matrix) == 50 and len({r["task_id"] for r in matrix}) == 50
    # Recompute every cell from the active selected trials, rather than trusting a cached matrix.
    for model in MODELS:
        path = REPO / f"data/trials/{model}.csv"
        inputs.append(path)
        rows = read_csv(path)
        assert len(rows) == 150
        for task in matrix:
            trials = [r for r in rows if r["task_id"] == task["task_id"]]
            assert len(trials) == 3
            passes = sum(
                r["status"] == "completed"
                and float(r["correctness"]) >= 0.999
                and float(r["process"]) >= 0.999
                for r in trials
            )
            assert passes == int(task[model]), (
                model,
                task["task_id"],
                passes,
                task[model],
            )
    shared = [r for r in matrix if all(int(r[m]) == 3 for m in MODELS[:3])]
    hard = [r for r in shared if r["difficulty"] == "hard"]
    if (len(shared), len(hard)) != (42, 12):
        raise ValueError(
            f"Unexpected overlap: {len(shared)} tasks, {len(hard)} hard; inspect current inputs."
        )
    assert all(int(r[m]) == 0 for r in matrix if int(r["number"]) == 39 for m in MODELS)
    with (DATA / "task_success.csv").open("w", newline="") as stream:
        fields = [
            "task_id",
            "number",
            "category",
            "difficulty",
            "short_description",
            "row_order",
            *MODELS,
            "shared_top_three",
        ]
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for row in matrix:
            writer.writerow(
                {
                    k: (row in shared if k == "shared_top_three" else row[k])
                    for k in fields
                }
            )

    cases = json.loads(inputs[2].read_text())
    selection_path = CURRENT / "tables/score_provenance.csv"
    selected_provenance = read_csv(selection_path)
    inputs.append(selection_path)
    selected = {
        str(n): next(c for c in cases if c["trial_name"].endswith(suffix))
        for n, suffix in [(25, "5qy4iHm"), (29, "Z4DQoGB")]
    }
    checks = {
        "shared_tasks": len(shared),
        "shared_hard_tasks": len(hard),
        "shared_task_ids": [r["task_id"] for r in shared],
        "trials": {},
    }
    for number, case in selected.items():
        rows = read_csv(REPO / "data/trials/opus-5.5.csv")
        trial = next(r for r in rows if r["trial_name"] == case["trial_name"])
        result = Path(case["source_trial_dir"]) / "result.json"
        raw = json.loads(result.read_text())
        assert raw["id"] == case["trial_id"] and trial["task_id"] == case["task_id"]
        selected_record = next(
            r for r in selected_provenance if r["trial_id"] == raw["id"]
        )
        assert selected_record["trial_name"] == case["trial_name"]
        assert selected_record["source_trial_dir"] == case["source_trial_dir"]
        assert selected_record["task_checksum"] == raw["task_checksum"]
        assert int(trial["attempt_index"]) == case["replicate"]
        assert float(trial["correctness"]) == 1 and float(trial["process"]) == (
            0.875 if number == "25" else 0.9375
        )
        checks["trials"][number] = {
            k: case[k]
            for k in [
                "trial_name",
                "trial_id",
                "task_id",
                "replicate",
                "source_trial_dir",
                "numerical_score_authority",
            ]
        }
        checks["trials"][number]["scores"] = {
            d: float(trial[d]) for d in ["correctness", "process"]
        }
        inputs.extend([result, Path(case["numerical_score_authority"])])

    app25 = Path(selected["25"]["artifact_root"]) / "outputs"
    final_path, intermediate_path = app25 / "system.gro", app25 / "complex_oriented.pdb"
    final, box = load_atoms(final_path)
    intermediate, _ = load_atoms(intermediate_path)
    protein = [a for a in final if a["resname"] in AMINO_ACIDS]
    ligand = [a for a in final if a["resname"] == "LIG"]
    iprotein = [a for a in intermediate if a["resname"] in AMINO_ACIDS]
    iligand = [a for a in intermediate if a["resname"] == "LIG"]
    # Audit selected amino-acid residues, excluding the ACE/NME caps from distance calculations.
    pair25 = nearest(
        ligand, [a for a in protein if a["resname"] not in ["ACE", "NME"]], box
    )
    assert abs(pair25["distance_A"] - 37.813362717431) < 1e-8
    pair_intermediate = nearest(
        iligand, [a for a in iprotein if a["resname"] not in ["ACE", "NME"]]
    )
    ca = [a for a in protein if a["name"] == "CA"]
    ica = [a for a in iprotein if a["name"] == "CA"]
    aliases = {"CYX": "CYS", "HIE": "HIS", "HID": "HIS", "HIP": "HIS"}
    assert [aliases.get(a["resname"], a["resname"]) for a in ca] == [
        aliases.get(a["resname"], a["resname"]) for a in ica
    ]
    assert all(old["resid"] - new["resid"] == 567 for new, old in zip(ca, ica))
    p, q = positions(ca), positions(ica)
    origin = q.mean(axis=0)
    q -= origin
    u, _, vt = np.linalg.svd((p - p.mean(axis=0)).T @ q)
    correction = np.eye(3)
    correction[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    translation = -p.mean(axis=0) @ rotation
    rmsd = float(
        np.sqrt(np.mean(np.sum(((p @ rotation + translation) - q) ** 2, axis=1)))
    )
    # One integer-box translation of the complete ligand selects the measured nearest image.
    image_shift = np.array(pair25["first_whole_molecule_image_shift_lattice"]) * box
    imaged = [
        dict(
            a,
            xyz=(
                np.array(a["xyz"]) + (image_shift if a["resname"] == "LIG" else 0)
            ).tolist(),
        )
        for a in final
    ]
    final_aligned = transform(imaged, rotation, translation)
    intermediate_aligned = transform(intermediate, np.eye(3), -origin)
    bonds25 = topology(app25 / "lig_openff_sage221.top")
    for name, atoms in [
        ("task25_intermediate", intermediate_aligned),
        ("task25_submitted", final_aligned),
    ]:
        write_pdb(
            derived / f"{name}_protein.pdb",
            [a for a in atoms if a["resname"] in AMINO_ACIDS],
            protein=True,
        )
        write_pdb(
            derived / f"{name}_ligand.pdb",
            [a for a in atoms if a["resname"] == "LIG"],
            bonds25,
        )
    endpoints25 = [
        final_aligned[pair25[key]["row"] - 1]["xyz"] for key in ["first", "second"]
    ]
    assert (
        abs(np.linalg.norm(np.diff(endpoints25, axis=0)) - pair25["distance_A"]) < 1e-8
    )
    checks["task25"] = {
        "final_artifact": str(final_path),
        "intermediate_artifact": str(intermediate_path),
        "box_A": box.tolist(),
        "final_nearest_pair": pair25,
        "intermediate_nearest_pair": pair_intermediate,
        "protein_CA_matches": len(ca),
        "protein_CA_rmsd_A": rmsd,
        "row_vector_rotation": rotation.tolist(),
        "final_translation_A": translation.tolist(),
        "intermediate_translation_A": (-origin).tolist(),
        "final_ligand_whole_molecule_translation_A": image_shift.tolist(),
        "display_endpoints_A": endpoints25,
        "display_receptor_center_A": [0, 0, 0],
        "display_ligand_center_A": positions(
            [a for a in final_aligned if a["resname"] == "LIG"]
        )
        .mean(axis=0)
        .tolist(),
    }
    inputs.extend([final_path, intermediate_path, app25 / "lig_openff_sage221.top"])

    app29 = Path(selected["29"]["artifact_root"]) / "outputs"
    atoms, box29 = load_atoms(app29 / "system.gro")
    amp = [a for a in atoms if a["resname"] == "AMP"]
    lipids = [a for a in atoms if a["resname"] in ["POPE", "POPG"]]
    carbon_pair = nearest(
        [a for a in amp if element(a["name"]) == "C"],
        [a for a in lipids if element(a["name"]) == "C"],
        box29,
    )
    assert abs(carbon_pair["distance_A"] - 1.368612436009551) < 1e-8
    assert (carbon_pair["first"]["row"], carbon_pair["second"]["row"]) == (7575, 20845)
    target_lipid = [a for a in atoms if (a["resname"], a["resid"]) == ("POPE", 808)]
    assert carbon_pair["first_whole_molecule_image_shift_lattice"] == [0, 0, 0]
    origin29 = (
        np.array(carbon_pair["first"]["xyz"]) + carbon_pair["second"]["xyz"]
    ) / 2
    aligned29 = transform(atoms, np.eye(3), -origin29)
    for name, chosen, topfile in [
        ("task29_ligand", amp, "AMP.itp"),
        ("task29_lipid", target_lipid, "POPE.itp"),
    ]:
        bonds = topology(app29 / topfile)
        lookup = {a["name"]: np.array(a["xyz"]) for a in chosen}
        max_bond = max(np.linalg.norm(lookup[a] - lookup[b]) for a, b in bonds)
        assert max_bond < 2.2, (name, max_bond, "Would need topology-based unwrapping")
        write_pdb(
            derived / f"{name}.pdb", transform(chosen, np.eye(3), -origin29), bonds
        )
    write_pdb(
        derived / "task29_protein.pdb",
        [a for a in aligned29 if a["resname"] in AMINO_ACIDS],
        protein=True,
    )
    top_text = (app29 / "topol.top").read_text()
    assert not re.search(r"\[\s*intermolecular_interactions\s*\]", top_text)
    checks["task29"] = {
        "artifact": str(app29 / "system.gro"),
        "box_A": box29.tolist(),
        "carbon_pair": carbon_pair,
        "global_translation_A": (-origin29).tolist(),
        "periodic_imaging": "none: pair and entire AMP/POPE are continuous in the saved image",
        "display_endpoints_A": [
            (np.array(carbon_pair[k]["xyz"]) - origin29).tolist()
            for k in ["first", "second"]
        ],
        "topology_separate_molecules": True,
        "intermolecular_interactions_declared": False,
    }
    inputs.extend(
        [
            app29 / n
            for n in [
                "system.gro",
                "AMP.itp",
                "POPE.itp",
                "topol.top",
                "em_test_mdrun.log",
            ]
        ]
    )
    write_json(HERE / "verified_geometry.json", checks)
    write_json(
        HERE / "source_manifest.json",
        {
            "manuscript_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip(),
            "inputs": [{"path": str(p), "sha256": sha256(p)} for p in inputs],
            "protected_local_files": protected,
        },
    )
    assert all(sha256(REPO / p) == digest for p, digest in protected.items())
    print(
        f"Verified {len(shared)} shared tasks ({len(hard)} hard); distances {pair25['distance_A']:.9f} and {carbon_pair['distance_A']:.9f} Å. CA RMSD {rmsd:.6f} Å."
    )


if __name__ == "__main__":
    main()
