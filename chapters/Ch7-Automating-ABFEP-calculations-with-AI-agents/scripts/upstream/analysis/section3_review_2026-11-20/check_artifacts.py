"""Targeted deterministic checks on saved coordinates, box lines, and printed ranks.

These are new analysis checks, distinct from original grading. No simulations,
verifiers, LLMs, or agent-generated scripts are run. All distances use nanometres
internally; reported distances are Angstroms. Source files are only read.
"""

import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from analyze_results import HERE, REPO, TABLES
from collect_case_evidence import load_events, text_values

CHECKS = HERE / "deterministic_checks"
AMINO_ACIDS = set(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL HID HIE HIP CYX CYM ASH GLH LYN".split()
)


def is_protein(name):
    return name in AMINO_ACIDS or (name[:1] in ["N", "C"] and name[1:] in AMINO_ACIDS)


def atom_record(line, row, pdb=False):
    if pdb:
        return {
            "row": row,
            "resid": line[22:26].strip(),
            "resname": line[17:20].strip(),
            "atom": line[12:16].strip(),
            "position_nm": [float(line[30:38]) / 10, float(line[38:46]) / 10, float(line[46:54]) / 10],
            "record": line,
        }
    # GRO permits extended precision: field width is the gap between decimals.
    decimals = [m.start() for m in re.finditer(r"\.", line[20:])]
    width = decimals[1] - decimals[0]
    return {
        "row": row,
        "resid": line[:5].strip(),
        "resname": line[5:10].strip(),
        "atom": line[10:15].strip(),
        "position_nm": [float(line[20 + i * width : 20 + (i + 1) * width]) for i in range(3)],
        "record": line,
    }


def load_gro(path):
    lines = path.read_text().splitlines()
    count = int(lines[1])
    box = np.array([float(v) for v in lines[count + 2].split()])
    assert len(box) in [3, 9]
    if len(box) == 9:
        assert np.allclose(box[3:], 0), "These selected GRO files must be orthorhombic."
    return [atom_record(line, i + 1) for i, line in enumerate(lines[2 : count + 2])], box[:3]


def closest(atoms_a, atoms_b, box=None):
    if not atoms_a or not atoms_b:
        return None
    a = np.array([atom["position_nm"] for atom in atoms_a])
    b = np.array([atom["position_nm"] for atom in atoms_b])
    best = (float("inf"), 0, 0)
    for start in range(0, len(b), 10000):
        delta = a[:, None, :] - b[None, start : start + 10000, :]
        if box is not None:
            assert np.all(box > 0)
            delta -= np.rint(delta / box) * box
        distances = np.sum(delta**2, axis=2)
        i, j = np.unravel_index(np.argmin(distances), distances.shape)
        if distances[i, j] < best[0]:
            best = (float(distances[i, j]), int(i), int(j) + start)
    return {"distance_A": float(np.sqrt(best[0]) * 10), "atom_a": atoms_a[best[1]], "atom_b": atoms_b[best[2]]}


def heavy(atoms):
    return [a for a in atoms if not a["atom"].lstrip("0123456789").startswith("H")]


