"""Prepare Figure 3.3 data; copied from orexin/figures/fig6 with local paths."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "figure_3_3"


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

    df = pd.read_csv(csv_path, comment="#")

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
        "kumar_without_na": "kumar_exp_v_abfe_df.csv",
        "kumar_with_na": "kumar_exp_v_abfe_df_na.csv",
    }

    for name, csv_path in csv_path_dict.items():
        df_exp_v_abfe_w_stat = make_exp_v_abfe_w_stat(DATA_DIR / csv_path, method="TI")
        df_exp_v_abfe_w_stat["Dataset"] = name
        df_exp_v_abfe_w_stat.to_csv(DATA_DIR / f"{name}_w_stats.csv", index=False)


if __name__ == "__main__":
    main()
