"""Save aligned protein complexes in the solvent-leg coordinate frame.

Run with the VAASU Python environment after make_solvent_leg_structures.py.
The protein and ligands are rotated and translated together.
"""

from collections import Counter
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdMolAlign, rdMolTransforms

CHAPTER = Path(__file__).resolve().parents[1]
ROOT = CHAPTER / "data/figures/figure_2/a-RBFE"
WORK = CHAPTER / "scripts/intermediates/figure_2/a-RBFE"
LIGAND_NAMES = ("11b", "13b")


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    protein = Chem.MolFromPDBFile(
        str(ROOT / "protein.pdb"),
        removeHs=False,
        sanitize=False,
        proximityBonding=False,
    )
    if protein is None:
        raise ValueError("Could not read protein.pdb.")
    ligands = [
        Chem.SDMolSupplier(str(ROOT / f"{name}.sdf"))[0] for name in LIGAND_NAMES
    ]
    if any(ligand is None for ligand in ligands):
        raise ValueError("Could not read both ligand SDF files.")

    # The input SDFs share the protein's coordinate frame and binding pocket.
    reference, target = ligands
    matches = target.GetSubstructMatches(reference, uniquify=False)
    if not matches:
        raise ValueError("The complete 11b scaffold was not found in 13b.")
    atom_maps = [list(zip(match, range(reference.GetNumAtoms()))) for match in matches]
    rmsd = rdMolAlign.GetBestRMS(target, reference, map=atom_maps)
    print(f"Aligned shared scaffold RMSD: {rmsd:.4f} angstrom")

    solvent_reference = Chem.MolFromPDBFile(
        str(WORK / "11b_solvent.pdb"),
        removeHs=False,
        sanitize=False,
        proximityBonding=False,
    )
    if solvent_reference is None:
        raise ValueError("Could not read 11b_solvent.pdb.")
    # Solvent PDBs retain the input ligand's heavy atoms first, in SDF order.
    atom_map = [(index, index) for index in range(reference.GetNumAtoms())]
    solvent_rmsd, transform = rdMolAlign.GetAlignmentTransform(
        reference, solvent_reference, atomMap=atom_map
    )
    print(f"Alignment to 11b solvent coordinates RMSD: {solvent_rmsd:.4f} angstrom")

    for name, ligand in zip(LIGAND_NAMES, ligands):
        ligand = Chem.AddHs(ligand, addCoords=True)

        # Put the ligand in chain B, retaining the atom names used in solvent.
        element_counts = Counter()
        for atom in ligand.GetAtoms():
            element = atom.GetSymbol().upper()
            element_counts[element] += 1
            atom.SetMonomerInfo(
                Chem.AtomPDBResidueInfo(
                    atomName=f"{element}{element_counts[element]}".rjust(4),
                    residueName="UNL",
                    residueNumber=1,
                    chainId="B",
                    isHeteroAtom=True,
                    occupancy=1.0,
                )
            )

        complex_molecule = Chem.CombineMols(protein, ligand)
        # One rigid transform preserves both binding poses and the same protein.
        rdMolTransforms.TransformConformer(complex_molecule.GetConformer(), transform)
        output = WORK / f"{name}_complex.pdb"
        Chem.MolToPDBFile(complex_molecule, str(output))
        print(f"Saved {output}")


if __name__ == "__main__":
    main()
