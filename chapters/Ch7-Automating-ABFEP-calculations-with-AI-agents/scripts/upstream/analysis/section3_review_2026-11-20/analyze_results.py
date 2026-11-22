"""Reproduce Section 3 summaries from the finalized manuscript exports.

Read-only outside this directory. No evaluations, grading, or source exports run.
"""

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE = Path("/biggin/b211/reub0138/Projects/LLMsxFEP")
REVIEWS = BASE / "MDArena_run_analysis_DD_regraded"
TABLES = HERE / "tables"
FIGURES = HERE / "figures"
sys.path.insert(0, str(REPO / "figures/figure_4"))
from make_figure_4 import PASS_THRESHOLD, mean_and_ci, strict_pass_by_task  # noqa: E402

sys.path.insert(0, str(REPO / "figures"))
from benchmark_versions import BENCHMARK_VERSIONS  # noqa: E402

MODELS = {
    "opus-5.5": "Claude Opus-5.5",
    "gpt-6.1-sol": "GPT-6.1 Sol",
    "gpt-6-astra": "GPT-6 Astra",
    "gemini-4-argon": "Gemini 4 Argon",
    "glm-5.2": "GLM-5.2",
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "opus-5": "Claude Opus-5",
    "gemini-3.7-flash": "Gemini 3.7 Flash",
    "gpt-5.6-terra": "GPT-5.6 Terra",
    "sonnet-5": "Claude Sonnet-5",
    "deepseek-v4": "DeepSeek V4.1 Flash",
    "qwen3-coder-480b": "Qwen3 Coder 480B A35B",
}
TYPES = {
    "analysis": "Analysis",
    "system_preparation": "System preparation",
    "free_energy": "Free energy",
    "enhanced_sampling": "Enhanced sampling",
    "parameterization": "Parameterization",
    "diagnostics": "Diagnostics",
    "quantum_chemistry": "Quantum chemistry",
}
MEMBRANE_TASKS = [23, 25, 26, 27, 29]
SHORT_DESCRIPTIONS = {
    1: "SMILES to solvated GROMACS ligand",
    2: "Reject incompatible trajectory concatenation",
    3: "Identify binding-pocket residues",
    4: "Trajectory side-chain distance",
    5: "Protein–ligand hydrogen bonds",
    6: "THR106 rotamer fractions",
    7: "TYK2 protein equilibration setup",
    8: "TYK2 clash assessment",
    9: "mGlu5 holo-to-apo conversion",
    10: "Magnesium coordination numbers",
    11: "Glycoinsulin AMBER-to-GROMACS conversion",
    12: "ICL1 crystallographic-water transfer",
    13: "Oxymyoglobin alternate-location cleanup",
    14: "Ligand pose and conformation RMSD",
    15: "MenG thermostat and COM-removal groups",
    16: "GAFF Ala-Phe ligand parameters",
    17: "ICL2 ProLIF interaction ranking",
    18: "Ion-charge scaling in water–decane",
    19: "Most-open TPC2 frame",
    20: "A2A ABFE dhdl analysis with alchemlyb",
    21: "OX2R crystallographic-water transfer",
    22: "Assess PepT2 PCA collective variable",
    23: "A2A–ZM241385 POPC membrane preparation",
    24: "SMIRNOFF ligand parameters",
    25: "mGlu5–51D POPC membrane preparation",
    26: "D3 POPC membrane preparation",
    27: "A2A–AZD4635 POPC membrane preparation",
    28: "PepT2 PCA umbrella-sampling setup",
    29: "PepT2–ampicillin membrane preparation",
    30: "CAM-ion pore umbrella sampling",
    31: "Na+ permeation and conductance",
    32: "DHODH OpenFE RBFE network",
    33: "D3 OpenFE RBFE network",
    34: "OX2R OpenFE RBFE network",
    35: "D3 OpenFE ABFE setup",
    36: "mGlu5 OpenFE ABFE setup",
    37: "A2A OpenFE ABFE setup",
    38: "PepT2–amoxicillin ORCA QM cluster",
    39: "D3 charged-ligand GROMACS ABFE setup",
    40: "MenG SAM RMSD with periodic imaging",
    41: "Argon-hydration REXEE simulation",
    42: "Expanded-ensemble fixed-weight conversion",
    43: "CB7–10 Wang–Landau simulation",
    44: "ATP8B1 helix RMSD with residue mapping",
    45: "ATP8B1 membrane insertion depth",
    46: "CHARMM topology and force-field repair",
    47: "Phosphoaspartate residue parameters",
    48: "CB7–10 alchemical metadynamics",
    49: "SLCO2A1 kinetic-energy validation",
    50: "Glycoinsulin beta-sheet propensity",
}
OUTCOMES = [
    "Full correctness and process",
    "Full correctness only",
    "Full process only",
    "Neither full",
    "Execution error",
]


