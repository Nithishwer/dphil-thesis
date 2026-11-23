from pathlib import Path
import logging
import shutil

import MDAnalysis as mda
from MDAnalysis.analysis import align

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/solvation_structures"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/solvation_structures"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    # Copy the apo most solvated gro from analysis
    shutil.copy(
        DATA_DIR / "apo_most_solvated.gro",
        INTERMEDIATE_DIR / "apo_most_solvated.gro",
    )

    # Load the final frame of Compound 6 ABFE 1 vdw20
    u = mda.Universe(
        DATA_DIR / "topol.tpr",
        DATA_DIR / "confout.gro",
    )

    # Fix atom names for UNK residues
    for atom in u.atoms:
        if atom.resname.strip().upper() == "UNK" and atom.name.endswith("x"):
            atom.name = atom.name[:-1].upper()  # remove trailing 'x'

    # Binding pocket selection
    bp_selection_string = (
        "name CA and resid 57 58 61 64 83 84 87 88 91 92 "
        "173 177 218 221 235 238 239 242 243 246"
    )

    # Water residue names to consider
    water_sel_string = "resname SOL "

    pocket = u.select_atoms(bp_selection_string)

    # PBC-aware COM
    com = pocket.center_of_mass(pbc=True)

    nearby_waters = u.select_atoms(
        f"{water_sel_string} and point {com[0]:.3f} {com[1]:.3f} {com[2]:.3f} 10.0"
    )

    # Keep whole water residues, not just atoms
    water_resids_to_keep = set(nearby_waters.residues.resids.tolist())

    if not water_resids_to_keep:
        logging.warning("No waters found near pocket")

    water_resid_str = " ".join(map(str, sorted(water_resids_to_keep)))

    # Final fixed selection: protein + waters near pocket COM, excluding PA/PC/OL
    final_selection = (
        f"(protein) or ({water_sel_string} and resid {water_resid_str}) or resname unk"
    )

    ag = u.select_atoms(final_selection)

    # Write a matching GRO using the first selected frame as reference
    u.trajectory[0]
    ag.write(INTERMEDIATE_DIR / "mGlu5_6_abfe_van1_vdw20_BP_waters.pdb")

    # Read the apo structure and the ligand structure and align them by C alphas
    u_apo = mda.Universe(INTERMEDIATE_DIR / "apo_most_solvated.gro")
    u_lig = mda.Universe(INTERMEDIATE_DIR / "mGlu5_6_abfe_van1_vdw20_BP_waters.pdb")

    # Select C alphas
    align.alignto(u_lig, u_apo, select="name CA")

    # Write aligned structures
    u_lig.atoms.write(
        INTERMEDIATE_DIR / "mGlu5_6_abfe_van1_vdw20_BP_waters_aligned.pdb"
    )


if __name__ == "__main__":
    main()
