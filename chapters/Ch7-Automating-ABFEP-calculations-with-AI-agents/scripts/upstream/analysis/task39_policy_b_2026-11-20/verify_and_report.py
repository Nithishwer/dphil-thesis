"""Validate the redo, render review copies, and list manual TeX updates only."""

import collections
import hashlib
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data"))
from apply_task39_policy_b import (  # noqa: E402
    DATA,
    FIRST,
    RECORD,
    TASK,
    equal,
    read_csv,
    read_json,
    sha256,
    write_csv,
)


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "|" + "---|" * len(headers),
                *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def main():
    decision = read_json(RECORD / "decision.json")
    protected = read_json(HERE / "preservation_manifest.json")
    cases = decision["trials"]
    expected = {
        "gpt-5.6-sol": 120,
        "gpt-5.6-terra": 102,
        "opus-5": 112,
        "gemini-3.7-flash": 104,
        "sonnet-5": 93,
        "glm-5.2": 94,
    }
    allowed_changes = {(c["model"], c["trial_name"]) for c in cases if c["changed"]}
    changes, task39, population = [], [], 0
    headline = {r["model"]: r for r in read_csv(DATA / "headline.csv")}
    for path in sorted((DATA / "trials").glob("*.csv")):
        current = read_csv(path)
        original = read_csv(HERE / "before/data/trials" / path.name)
        before = {(r["task_id"], r["trial_name"], r["attempt_index"]): r for r in original}
        assert len(current) == len(before) and len({r["task_id"] for r in current}) == 50
        before_strict = sum(
            r["status"] == "completed" and all(float(r[d] or 0) >= 0.999 for d in ["correctness", "process"])
            for r in original
        )
        strict = 0
        for row in current:
            old = before[row["task_id"], row["trial_name"], row["attempt_index"]]
            fields = {key for key in row if row[key] != old[key]}
            if fields:
                assert (path.stem, row["trial_name"]) in allowed_changes and fields == {"correctness", "process"}
                assert (
                    row["status"] == "completed" and float(row["correctness"]) == 0.9 and float(row["process"]) == 0.6
                )
                changes.append((path.stem, row["trial_name"]))
            passed = row["status"] == "completed" and all(
                float(row[d] or 0) >= 0.999 for d in ["correctness", "process"]
            )
            strict += passed
            if row["task_id"] == TASK and len(current) == 150:
                task39.append(row)
                assert not passed
        assert strict == expected.get(path.stem, before_strict)
        assert abs(strict / len(current) - float(headline[path.stem]["strict_pass_at_1"])) < 1e-12
        if len(current) == 50:
            for folder in ["trials", "task_summary", "category_summary", "metrics"]:
                assert sha256(DATA / folder / path.name) == sha256(HERE / "before/data" / folder / path.name)
        population += len(current)
    assert population == 2100 and len(headline) == 18 and set(changes) == allowed_changes and len(changes) == 16
    assert len(task39) == 36 and sum(r["status"] != "completed" for r in task39) == 9
    assert (
        sum(
            r["status"] == "completed" and float(r["correctness"]) == 0.9 and float(r["process"]) == 0.6 for r in task39
        )
        == 26
    )
    assert sum(r["status"] == "completed" and float(r["correctness"]) == 0 for r in task39) == 1
    criteria = read_csv(RECORD / "criterion_decisions.csv")
    assert len(criteria) == 390
    charge_criteria = {
        "C6": "alchemical_chloride_counterion_is_present_and_neutralized",
        "P2": "did_the_agent_recognize_that_annihilatin",
        "P4": "did_the_agent_update_or_generate_the_com",
    }
    for code, name in charge_criteria.items():
        selected = [row for row in criteria if row["criterion_id"] == code]
        assert len(selected) == 26
        assert all(row["criterion_name"] == name and float(row["approved_B_value"]) == 0 for row in selected)
    for trial_id in {r["trial_id"] for r in criteria}:
        for dimension, expected_score in [("correctness", 0.9), ("process", 0.6)]:
            group = [r for r in criteria if r["trial_id"] == trial_id and r["dimension"] == dimension]
            score = sum(float(r["weight"]) * float(r["approved_B_value"]) for r in group) / sum(
                float(r["weight"]) for r in group
            )
            assert abs(score - expected_score) < 1e-12
    current_matrix = read_csv(HERE / "current/tables/task_success_matrix.csv")
    old_matrix = read_csv(FIRST / "tables/task_success_matrix.csv")
    assert [r["task_id"] for r in current_matrix] == [r["task_id"] for r in old_matrix]
    for old, row in zip(old_matrix, current_matrix):
        if row["task_id"] != TASK:
            assert old == row
    quadrants = {r["model"]: r for r in read_csv(HERE / "current/tables/correctness_process_counts.csv")}
    for old in read_csv(FIRST / "tables/correctness_process_counts.csv"):
        row = quadrants[old["model"]]
        delta = sum(model == old["model"] for model, _ in changes)
        assert int(row["Full correctness and process"]) == int(old["Full correctness and process"]) - delta
        assert int(row["Neither full"]) == int(old["Neither full"]) + delta
        assert all(row[key] == old[key] for key in ["Execution error", "Full process only", "Full correctness only"])
    with ThreadPoolExecutor(max_workers=8) as pool:
        modified = list(
            pool.map(
                lambda item: item[0] if sha256(Path(item[0])) != item[1] else None,
                protected["original_records"].items(),
            )
        )
    assert not any(modified)
    assert all(sha256(Path(path)) == digest for path, digest in protected["canonical_tasks"].items())
    assert all(sha256(REPO / path) == digest for path, digest in protected["tex"].items())
    preserved_prefixes = [
        "analysis/section3_review_2026-11-20/",
        "figures/figure_1/",
        "figures/figure_2/",
        "figures/archived/",
    ]
    assert all(
        sha256(REPO / path) == digest
        for path, digest in protected["tracked"].items()
        if any(path.startswith(prefix) for prefix in preserved_prefixes)
    )
    metrics = read_csv(HERE / "aggregate_before_after.csv")
    lookup = {(r["model"], r["stage"]): r for r in metrics}
    for model in headline:
        assert all(
            equal(lookup[model, "before"][key], lookup[model, "after"][key])
            for key in ["total_cost_usd", "mean_cost_usd", "figure_mean_cost_usd", "n_recorded_costs"]
        )
    hashes = {str(p): sha256(p) for p in DATA.rglob("*.csv")}
    subprocess.run([sys.executable, str(DATA / "apply_task39_policy_b.py")], check=True, stdout=subprocess.DEVNULL)
    assert all(sha256(Path(path)) == digest for path, digest in hashes.items())
    # Confirm all recorded generator/data hashes correspond to the final run.
    manifest = read_json(HERE / "current/input_manifest.json")
    assert all(sha256(Path(row["path"])) == row["sha256"] for row in manifest["inputs"])

    validation = HERE / "validation"
    validation.mkdir(exist_ok=True)
    publication = [
        REPO / f"figures/{name}/{name}.pdf" for name in ["figure_3", "figure_4", "figure_S1", "figure_A1", "figure_A2"]
    ]
    panels = publication + sorted((HERE / "current/figures").glob("*.pdf"))
    for panel in panels:
        subprocess.run(
            ["pdftoppm", "-scale-to", "1800", "-singlefile", "-png", str(panel), str(validation / panel.stem)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    missing, duplicate = [], {}
    for name in ["main.tex", "SI.tex"]:
        text = (REPO / name).read_text()
        assert collections.Counter(re.findall(r"\\begin\{([^}]+)\}", text)) == collections.Counter(
            re.findall(r"\\end\{([^}]+)\}", text)
        )
        for path in re.findall(r"\\(?:includegraphics(?:\[[^]]*\])?|suppfigure)\{([^}]+)\}", text):
            if "#" not in path and not any(
                (REPO / (path + suffix)).exists() for suffix in ["", ".pdf", ".png", ".eps"]
            ):
                missing.append({"tex_file": name, "asset": path})
        labels = collections.Counter(re.findall(r"\\label\{([^}]+)\}", text))
        duplicate[name] = [key for key, count in labels.items() if count > 1]

    # Recover the saved Task 32 evidence; this reads records and does not execute agent code.
    task32 = next(
        r
        for r in read_csv(FIRST / "tables/score_provenance.csv")
        if r["trial_name"] == "32_fep_openfe_rbfe_dhodh__Y9ZuSSz"
    )
    raw = read_json(Path(task32["source_trial_dir"]) / "result.json")
    assert raw["id"] == task32["trial_id"] and raw["exception_info"] is None
    saved_report = Path(task32["review_case"]) / "report.md"
    (validation / "task32_evidence.md").write_text(
        f"# Saved Task 32 review (read-only copy)\n\nSource: {saved_report}\nSHA256: {sha256(saved_report)}\n\n"
        + saved_report.read_text()
    )
    changes32 = {
        "trial_id": raw["id"],
        "source": task32["source_trial_dir"],
        "agent_execution": raw["agent_execution"],
        "verifier": raw["verifier"],
        "exception_info": raw["exception_info"],
        "scores": raw["verifier_result"]["rewards"],
    }
    (validation / "task32_runtime.json").write_text(json.dumps(changes32, indent=2) + "\n")

    updates = []
    instructions = [
        (
            "main.tex",
            "In Task~39",
            "Replace the Task 39/32 paragraph",
            "Task 39 concerns the complex leg for one +1 ligand (11a), not a set of ligands. All 36 repeated trials fail strict success under Policy B. The nine strongest-three completed trials acknowledge the charge change but do not implement the scored ion/index treatment and receive C=0.9/P=0.6. Recognition/deferred plans are insufficient; co-alchemical ions are not the only scientifically possible charge-treatment strategy. Task 32 failed through incomplete delivery after a charging/network-planning command continued in the background: the agent ended its turn and verification began without the required outputs. No Harbor agent timeout was recorded; grades stay unchanged.",
        ),
        (
            "main.tex",
            "The reported results have incorporated",
            "Document harmonization in Methods",
            "Retrospectively apply C6, P2 and ion-specific P4 consistently across the twelve repeated configurations; preserve accepted method-independent corrections and original run records. Do not describe the ion-order question as independently revalidated. The broader claim that all cohort criteria are comparable remains outside this specific approval.",
        ),
        (
            "main.tex",
            "When the analysis was restricted",
            "Update adjusted and conditional means",
            "Gemini 4 Argon: correctness 82.47% adjusted / 98.18% conditional; process 82.99% / 98.79%. GLM: correctness 82.30% / 90.11%; process 83.89% / 91.85%. The old conditional values were already stale before Policy B. Conditioning on completion does not identify model versus harness causes.",
        ),
        (
            "main.tex",
            "GLM-5.2 passed 39",
            "Correct GLM repeatability",
            "38/50 tasks at least once, 24/50 on all three (previously 39/50 and 24/50).",
        ),
        (
            "main.tex",
            "71.3\\% to 76.7",
            "Correct Gemini cost-comparison success rate",
            "Gemini 3.7 Flash rises from its revised 69.3% to Gemini 4 Argon's unchanged 76.7%, rather than 71.3% to 76.7%. Recorded costs are unchanged. Cost-panel references should point to Figure 4B, not 3B.",
        ),
        (
            "main.tex",
            "We evaluate 12+",
            "Correct the commented abstract population",
            "18 configurations, 2,100 trials: twelve repeated configurations contribute 1,800 and six historical configurations contribute 300. The live abstract and conclusion placeholders are otherwise unchanged.",
        ),
        (
            "SI.tex",
            "Although the prompt specifies",
            "Correct Task 39 scientific requirement wording",
            "The scored requirement is implemented charge compensation through the co-alchemical chloride and associated index; recognition or an unimplemented plan is insufficient. Do not claim this is the only scientifically valid strategy. Accept valid explicit B states or couple-moltype for the ligand pathway.",
        ),
        (
            "SI.tex",
            "The deterministic verifier carries out four",
            "Describe the actual harmonized assessment",
            "Ten equally weighted correctness criteria and five equally weighted process criteria. Preserve the accepted representation corrections. Across 26 completed setups, C=9/10 and P=3/5. Nine errors retain raw grades but adjusted scores are zero; the completed empty GLM trial stays zero. The 16 changed passes are three each for Sol-5.6, Terra, Opus-5, Flash-3.7 and Sonnet-5, plus one GLM trial.",
        ),
        (
            "SI.tex",
            "omitted from main-text Figure~3",
            "Correct S1 reference",
            "S1 complements current main-text Figure 4 (difficulty/cost), not Figure 3 (timeline/rewards).",
        ),
        (
            "SI.tex",
            "figures/codex_regrade_human/figure_A1",
            "Update outcome asset and caption manually",
            "Use figures/figure_A1/figure_A1.pdf; its existing renderer selects ten configurations, not the seven described in the current legacy caption. The selection/design were preserved during regeneration.",
        ),
        (
            "SI.tex",
            "figures/codex_regrade_human/figure_A2",
            "Update task-type asset and caption manually",
            "Use figures/figure_A2/figure_A2.pdf with the same ten selected configurations. The current TeX references a missing historical asset; no alias was inserted that would silently contradict its seven-model caption.",
        ),
    ]
    for name, needle, action, replacement in instructions:
        for line, text in enumerate((REPO / name).read_text().splitlines(), 1):
            if needle in text:
                updates.append(
                    {
                        "file": name,
                        "line": line,
                        "action": action,
                        "manual_update": replacement,
                        "status": "not applied: user forbids TeX changes",
                    }
                )
    write_csv(HERE / "manual_tex_updates.csv", updates)
    result = {
        "baseline_commit": decision["baseline_commit"],
        "n_configurations": 18,
        "n_trials": population,
        "changed_trials": 16,
        "task39_completed_setups_at_09_06": 26,
        "task39_repeated_strict_passes": 0,
        "policy_A_previously_applied": False,
        "tex_files_checked": len(protected["tex"]),
        "all_tex_files_byte_identical": True,
        "original_record_files_checked": len(protected["original_records"]),
        "original_records_unchanged": True,
        "canonical_task_files_checked": len(protected["canonical_tasks"]),
        "canonical_task_files_unchanged": True,
        "historical_v01_exports_byte_identical": True,
        "unrelated_trial_fields_costs_and_Task32_Task35_scores_unchanged": True,
        "latest_Figure2_PNG_PPTX_unchanged": True,
        "original_frozen_review_unchanged": True,
        "overlay_replay_byte_identical": True,
        "figure_panels_rendered": len(panels),
        "tex_compiler": next((x for x in ["latexmk", "pdflatex", "xelatex", "tectonic"] if shutil.which(x)), None),
        "compiled": False,
        "existing_unresolved_tex_assets": missing,
        "duplicate_tex_labels": duplicate,
    }
    (validation / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    report = [
        "# Task 39 Policy B: redo against the updated checkout\n",
        f"Baseline commit: `{decision['baseline_commit']}` (`Updated Figure 2`). The input scores match the surviving pre-update evidence baseline; no Policy A changes were present. Exactly 16 score pairs changed from 1/1 to 0.9/0.6. Ten newer completed setups already had these scores. All 36 selected repeated Task 39 trials now fail strict success. The nine error trials retain their raw grades and stay zero in adjusted metrics; the completed empty GLM trial stays zero. **Every TeX file is byte-identical to the updated checkout**, as explicitly requested in the latest instruction.\n",
        "## Before/after aggregate metrics\n\nEach affected configuration has 150 trials. C/P means are adjusted; CIs use the existing 2,000 task-clustered bootstrap resamples, seed 0, 95% percentile limits. Cost per strict pass uses the existing plotted mean cost divided by strict success; GLM retains the supplied-mean/token allocation assumption. Recorded costs/coverage are unchanged.\n",
    ]
    models = [r["model"] for r in read_csv(HERE / "before/data/headline.csv") if r["model"] in expected]
    report.append(
        table(
            [
                "Configuration",
                "Passes before → after",
                "After strict rate [95% CI]",
                "Mean C before → after",
                "Mean P before → after",
                "USD per strict pass before → after",
            ],
            [
                [
                    m,
                    f"{lookup[m, 'before']['strict_passes']} → {lookup[m, 'after']['strict_passes']}",
                    f"{float(lookup[m, 'after']['strict_pass_at_1']):.2%} [{float(lookup[m, 'after']['strict_ci_low']):.2%}, {float(lookup[m, 'after']['strict_ci_high']):.2%}]",
                    *[
                        f"{float(lookup[m, 'before'][key]):.6f} → {float(lookup[m, 'after'][key]):.6f}"
                        for key in ["mean_correctness_adj", "mean_process_adj"]
                    ],
                    f"{float(lookup[m, 'before']['cost_per_strict_pass_usd']):.4f} → {float(lookup[m, 'after']['cost_per_strict_pass_usd']):.4f}",
                ]
                for m in models
            ],
        )
    )
    repeatability = []
    repeat_counts = {}
    for model in models:
        for stage, root in [("before", HERE / "before/data"), ("after", DATA)]:
            for row in read_csv(root / f"metrics/{model}.csv"):
                if row["metric"] in ["pass@3", "pass^3"]:
                    count = round(float(row["value"]) * int(row["n_tasks"]))
                    repeat_counts[model, stage, row["metric"]] = count
                    repeatability.append({"model": model, "stage": stage, **row, "task_count": count})
    write_csv(HERE / "repeatability_before_after.csv", repeatability)
    report.append(
        "\nRepeatability changes (task counts out of 50; confidence intervals are in `repeatability_before_after.csv`):\n"
    )
    report.append(
        table(
            ["Configuration", "Pass@3 tasks before → after", "Pass³ tasks before → after"],
            [
                [
                    model,
                    *[
                        f"{repeat_counts[model, 'before', metric]} → {repeat_counts[model, 'after', metric]}"
                        for metric in ["pass@3", "pass^3"]
                    ],
                ]
                for model in models
            ],
        )
    )
    report.append(
        "\nAll other configurations' totals are unchanged. Full before/after correctness/process CIs, conditional means and costs are in `aggregate_before_after.csv`. Every difficulty/type metric and its task-bootstrap CI is in `breakdown_before_after.csv`.\n\n## Exact changes and provenance\n\n`data/adjudications/task39_policy_b/decision.json` verifies exact UUIDs, trial names, task checksums and replicate identities. The 390 scored criterion decisions for 26 completed setups are beside it. C6/P2/ion-specific P4 remain failures; non-charge decisions are carried forward without new artifact validation. The separate ion-order question is deferred. `trial_changes.csv` gives full source and prior final-grade paths.\n"
    )
    report.append(
        table(
            ["Configuration", "R", "Exact trial", "UUID", "C/P before → after"],
            [
                [r["model"], r["replicate"], r["trial_name"], r["trial_id"], "1/1 → 0.9/0.6"]
                for r in read_csv(RECORD / "trial_changes.csv")
            ],
        )
    )
    report.append(
        "\nThe reset removed the untracked focused follow-up. Its required Task 39 basis was reconstructed transparently from `analysis/section3_review_2026-11-20/tables/score_provenance.csv`, the first review's exact case UUIDs, and saved original/final criterion records. The reconstructed report/1,404-row worksheet are in `analysis/section3_followup_2026-11-20/`; they are labelled as a reconstruction, not a verbatim restoration. Missing older finalized per-criterion values remain `not reconstructable`; no unobserved value is claimed as a recovered observation. Original grades are untouched.\n\n## Regenerated figures and tables\n\n- Main Figure 3 (18 configurations, timeline plus five reward panels), Figure 4 (nine difficulty/cost configurations), S1 (complementary nine), A1 (ten outcomes) and A2 (same ten, task types): PDF and PNG using existing generators/designs/selections. Fixed stale Figure 3/4 output stems and S1's renderer import so the intended filenames are regenerated. No changes to Figure 1, the latest illustrative Figure 2 PNG/PowerPoint or archived figures.\n- Six affected trial/task/category/metric CSVs plus `data/headline.csv` (25 active data files). Costs and unrelated fields are preserved; legacy correctness-only `pass_rate` retains its existing meaning.\n- `current/figures/`: five-model/all-twelve task heatmaps, repeatability counts, correctness–process disagreement (each PDF/PNG). `current/tables/` contains task matrices, 0/3–3/3 counts, Pass@1/@3/Pass³, shared success, never/inconsistent tasks, workflow/membrane and paired differences, trial classifications, quadrant counts, and complete score provenance. The surviving original review remains frozen.\n- `overlap_before_after.csv`: strongest-three shared 3/3 remains 42 tasks/12 hard; five-main intersections stay unchanged. Older-five shared 3/3 falls 21→20; older-six at-least-one falls 32→31. All other task vectors/row order are preserved.\n\n## TeX updates for manual application (not applied)\n\nThe latest instruction explicitly prohibits all TeX edits. Your new representative-task caption/label, citations and section headings therefore remain intact. The following list replaces the previous task's requested direct text edits:\n"
    )
    report.append(
        table(
            ["File:line", "Action", "Required update"],
            [[f"{r['file']}:{r['line']}", r["action"], r["manual_update"]] for r in updates],
        )
    )
    report.append(
        "\nIn particular, the SI still points to the two missing `figures/codex_regrade_human/` PDFs and describes seven configurations; the regenerated A1/A2 assets retain their existing ten-configuration selection. No compatibility aliases were added that would silently change the meaning of those captions. This remains a manual TeX task.\n\n## Task 32 and remaining evidence limits\n\nTask 32 `32_fep_openfe_rbfe_dhodh__Y9ZuSSz` retains C=0/P=1 and completed status with no Harbor exception. All five scored correctness criteria fail because the required final ligand SDF, mapped network, transformations and summary were absent; only the 58,830-byte uncharged intermediate survived. Ligand preparation completed in 11.508 s. The later command `time python scripts/plan_rbfe_network.py 2>&1 | grep -v -i warn | tail -40` exceeded a 120-second native tool wait and continued in the background. The agent scheduled a 1,200-second wakeup but ended its turn; Harbor verification began before that wakeup, with the required outputs absent. This supports incomplete delivery, not the draft's slow-alignment/Harbor-timeout account. The unique lifecycle cause remains unresolved. Saved evidence is copied read-only in `validation/task32_evidence.md` and runtime timestamps in `validation/task32_runtime.json`. No grades changed.\n\nOther pre-existing text needing separate review remains untouched: Task 11/Gemini outcome wording; Task 25/29 correctness/process and force-causality descriptions; the universal highest-timeout claim; the universal Opus-5 judge claim; the unverified v1.0 archive claim; and abstract/conclusion/bibliography placeholders. Task 35 and the separate ion-order investigation were not expanded.\n\n## Validation/reproduction\n\nNine panels were rendered for visual inspection. Static TeX environment checks pass; existing unresolved assets are recorded rather than changed. No TeX compiler is installed, so no manuscript/SI compilation or pagination claim is made. All TeX bytes, original run/grade records, canonical tasks, historical v0.1 exports, costs and unrelated task scores are preserved. The overlay replays without changing active CSV bytes.\n"
    )
    report.append("\n```json\n" + json.dumps(result, indent=2) + "\n```\n")
    report.append(
        "\n```bash\nPYTHONDONTWRITEBYTECODE=1 ../MDArena-dev/.venv/bin/python data/apply_task39_policy_b.py\nPYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/task39_policy_b_2026-11-20/regenerate.py\nPYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/task39_policy_b_2026-11-20/verify_and_report.py\n```\n\nNo agents, LLM judges, simulations or canonical-task edits are invoked. No TeX is written. Committing/pushing are left to the user. `file_changes.csv` lists every new/modified deliverable, including pre-update CSV snapshots.\n"
    )
    (HERE / "change_report.md").write_text("\n".join(report))

    changed_paths = subprocess.check_output(
        ["git", "diff", "--name-only", decision["baseline_commit"]], cwd=REPO, text=True
    ).splitlines()
    allowed = {"CONTEXT.md", "data/headline.csv"}
    for model in expected:
        allowed.update(
            f"data/{folder}/{model}.csv" for folder in ["trials", "task_summary", "category_summary", "metrics"]
        )
    for name in ["figure_3", "figure_4", "figure_S1", "figure_A1", "figure_A2"]:
        allowed.update(f"figures/{name}/{name}.{suffix}" for suffix in ["pdf", "png"])
    allowed.update(f"figures/{name}/make_{name}.py" for name in ["figure_3", "figure_4", "figure_S1"])
    assert set(changed_paths) <= allowed, set(changed_paths) - allowed
    inventory = []
    for path in changed_paths:
        original = subprocess.check_output(["git", "show", f"{decision['baseline_commit']}:{path}"], cwd=REPO)
        inventory.append(
            {
                "path": path,
                "status": "modified",
                "before_sha256": hashlib.sha256(original).hexdigest(),
                "after_sha256": sha256(REPO / path),
            }
        )
    for path in sorted(
        {
            *HERE.rglob("*"),
            *RECORD.rglob("*"),
            *(REPO / "analysis/section3_followup_2026-11-20").rglob("*"),
            DATA / "apply_task39_policy_b.py",
        }
    ):
        if path.is_file() and path.name != "file_changes.csv" and "__pycache__" not in path.parts:
            inventory.append(
                {
                    "path": str(path.relative_to(REPO)),
                    "status": "created",
                    "before_sha256": "",
                    "after_sha256": sha256(path),
                }
            )
    inventory.append(
        {
            "path": str((HERE / "file_changes.csv").relative_to(REPO)),
            "status": "created",
            "before_sha256": "",
            "after_sha256": "self",
        }
    )
    write_csv(HERE / "file_changes.csv", inventory)
    print(
        "Verified redo: 16 approved changes, 2,100 trials, zero TeX changes, protected original/canonical records. Wrote change_report.md and manual_tex_updates.csv."
    )


if __name__ == "__main__":
    main()