def write_csv(frame, name):
    frame.to_csv(TABLES / f"{name}.csv", index=False)


def read_json(path):
    text = path.read_text()
    # Preserve the recorded malformed redaction; repair only the in-memory parse.
    return json.loads(text.replace('"delete": [REDACTED]', '"delete": null'))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_figure(fig, stem):
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def heatmap(tasks, matrix, models, stem):
    colours = ["#F0E4DC", "#D7AD73", "#7BB5BC", "#277E73"]
    fig, ax = plt.subplots(figsize=(10.8 if len(models) == 5 else 15.3, 13.8))
    ax.imshow(matrix[models], cmap=ListedColormap(colours), norm=BoundaryNorm(np.arange(-0.5, 4), 4), aspect="auto")
    ax.set_xticks(range(len(models)), [MODELS[m] for m in models], rotation=35, ha="right", fontsize=9)
    labels = [f"{int(r.number):02d}  {r.short_description}  [{r.difficulty[0].upper()}]" for r in tasks.itertuples()]
    ax.set_yticks(range(50), labels, fontsize=8)
    ax.tick_params(length=0)
    for i, row in enumerate(matrix[models].to_numpy()):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", fontsize=8, color="white" if value == 3 else "#202020")
    previous = None
    for i, row in enumerate(tasks.itertuples()):
        if row.category != previous:
            ax.axhline(i - 0.5, color="white", linewidth=2)
            size = int((tasks.category == row.category).sum())
            ax.text(
                1.015,
                1 - (i + (size - 1) / 2 + 0.5) / 50,
                TYPES[row.category],
                transform=ax.transAxes,
                rotation=-90 if size >= 4 else 0,
                va="center",
                ha="left",
                fontsize=8 if size <= 4 else 9,
            )
            previous = row.category
    ax.set_xticks(np.arange(-0.5, len(models)), minor=True)
    ax.set_yticks(np.arange(-0.5, 50), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.4)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Strict passes across three selected attempts per task", fontsize=13, pad=12)
    handles = [Patch(facecolor=c, label=f"{i}/3") for i, c in enumerate(colours)]
    fig.legend(handles=handles, loc="lower center", ncols=4, frameon=False, bbox_to_anchor=(0.62, 0.005))
    fig.text(
        0.62,
        0.04,
        "E = easy; M = medium; H = hard. Rows have the same order in both versions.",
        ha="center",
        fontsize=8,
    )
    fig.subplots_adjust(left=0.41 if len(models) == 5 else 0.30, right=0.94, bottom=0.15, top=0.96)
    save_figure(fig, stem)


