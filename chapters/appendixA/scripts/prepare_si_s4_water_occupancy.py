#!/usr/bin/env python3
"""Collect VDW-window binding-pocket resolvation data into CSV files."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

CHAPTER_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CHAPTER_DIR.parents[1]
DATA_DIR = CHAPTER_DIR / "data/si_s4_inputs"
INTERMEDIATE_DIR = CHAPTER_DIR / "scripts/intermediates/si_s4"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)


ROOT = DATA_DIR
OUT_DIR = INTERMEDIATE_DIR

DATASETS = [
    {
        "key": "kumar",
        "label": "Kumar D3",
        "kind": "avg_dirs",
        "analysis_dir": ROOT / "kumar",
    },
    {
        "key": "lenselink",
        "label": "Lenselink A2A",
        "kind": "summary",
        "analysis_dir": ROOT / "lenselink",
    },
    {
        "key": "deflorian",
        "label": "DeFlorian A2A",
        "kind": "summary",
        "analysis_dir": ROOT / "deflorian",
    },
    {
        "key": "minetti",
        "label": "Minetti A2A",
        "kind": "avg_dirs",
        "analysis_dir": ROOT / "minetti",
    },
]

ENSEMBLE_RE = re.compile(
    r"^(?P<compound>.+)_van_(?P<repeat>\d+)_(?P<window>vdw\.(?P<idx>\d+))$"
)
ID_RE = re.compile(r"^(?P<compound>.+)_(?P<window>vdw\.(?P<idx>\d+))$")


def natural_key(value: object) -> list[object]:
    return [
        int(bit) if bit.isdigit() else bit for bit in re.split(r"(\d+)", str(value))
    ]


def repeat_id(ensemble: object) -> str:
    match = re.search(r"(\d+)$", str(ensemble))
    return match.group(1) if match else str(ensemble)


def load_summary_dataset(dataset: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    wdir = dataset["analysis_dir"] / "wdir"
    summary = pd.read_csv(wdir / "vdw_water_occupancy_summary.csv").rename(
        columns={"compound": "Compound", "vanilla": "Repeat"}
    )
    summary["Repeat"] = summary["Repeat"].astype(str)
    summary["Compound"] = summary["Compound"].astype(str)
    summary["window_index"] = summary["window_index"].astype(int)

    apo = pd.read_csv(wdir / "apo_reference_means.csv").rename(
        columns={"ensemble": "apo_run"}
    )
    apo["Repeat"] = apo["apo_run"].map(repeat_id)
    return summary, apo


def load_avg_dir_dataset(dataset: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    wdir = dataset["analysis_dir"] / "wdir"
    for avg_path in sorted(wdir.glob("*/avg_water_occupancy.csv"), key=natural_key):
        if avg_path.parent.name == "apo":
            continue
        avg = pd.read_csv(avg_path)
        avg.columns = [column.strip() for column in avg.columns]
        if {"ensemble", "occupancy"}.issubset(avg.columns):
            for ensemble, occupancy in avg[["ensemble", "occupancy"]].itertuples(
                index=False, name=None
            ):
                match = ENSEMBLE_RE.match(ensemble)
                if not match:
                    continue
                rows.append(
                    {
                        "Compound": match.group("compound"),
                        "Repeat": match.group("repeat"),
                        "window": match.group("window"),
                        "window_index": int(match.group("idx")),
                        "occupancy": occupancy,
                    }
                )
        elif {"id", "van", "occupancy"}.issubset(avg.columns):
            for row_id, repeat, occupancy in avg[["id", "van", "occupancy"]].itertuples(
                index=False, name=None
            ):
                match = ID_RE.match(str(row_id))
                if not match:
                    continue
                rows.append(
                    {
                        "Compound": match.group("compound"),
                        "Repeat": str(repeat),
                        "window": match.group("window"),
                        "window_index": int(match.group("idx")),
                        "occupancy": occupancy,
                    }
                )
        else:
            raise SystemExit(f"{avg_path} has unsupported columns={list(avg.columns)}")

    if not rows:
        raise SystemExit(f"No VDW rows found in {wdir}")

    apo_features = pd.read_csv(wdir / "apo" / "WaterOccupancy_features.csv")
    apo = (
        apo_features.groupby("ensemble", as_index=False)["occupancy"]
        .mean()
        .rename(columns={"ensemble": "apo_run"})
    )
    apo["Repeat"] = apo["apo_run"].map(repeat_id)
    return pd.DataFrame(rows), apo


def load_dataset(dataset: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    if dataset["kind"] == "summary":
        summary, apo = load_summary_dataset(dataset)
    else:
        summary, apo = load_avg_dir_dataset(dataset)

    summary = summary.copy()
    summary["dataset"] = dataset["key"]
    summary["dataset_label"] = dataset["label"]
    apo = pd.DataFrame(
        [
            {
                "apo_run": "apo_mean",
                "occupancy": apo["occupancy"].mean(),
                "Repeat": "mean",
            }
        ]
    )
    apo["dataset"] = dataset["key"]
    apo["dataset_label"] = dataset["label"]
    return summary, apo


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    apos = []
    for dataset in DATASETS:
        summary, apo = load_dataset(dataset)
        summaries.append(summary)
        apos.append(apo)

    all_apo = pd.concat(apos, ignore_index=True)
    a2a_apo = all_apo[all_apo["dataset_label"].str.endswith("A2A")]
    all_apo = pd.concat(
        [
            all_apo[~all_apo["dataset_label"].str.endswith("A2A")],
            pd.DataFrame(
                [
                    {
                        "apo_run": "a2a_apo_mean",
                        "occupancy": a2a_apo["occupancy"].mean(),
                        "Repeat": "mean",
                        "dataset": "a2a_apo",
                        "dataset_label": "A2A apo mean",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    pd.concat(summaries, ignore_index=True).to_csv(
        OUT_DIR / "all_datasets_vdw_water_occupancy_summary.csv", index=False
    )
    all_apo.to_csv(OUT_DIR / "all_datasets_apo_reference_means.csv", index=False)


if __name__ == "__main__":
    main()
