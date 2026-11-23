#!/usr/bin/env python3
"""Gather Deflorian A2A PCA projections for published SI Figure S9."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s9"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s9"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


OUT = INTERMEDIATE_DIR
SOURCE = DATA_DIR / "pca_projection_df_all_cmp_clustered.csv"
EXPECTED_COMPOUNDS = ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4q", "4r"]
EXPECTED_STATES = {"apo", "vdw.20", "holo"}
OUTPUT_COLUMNS = [
    "dataset",
    "compound",
    "state",
    "ensemble",
    "timestep",
    *[f"PC{i}" for i in range(1, 9)],
]


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing source PCA projection: {SOURCE}")

    table = pd.read_csv(SOURCE)
    table = table.drop(
        columns=[column for column in table.columns if column.startswith("Unnamed")]
    )
    table["dataset"] = "deflorian"
    table = table[OUTPUT_COLUMNS]

    compounds = sorted(c for c in table["compound"].unique() if c != "apo")
    states = set(table["state"])
    if compounds != EXPECTED_COMPOUNDS:
        raise ValueError(f"Unexpected compounds: {compounds}")
    if states != EXPECTED_STATES:
        raise ValueError(f"Unexpected states: {sorted(states)}")

    output = OUT / "deflorian_pca_projection.csv"
    table.to_csv(output, index=False)
    print(f"deflorian: {len(table)} rows, compounds={compounds}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