def main():
    CHECKS.mkdir(exist_ok=True)
    cases = json.loads((HERE / "evidence/case_evidence.json").read_text())
    geometry = []
    boxes = []
    rankings = []
    hashes = {}
    for case in cases:
        app = Path(case["artifact_root"])
        number = case["number"]
        model = case["model"]
        rep = case["replicate"]
        if number == 11:
            path = app / "outputs/system.gro"
            if path.exists():
                atoms, box = load_gro(path)
                hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                boxes.append(
                    {
                        "model": model,
                        "replicate": rep,
                        "trial_name": case["trial_name"],
                        "path": str(path),
                        "atom_count": len(atoms),
                        "box_nm": box.tolist(),
                        "usable_positive_box": bool(np.all(box > 0)),
                        "strict_pass": case["strict_pass"],
                        "status": case["status"],
                    }
                )
            else:
                boxes.append(
                    {
                        "model": model,
                        "replicate": rep,
                        "trial_name": case["trial_name"],
                        "path": str(path),
                        "absent": True,
                        "strict_pass": case["strict_pass"],
                        "status": case["status"],
                    }
                )
        if model == "opus-5.5" and number in [25, 29]:
            path = app / "outputs/system.gro"
            atoms, box = load_gro(path)
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            ligand_names = ["LIG"] if number == 25 else ["AMP", "AIC"]
            ligands = [a for a in atoms if a["resname"] in ligand_names]
            partners = (
                [a for a in atoms if is_protein(a["resname"])]
                if number == 25
                else [a for a in atoms if a["resname"] in ["POPE", "POPG"]]
            )
            record = {
                "task": number,
                "replicate": rep,
                "trial_name": case["trial_name"],
                "path": str(path),
                "sha256": hashes[str(path)],
                "box_nm": box.tolist(),
                "n_ligand_atoms": len(ligands),
                "n_partner_atoms": len(partners),
                "all_direct": closest(ligands, partners),
                "all_periodic": closest(ligands, partners, box),
                "heavy_periodic": closest(heavy(ligands), heavy(partners), box),
            }
            if number == 25:
                record["intermediates"] = []
                for intermediate in sorted((app / "outputs").rglob("*complex*.pdb")):
                    structures = [
                        atom_record(line, i + 1, True)
                        for i, line in enumerate(intermediate.read_text().splitlines())
                        if line.startswith(("ATOM  ", "HETATM"))
                    ]
                    ilig = [a for a in structures if a["resname"] in ["LIG", "51D"]]
                    iprot = [a for a in structures if is_protein(a["resname"])]
                    if ilig and iprot:
                        hashes[str(intermediate)] = hashlib.sha256(intermediate.read_bytes()).hexdigest()
                        entry = {
                            "path": str(intermediate),
                            "ligand_atoms": len(ilig),
                            "protein_atoms": len(iprot),
                            "all_direct": closest(ilig, iprot),
                            "heavy_direct": closest(heavy(ilig), heavy(iprot)),
                        }
                        old_ca = [a for a in iprot if a["atom"] == "CA"]
                        new_ca = [a for a in partners if a["atom"] == "CA"]
                        old_lig = {a["atom"]: a for a in ilig}
                        new_lig = {a["atom"]: a for a in ligands}
                        common = sorted(old_lig.keys() & new_lig.keys())
                        if len(old_ca) == len(new_ca) and len(common) >= 6:
                            dp = np.array([a["position_nm"] for a in new_ca]) - np.array(
                                [a["position_nm"] for a in old_ca]
                            )
                            dl = np.array([new_lig[a]["position_nm"] for a in common]) - np.array(
                                [old_lig[a]["position_nm"] for a in common]
                            )
                            entry.update(
                                {
                                    "protein_CA_translation_nm": dp.mean(axis=0).tolist(),
                                    "ligand_translation_nm": dl.mean(axis=0).tolist(),
                                    "protein_minus_ligand_translation_nm": (dp.mean(axis=0) - dl.mean(axis=0)).tolist(),
                                    "protein_translation_max_residual_A": float(
                                        np.max(np.linalg.norm(dp - dp.mean(axis=0), axis=1)) * 10
                                    ),
                                    "ligand_translation_max_residual_A": float(
                                        np.max(np.linalg.norm(dl - dl.mean(axis=0), axis=1)) * 10
                                    ),
                                }
                            )
                        record["intermediates"].append(entry)
            else:
                record["carbon_periodic"] = closest(
                    [a for a in ligands if a["atom"].startswith("C")],
                    [a for a in partners if a["atom"].startswith("C")],
                    box,
                )
                topology = app / "outputs/topol.top"
                text = topology.read_text()
                record["topology_path"] = str(topology)
                record["topology_molecules_section"] = text.split("[ molecules ]")[-1].split("[molecules]")[-1][-3000:]
                record["intermolecular_interactions_declared"] = bool(
                    re.search(r"\[\s*intermolecular_interactions\s*\]", text)
                )
                log = app / "outputs/em_test_mdrun.log"
                if log.exists():
                    logtext = log.read_text()
                    record["minimization_log_path"] = str(log)
                    record["minimization_log_tail"] = logtext[-2200:]
                    match = re.search(r"Maximum force\s*=\s*inf on atom (\d+)", logtext)
                    if match:
                        atom_id = int(match.group(1))
                        target = atoms[atom_id - 1]
                        record["reported_infinite_force_atom"] = target
                        record["infinite_force_atom_nearest_periodic"] = closest(
                            [target], [a for a in atoms if a["row"] != atom_id], box
                        )
            geometry.append(record)
        if model == "gemini-4-argon" and number == 17 and rep in [2, 3]:
            transcript, events = load_events(Path(case["source_trial_dir"]), Path(case["review_case"]))
            target = 5 if rep == 2 else 17
            label, event = events[target - 1]
            text = "\n".join(text_values(event))
            observation = text.split("OBSERVATION:")[-1]
            rows = []
            ligand = None
            protein = None
            # Pandas multi-index printing suppresses repeated ligand/protein labels.
            for line in observation.splitlines():
                tokens = line.split()
                if not tokens:
                    continue
                if tokens[0].startswith("HIT325"):
                    ligand = tokens.pop(0).split(".")[0]
                if tokens and re.fullmatch(r"[A-Z]{3}\d+(?:\.[A-Za-z0-9]+)?", tokens[0]):
                    protein = tokens.pop(0).split(".")[0]
                if (
                    ligand
                    and protein
                    and len(tokens) >= 2
                    and tokens[0] in ["Hydrophobic", "PiStacking", "VdWContact", "HBDonor", "HBAcceptor", "PiCation"]
                ):
                    interaction = tokens.pop(0)
                    if "/" in tokens[0]:
                        tokens.pop(0)
                    try:
                        occupancy = float(tokens[0])
                    except ValueError:
                        continue
                    rows.append(
                        {
                            "ligand_residue": ligand,
                            "protein_residue": protein,
                            "interaction_type": interaction,
                            "occupancy": occupancy,
                        }
                    )
            reference_path = (
                REPO.parent
                / "MDArena-dev/tasks/17_prolif_int/tests/correctness/expected_outputs/prolif_interactions.csv"
            )
            reference = list(csv.DictReader(reference_path.open()))
            ref = {
                (r["ligand_residue"], r["protein_residue"], r["interaction_type"]): float(r["occupancy"])
                for r in reference
            }
            first = rows[:10]
            observed = {
                (r["ligand_residue"], r["protein_residue"], r["interaction_type"]): r["occupancy"] for r in first
            }
            assert set(ref) == set(observed), (rep, rows)
            max_error = max(abs(observed[key] - ref[key]) for key in ref)
            assert max_error < 0.01
            assert all(rows[i]["occupancy"] >= rows[i + 1]["occupancy"] for i in range(len(rows) - 1))
            after = []
            for later_label, later_event in events[target:]:
                later = "\n".join(text_values(later_event))
                line = later.splitlines()
                command = re.search(r'"command"\s*:\s*"(.*)', later)
                after.append({"event": later_label, "summary": command.group(1)[:700] if command else later[:700]})
            rankings.append(
                {
                    "replicate": rep,
                    "trial_name": case["trial_name"],
                    "transcript": str(transcript),
                    "ranking_event": target,
                    "recorded_ranking_rows": len(rows),
                    "recorded_first_ten": first,
                    "same_row_set_as_reference": True,
                    "maximum_occupancy_error_percentage_points": max_error,
                    "reference_path": str(reference_path),
                    "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                    "subsequent_events": after,
                    "method": "Parse historical stdout only; normalize chain suffixes; compare unordered tied ranks and numeric occupancies to saved reference. No ProLIF recomputation.",
                }
            )
    result = {
        "method": "New deterministic artifact inspection, distinct from original grading. Fixed-width PDB/GRO parsing; nanometres to Angstroms; orthorhombic 3D minimum-image distances.",
        "coordinate_geometry": geometry,
        "task11_delivered_boxes": boxes,
        "task17_recorded_rankings": rankings,
        "source_sha256": hashes,
    }
    (CHECKS / "artifact_results.json").write_text(json.dumps(result, indent=2) + "\n")
    pd.DataFrame(boxes).to_csv(TABLES / "task11_delivered_boxes.csv", index=False)
    print(
        "Checked",
        len(geometry),
        "Opus coordinate artifacts,",
        len(boxes),
        "Task 11 deliveries, and",
        len(rankings),
        "saved Task 17 rankings.",
    )
    for r in geometry:
        print(
            "Task",
            r["task"],
            "replicate",
            r["replicate"],
            "all periodic",
            r["all_periodic"]["distance_A"],
            "heavy periodic",
            r["heavy_periodic"]["distance_A"],
        )


if __name__ == "__main__":
    main()