def provenance(trials, sources):
    verified_tables = {}
    verified_root = BASE / "MDArena_v2_runs/analysis/analysis_v0.2c_codex_regraded_human_verified"
    for model, version in BENCHMARK_VERSIONS.items():
        if version == "v0.2":
            path = verified_root / model / "tables/trials.csv"
            verified_tables[model] = (path, pd.read_csv(path).set_index("trial_name"))
    cases = {}
    for folder in ["astra", "sol-6.1", "opus-5.5", "gemini-4-argon", "deepseek-v4"]:
        for path in sorted((REVIEWS / folder).glob("*/case.json")):
            case = read_json(path)
            cases[case.get("trial_name", Path(case["source"]).name)] = (path.parent, case)
    source_map = sources.set_index(["model", "task_id", "attempt_index"])

    def inspect(row):
        source = source_map.loc[(row.model, row.task_id, row.attempt_index)]
        raw_path = Path(source.source_trial_dir) / "result.json"
        raw = read_json(raw_path)
        archived = read_json(Path(source.analysis_trial_dir) / "result.json")
        assert raw["id"] == archived["id"]
        rewards = (raw.get("verifier_result") or {}).get("rewards") or {}
        case_folder, case = cases.get(row.trial_name, (None, {}))
        audit_scores = case.get("original_scores", {})
        final_path = case_folder / "regraded-reward.json" if case_folder else None
        reviewed = read_json(final_path) if final_path and final_path.exists() else {}
        verified_path = None
        if row.model in verified_tables:
            verified_path, verified = verified_tables[row.model]
            reviewed = verified.loc[row.trial_name, ["correctness", "process"]].to_dict()
        unresolved = []
        for dim in ["correctness", "process"]:
            expected = reviewed.get(dim, rewards.get(dim))
            if expected is not None and not pd.isna(getattr(row, dim)):
                if abs(float(expected) - getattr(row, dim)) > 1e-9:
                    unresolved.append(dim)
        return {
            "model": row.model,
            "task_id": row.task_id,
            "replicate": row.attempt_index,
            "trial_name": row.trial_name,
            "trial_id": raw["id"],
            "status": row.status,
            "final_correctness": row.correctness,
            "final_process": row.process,
            "raw_correctness": rewards.get("correctness"),
            "raw_process": rewards.get("process"),
            "audit_original_correctness": audit_scores.get("correctness"),
            "audit_original_process": audit_scores.get("process"),
            "review_correctness": reviewed.get("correctness"),
            "review_process": reviewed.get("process"),
            "review_case": str(case_folder) if case_folder else "",
            "final_score_record": str(verified_path or final_path) if reviewed else str(raw_path),
            "source_trial_dir": source.source_trial_dir,
            "analysis_trial_dir": source.analysis_trial_dir,
            "selection_record": source.selection_record,
            "task_checksum": raw.get("task_checksum"),
            "raw_result_sha256": sha256(raw_path),
            "unresolved_export_dimensions": ";".join(unresolved),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(inspect, trials.itertuples()))
    frame = pd.DataFrame(records)
    write_csv(frame, "score_provenance")
    write_csv(frame[frame.unresolved_export_dimensions.ne("")], "unresolved_score_provenance")
    return frame


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode().split("\0")
    protection_path = HERE / "preservation_manifest.json"
    if not protection_path.exists():
        protected = {name: sha256(REPO / name) for name in tracked if name and not name.startswith("analysis/")}
        protection_path.write_text(json.dumps(protected, indent=2) + "\n")
    headline = pd.read_csv(REPO / "data/headline.csv").set_index("model")
    frames = []
    input_files = [REPO / "main.tex", REPO / "data/headline.csv", REPO / "data/trial_sources.csv"]
    for path in sorted((REPO / "data/trials").glob("*.csv")):
        frame = pd.read_csv(path)
        frame.insert(0, "model", path.stem)
        expected = 1 if BENCHMARK_VERSIONS[path.stem] == "v0.1" else 3
        assert len(frame) == 50 * expected and frame.task_id.nunique() == 50
        assert frame.groupby("task_id").size().eq(expected).all()
        assert not frame.duplicated(["task_id", "attempt_index"]).any()
        frame["full_correctness"] = frame.correctness.fillna(0).ge(PASS_THRESHOLD)
        frame["full_process"] = frame.process.fillna(0).ge(PASS_THRESHOLD)
        frame["strict_pass"] = frame.status.eq("completed") & frame.full_correctness & frame.full_process
        records = frame.fillna("").to_dict("records")
        assert (
            abs(np.mean(list(strict_pass_by_task(records).values())) - headline.loc[path.stem, "strict_pass_at_1"])
            < 1e-12
        )
        frame["benchmark_version"] = BENCHMARK_VERSIONS[path.stem]
        frames.append(frame)
        input_files += [path, REPO / "data/task_summary" / path.name, REPO / "data/metrics" / path.name]
    trials = pd.concat(frames, ignore_index=True)
    assert len(trials) == 2100 and trials.model.nunique() == 18
    repeated = trials[trials.model.isin(MODELS)].copy()
    historical = trials[~trials.model.isin(MODELS)].copy()
    assert len(repeated) == 1800 and len(historical) == 300
    repeated["outcome"] = np.select(
        [
            repeated.status.ne("completed"),
            repeated.full_correctness & repeated.full_process,
            repeated.full_correctness,
            repeated.full_process,
        ],
        [OUTCOMES[4], OUTCOMES[0], OUTCOMES[1], OUTCOMES[2]],
        default=OUTCOMES[3],
    )
    tasks = pd.read_csv(REPO / "data/task_summary/opus-5.5.csv")[["task_id", "title", "category", "difficulty"]]
    for model in MODELS:
        other = pd.read_csv(REPO / f"data/task_summary/{model}.csv").set_index("task_id")
        assert (
            other.loc[tasks.task_id, ["category", "difficulty"]].to_numpy().tolist()
            == tasks[["category", "difficulty"]].to_numpy().tolist()
        )
    tasks["number"] = tasks.task_id.str[:2].astype(int)
    tasks["type_order"] = tasks.category.map({name: i for i, name in enumerate(TYPES)})
    tasks = tasks.sort_values(["type_order", "number"]).reset_index(drop=True)
    tasks["short_description"] = tasks.number.map(SHORT_DESCRIPTIONS)
    tasks["row_order"] = np.arange(1, 51)
    write_csv(tasks, "task_metadata")
    counts = (
        repeated.groupby(["task_id", "model"]).strict_pass.sum().unstack().astype(int).loc[tasks.task_id, list(MODELS)]
    )
    write_csv(tasks.merge(counts.reset_index(), on="task_id"), "task_success_matrix")
    repeated = repeated.merge(
        tasks[["task_id", "category", "difficulty", "number", "title"]], on="task_id", validate="many_to_one"
    )
    write_csv(repeated, "repeated_trial_classification")
    write_csv(historical, "historical_trials_separate")
    summaries = []
    for model in MODELS:
        values = counts[model]
        metrics = pd.read_csv(REPO / f"data/metrics/{model}.csv").set_index("metric")
        for metric, value in [
            ("strict pass@1", values.sum() / 150),
            ("pass@3", values.gt(0).mean()),
            ("pass^3", values.eq(3).mean()),
        ]:
            assert abs(metrics.loc[metric, "value"] - value) < 1e-12, (model, metric)
        summaries.append(
            {
                "model": model,
                "configuration": MODELS[model],
                "benchmark_version": BENCHMARK_VERSIONS[model],
                "n_tasks": 50,
                "n_trials": 150,
                "strict_passes": int(values.sum()),
                "strict_pass_at_1": values.sum() / 150,
                "pass_at_3_tasks": int(values.gt(0).sum()),
                "pass_cubed_tasks": int(values.eq(3).sum()),
                **{f"tasks_{k}_of_3": int(values.eq(k).sum()) for k in range(4)},
            }
        )
    summary = pd.DataFrame(summaries)
    write_csv(summary, "repeatability_summary")
    unresolved = counts.stack().rename("strict_passes").reset_index()
    unresolved = unresolved[unresolved.strict_passes.lt(3)].merge(tasks, on="task_id")
    write_csv(unresolved, "never_or_inconsistent_tasks")
    overlaps = []
    for labels in [list(MODELS)[:3], list(MODELS)[:4], list(MODELS)[:3] + ["glm-5.2"], list(MODELS)[:5], list(MODELS)]:
        for condition, shared in [
            ("all_three_attempts", counts[labels].eq(3).all(axis=1)),
            ("at_least_one_attempt", counts[labels].gt(0).all(axis=1)),
        ]:
            found = tasks.set_index("task_id").loc[shared[shared].index]
            overlaps.append(
                {
                    "models": ";".join(labels),
                    "condition": condition,
                    "n_tasks": len(found),
                    "n_hard": int(found.difficulty.eq("hard").sum()),
                    "task_ids": ";".join(found.index),
                }
            )
    write_csv(pd.DataFrame(overlaps), "shared_success")
    top3 = counts.iloc[:, :3].eq(3).all(axis=1)
    write_csv(
        tasks.merge(counts.iloc[:, :5], on="task_id").assign(shared_top_three=tasks.task_id.map(top3)),
        "strongest_three_all_tasks",
    )
    category_rows = []
    for model in MODELS:
        for kind in list(TYPES) + ["membrane_preparation_subset"]:
            selected = repeated[
                (repeated.model == model)
                & (
                    repeated.number.isin(MEMBRANE_TASKS)
                    if kind == "membrane_preparation_subset"
                    else repeated.category.eq(kind)
                )
            ]
            by_task = selected.groupby("task_id").strict_pass.mean()
            mean, down, up = mean_and_ci(by_task.tolist())
            category_rows.append(
                {
                    "model": model,
                    "task_type": kind,
                    "n_tasks": len(by_task),
                    "n_trials": len(selected),
                    "strict_passes": int(selected.strict_pass.sum()),
                    "strict_pass_rate": mean,
                    "ci_low": mean - down if len(by_task) > 1 else np.nan,
                    "ci_high": mean + up if len(by_task) > 1 else np.nan,
                    "tasks_with_any_pass": int(by_task.gt(0).sum()),
                    "tasks_all_three_pass": int(by_task.eq(1).sum()),
                }
            )
    workflow = pd.DataFrame(category_rows)
    write_csv(workflow, "workflow_comparison")
    write_csv(tasks[tasks.number.isin(MEMBRANE_TASKS)].merge(counts, on="task_id"), "membrane_task_success")
    paired = []
    contrasts = [
        ("gemini-4-argon", "opus-5.5"),
        ("gemini-4-argon", "gpt-6.1-sol"),
        ("opus-5.5", "gpt-6.1-sol"),
        ("gpt-6.1-sol", "gpt-6-astra"),
        ("glm-5.2", "gpt-6.1-sol"),
    ]
    for kind in list(TYPES) + ["membrane_preparation_subset"]:
        task_ids = tasks.loc[
            tasks.number.isin(MEMBRANE_TASKS) if kind == "membrane_preparation_subset" else tasks.category.eq(kind),
            "task_id",
        ]
        for a, b in contrasts:
            diffs = ((counts.loc[task_ids, a] - counts.loc[task_ids, b]) / 3).tolist()
            mean, down, up = mean_and_ci(diffs)
            paired.append(
                {
                    "task_type": kind,
                    "configuration_a": a,
                    "configuration_b": b,
                    "n_tasks": len(diffs),
                    "paired_difference": mean,
                    "ci_low": mean - down if len(diffs) > 1 else np.nan,
                    "ci_high": mean + up if len(diffs) > 1 else np.nan,
                    "tasks_a_better": sum(v > 0 for v in diffs),
                    "tasks_b_better": sum(v < 0 for v in diffs),
                    "tasks_tied": sum(v == 0 for v in diffs),
                }
            )
    write_csv(pd.DataFrame(paired), "paired_workflow_differences")
    quadrants = pd.crosstab(repeated.model, repeated.outcome).reindex(index=MODELS, columns=OUTCOMES, fill_value=0)
    assert quadrants.sum(axis=1).eq(150).all()
    write_csv(quadrants.reset_index(), "correctness_process_counts")
    heatmap(tasks, counts, list(MODELS)[:5], "task_heatmap_five")
    heatmap(tasks, counts, list(MODELS), "task_heatmap_all_twelve")
    fig, (ax, count_ax) = plt.subplots(
        1,
        2,
        figsize=(13.0, 5.0),
        sharey=True,
        gridspec_kw={"width_ratios": [4.0, 1.55], "wspace": 0.04},
    )
    colours = ["#277E73", "#75B1BF", "#E7B66A", "#B89B85", "#D5D5D5"]
    left = np.zeros(12)
    for outcome, colour in zip(OUTCOMES, colours):
        numbers = quadrants[outcome].to_numpy()
        ax.barh(range(12), numbers, left=left, color=colour, edgecolor="white", label=outcome)
        for i, n in enumerate(numbers):
            if n >= 5:
                ax.text(
                    left[i] + n / 2,
                    i,
                    str(n),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if outcome == OUTCOMES[0] else "black",
                )
        left += numbers
    ax.set_yticks(range(12), MODELS.values(), fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 150)
    ax.set_xlabel("Trials (150 selected trials per configuration)")
    ax.spines[["top", "right"]].set_visible(False)
    count_ax.set_xlim(-0.5, 4.5)
    count_ax.axis("off")
    for j, heading in enumerate(["Both", "C only", "P only", "Neither", "Error"]):
        count_ax.text(
            (j + 0.5) / 5, 1.01, heading, transform=count_ax.transAxes, ha="center", fontsize=8, fontweight="bold"
        )
        for i, value in enumerate(quadrants.iloc[:, j]):
            count_ax.text(j, i, str(value), ha="center", va="center", fontsize=8)
    fig.legend(loc="lower center", ncols=3, frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.20, right=0.99, top=0.92, bottom=0.24)
    save_figure(fig, "correctness_process_disagreement")
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    left = np.zeros(12)
    for k, colour in enumerate(["#F0E4DC", "#D7AD73", "#7BB5BC", "#277E73"]):
        numbers = summary[f"tasks_{k}_of_3"].to_numpy()
        ax.barh(range(12), numbers, left=left, color=colour, edgecolor="white", label=f"{k}/3 strict passes")
        for i, n in enumerate(numbers):
            if n >= 2:
                ax.text(
                    left[i] + n / 2,
                    i,
                    str(n),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if k == 3 else "black",
                )
        left += numbers
    ax.set_yticks(range(12), MODELS.values(), fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 50)
    ax.set_xlabel("Tasks (50 tasks per configuration)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.legend(loc="lower center", ncols=4, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save_figure(fig, "repeatability_task_counts")
    sources = pd.read_csv(REPO / "data/trial_sources.csv").fillna("")
    traced = provenance(trials, sources)
    input_files += [
        REVIEWS / "manifest.json",
        REVIEWS / "regraded-scores.json",
        REVIEWS / "user-verdict-application.json",
        REVIEWS / "export_rsc_data.py",
        BASE / "MDArena_run_analysis_DD/input-audit.json",
        BASE / "MDArena_evals/export_rsc_data.py",
        REPO / "figures/figure_4/make_figure_4.py",
        REPO / "figures/benchmark_versions.py",
    ]
    older = BASE / "MDArena_v2_runs/analysis"
    input_files += list((older / "analysis_v0.2c_codex_regraded_human_verified").glob("*/tables/trials.csv"))
    input_files += list((older / "yolo_sol_checking_tasks/task_review_nd_suggestions").glob("*.md"))
    input_files += list((older / "yol_sol_checking_tasks_human checked/task_review_nd_suggestions").glob("*.md"))
    input_files += [older / "analysis_v0.2c_codex_regraded_human_verified/comparison.md"]
    manifest = {
        "manuscript_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "n_configurations": 18,
        "n_trials": 2100,
        "n_repeated_configurations": 12,
        "n_repeated_trials": 1800,
        "strict_threshold": PASS_THRESHOLD,
        "bootstrap_resamples": 2000,
        "bootstrap_seed": 0,
        "score_authority": "Finalized manuscript CSVs; traced against saved original and regraded scores, without modifying scores.",
        "inputs": [{"path": str(p), "sha256": sha256(p)} for p in input_files],
    }
    (HERE / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(summary.to_string(index=False))
    print(pd.DataFrame(overlaps)[["models", "condition", "n_tasks", "n_hard"]].to_string(index=False))
    print(quadrants.to_string())
    print("Traced", len(traced), "selected trials. Outputs:", HERE)


if __name__ == "__main__":
    main()
