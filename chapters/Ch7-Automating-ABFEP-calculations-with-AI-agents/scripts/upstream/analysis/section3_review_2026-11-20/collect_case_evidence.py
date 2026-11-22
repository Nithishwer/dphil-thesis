"""Collect existing criteria, artifacts, and trajectory evidence for the five tasks.

No grading or scientific commands from agent transcripts are executed.
"""

import hashlib
import json
import re
from pathlib import Path

import pandas as pd
from analyze_results import HERE, MODELS, TABLES, read_json

EVIDENCE = HERE / "evidence"
FOCUS = list(MODELS)[:5]
PATTERNS = {
    11: r"box|grompp|editconf|periodic|zero|non.?periodic",
    17: r"occupanc|Hydrophobic|HBDonor|HBAcceptor|to_csv|top.?ten|top.?10|numbering|resid|timeout",
    25: r"min lig.prot|lig_final|lig_from_pack|merge.py|assemble.py|coordinates|crystal.*pose|pocket|grompp",
    29: r"infinite|1\.37|1\.36|C316|Fmax|converg|query_pairs|fix.py|mdrun|not ready|un.minimis|un.minimiz",
    39: r"counter.?ion|co.alchem|co.?decoupl|net.charge|charged.endpoint|charge.correction|electrostatic|finite.size|neutraliz|neutralis|B.state|couple.moltype|Boresch",
}


def text_values(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in text_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in text_values(item)]
    return []


