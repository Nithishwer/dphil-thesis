from pathlib import Path

import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s5"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s5"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


PROJECT_ROOT = CHAPTER_DIR
FIGURE_DIR = INTERMEDIATE_DIR


def make_exp_v_abfe_w_stat(batch_path=None, mode="exploratory"):
    """
    Convert the incremental Lenselink GCMC ligand summary into the same
    Experimental_G/Predicted_G/_Error table shape used by the main figure scripts.
    """

    mode = mode.lower()
    if mode not in {"exploratory", "strict"}:
        raise ValueError("mode must be one of: exploratory, strict")

    batch_path = Path(batch_path) if batch_path is not None else (DATA_DIR / "batch")
    summary_path = batch_path / "aggregates" / f"ligand_summary_{mode}.csv"
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)

    df = pd.read_csv(summary_path)
    if df.empty:
        raise ValueError(f"No ligand rows in {summary_path}")

    df = df.copy()
    df["Experimental_Error"] = 1.0
    df["Dataset"] = f"lenselink_gcmc_{mode}"
    df["Source_Batch"] = str(batch_path)

    columns = [
        "Lig_Name",
        "Experimental_G",
        "Experimental_Error",
        "Predicted_G",
        "Predicted_Error",
        "n_replicates_used",
        "included_starts",
        "excluded_starts",
        "Dataset",
        "Source_Batch",
    ]
    return df[columns]


def main():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    batch_path = DATA_DIR / "batch"
    for mode in ("exploratory", "strict"):
        try:
            df = make_exp_v_abfe_w_stat(batch_path=batch_path, mode=mode)
        except ValueError:
            continue

        out_csv = FIGURE_DIR / f"lenselink_gcmc_{mode}_w_stats.csv"
        df.to_csv(out_csv, index=False)
        print(out_csv)


if __name__ == "__main__":
    main()
