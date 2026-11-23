from pathlib import Path
import os

import MDAnalysis as mda
from MDAnalysis.analysis import align

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/binding_pocket"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/binding_pocket"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

# --- USER SETTINGS ---


def prepare_gro_for_viz(gro_paths):
    """
    Loads multiple .gro files into MDAnalysis Universes, aligns them by protein CA atoms,
    fixes atom names in residue 'UNK' (removing trailing 'x'), and saves each as '_for_viz.pdb'.

    Parameters
    ----------
    gro_paths : list of str
        Paths to .gro files to process.

    Returns
    -------
    dict
        Dictionary mapping each input path to its corresponding MDAnalysis Universe.
    """
    universes = {}
    if not gro_paths:
        raise ValueError("No .gro file paths provided.")

    # Load all universes
    for path in gro_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
        universes[path] = mda.Universe(path)

    # Choose first Universe as reference for alignment
    ref_universe = list(universes.values())[0]
    ref_selection = ref_universe.select_atoms("protein and name CA")
    if ref_selection.n_atoms == 0:
        raise ValueError("Reference universe has no protein CA atoms for alignment.")

    # Align all other universes to the reference
    for path, u in universes.items():
        mobile_selection = u.select_atoms("protein and name CA")
        if mobile_selection.n_atoms == 0:
            print(f"Warning: {path} has no protein CA atoms. Skipping alignment.")
            continue
        align.alignto(u, ref_universe, select="protein and name CA")

        # Fix atom names for UNK residues
        for atom in u.atoms:
            if atom.resname.strip().upper() == "UNK" and atom.name.endswith("x"):
                atom.name = atom.name[:-1].upper()  # remove trailing 'x'

        # Save aligned version
        base, ext = os.path.splitext(path)
        out_path = INTERMEDIATE_DIR / f"{Path(base).name}_for_viz.pdb"
        u.atoms.write(out_path)
        print(f"Saved aligned PDB: {out_path}")

    return universes


gro_file = DATA_DIR / "em.gro"
prepare_gro_for_viz([gro_file])
