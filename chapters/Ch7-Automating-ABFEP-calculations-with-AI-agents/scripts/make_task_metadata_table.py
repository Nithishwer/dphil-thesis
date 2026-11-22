#!/usr/bin/env python3
"""Table A1 - per-task metadata, generated from each task's `task.toml`.

The table this replaces was built from three CSVs (`methods_task_table.csv`,
`packages_task_table.csv`, `systems_task_table.csv`) that had no link to the
tasks and had drifted from them: the same task could be "Trajectory analysis" in
the table and `analysis` in `task.toml`, and the package column carried names
that are not in the vocabulary at all (`AmberTools`, `openmmtools`, `MPI /
OpenMPI / mpi4py`, `Matplotlib`) while omitting one that is (`ProLIF`).
`task.toml` is the single source of truth and the benchmark's own validator
enforces the vocabularies, so a generated table cannot drift from the dataset
again.

The method column is the biggest change. It held 14 free-text tags, several per
task; `task_type` holds 7 controlled values, exactly one per task. Single-valued
is deliberate: per-type success rates ("5 of 7 system preparation tasks solved")
only have a denominator if each task is counted once.

Usage:
    python make_task_metadata_table.py                  # finds MDArena-dev nearby
    MDARENA_REPO=/path/to/MDArena-dev python make_task_metadata_table.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

HERE = Path(__file__).resolve().parent
CHAPTER = Path(__file__).resolve().parents[1]
REPO_NAME = "MDArena-dev"
OUT = CHAPTER / "scripts/intermediates/task_metadata_table.tex"

# Column widths as fractions of \textwidth. The five columns are separated by
# four gaps of 2*tabcolsep, which the paper sets to 2pt, so 16pt of a 397pt text
# block goes to gaps and the fractions can sum to about 0.96 before the table
# overflows the margin. Summing to much less than that leaves a visible band of
# unused page down the right-hand side.
#
# The last column is sized by its heading, not its contents. "Difficulty" is
# wider at \scriptsize than "Medium", and a p-column does not stretch to fit an
# oversized header - it lets it stick out past the rules instead, which is what
# 0.07\textwidth (27.8pt against a 397.5pt text block) did.
WIDTHS = (0.19, 0.15, 0.29, 0.24, 0.09)

DISPLAY = {
    "analysis": "Analysis",
    "system_preparation": "System preparation",
    "free_energy": "Free energy",
    "enhanced_sampling": "Enhanced sampling",
    "parameterization": "Parameterization",
    "diagnostics": "Diagnostics",
    "quantum_chemistry": "Quantum chemistry",
    "membrane_protein": "Membrane protein",
    "soluble_protein": "Soluble protein",
    "small_molecule_system": "Small-molecule system",
    "peptide": "Peptide",
    "none": "None",
}


def find_repo() -> Path | None:
    """Search this directory and every ancestor for a MDArena-dev checkout."""
    local = CHAPTER / "data/benchmark"
    if (local / "tasks").is_dir():
        return local
    for base in (HERE, *HERE.parents):
        candidate = base / REPO_NAME
        if (candidate / "tasks").is_dir():
            return candidate
    return None


def tex_escape(text: str) -> str:
    for old, new in (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ):
        text = text.replace(old, new)
    return text


def breakable(text: str) -> str:
    """Allow a long identifier to wrap at its underscores.

    Task ids are the longest cells in the table and have no spaces, so without
    this a single id sets the column width for all 50 rows.
    """
    return tex_escape(text).replace(r"\_", r"\_\allowbreak{}")


def main() -> int:
    override = os.environ.get("MDARENA_REPO")
    repo = Path(override).expanduser() if override else find_repo()
    if repo is None:
        sys.exit(
            f"Found no {REPO_NAME} checkout with a tasks/ directory in or above\n"
            f"    {HERE}\n"
            f"Point MDARENA_REPO at one, e.g.\n"
            f"    MDARENA_REPO=/path/to/{REPO_NAME} python {Path(__file__).name}"
        )

    tasks_dir = repo / "tasks"
    if not tasks_dir.is_dir():
        sys.exit(f"No tasks/ directory under {repo}.")

    records = []
    for toml_path in sorted(tasks_dir.glob("*/task.toml")):
        with toml_path.open("rb") as handle:
            records.append(tomllib.load(handle)["metadata"])
    if not records:
        sys.exit(f"Found {tasks_dir} but no task.toml files in it.")

    colspec = "".join(f"L{{{w}\\textwidth}}" for w in WIDTHS)
    header = "Task ID & Task type & System & Packages & Difficulty \\\\"

    lines = [
        f"\\begin{{longtable}}{{@{{}}{colspec}@{{}}}}",
        "\\caption{Per-task metadata for the 50 MDArena tasks, taken from the "
        "\\texttt{[metadata]} block of each task's \\texttt{task.toml}. Task type "
        "and system type are single-valued controlled vocabularies; packages is "
        "multi-valued, and a dash means the reference solution uses no "
        "domain-specific package."
        "}\\label{tab:task-metadata}\\\\",
        "\\toprule",
        header,
        "\\midrule",
        "\\endfirsthead",
        "\\caption[]{Per-task metadata for the 50 MDArena tasks (continued).}\\\\",
        "\\toprule",
        header,
        "\\midrule",
        "\\endhead",
        "\\midrule",
        "\\multicolumn{5}{r}{Continued on next page}\\\\",
        "\\endfoot",
        "\\bottomrule",
        "\\endlastfoot",
    ]

    for m in records:
        packages = m.get("packages") or []
        pkg_cell = (
            "; \\allowbreak{}".join(tex_escape(p) for p in packages)
            if packages
            else "--"
        )
        stype = DISPLAY.get(m["system_type"], m["system_type"])
        sname = m.get("system_name", "")
        # The type is the controlled value and the name is free text, so the name
        # goes in parentheses after it rather than replacing it. A task with no
        # nameable system carries the type alone.
        system_cell = (
            stype if sname in ("", "none") else f"{stype} ({tex_escape(sname)})"
        )
        lines.append(
            f"\\texttt{{{breakable(m['task_id'])}}} & "
            f"{DISPLAY.get(m['task_type'], m['task_type'])} & "
            f"{system_cell} & {pkg_cell} & "
            f"{m['difficulty'].capitalize()} \\\\"
        )
    lines.append("\\end{longtable}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Read {len(records)} tasks from {repo}")
    print(f"Wrote {OUT}")

    import collections

    for field in ("task_type", "system_type", "difficulty"):
        counts = collections.Counter(r[field] for r in records)
        print(f"  {field}: " + ", ".join(f"{k}={v}" for k, v in counts.most_common()))
    pkgs = collections.Counter(p for r in records for p in r.get("packages", []))
    print(f"  packages: {len(pkgs)} distinct, {sum(pkgs.values())} assignments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
