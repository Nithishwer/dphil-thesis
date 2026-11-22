"""Replay the approved Task 39 adjudication on manuscript CSV exports only.

Original runs, grading records, canonical tasks and every TeX file are read-only.
Run with ../MDArena-dev/.venv/bin/python after importing upstream exports.
"""

import csv
import hashlib
import io
import json
import math
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
FIRST = REPO / "analysis/section3_review_2026-11-20"
REVIEW = REPO / "analysis/section3_followup_2026-11-20"
WORK = REPO / "analysis/task39_policy_b_2026-11-20"
RECORD = DATA / "adjudications/task39_policy_b"
TASK = "39_fep_gmx_d3_abfe"
sys.path.insert(0, str(REPO.parent / "MDArena-dev"))
from analysis.compare import headline_table  # noqa: E402

from analysis import aggregate  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text().replace('"delete": [REDACTED]', '"delete": null'))


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    text = stream.getvalue()
    if not path.exists() or path.read_text() != text:
        path.write_text(text)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def equal(a, b):
    if str(a) == str(b):
        return True
    try:
        return (pd.isna(float(a)) and pd.isna(float(b))) or math.isclose(float(a), float(b), abs_tol=1e-12)
    except (ValueError, TypeError):
        return (pd.isna(a) or a == "") and (pd.isna(b) or b == "")


def merge_numeric(path, calculated, key, fields):
    """Preserve existing row order, schema and unchanged numeric text."""
    rows = read_csv(path)
    lookup = calculated.set_index(key).to_dict("index")
    assert {row[key] for row in rows} == set(lookup)
    for row in rows:
        for field in fields:
            value = lookup[row[key]][field]
            if not equal(row[field], value):
                row[field] = "" if pd.isna(value) else value
    write_csv(path, rows)


def summarize(trials, metadata):
    # Same estimators and legacy correctness-only pass_rate as the upstream exporter.
    tasks = aggregate.task_level_summary(trials, metadata)
    categories = aggregate.group_summary(tasks, "category")
    completed = trials[trials.status.eq("completed")]
    rates = completed.assign(passed=completed.correctness.ge(aggregate.PASS_THRESHOLD)).groupby("task_id").passed.mean()
    tasks = tasks.rename(columns={"strict_pass_at_1": "pass_rate"})
    tasks["pass_rate"] = tasks.task_id.map(rates)
    categories = categories.rename(columns={"strict_pass_at_1": "pass_rate"})
    categories["pass_rate"] = categories.category.map(tasks.groupby("category").pass_rate.mean())
    return tasks, categories, aggregate.metrics_table(trials, [1, 2, 3]), aggregate.overall_summary(trials)


