"""Regenerate Policy B summaries/figures; keep TeX and prior evidence snapshots intact."""

import contextlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data"))
from apply_task39_policy_b import (  # noqa: E402
    DATA,
    RECORD,
    TASK,
    aggregate,
    sha256,
    write_csv,
)

sys.path.insert(0, str(HERE.parent / "section3_review_2026-11-20"))
import analyze_results as exploratory  # noqa: E402

sys.path.insert(0, str(REPO / "figures/figure_4"))
import make_figure_4 as costs  # noqa: E402


def main():
    logs = HERE / "logs"
    logs.mkdir(exist_ok=True)
    current = HERE / "current"
    current.mkdir(exist_ok=True)
    cases = {r["trial_id"]: r for r in json.loads((RECORD / "decision.json").read_text())["trials"]}
    exploratory.HERE, exploratory.TABLES, exploratory.FIGURES = current, current / "tables", current / "figures"
    original_provenance = exploratory.provenance

    def provenance(trials, sources):
        frame = original_provenance(trials, sources)
        frame["prior_score_authority"] = frame.final_score_record
        frame["approved_policy_record"] = ""
        for index, row in frame.iterrows():
            if row.trial_id not in cases:
                continue
            case = cases[row.trial_id]
            assert row.trial_name == case["trial_name"] and row.task_id == TASK
            frame.at[index, "approved_policy_record"] = str(RECORD / "decision.json")
            if case["completed_setup"]:
                assert row.final_correctness == 0.9 and row.final_process == 0.6
                frame.at[index, "final_score_record"] = str(RECORD / "decision.json")
                frame.at[index, "review_correctness"], frame.at[index, "review_process"] = 0.9, 0.6
                frame.at[index, "unresolved_export_dimensions"] = ""
        assert frame.unresolved_export_dimensions.eq("").all()
        exploratory.write_csv(frame, "score_provenance")
        exploratory.write_csv(frame[frame.unresolved_export_dimensions.ne("")], "unresolved_score_provenance")
        return frame

    exploratory.provenance = provenance
    with (logs / "exploratory.log").open("w") as stream, contextlib.redirect_stdout(stream):
        exploratory.main()

    aggregate_rows, breakdown_rows = [], []
    for path in sorted((DATA / "trials").glob("*.csv")):
        model = path.stem
        metadata = pd.read_csv(DATA / f"task_summary/{path.name}")[["task_id", "category", "difficulty"]]
        for stage, root in [("before", HERE / "before/data"), ("after", DATA)]:
            trials = pd.read_csv(root / "trials" / path.name)
            overall = aggregate.overall_summary(trials)
            passed = int(round(overall["strict_pass_at_1"] * len(trials)))
            mean_cost = overall["mean_cost_usd"]
            basis = "mean of available recorded trial costs"
            if model in costs.FLAT_COST_GBP or model in costs.TOKEN_PRICES_USD_PER_MILLION:
                prices = costs.TOKEN_PRICES_USD_PER_MILLION.get(model, costs.TOKEN_PRICE_WEIGHTS)
                flat = costs.FLAT_COST_GBP.get(model)
                _, mean_cost = costs.estimated_costs(
                    trials.fillna("").to_dict("records"), prices, flat * costs.GBP_TO_USD if flat else None
                )
                basis = "existing figure estimate; recorded cost fields unchanged"
            aggregate_rows.append(
                {
                    "model": model,
                    "stage": stage,
                    "n_trials": len(trials),
                    "strict_passes": passed,
                    "strict_pass_at_1": overall["strict_pass_at_1"],
                    "strict_ci_low": overall["strict_pass_at_1_ci"][0],
                    "strict_ci_high": overall["strict_pass_at_1_ci"][1],
                    **{
                        k: overall[k]
                        for k in [
                            "mean_correctness_adj",
                            "mean_process_adj",
                            "mean_correctness_cond",
                            "mean_process_cond",
                            "n_completed",
                            "n_error",
                            "total_cost_usd",
                            "mean_cost_usd",
                        ]
                    },
                    "correctness_ci_low": overall["mean_correctness_adj_ci"][0],
                    "correctness_ci_high": overall["mean_correctness_adj_ci"][1],
                    "process_ci_low": overall["mean_process_adj_ci"][0],
                    "process_ci_high": overall["mean_process_adj_ci"][1],
                    "n_recorded_costs": int(trials.cost_usd.notna().sum()),
                    "figure_mean_cost_usd": mean_cost,
                    "cost_per_strict_pass_usd": mean_cost / overall["strict_pass_at_1"] if passed else None,
                    "cost_basis": basis,
                }
            )
            joined = trials.merge(metadata, on="task_id", validate="many_to_one")
            for column in ["difficulty", "category"]:
                for label, group in joined.groupby(column):
                    for row in aggregate.metrics_table(group, [1, 2, 3] if len(trials) == 150 else [1]).to_dict(
                        "records"
                    ):
                        breakdown_rows.append(
                            {
                                "model": model,
                                "stage": stage,
                                "breakdown": column,
                                "group": label,
                                "n_trials": len(group),
                                **row,
                            }
                        )
    write_csv(HERE / "aggregate_before_after.csv", aggregate_rows)
    write_csv(HERE / "breakdown_before_after.csv", breakdown_rows)

    before_matrix = pd.read_csv(HERE.parent / "section3_review_2026-11-20/tables/task_success_matrix.csv").set_index(
        "task_id"
    )
    after_matrix = pd.read_csv(current / "tables/task_success_matrix.csv").set_index("task_id")
    top3 = list(exploratory.MODELS)[:3]
    older = [m for m in exploratory.MODELS if exploratory.BENCHMARK_VERSIONS[m] == "v0.2"]
    subsets = {
        "strongest_three": top3,
        "plus_Gemini": top3 + ["gemini-4-argon"],
        "plus_GLM": top3 + ["glm-5.2"],
        "five_main": top3 + ["gemini-4-argon", "glm-5.2"],
        "all_twelve": list(exploratory.MODELS),
        "older_five": [m for m in older if m not in ["glm-5.2", "qwen3-coder-480b"]],
        "older_six": [m for m in older if m != "qwen3-coder-480b"],
    }
    overlaps = []
    for label, models in subsets.items():
        for condition in ["all_three", "at_least_one"]:
            values = {}
            for stage, matrix in [("before", before_matrix), ("after", after_matrix)]:
                selected = matrix[models]
                mask = selected.eq(3).all(axis=1) if condition == "all_three" else selected.gt(0).all(axis=1)
                tasks = matrix.loc[mask]
                values.update(
                    {
                        f"{stage}_tasks": len(tasks),
                        f"{stage}_hard": int(tasks.difficulty.eq("hard").sum()),
                        f"{stage}_task_ids": ";".join(tasks.index),
                    }
                )
            overlaps.append({"subset": label, "models": ";".join(models), "condition": condition, **values})
    write_csv(HERE / "overlap_before_after.csv", overlaps)

    scripts = [
        "figure_3/make_figure_3.py",
        "figure_4/make_figure_4.py",
        "figure_S1/make_figure_S1.py",
        "figure_A1/make_figure_A1.py",
        "figure_A2/make_figure_A2.py",
    ]
    for relative in scripts:
        script = REPO / "figures" / relative
        with (logs / f"{script.stem}.log").open("w") as stream:
            subprocess.run([sys.executable, str(script)], cwd=REPO, check=True, stdout=stream, stderr=subprocess.STDOUT)
    manifest_path = current / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["score_authority"] = (
        "Current manuscript CSVs including the approved Task 39 Policy B overlay; original grades unchanged."
    )
    generators = [REPO / "figures" / relative for relative in scripts] + [
        Path(__file__).resolve(),
        DATA / "apply_task39_policy_b.py",
        RECORD / "decision.json",
        HERE.parent / "section3_review_2026-11-20/analyze_results.py",
        REPO.parent / "MDArena-dev/analysis/aggregate.py",
    ]
    indexed = {r["path"]: r for r in manifest["inputs"]}
    indexed.update({str(p): {"path": str(p), "sha256": sha256(p)} for p in generators})
    manifest["inputs"] = list(indexed.values())
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        "Regenerated five publication/SI assets and four exploratory panels with existing selections/styles; no TeX writes."
    )


if __name__ == "__main__":
    main()
