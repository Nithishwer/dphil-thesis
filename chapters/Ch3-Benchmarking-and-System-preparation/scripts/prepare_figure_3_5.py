"""Snapshot current Deflorian OX2 set 1 results, retaining missing values as NA."""

import csv
import math
import re
from pathlib import Path

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data" / "figure_3_5"
SOURCE_DIR = Path("/biggin/b211/reub0138/Projects/orexin")
SOURCE_FOLDERS = {
    "without_na": SOURCE_DIR / "deflorian_set_1_j13_v1",
    "with_na": SOURCE_DIR / "deflorian_set_1_j13_v2_na",
}
METHODS = ("MBAR", "BAR", "TI")


def read_results(path):
    """Accept one finite total row; malformed results should not become NA."""
    with path.open(newline="") as stream:
        totals = [row for row in csv.DictReader(stream) if row["state"] == "total"]
    if len(totals) != 1:
        raise ValueError(f"{path}: expected exactly one total row")
    values = {}
    for method in METHODS:
        for column in (method, f"{method}_Error"):
            value = float(totals[0][column])
            if not math.isfinite(value) or (column.endswith("_Error") and value < 0):
                raise ValueError(f"{path}: invalid {column}")
            values[column] = value
    return values


def main():
    experimental_path = SOURCE_FOLDERS["with_na"] / "deflorian_set1_exp_data.csv"
    with experimental_path.open(newline="") as stream:
        experimental = {
            row["compound"]: float(row["experimental_dg_kcal_mol"])
            for row in csv.DictReader(stream)
        }

    rows = []
    for compound, experimental_dg in sorted(experimental.items()):
        paths = {}
        repeats = {1, 2, 3}
        for condition, folder in SOURCE_FOLDERS.items():
            for run in sorted((folder / compound).glob("abfe_van*_hrex_r1")):
                # Only current numbered runs qualify; abfe_old is excluded.
                match = re.fullmatch(r"abfe_van(\d+)_hrex_r1", run.name)
                if match:
                    repeat = int(match[1])
                    repeats.add(repeat)
                    paths[condition, repeat] = run / "analysis" / "abfe_results.csv"

        for condition, folder in SOURCE_FOLDERS.items():
            for repeat in sorted(repeats):
                path = paths.get(
                    (condition, repeat),
                    folder
                    / compound
                    / f"abfe_van{repeat}_hrex_r1/analysis/abfe_results.csv",
                )
                row = {
                    "Compound": compound,
                    "Condition": condition,
                    "Repeat": repeat,
                    "Experimental_G": experimental_dg,
                    "Experimental_Error": 1.0,
                    "Source": str(path),
                }
                if path.is_file():
                    row.update(read_results(path))
                rows.append(row)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "deflorian_set1_repeats.csv"
    columns = [
        "Compound",
        "Condition",
        "Repeat",
        "Experimental_G",
        "Experimental_Error",
        *[column for method in METHODS for column in (method, f"{method}_Error")],
        "Source",
    ]
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, restval="NA")
        writer.writeheader()
        writer.writerows(rows)
    for condition in SOURCE_FOLDERS:
        available = [
            row for row in rows if row["Condition"] == condition and "MBAR" in row
        ]
        print(
            f"{condition}: {len(available)} repeats, "
            f"{len({row['Compound'] for row in available})} compounds"
        )
    print(output)


if __name__ == "__main__":
    main()