def freeze_decision():
    path = RECORD / "decision.json"
    if path.exists():
        return read_json(path)
    WORK.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode().split("\0")
    sources = read_csv(DATA / "trial_sources.csv")
    original_paths = set()
    for source in sources:
        for relative in ["result.json", "verifier/reward.json", "verifier/reward-details.json"]:
            source_path = Path(source["source_trial_dir"]) / relative
            if source_path.is_file():
                original_paths.add(source_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        originals = dict(pool.map(lambda p: (str(p), sha256(p)), sorted(original_paths)))
    canonical = REPO.parent / "MDArena-dev/tasks"
    canonical_files = [
        p
        for p in canonical.rglob("*")
        if p.is_file() and (p.name in ["instruction.md", "task.toml", "judge.toml", "checks.py", "test.sh"])
    ]
    dump(
        WORK / "preservation_manifest.json",
        {
            "tracked": {p: sha256(REPO / p) for p in tracked if p},
            "tex": {str(p.relative_to(REPO)): sha256(p) for p in REPO.rglob("*.tex") if ".git" not in p.parts},
            "original_records": originals,
            "canonical_tasks": {str(p): sha256(p) for p in canonical_files},
        },
    )
    for source_path in sorted(DATA.rglob("*.csv")):
        if "adjudications" in source_path.parts:
            continue
        dest = WORK / "before/data" / source_path.relative_to(DATA)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, dest)

    provenance = read_csv(FIRST / "tables/score_provenance.csv")
    repeated = {r["model"] for r in read_csv(FIRST / "tables/repeatability_summary.csv")}
    selected = [r for r in provenance if r["task_id"] == TASK and r["model"] in repeated]
    saved_cases = {r["trial_id"]: r for r in read_json(FIRST / "evidence/case_evidence.json") if r["number"] == 39}
    assert len(selected) == len(saved_cases) == 36
    indexed_sources = {(r["model"], r["trial_name"]): r for r in sources}
    cases, worksheet = [], []
    for trial in selected:
        source = indexed_sources[trial["model"], trial["trial_name"]]
        original = read_json(Path(source["source_trial_dir"]) / "result.json")
        evidence = saved_cases[trial["trial_id"]]
        assert original["id"] == trial["trial_id"] and original["task_checksum"] == trial["task_checksum"]
        assert evidence["trial_name"] == trial["trial_name"] and source["task_id"] == TASK
        assert source["attempt_index"] == trial["replicate"]
        row = next(r for r in read_csv(DATA / f"trials/{trial['model']}.csv") if r["trial_name"] == trial["trial_name"])
        assert (
            row["attempt_index"] == trial["replicate"] and row["task_id"] == TASK and row["status"] == trial["status"]
        )
        assert all(equal(row[d], trial[f"final_{d}"]) for d in ["correctness", "process"]), (
            "Current inputs differ from the evidence baseline; reconcile before applying."
        )
        completed_setup = row["status"] == "completed" and float(row["correctness"] or 0) > 0
        target = (
            {"correctness": 0.9, "process": 0.6} if completed_setup else {d: row[d] for d in ["correctness", "process"]}
        )
        case = {
            key: trial[key]
            for key in [
                "model",
                "task_id",
                "replicate",
                "trial_name",
                "trial_id",
                "status",
                "task_checksum",
                "source_trial_dir",
                "final_score_record",
            ]
        }
        case.update(
            cohort="v0.2" if "analysis_v0.2c" in trial["final_score_record"] else "newer",
            prior_export_scores={d: row[d] for d in target},
            approved_export_scores=target,
            completed_setup=completed_setup,
            changed=any(not equal(row[d], target[d]) for d in target),
        )
        cases.append(case)
        original_details = read_json(Path(evidence["original_details_path"]))
        final_details = (
            read_json(Path(evidence["final_details_path"])) if evidence["criteria_are_adjudicated"] else None
        )
        for dimension in ["correctness", "process"]:
            for index, criterion in enumerate(original_details[dimension]["criteria"]):
                code = f"{'C' if dimension == 'correctness' else 'P'}{index + 1}"
                final = (
                    next((c for c in final_details[dimension]["criteria"] if c["name"] == criterion["name"]), None)
                    if final_details
                    else None
                )
                current_value = (
                    final["value"]
                    if final
                    else "not reconstructable"
                    if case["cohort"] == "v0.2"
                    else criterion["value"]
                )
                weight = criterion.get("weight", 1)
                approved = (
                    float(code not in ["C6", "P2", "P4"])
                    if completed_setup and weight
                    else current_value
                    if isinstance(current_value, (int, float))
                    else criterion["value"]
                )
                worksheet.append(
                    {
                        "model": trial["model"],
                        "cohort": case["cohort"],
                        "task_id": TASK,
                        "replicate": trial["replicate"],
                        "trial_name": trial["trial_name"],
                        "trial_id": trial["trial_id"],
                        "status": trial["status"],
                        "criterion_id": code,
                        "criterion_name": criterion["name"],
                        "dimension": dimension,
                        "wording": criterion.get("description", ""),
                        "weight": weight,
                        "original_value": criterion["value"],
                        "current_finalized_value": current_value,
                        "approved_B_value": approved,
                        "approved_B_weight": weight,
                        "rationale": "Scored implemented-charge requirement; recognition/deferred plan insufficient"
                        if completed_setup and code in ["C6", "P2", "P4"]
                        else "Carry forward accepted method-independent decision; no fresh artifact validation"
                        if completed_setup and weight
                        else "Original diagnostic/partial observation retained; no new grading",
                        "original_explanation": criterion.get("reasoning", ""),
                        "original_record": evidence["original_details_path"],
                        "prior_score_authority": trial["final_score_record"],
                    }
                )
    assert (
        len(worksheet) == 1404
        and sum(c["changed"] for c in cases) == 16
        and sum(c["completed_setup"] for c in cases) == 26
    )
    # The reset removed the untracked follow-up. Rebuild only the approved Task 39 basis.
    write_csv(REVIEW / "tables/task39_criterion_proposals.csv", worksheet)
    dump(REVIEW / "recovered_task39_cases.json", cases)
    (REVIEW / "report.md").write_text(
        "# Recovered Task 39 approval basis\n\nThe repository reset removed the original untracked focused follow-up report and worksheet. This is a transparent reconstruction of the Task 39 evidence needed for the already approved Policy B, not a verbatim restoration of that report or a new grading. The full earlier Section 3 review survives in `analysis/section3_review_2026-11-20/`. Exact UUIDs, trial names, task checksums and original/final criterion records were recovered from its frozen provenance and the original saved records.\n\nWei-Tse selected Policy B: C6, P2 and ion-specific P4 remain scored implemented-charge requirements; recognition or an unimplemented deferred plan is insufficient. Accepted method-independent restraint, lambda, ligand-perturbation and file decisions are carried forward. The separate ion-order investigation is deferred; no new artifact validation or LLM judging is performed.\n\nAll 36 current Task 39 export score pairs match the earlier evidence baseline; no Policy A update was present. Policy B changes 16 older completed setups from 1/1 to 0.9/0.6. Ten newer completed setups already have 0.9/0.6. The nine execution-error trials and completed empty GLM trial retain their existing raw export grades; errors remain zero in adjusted metrics. All 36 repeated trials fail strict success.\n\nThe recovered worksheet has 1,404 original criterion rows (540 positive-weight rows and 864 diagnostics). Older finalized criterion values remain explicitly `not reconstructable` when only aggregate exports survive. Approved non-charge values for completed setups carry forward the accepted semantic decisions; they are not asserted to be recovered observations. No partial-credit reassessment is applied to error trials.\n\n`recovered_task39_cases.json` lists all selected identities and score authorities. The approved application record, affected aggregate metrics and reproduction instructions are in `data/adjudications/task39_policy_b/` and `analysis/task39_policy_b_2026-11-20/`. Task 35 is unchanged. All TeX files are preserved at the user's latest instruction.\n"
    )
    approved_rows = [
        r
        for r in worksheet
        if float(r["weight"]) > 0 and any(c["trial_id"] == r["trial_id"] and c["completed_setup"] for c in cases)
    ]
    write_csv(RECORD / "criterion_decisions.csv", approved_rows)
    decision = {
        "policy": "Task 39 Policy B",
        "authority": "Wei-Tse; explicit user approval in this conversation",
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "policy_A_previously_applied": False,
        "evidence_recovery": "Original follow-up removed by reset; reconstructed from frozen first-review exact UUIDs and saved grading records, without new grading",
        "first_review_provenance_sha256": sha256(FIRST / "tables/score_provenance.csv"),
        "recovered_worksheet_sha256": sha256(REVIEW / "tables/task39_criterion_proposals.csv"),
        "rationale": "Retain scored C6/P2/ion-specific P4; carry forward accepted non-charge decisions. Separate ion-order investigation deferred.",
        "tex_changes_authorized": False,
        "trials": cases,
    }
    dump(path, decision)
    return decision


