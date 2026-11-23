from pathlib import Path
import logging
import os
import json

import pandas as pd
import numpy as np

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/water_occupancy/solvated"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/water_occupancy/solvated"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    """Main function to run the analysis"""

    # Load configuration
    config_path = DATA_DIR / "config.json"
    config = json.loads(config_path.read_text())
    analysis_output_dir = DATA_DIR
    cumulative_df = pd.DataFrame()

    for cmp in config["compounds"][:]:
        # Log
        logging.info("Analyzing compound %s ...", cmp)

        # Create output directory
        cmp_output_dir = os.path.join(analysis_output_dir, cmp)
        avg_df = pd.read_csv(os.path.join(cmp_output_dir, "avg_water_occupancy.csv"))
        cumulative_df = pd.concat([cumulative_df, avg_df], ignore_index=True)

    cumulative_df["window"] = cumulative_df["id"].str.split("_").str[1]
    cumulative_df["cmp"] = cumulative_df["id"].str.split("_").str[0]

    # Making apo solvation area
    apo_water_features_df = pd.read_csv(
        os.path.join(analysis_output_dir, "apo", "WaterOccupancy_features.csv")
    )
    apo_range_dict = {}
    for apo_run in apo_water_features_df["ensemble"].unique():
        apo_range_dict[apo_run] = np.mean(
            apo_water_features_df[apo_water_features_df["ensemble"] == apo_run][
                "occupancy"
            ]
        )

    logging.info("Apo occupancy ranges: %s", apo_range_dict)

    # Save Cumulative df
    cumulative_df.to_csv(
        INTERMEDIATE_DIR / "cumulative_water_occupancy_all_cmp_solvated.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
