"""Record benchmark versions, grading history, prompts, and targeted trace excerpts."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
from analyze_results import BASE, HERE, MODELS, REPO, REVIEWS, TABLES, read_json
from collect_case_evidence import load_events, text_values


def git(repo, *args):
    return subprocess.check_output(["git", "-c", f"safe.directory={repo}", "-C", str(repo), *args], text=True).strip()


def main():
    cases = read_json(HERE / "evidence/case_evidence.json")
    prompts = []
    behaviour = []
    for case in cases:
        if case["number"] != 39:
            continue
        source = Path(case["source_trial_dir"])
        review = Path(case["review_case"]) if case["review_case"] else None
        transcript, events = load_events(source, review)
        prompt = ""
        for _, event in events[:12]:
            candidates = [s for s in text_values(event) if "lambda" in s and "/app/inputs" in s and len(s) > 1000]
            if candidates:
                prompt = max(candidates, key=len).split("EVENT METADATA:")[0]
                break
        assert prompt, (case["model"], case["replicate"], "No task instruction located")
        prompts.append(
            {
                "model": case["model"],
                "replicate": case["replicate"],
                "trial_name": case["trial_name"],
                "source": str(transcript),
                "prompt": prompt,
                "sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "mentions_counterion": bool(re.search(r"counter.?ion|co.alchem", prompt, re.I)),
                "mentions_charge_correction": bool(re.search(r"charge.correct|finite.size", prompt, re.I)),
            }
        )
        final_quotes = []
        for artifact in case["artifact_texts"]:
            if artifact["path"].endswith("final_answer.txt") or artifact["path"].endswith("setup_manifest.json"):
                for line in artifact["text"].splitlines():
                    if re.search(
                        r"charged.endpoint|net.charge|co.alchem|finite.size|charge.correct|electrostatic.*correct",
                        line,
                        re.I,
                    ):
                        # A repeated grompp warning is not the agent's written scientific decision.
                        if "WARNING 1 [file" not in line and len(line) < 2200:
                            final_quotes.append({"path": artifact["path"], "quote": line})
        final_quotes = list({(q["path"], q["quote"]): q for q in final_quotes}.values())
        recognition = (
            "Explicit final disclosure"
            if final_quotes
            else "No final disclosure found; inspect trajectory and completion status"
        )
        if case["model"] == "glm-5.2" and case["replicate"] == 1:
            disposition = "Explicitly no co-alchemical ion; no implemented quantitative correction; final pass comes from historical rescore."
        elif case["model"] in ["opus-5.5", "gpt-6.1-sol", "gpt-6-astra"]:
            disposition = "Charge-changing endpoint disclosed; no co-alchemical ion or calculated charge correction; final counterion penalties retained."
        elif case["model"] == "gemini-4-argon":
            disposition = "Net-charge concern appears in trajectory; no completed charge treatment; two timeouts and one completed partial-score setup."
        else:
            disposition = "Historical cohort: final success is not proof of co-ion treatment. Original criteria, prompt, and review policy are retained in the evidence."
        behaviour.append(
            {
                "model": case["model"],
                "replicate": case["replicate"],
                "trial_name": case["trial_name"],
                "final_correctness": case["final_correctness"],
                "final_process": case["final_process"],
                "status": case["status"],
                "recognition": recognition,
                "interpretation": disposition,
                "final_quotes": final_quotes,
            }
        )
    (HERE / "evidence/task39_prompts_and_disclosures.json").write_text(
        json.dumps({"prompts": prompts, "behaviour": behaviour}, indent=2) + "\n"
    )
    pd.DataFrame([{k: v for k, v in r.items() if k != "final_quotes"} for r in behaviour]).to_csv(
        TABLES / "task39_behaviour.csv", index=False
    )
    benchmark = REPO.parent / "MDArena-dev"
    version_files = [benchmark / "pyproject.toml", benchmark / "docs/DATASET_VERSIONS.md"]
    commands = [
        BASE / "MDArena_v4_runs/gemini-4-argon/gemini_sol_runtime.py",
        BASE / "MDArena_v4_runs/gemini-4-argon/opencode-gemini-4-argon-remaining-73-sol-judge.yaml",
        BASE / "MDArena_v4_runs/deepseek-v4/codex-judge",
    ]
    configurations = {str(p): p.read_text() for p in commands if p.is_file()}
    context = {
        "local_benchmark_commit": git(benchmark, "rev-parse", "HEAD"),
        "local_benchmark_tags": git(benchmark, "tag", "--list"),
        "other_benchmark_commit": git(BASE / "MDArena-dev", "rev-parse", "HEAD"),
        "frozen_DD_input_audit": {
            key: read_json(BASE / "MDArena_run_analysis_DD/input-audit.json")[key]
            for key in ["repository_commit", "selection"]
        },
        "frozen_adjudication_manifest_commit": read_json(REVIEWS / "manifest.json")["repo_commit"],
        "version_documents": {
            str(p): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "text": p.read_text()} for p in version_files
        },
        "judge_configuration_evidence": configurations,
    }
    (HERE / "evidence/benchmark_and_grading_context.json").write_text(json.dumps(context, indent=2) + "\n")
    provenance = pd.read_csv(TABLES / "score_provenance.csv")
    histories = []
    for model in MODELS:
        group = provenance[provenance.model == model]
        raw_changed = (group.raw_correctness.fillna(-1) != group.final_correctness.fillna(-1)) | (
            group.raw_process.fillna(-1) != group.final_process.fillna(-1)
        )
        histories.append(
            {
                "model": model,
                "n_trials": 150,
                "raw_to_final_score_pairs_changed": int(raw_changed.sum()),
                "final_score_records": ";".join(sorted(group.final_score_record.unique())),
            }
        )
    pd.DataFrame(histories).to_csv(TABLES / "grading_history_summary.csv", index=False)
    checks = []
    for case in cases:
        if case["number"] == 11 and case["model"] in ["gpt-6.1-sol", "gpt-6-astra", "opus-5.5", "gemini-4-argon"]:
            hits = []
            for artifact in case["artifact_texts"]:
                if artifact["path"].endswith("final_answer.txt"):
                    hits += [
                        {"source": artifact["path"], "text": line}
                        for line in artifact["text"].splitlines()
                        if re.search(r"box|validat|grompp|periodic", line, re.I)
                    ]
            hits += [
                {"source": case["trajectory_path"], "event": entry["event"], "text": entry["text"]}
                for entry in case["trajectory_excerpts"]
                if re.search(
                    r"temp.*box|box.*temp|/tmp/.*gro|validation.*gro|work/.*gro|/app/outputs/system.gro",
                    entry["text"],
                    re.I,
                )
            ]
            checks.append(
                {
                    "model": case["model"],
                    "replicate": case["replicate"],
                    "trial_name": case["trial_name"],
                    "excerpts": hits,
                }
            )
    (HERE / "evidence/task11_validation_excerpts.json").write_text(json.dumps(checks, indent=2) + "\n")
    print("Recorded prompt/disclosure comparisons, benchmark versions, grading history, and validation excerpts.")


if __name__ == "__main__":
    main()
