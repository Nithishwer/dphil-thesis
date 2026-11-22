"""Align 13b to 11b and save separate water-solvated PDBs for the figure.

Source GROMACS's GMXRC before running with the VAASU Python environment.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import gromacs
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolAlign

CHAPTER = Path(__file__).resolve().parents[4]
ROOT = CHAPTER / "data/figures/figure_2/a-RBFE"
LIGAND_NAMES = ("11b", "13b")
PADDING_NM = 1.0


def main():
    ligands = [
        Chem.SDMolSupplier(str(ROOT / f"{name}.sdf"))[0] for name in LIGAND_NAMES
    ]
    if any(ligand is None for ligand in ligands):
        raise ValueError("Could not read both ligand SDF files.")

    # Match the complete 11b scaffold, considering its symmetric atom mappings.
    reference, target = ligands
    matches = target.GetSubstructMatches(reference, uniquify=False)
    if not matches:
        raise ValueError("The complete 11b scaffold was not found in 13b.")
    atom_maps = [list(zip(match, range(reference.GetNumAtoms()))) for match in matches]
    rmsd = rdMolAlign.GetBestRMS(target, reference, map=atom_maps)
    print(f"Aligned shared scaffold RMSD: {rmsd:.4f} angstrom")
    ligands = [Chem.AddHs(ligand, addCoords=True) for ligand in ligands]

    # Apply one translation to both ligands so boxing preserves their alignment.
    positions = np.concatenate([mol.GetConformer().GetPositions() for mol in ligands])
    lower, upper = positions.min(axis=0), positions.max(axis=0)
    box_nm = float((upper - lower).max() / 10 + 2 * PADDING_NM)
    translation = box_nm * 10 / 2 - (lower + upper) / 2

    with TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        for name, ligand in zip(LIGAND_NAMES, ligands):
            conformer = ligand.GetConformer()
            conformer.SetPositions(conformer.GetPositions() + translation)
            ligand_pdb = str(temporary / f"{name}.pdb")
            boxed_gro = str(temporary / f"{name}_box.gro")
            output_pdb = str(ROOT / f"{name}_solvent.pdb")
            Chem.MolToPDBFile(ligand, ligand_pdb)
            gromacs.editconf(f=ligand_pdb, o=boxed_gro, box=[box_nm] * 3, c=False)
            gromacs.solvate(cp=boxed_gro, cs="spc216.gro", o=output_pdb)
            print(f"Saved {output_pdb}")


if __name__ == "__main__":
    main()