def load_events(source, review):
    normalized = review / "evidence/transcript.txt" if review else None
    if normalized and normalized.exists():
        text = normalized.read_text()
        chunks = re.split(r"^===== EVENT (.*?) =====\n", text, flags=re.M)
        events = []
        for i in range(1, len(chunks), 2):
            try:
                record = json.loads(chunks[i + 1])
            except json.JSONDecodeError:
                record = {"message": chunks[i + 1]}
            events.append((chunks[i], record))
        return normalized, events
    trajectory = source / "agent/trajectory.json"
    if trajectory.exists():
        data = read_json(trajectory)
        return trajectory, [(f"step {s.get('step_id', i + 1)}", s) for i, s in enumerate(data.get("steps", []))]
    sessions = sorted((source / "agent/sessions").rglob("*.jsonl"))
    events = []
    for path in sessions:
        for i, line in enumerate(path.read_text().splitlines(), 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append((f"{path.relative_to(source)}:{i}", record))
    return source / "agent/sessions", events


def extract_events(events, pattern):
    excerpts = []
    for label, event in events:
        body = event.get("message", event)
        values = text_values(body)
        # ATIF stores tool results outside message; include those when present.
        for key in ["observation", "tool_calls"]:
            if key in event:
                values.extend(text_values(event[key]))
        seen = set()
        for text in values:
            for match in list(re.finditer(pattern, text, re.I))[:8]:
                start = max(0, text.rfind("\n", 0, match.start()) + 1)
                end = text.find("\n", match.end())
                end = len(text) if end < 0 else end
                snippet = text[start:end]
                if len(snippet) > 1600:
                    start = max(start, match.start() - 350)
                    snippet = text[start : min(end, match.end() + 900)]
                if snippet not in seen:
                    excerpts.append({"event": label, "timestamp": event.get("timestamp"), "text": snippet})
                    seen.add(snippet)
    return excerpts


def read_artifact_texts(app, number):
    patterns = {
        11: ["final_answer.txt", "outputs/*.md", "outputs/*.py", "outputs/*grompp*.log"],
        17: ["final_answer.txt", "outputs/*.csv", "outputs/*.md"],
        25: [
            "final_answer.txt",
            "outputs/preparation_report.md",
            "outputs/work/assemble.py",
            "outputs/work/merge.py",
            "outputs/work/combine.py",
            "outputs/work/lig.py",
            "outputs/*grompp*.log",
        ],
        29: [
            "final_answer.txt",
            "outputs/*report*.md",
            "outputs/em_test_mdrun.log",
            "outputs/grompp_em.log",
            "outputs/*/fix.py",
        ],
        39: ["final_answer.txt", "outputs/setup_manifest.json", "outputs/**/*report*.md", "outputs/**/*.md"],
    }
    texts = []
    for pattern in patterns[number]:
        for path in sorted(app.glob(pattern)):
            if path.is_file() and path.stat().st_size < 2_000_000:
                texts.append(
                    {
                        "path": str(path),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "text": path.read_text(errors="replace"),
                    }
                )
    return texts


def main():
    EVIDENCE.mkdir(exist_ok=True)
    provenance = pd.read_csv(TABLES / "score_provenance.csv").fillna("")
    trials = pd.read_csv(TABLES / "repeated_trial_classification.csv")
    selected = trials[(trials.model.isin(FOCUS) & trials.number.isin(PATTERNS)) | trials.number.eq(39)]
    summaries, criteria_rows, cases = [], [], []
    for trial in selected.sort_values(["number", "model", "attempt_index"]).itertuples():
        source_row = provenance[(provenance.model == trial.model) & (provenance.trial_name == trial.trial_name)].iloc[0]
        source = Path(source_row.source_trial_dir)
        review = Path(source_row.review_case) if source_row.review_case else None
        original_details_path = (
            review / "evidence/reward-details.json" if review else source / "verifier/reward-details.json"
        )
        if not original_details_path.exists():
            original_details_path = source / "verifier/reward-details.json"
        original_details = read_json(original_details_path) if original_details_path.exists() else {}
        final_details_path = review / "regraded-reward-details.json" if review else original_details_path
        final_details = read_json(final_details_path) if final_details_path.exists() else original_details
        verdict = read_json(review / "user-verdict.json") if review and (review / "user-verdict.json").exists() else {}
        assessment = read_json(review / "assessment.json") if review and (review / "assessment.json").exists() else {}
        app = source / "artifacts/app"
        if not app.exists() and review:
            app = review / "evidence/artifacts"
        transcript, events = load_events(source, review)
        excerpts = extract_events(events, PATTERNS[int(trial.number)])
        original_failed, final_failed = [], []
        for authority, details in [("original", original_details), ("final_recorded_criteria", final_details)]:
            for dimension in ["correctness", "process"]:
                for i, criterion in enumerate(details.get(dimension, {}).get("criteria", [])):
                    value = criterion.get("value")
                    if value is None or not isinstance(value, (int, float)) or value >= 0.999:
                        continue
                    entry = {
                        "model": trial.model,
                        "task_id": trial.task_id,
                        "replicate": trial.attempt_index,
                        "trial_name": trial.trial_name,
                        "authority": authority,
                        "dimension": dimension,
                        "criterion_id": f"{dimension}:{i}:{criterion['name']}",
                        "name": criterion["name"],
                        "weight": criterion.get("weight", 1),
                        "value": value,
                        "description": criterion.get("description", ""),
                        "raw": criterion.get("raw"),
                        "reasoning": criterion.get("reasoning", ""),
                        "record": str(original_details_path if authority == "original" else final_details_path),
                    }
                    criteria_rows.append(entry)
                    (original_failed if authority == "original" else final_failed).append(entry)
        saved_checks = []
        if review:
            for path in sorted((review / "checks").glob("*.json")):
                if path.stat().st_size < 100_000:
                    saved_checks.append({"path": str(path), "result": read_json(path)})
        original_scores = {
            "correctness": source_row.audit_original_correctness or source_row.raw_correctness,
            "process": source_row.audit_original_process or source_row.raw_process,
        }
        # Empty strings, unlike numerical zeros, mean no audit score was recorded.
        for dimension in ["correctness", "process"]:
            audit_value = source_row[f"audit_original_{dimension}"]
            original_scores[dimension] = source_row[f"raw_{dimension}"] if audit_value == "" else audit_value
        case = {
            "model": trial.model,
            "task_id": trial.task_id,
            "number": int(trial.number),
            "replicate": int(trial.attempt_index),
            "trial_name": trial.trial_name,
            "trial_id": source_row.trial_id,
            "status": trial.status,
            "final_correctness": None if pd.isna(trial.correctness) else trial.correctness,
            "final_process": None if pd.isna(trial.process) else trial.process,
            "strict_pass": bool(trial.strict_pass),
            "original_scores": original_scores,
            "source_trial_dir": str(source),
            "review_case": str(review) if review else None,
            "numerical_score_authority": source_row.final_score_record,
            "criteria_are_adjudicated": final_details_path != original_details_path,
            "source_result_sha256": source_row.raw_result_sha256,
            "artifact_root": str(app),
            "trajectory_path": str(transcript),
            "trajectory_event_count": len(events),
            "trajectory_excerpts": excerpts,
            "artifact_texts": read_artifact_texts(app, int(trial.number)),
            "original_failed_criteria": original_failed,
            "final_failed_criteria": final_failed,
            "user_verdict": verdict,
            "historical_assessment": assessment,
            "historical_deterministic_checks": saved_checks,
            "original_details_path": str(original_details_path),
            "final_details_path": str(final_details_path),
        }
        cases.append(case)
        summaries.append(
            {
                key: case[key]
                for key in [
                    "model",
                    "task_id",
                    "replicate",
                    "trial_name",
                    "trial_id",
                    "status",
                    "final_correctness",
                    "final_process",
                    "strict_pass",
                    "source_trial_dir",
                    "review_case",
                    "artifact_root",
                    "trajectory_path",
                    "trajectory_event_count",
                ]
            }
        )
        print(
            trial.model,
            trial.task_id,
            trial.attempt_index,
            "events",
            len(events),
            "excerpts",
            len(excerpts),
            flush=True,
        )
    (EVIDENCE / "case_evidence.json").write_text(json.dumps(cases, indent=2, default=str) + "\n")
    pd.DataFrame(summaries).to_csv(TABLES / "case_trial_inventory.csv", index=False)
    pd.DataFrame(criteria_rows).to_csv(TABLES / "case_failed_criteria.csv", index=False)
    print("Collected", len(cases), "case trials.")


if __name__ == "__main__":
    main()
