from pathlib import Path

import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/mglu5_abfe"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/mglu5_abfe"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


def make_exp_v_abfe_w_stat(csv_path, method="MBAR"):
    """
    method: one of ["MBAR", "BAR", "TI"]
    Uses the corresponding columns:
       MBAR → ("MBAR", "MBAR_Error")
       BAR  → ("BAR", "BAR_Error")
       TI   → ("TI", "TI_Error")
    """

    method = method.upper()
    valid = {"MBAR", "BAR", "TI"}
    if method not in valid:
        raise ValueError(f"method must be one of {valid}")

    # Map method to its value and error column
    value_col = method

    df = pd.read_csv(DATA_DIR / csv_path, comment="#")

    # Compute stats by ligand
    grouped = (
        df.groupby("Lig_Name")
        .agg(
            Experimental_G=("Experimental_G", "mean"),
            Predicted_G=(value_col, "mean"),
            Predicted_Error=(value_col, "std"),
        )
        .reset_index()
    )

    # Add constant experimental error
    grouped["Experimental_Error"] = 1.0

    # Rename final dataframe
    exp_v_abfe_w_stat = grouped.copy()

    return exp_v_abfe_w_stat


def main():
    csv_path_dict = {
        "initial": "exp_v_abfe_df_van_reps_all_hrex.csv",
        "solvated": "exp_v_abfe_df_van_reps_all_hrex_solvated.csv",
    }

    for name, csv_path in csv_path_dict.items():
        df_exp_v_abfe_w_stat = make_exp_v_abfe_w_stat(csv_path, method="TI")
        df_exp_v_abfe_w_stat["Dataset"] = name
        df_exp_v_abfe_w_stat.to_csv(
            INTERMEDIATE_DIR / f"{name}_w_stats.csv", index=False
        )


if __name__ == "__main__":
    main()
