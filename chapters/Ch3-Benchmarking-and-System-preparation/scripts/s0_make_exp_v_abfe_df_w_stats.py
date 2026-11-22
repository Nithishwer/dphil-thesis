"""Prepare the per-ligand tables used by thesis Figure 3.1."""

from pathlib import Path

import pandas as pd

CHAPTER = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER / "data" / "figure_3_1"
TABLE_DIR = CHAPTER / "scripts" / "intermediates" / "figure_3_1"


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

    df = pd.read_csv(csv_path)

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
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    csv_path_dict = {
        "initial": "exp_v_abfe_df_van_reps_all.csv",
        "apo": "exp_v_abfe_df_v3_apo.csv",
        "hrex": "exp_v_abfe_df_van_reps_all_hrex.csv",
        "Ehrex": "exp_v_abfe_df_van_reps_all_Ehrex.csv",
    }

    for name, csv_path in csv_path_dict.items():
        df_exp_v_abfe_w_stat = make_exp_v_abfe_w_stat(DATA_DIR / csv_path, method="TI")
        df_exp_v_abfe_w_stat["Dataset"] = name
        output = TABLE_DIR / (Path(csv_path).stem + "_w_stats.csv")
        df_exp_v_abfe_w_stat.to_csv(output, index=False)


if __name__ == "__main__":
    main()
