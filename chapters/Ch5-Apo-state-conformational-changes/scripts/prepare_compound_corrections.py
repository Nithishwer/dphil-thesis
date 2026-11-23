from pathlib import Path

import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/compound_reus"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/compound_correction"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

compounds = ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4q", "4r"]

reus_dict = {"Lig_Name": [], "reus_correction": []}

for compound in compounds:
    df = pd.read_csv(DATA_DIR / f"intersection_points_{compound}_van1_apo_3.csv")
    # Get the free where category is colvars_100_pct_forward and line_type = {compound}_van1
    reus_corr = df["free"][
        (df["category"] == "colvars_100_pct_forward")
        & (df["line_type"] == f"{compound}_van1")
    ].values[0]
    print(f"REUS Correction for {compound} is: {reus_corr}")
    reus_dict["Lig_Name"].append(compound)
    reus_dict["reus_correction"].append(reus_corr)

# Convert reus dict to df and save it as csv
pd.DataFrame(reus_dict).to_csv(INTERMEDIATE_DIR / "reus_correction.csv", index=False)