def main():
    decision = freeze_decision()
    sources = {(r["model"], r["trial_name"]): r for r in read_csv(DATA / "trial_sources.csv")}
    for case in decision["trials"]:
        source = sources[case["model"], case["trial_name"]]
        raw = read_json(Path(source["source_trial_dir"]) / "result.json")
        assert raw["id"] == case["trial_id"] and raw["task_checksum"] == case["task_checksum"]
        assert source["source_trial_dir"] == case["source_trial_dir"] and source["attempt_index"] == case["replicate"]
        row = next(r for r in read_csv(DATA / f"trials/{case['model']}.csv") if r["trial_name"] == case["trial_name"])
        assert row["task_id"] == TASK and row["attempt_index"] == case["replicate"] and row["status"] == case["status"]
        assert all(
            equal(row[d], case["prior_export_scores"][d]) or equal(row[d], case["approved_export_scores"][d])
            for d in ["correctness", "process"]
        )
    changes, models = [], set()
    for case in decision["trials"]:
        if not case["changed"]:
            continue
        path = DATA / f"trials/{case['model']}.csv"
        rows = read_csv(path)
        row = next(
            r
            for r in rows
            if (r["task_id"], r["trial_name"], r["attempt_index"]) == (TASK, case["trial_name"], case["replicate"])
        )
        for dimension, value in case["approved_export_scores"].items():
            if not equal(row[dimension], value):
                row[dimension] = value
        write_csv(path, rows)
        models.add(case["model"])
        changes.append(
            {
                key: case[key]
                for key in [
                    "model",
                    "task_id",
                    "replicate",
                    "trial_name",
                    "trial_id",
                    "source_trial_dir",
                    "final_score_record",
                ]
            }
            | {f"before_{d}": case["prior_export_scores"][d] for d in ["correctness", "process"]}
            | {f"after_{d}": case["approved_export_scores"][d] for d in ["correctness", "process"]}
        )
    write_csv(RECORD / "trial_changes.csv", changes)
    summaries = {}
    fields = [
        "mean_correctness_adj",
        "mean_process_adj",
        "mean_correctness_cond",
        "std_correctness_cond",
        "mean_process_cond",
        "std_process_cond",
        "pass_rate",
    ]
    for model in sorted(models):
        trials = pd.read_csv(DATA / f"trials/{model}.csv")
        metadata = pd.read_csv(DATA / f"task_summary/{model}.csv")[["task_id", "title", "category", "difficulty"]]
        tasks, categories, metrics, summaries[model] = summarize(trials, metadata)
        merge_numeric(DATA / f"task_summary/{model}.csv", tasks, "task_id", fields)
        merge_numeric(
            DATA / f"category_summary/{model}.csv",
            categories,
            "category",
            [f for f in fields if f in categories.columns],
        )
        merge_numeric(DATA / f"metrics/{model}.csv", metrics, "metric", ["value", "ci_low", "ci_high"])
    combined = pd.DataFrame(read_csv(DATA / "headline.csv")).set_index("model")
    fields = ["strict_pass_at_1", "strict_ci_low", "strict_ci_high", "mean_correctness_adj", "mean_process_adj"]
    for row in headline_table(summaries).to_dict("records"):
        for field in fields:
            combined.at[row["model"], field] = str(row[field])
    merge_numeric(DATA / "headline.csv", combined.reset_index(), "model", fields)
    print(
        "Applied Policy B: exactly 16 completed score pairs changed; original raw error grades and all TeX files untouched."
    )


if __name__ == "__main__":
    main()
