"""Assemble the independent-review report from saved analysis outputs and evidence."""

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from analyze_results import BENCHMARK_VERSIONS, HERE, MODELS, REPO, TABLES, TYPES


def table(frame):
    return frame.fillna("").to_markdown(index=False, floatfmt=".4f") + "\n"


def quote(text):
    return "\n".join("> " + line for line in str(text).splitlines()) + "\n"


def shortened(text, limit=1400):
    return text if len(text) <= limit else text[:limit] + " […]"


def main():
    def read(name):
        return pd.read_csv(TABLES / f"{name}.csv")

    manifest = json.loads((HERE / "input_manifest.json").read_text())
    context = json.loads((HERE / "evidence/benchmark_and_grading_context.json").read_text())
    cases = json.loads((HERE / "evidence/case_evidence.json").read_text())
    checks = json.loads((HERE / "deterministic_checks/artifact_results.json").read_text())
    summary = read("repeatability_summary")
    matrix = read("task_success_matrix")
    overlap = read("shared_success")
    all_tasks = read("strongest_three_all_tasks")
    workflow = read("workflow_comparison")
    counts = read("correctness_process_counts")
    sections = []

    def add(text):
        sections.append(text.strip() + "\n")

    def add_table(frame):
        sections.append(table(frame))

    protected = json.loads((HERE / "preservation_manifest.json").read_text())
    changed = [
        name for name, digest in protected.items() if hashlib.sha256((REPO / name).read_bytes()).hexdigest() != digest
    ]
    score_sources = read("score_provenance")

    def source_unchanged(row):
        path = Path(row.source_trial_dir) / "result.json"
        return hashlib.sha256(path.read_bytes()).hexdigest() == row.raw_result_sha256

    with ThreadPoolExecutor(max_workers=8) as pool:
        unchanged = list(pool.map(source_unchanged, score_sources.itertuples()))
    geometry_changed = [
        path
        for path, digest in checks["source_sha256"].items()
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest
    ]
    assert not changed and all(unchanged) and not geometry_changed
    preservation = {
        "tracked_manuscript_files_checked": len(protected),
        "changed_tracked_files": changed,
        "original_result_records_checked": len(unchanged),
        "all_original_results_unchanged": all(unchanged),
        "coordinate_sources_checked": len(checks["source_sha256"]),
        "changed_coordinate_sources": geometry_changed,
        "scope": "Pre-analysis tracked manuscript hashes; original result hashes recorded during provenance audit; coordinate hashes from deterministic checks.",
    }
    (HERE / "preservation_check.json").write_text(json.dumps(preservation, indent=2) + "\n")

    add(f"""# MDArena Section 3 evidence review

Prepared 20 November 2026 for revision decisions. Manuscript baseline: `{manifest["manuscript_commit"]}`. All numerical results use that checkout's finalized manuscript CSVs. The manuscript, canonical task files, original records, and existing figures were preserved. This review contains no new agent evaluation or LLM grading.

## Confirmed findings

1. The selected dataset contains **18 configurations and 2100 trials**: twelve configurations × 50 tasks × three attempts (1800 trials), plus six historical configurations × 50 tasks × one attempt (300 trials). All twelve repeated configurations reproduce the saved Strict-Pass@1, Pass@3, and Pass³ metrics.
2. Claude Opus-5.5, GPT-6.1 Sol, and GPT-6 Astra share **42 tasks scored as strict passes in all three attempts, including 12 hard tasks**. This becomes 30 tasks including 10 hard tasks when Gemini 4 Argon is added, 23 including three hard tasks when GLM-5.2 alone is added, and 18 including three hard tasks when both are added. These are shared outcomes under the finalized scoring, not proof of future reliability or independent physical validation of every artifact.
3. The predefined membrane-preparation subset reproduces **Gemini 12/15, Opus 11/15, and Sol/Astra 5/15 each**. The difference spans several systems. Gemini passes all attempts on Tasks 23, 25, 26, and 27, but none on 29; the OpenAI models' five passes come mainly from D3 preparation (Task 26). GLM has 0/15 on this subset despite 63.3% overall strict success.
4. The two displaced-ligand Opus Task 25 structures are real, with independently reproduced periodic all-atom ligand–protein minima of **30.188 Å in replicate 1 and 37.813 Å in replicate 3**. Replicate 2 retains close contact and passes. The draft incorrectly attributes both displacement failures to correctness checks: replicate 3 has full correctness and fails the binding-pose **process** criterion.
5. The Opus Task 29 replicate 2 carbon contact is **1.368612 Å**, between ligand AMP C6 and lipid POPE C316. That trial has **full correctness (1.0000)** and process 0.9375. Its minimization log reports an infinite force on a different lipid atom. A new coordinate check finds a separate **0.054772 Å lipid–lipid contact involving that reported atom**. Severe assembly clashes are established; the quoted ligand–lipid pair is not established as the unique cause of the infinite force or of a correctness penalty.
6. Sol and Astra do deliver zero-box Task 11 structures after validating separate temporary boxed structures. Opus delivers positive boxes in all three passing attempts. **Gemini passes one attempt and times out without the required final GRO in two**; the draft's claim that Gemini fails all three because of absent box vectors is incorrect.
7. Task 39 is especially sensitive to grading history. The strongest three explicitly disclose a charged endpoint and do not implement a co-alchemical ion or calculate a charge correction; their final counterion penalties are retained. **GLM's passing attempt also explicitly says no co-alchemical ion was added.** The older v0.2 review accepted its setup after removing that unstated requirement from scoring, whereas the newer review retained the penalty. GLM's pass is therefore not evidence of a superior charge-treatment implementation, and cross-cohort scores are not fully harmonized on this example.
8. Gemini's failed Task 17 repeats do contain the correct top-ten interaction set in stdout before the 900-second timeout. A new text-only check reproduces agreement with the saved reference to within **0.004615 percentage points**, allowing tied-row reordering and chain-suffix normalization. Neither required output is delivered. Subsequent events mainly investigate residue numbering and parser/converter internals.
9. The preliminary disagreement counts are correct: **14 Sol** and **15 Astra** completed trials have full process but incomplete correctness; **two Opus** trials have full correctness but incomplete process. These are distinct from execution errors. Full credit in one dimension is evidence about that checklist, not an exhaustive scientific endorsement.

## Analysis inputs and methods

### Final score authority and trial selection

`data/trials/<configuration>.csv` defines the selected trials and final numerical scores. `data/task_summary` supplies the existing task identity, description, task type, and difficulty. `data/headline.csv` and `data/metrics` are independent aggregate checks. `data/trial_sources.csv` resolves the selected names and attempt indices to analysis copies, current original directories, and selection records. Every analysis/source result ID was matched for all 2100 rows. The complete UUID and source mapping is embedded in `tables/score_provenance.csv`, with the audited case UUIDs also printed below.

The six historical configurations use their task-specific `analysis/task_job_map.csv` selections under `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena_evals`. They retain the frozen v0.1.0 task metadata, including the original Task 15 and 11/23/16 easy/medium/hard distribution. They are kept separate from all repeatability and shared-success analyses.

The seven v0.2 configurations use the frozen `MDArena_v2_runs/reduced_outputs/runs.toml` selection. Raw records are retained in that compact archive and in the local `MDArena_eval/v0.2` tree, except GPT-5.6's raw runs under `MDArena_v2_runs/jobs`. Their final score authority is **`MDArena_v2_runs/analysis/analysis_v0.2c_codex_regraded_human_verified/<model>/tables/trials.csv`**. All 1050 final correctness/process score pairs match these human-verified tables exactly. The archive's comparison report records:

> Human-verified Codex regrade of MDArena v0.2b from …/yol_sol_checking_tasks_human checked/task_review_nd_suggestions into …/analysis_v0.2c_codex_regraded_human_verified

The original raw-to-final changes are substantial: 512 of these 1050 score pairs differ. They were not silently replaced with raw results. The accessible `yolo_sol_checking_tasks/task_review_nd_suggestions` notes explain the broad regrading; `yol_sol_checking_tasks_human checked/task_review_nd_suggestions` supplies the later human changes to seven tasks. The intermediate v0.2a directory is not readable under current filesystem permissions, but the final v0.2c tables, v0.2b tables, comparison provenance, and task-specific review notes are readable. A complete machine-readable per-trial final criterion JSON was not located for this older human-verified export; original criterion observations must therefore be distinguished from the final rescore.

GPT-6.1 Sol, GPT-6 Astra, and Opus-5.5 use the frozen `MDArena_run_analysis_DD/input-audit.json` selection and its `inputs` tree. It records 450 qualifying completed trials and 249 excluded earlier attempts. This is a qualifying-run selection, not an all-attempt estimate of infrastructure reliability. Final scores incorporate the recorded 78-case review, 39 cases with changed criteria, and user decisions in `MDArena_run_analysis_DD_regraded/regraded-scores.json`, `user-verdict-application.json`, and per-case `user-verdict.json`. Gemini 4 Argon and DeepSeek V4.1 use their finalized v4 selections and their later per-case regrade records in the same review root. No exporter was rerun against manuscript files.

`tables/score_provenance.csv` traces all final score pairs against those authorities. No score-pair mismatch remains unresolved after identifying v0.2c. Changes relative to the raw source records are summarized below; zeroing an execution-error score and recovering a previously missing grade can also change a pair, so these counts are not counts of successful-task promotions.
""")
    history = read("grading_history_summary")
    add_table(history[["model", "raw_to_final_score_pairs_changed"]])
    add(
        "### Complete configuration and cohort inventory\n\nThe six one-attempt configurations are historical context only; they do not enter any repeated-task overlap or repeatability result."
    )
    inventory = pd.read_csv(REPO / "data/headline.csv")
    inventory["benchmark_cohort"] = inventory.model.map(BENCHMARK_VERSIONS)
    inventory["analysis_role"] = inventory.model.map(
        lambda name: "Repeated" if name in MODELS else "Historical single attempt"
    )
    inventory["strict_passes"] = (inventory.strict_pass_at_1 * inventory.n_trials).round().astype(int)
    add_table(
        inventory[
            ["model", "benchmark_cohort", "analysis_role", "n_tasks", "n_trials", "strict_passes", "strict_pass_at_1"]
        ]
    )
    add(f"""### Benchmark versions and grading comparability

The manuscript calls six historical configurations v0.1, seven repeated configurations v0.2, and five newer repeated configurations v1.0. These cohort labels are preserved in every table. They are not inferred from the v2/v3/v4 folder names.

The local benchmark checkout is `{context["local_benchmark_commit"]}`; the other benchmark checkout is `{context["other_benchmark_commit"]}`. The frozen DD input and adjudication manifests identify benchmark commit `{context["frozen_DD_input_audit"]["repository_commit"]}`. The local checkout's package version remains 0.2.0 and its dataset-version document describes an unreleased v0.3.0, while the manuscript claims a v1.0.0 archive. A release/tag mapping for that manuscript claim was not established here. The report therefore labels v1.0 as the **manuscript cohort**, not a verified archival release.

The benchmark version document records changes to task content, judge access to trajectories, weighting, and process rubrics. Task 39 provides a concrete unresolved difference in final scoring policy between cohorts, discussed below. Task 35's shared success also needs care: the user verdict explicitly says **“My verdict regrade to pass: Mark all of them as correct”**, after a review found native charged-ligand OpenFE protocol validation blocked in some original runs. The awarded final passes are retained; they are not new evidence that those original protocols validated successfully. This qualification applies when describing the shared 42 as scientific workflow successes.

The draft's statement that Claude Opus-5 judged every repeated run also requires correction or a complete judge-provenance qualification. The saved Gemini remaining-batch YAML explicitly specifies `REWARDKIT_JUDGE: codex` and `REWARDKIT_MODEL: gpt-6.1-sol`; its runtime is described as “Gemini batch with a Codex-authenticated judge.” A DeepSeek `codex-judge` wrapper is also saved. This audit did not assign a judge model to every individual historical process judgment. Configuration evidence is preserved in `evidence/benchmark_and_grading_context.json`.

### Metric definitions and uncertainty

Strict success requires `status == completed`, correctness ≥0.999, and process ≥0.999, matching the manuscript's analysis functions and their full-score tolerance. Missing scores and execution errors do not pass. No legacy correctness-only `pass_rate` is used. For three attempts per task, task success is 0, 1, 2, or 3; Strict-Pass@1 is total strict passes/150; Pass@3 is tasks with at least one strict pass/50; Pass³ is tasks with all three strict passes/50.

The review imports `strict_pass_by_task`, `PASS_THRESHOLD`, and `mean_and_ci` from the existing performance/cost generator, now `figures/figure_4/make_figure_4.py`. All global strict rates match `headline.csv`; all twelve repeated configurations also match the saved `strict pass@1`, `pass@3`, and `pass^3` metrics. The error category remains separate from the four completed-trial correctness/process categories.

Exploratory workflow intervals use 2000 percentile bootstrap resamples of **tasks**, seed 0. Paired contrasts resample task-level differences within the same predefined workflow. Three attempts are not treated as three independent tasks. The one-task quantum-chemistry category receives no bootstrap interval. These exploratory contrasts are not adjusted for multiple comparisons and do not establish a general ranking beyond the sampled workflows.

New deterministic checks are isolated in `deterministic_checks/artifact_results.json`: fixed-width PDB/GRO parsing (including extended GRO precision), explicit Å↔nm conversion, and three-dimensional orthorhombic minimum-image distances on the exact saved coordinates. Atom selections and closest atom records are retained. The Task 17 check parses saved stdout and compares it with the saved CSV reference; it does not recompute a trajectory fingerprint. No new simulation, verifier run, or LLM grading was performed. Historical deterministic checks are clearly labelled as historical when cited.

## Repeatability and shared task outcomes

### Complete repeatability summary

All counts refer to 50 tasks and 150 selected trials per configuration. The columns 0/3 through 3/3 count tasks, not trials. Pass@3 and Pass³ below are task counts out of 50.
""")
    add_table(
        summary[
            [
                "configuration",
                "benchmark_version",
                "strict_passes",
                "strict_pass_at_1",
                "pass_at_3_tasks",
                "pass_cubed_tasks",
                "tasks_0_of_3",
                "tasks_1_of_3",
                "tasks_2_of_3",
                "tasks_3_of_3",
            ]
        ]
    )
    add("""![Task-count summary](figures/repeatability_task_counts.png)

The strongest three have localized recurring failures. Opus never passes Task 39; its inconsistent tasks are 25 (1/3), 29 (1/3), and 32 (2/3). Sol has four never-passing tasks (11, 23, 27, 39) and three inconsistent tasks (18, 25, 29, each 1/3). Astra also has four never-passing tasks (11, 23, 25, 39), with 18, 27, and 29 each 1/3. Thus the identical 88% overall OpenAI rates conceal different outcomes on Tasks 25 and 27. Repeated zeroes identify recurring failures under this selection and setup; they do not establish intrinsic unsolvability. Repeated success is likewise not proof of future reliability.

### Shared successes across model groups

The “all three attempts” row requires every included configuration to pass all three attempts at a task. “At least one attempt” requires each included configuration to pass at least once; it does not require a shared matched replicate.
""")
    add_table(overlap[["models", "condition", "n_tasks", "n_hard"]])
    add("""### The shared 42 tasks

Every task in this table is 3/3 for **each** of Opus-5.5, Sol, and Astra. The two right-hand columns show why that finding does not automatically extend to Gemini or GLM. Descriptions and difficulty are the existing task metadata, shortened only for display.
""")
    shared = all_tasks[all_tasks.shared_top_three]
    add_table(shared[["task_id", "short_description", "category", "difficulty", "gemini-4-argon", "glm-5.2"]])
    add("""### The remaining eight tasks

Each outcome is the number of strict passes out of three. These eight contain both hard membrane tasks and easier conversion/parameter-editing tasks; the failures are not confined to the hard tier.
""")
    add_table(
        all_tasks[~all_tasks.shared_top_three][
            ["task_id", "short_description", "category", "difficulty"] + list(MODELS)[:5]
        ]
    )
    add("""### Main-text candidate and full heatmaps

The cells encode 0/3, 1/3, 2/3, and 3/3 as four discrete colours, with the number printed in every cell. Rows are grouped by the seven existing task types, then ascending task number; the five-configuration and twelve-configuration versions use exactly the same row order. E/M/H annotate the existing difficulty. The labels below are display abbreviations, not new scientific classifications. No molecular illustrations are included.

![Five-configuration heatmap](figures/task_heatmap_five.png)

![All repeated configurations](figures/task_heatmap_all_twelve.png)

The underlying `tables/task_success_matrix.csv` includes canonical task IDs, full scientific descriptions, difficulty, display order, and all twelve counts. The complete matrix is reproduced in two readable column blocks below.
""")
    add_table(matrix[["task_id", "short_description", "category", "difficulty"] + list(MODELS)[:5]])
    add_table(matrix[["task_id"] + list(MODELS)[5:]])
    add("""### Every task that never passes or passes inconsistently

The following model-specific lists use the finalized counts. “Never” means 0/3 in this selection; “inconsistent” means 1/3 or 2/3. The full scientific descriptions are in the metadata/matrix tables, and each task has a readable description here.
""")
    for model in MODELS:
        add(f"#### {MODELS[model]}")
        subset = matrix[matrix[model] < 3][["task_id", "short_description", "difficulty", model]].rename(
            columns={model: "strict_passes_of_3"}
        )
        add_table(subset)
    add("""## Scientific workflow differences

### All seven existing task types

The table reports strict trial passes/selected trials; category task denominators are in the column headings. The separate membrane subset is the predefined set **23, 25, 26, 27, 29**, all hard system-preparation tasks. It is not an additional eighth task type. Full rate intervals, task denominators, and counts of tasks with any/all passes are in `tables/workflow_comparison.csv`.
""")
    wide = (
        workflow.assign(cell=workflow.strict_passes.astype(str) + "/" + workflow.n_trials.astype(str))
        .pivot(index="model", columns="task_type", values="cell")
        .reindex(MODELS)
    )
    names = {
        name: f"{label} ({int(workflow[workflow.task_type == name].iloc[0].n_tasks)} tasks)"
        for name, label in TYPES.items()
    }
    names["membrane_preparation_subset"] = "Membrane subset (5 tasks)"
    add_table(wide[list(TYPES) + ["membrane_preparation_subset"]].rename(columns=names).reset_index())
    add("""### Membrane preparation and the individual systems

The preliminary 12/15, 11/15, and 5/15 counts all reproduce. They refer to five tasks, not fifteen independent systems.
""")
    add_table(read("membrane_task_success")[["task_id", "short_description"] + list(MODELS)[:5]])
    add("""Gemini's advantage over Sol spans Task 23 (+3 passes), 25 (+2), and 27 (+3), offset by Task 29 (−1); Task 26 is tied at 3/3. Opus's six-pass advantage over Sol comes entirely from Tasks 23 and 27 (+3 each); Tasks 25, 26, and 29 are tied. Astra exchanges Sol's single success on 25 for a single success on 27, giving the same 5/15 total through a different task profile. GLM fails all fifteen selected membrane attempts, so its shortfall is not driven by just one task.

Gemini's one-pass advantage over Opus is especially fragile: it gains two passes on mGlu5 (25) and loses one on PepT2 (29), while the other three tasks tie. The paired task-bootstrap difference is +6.7 percentage points, with a 95% interval of **−20.0 to +40.0**. Gemini−Sol is +46.7 points (0.0 to +93.3); Opus−Sol is +40.0 points (0.0 to +80.0). These wide five-task intervals support discussing task-specific contrasts rather than declaring a generally superior membrane-preparation model.

### Which other workflow contrasts are informative

* **Analysis:** the strongest three are all 39/39 across thirteen tasks. Gemini is 37/39, with its entire two-trial deficit arising on Task 17. GLM is 33/39, with differences on three tasks (5, 19, 45). The Gemini finding is a delivery bottleneck on one task, not a broad failure of trajectory-analysis competence.
* **System preparation:** Opus reaches 32/36; Sol, Astra, and Gemini each have 23/36 despite very different component tasks. Removing only the scientifically defined membrane subset leaves Opus 21/21, Sol/Astra 18/21, Gemini 11/21, and GLM 15/21 on seven other preparation tasks. Equal category totals therefore conceal a real workflow trade-off, and Gemini's membrane advantage does not generalize to all system preparation.
* **Free energy:** Sol/Astra are 21/24, Opus 20/24, and Gemini/GLM 15/24 across eight tasks. The OpenAI advantage over Opus is exactly **one failed Opus attempt on DHODH Task 32**, not a category-wide advantage. GLM passes OX2R RBFE Task 34 in all three attempts while Gemini passes none; conversely Gemini passes mGlu5 and A2A ABFE Tasks 36 and 37 in all three attempts, while GLM passes neither. Those differences span multiple predefined workflows, but Task 39's distinct historical rescoring policy must be separated from model-capability interpretation.
* **Enhanced sampling:** the strongest three are 21/21 across seven tasks. Gemini is 14/21, with 0/3 on 30 and 42 and 2/3 on 43. GLM is 10/21, with differences on 28, 30, 41, 42, and 43. These are several-task patterns, stronger evidence than a one-task reversal, while successful bounded setup is still not evidence about long production sampling.
* **Parameterization:** Opus is 15/15, Sol/Astra 13/15, Gemini 12/15. Those differences are entirely Task 18 ion-charge scaling. They should be discussed as a specific parameter-preservation problem, not a general parameterization ranking. GLM's 9/15 deficit spans 18, 24, 46, and 47.
* **Diagnostics:** the strongest three and GLM all achieve 12/12 across four tasks despite their large overall ranking difference. Gemini's 11/12 comes from one failure on Task 15. This supports bounded competence on these four diagnostic tasks; it does not establish general diagnostic reliability.
* **Quantum chemistry:** this category has one task and three attempts. The strongest three and Gemini are 3/3; GLM is 1/3. This is too sparse for a broad claim about quantum-chemistry workflows or a task-bootstrap confidence interval.

All predefined paired contrasts and their contributing task counts are reproduced below; no post-hoc subsets were optimized to find reversals.
""")
    add_table(read("paired_workflow_differences"))
    add("""## Scientific case audits

For each audited task, the inventory below includes all three selected attempts of the five highlighted configurations, plus all twelve configurations on Task 39. Exact trial names, UUIDs, original/final scores, criterion names/weights/explanations, artifact paths, and relevant transcript excerpts appear in the detailed appendix. Original criterion failures are not called final failures when a later score authority superseded them.

### Task 25 displaced ligand during final assembly

The discrepancy is resolved by distinguishing the two score dimensions and by identifying the correct replicate. All three Opus structures were checked, including the successful one.
""")
    geom = [r for r in checks["coordinate_geometry"] if r["task"] == 25]
    add_table(
        pd.DataFrame(
            [
                {
                    "replicate": r["replicate"],
                    "trial_suffix": r["trial_name"].split("__")[-1],
                    "periodic_all_atom_min_A": r["all_periodic"]["distance_A"],
                    "periodic_heavy_atom_min_A": r["heavy_periodic"]["distance_A"],
                    "direct_all_atom_min_A": r["all_direct"]["distance_A"],
                }
                for r in geom
            ]
        )
    )
    add_table(
        pd.DataFrame(
            [
                {
                    "replicate": c["replicate"],
                    "trial_name": c["trial_name"],
                    "original_C": c["original_scores"]["correctness"],
                    "original_P": c["original_scores"]["process"],
                    "final_C": c["final_correctness"],
                    "final_P": c["final_process"],
                    "strict_pass": c["strict_pass"],
                }
                for c in cases
                if c["number"] == 25 and c["model"] == "opus-5.5"
            ]
        )
    )
    add("""**Observed geometry and provenance.** The 30.2 Å value belongs to `8YSEgrj`, replicate 1; 37.8 Å belongs to `5qy4iHm`, replicate 3. The primary structures are each source trial's `artifacts/app/outputs/system.gro`; full absolute paths and SHA256s are printed in the appendix and deterministic-check JSON. GRO coordinates are nm; reported values multiply by ten. Protein atoms are selected by amino-acid residue identity; ligand atoms are the `LIG` residue. The minima are recomputed over every selected ligand/protein pair with minimum-image wrapping in all three box dimensions. The corresponding heavy-atom separations remain 31.797 and 38.634 Å. Thus neither a missing periodic image, a choice to include hydrogens, nor a factor-of-ten unit error explains the displacement.

In replicate 1, the saved `outputs/work/complex_oriented.pdb` has a direct ligand–protein minimum of 1.80816 Å. The assembly code reads ligand coordinates from `outputs/work/test/lig_final.pdb` and converts Å to nm, while protein coordinates come from the separately translated tleap/ParmEd system. The saved native event contains the pre-assembly check `min lig-prot 1.8081603911157875`. The later `assemble.py` line is `x,y,z=[float(l[30+8*k:38+8*k])/10 for k in range(3)]`. The defect is a coordinate-frame mismatch at final merge, not the Å-to-nm conversion itself. The final report nevertheless claims “The ligand was kept exactly at its crystal pose (heavy-atom coordinates unchanged; hydrogens added).”

In replicate 3, `outputs/complex_oriented.pdb` likewise retains close ligand contact (fresh all-atom minimum 1.75787 Å). The saved `merge.py` logic resets ligand coordinates using `lig.coordinates=np.array([pk[a.name] for a in lig.atoms])` from uncentred `lig_from_pack.pdb`. Protein and ligand then receive different net translations. Comparing matching protein CAs and ligand atom names between the saved intermediate and final GRO gives a protein-minus-ligand translation of **(4.269004, 4.269105, 5.014554) nm**, within coordinate rounding of half the **(8.538, 8.538, 10.029) nm** box. A relative half-box shift is not the whole-box periodic equivalence that would preserve the complex. The final periodic separation confirms loss of the binding pose.

Replicate 2 is the control against an unrepresentative example: `miVipsZ` has a final periodic all-atom minimum 1.93579 Å and heavy-atom minimum 2.97392 Å, and full exported correctness/process. Its saved `complex_prepared.pdb` also contains close ligand contact. This establishes that the problematic final merge did not occur in all three attempts.

**What the scores detected.** Replicate 1 has two weight-1 correctness zeroes: `mglu5_receptor_matches_native_sequence` and `protein_centered_in_membrane`, producing 9/11 = 0.8182. The original audit traced the centering zero to the sequence gate (an extra Ser568 expression tag), rather than demonstrating a displaced receptor: its historical periodic centering estimate is only 0.434 Å. The user retained both original scoring values. The ligand-pose problem is separately caught by weight-1 process criterion `did_the_agent_retain_the_51d_ligand_in_t`, one of eight process checks, giving 7/8 = 0.875.

Replicate 3 passes all eleven scored correctness checks and fails that same one of eight process checks. The correctness checklist establishes selected receptor, composition, compilation, charge, and packing properties but has no effective final binding-pose test. Its full correctness therefore does not contradict the observed displaced ligand. The final user verdict for Task 25 says “Genuine failure no regrade required”; neither trial was promoted in this review.

**Supported interpretation and manuscript accuracy.** Two attempts support successful intermediate preparation followed by an invalid final artifact and high partial credit despite a consequential defect. The current numerical distances are accurate, but “failing the correctness checks for binding pocket geometry” is not: the process check detects pose loss; replicate 1's correctness failures are different, and replicate 3 retains full correctness. The task calls the source crystallographic 7TM ligand site “orthosteric”; the historical audit notes that the source site's allosteric/orthosteric terminology is inaccurate. Retention of the supplied pose is the evidence-supported issue, without adopting that terminology claim.

### Task 29 final structural clashes

The claimed 1.37 Å ligand–lipid carbon distance occurs in Opus **replicate 2**, `29_pept2_beta_lactam_membrane_se__Z4DQoGB`, whose final scores remain **correctness 1.0000, process 0.9375, strict fail**. The claim does not describe the other failed replicate, whose defect is membrane underpacking.
""")
    geom29 = [r for r in checks["coordinate_geometry"] if r["task"] == 29]
    add_table(
        pd.DataFrame(
            [
                {
                    "replicate": r["replicate"],
                    "trial_suffix": r["trial_name"].split("__")[-1],
                    "ligand_lipid_all_atom_min_A": r["all_periodic"]["distance_A"],
                    "ligand_lipid_heavy_atom_min_A": r["heavy_periodic"]["distance_A"],
                }
                for r in geom29
            ]
        )
    )
    add("""**Atom identities and nonbonded relationship.** The final `outputs/system.gro` has ligand residue **702 AMP**, atom **C6**, global atom row **7575**, at **(5.246, 7.258, 5.184) nm**. Its nearest lipid heavy atom is residue **808 POPE**, atom **C316**, global row **20845**, at **(5.301, 7.267, 5.309) nm**. Their periodic distance is **1.368612436 Å**. They belong to separate AMP and POPE molecule types in the submitted topology, not a covalent bond. No top-level intermolecular-interaction section is declared. The still shorter all-atom contact is **0.850235 Å**, AMP H12 (row 7595) to POPE H15X (row 20843). The exact GRO records and topology molecule section are saved with the new result.

**Association with minimization.** `outputs/em_test_mdrun.log` records initial LJ short-range energy **1.54165×10²⁵ kJ/mol**, termination after 15 steps without attaining the requested Fmax<1000, and:

> Energy minimization has stopped because the force on at least one atom is not finite.
> Maximum force = inf on atom 44170

Atom 44170 in the submitted coordinates is **POPG residue 994 H4X**, at **(1.211, 9.090, 3.566) nm**. A fresh nearest-neighbour check finds **POPE residue 889 C34**, row **31014**, at **(1.212, 9.085, 3.568) nm**, only **0.054772256 Å** away. This is a separate lipid–lipid near-overlap involving the reported atom. No force or energy was recomputed, so the review does not prove a unique floating-point failure mechanism. It does establish why assigning the log's infinite force specifically to the 1.37 Å ligand–lipid pair is unsupported.

**Recognised, checked, and delivered.** The saved Packmol input constrained the protein but omitted the ligand; AMP was merged afterwards from `lig_pose.npy`. A later `fix.py` global periodic neighbour scan used `query_pairs(0.1 nm)` with molecule groups including `('P',7555),('AMP',43)`. This would include ligand–lipid pairs, so the historical audit proposed credit for the literal “check or handle” criterion. However, its 1 Å threshold is too narrow to exclude all serious heavy-atom clashes, it printed lipid indices rather than fixing the final pocket, and the proposed `fixed.gro` was not delivered. The agent's final answer explicitly says:

> system.gro is therefore topologically complete and passes grompp, but its coordinates cannot be minimised as they stand and are not ready for MD.

The weight-1 process criterion `checks_lipid_clashes_near_ligand` was originally zero; the task-wide user decision retained that zero despite the audit's proposed narrow correction. That is one of sixteen process checks, explaining 0.9375. The full correctness score did not test and reject the final overlap. Thus “and therefore failing the checks” conflates a demonstrated physical problem, the log's broader failure, and the actual scoring reason.

Replicate 1 (`VNfS7Ud`) passes both dimensions; fresh minimum ligand–lipid heavy-atom separation is 3.7882 Å. Replicate 3 (`LPurh2R`) has correctness 0.9091/process 1.0000 and fails `protein_lipid_radial_voids_absent` (one of eleven correctness checks). The historical independent audit corroborates underpacking outside the protein envelope after whole-lipid deletion, despite a scratch-minimized intermediate. The final submitted structure remains unminimized. In its saved coordinates the ligand is named **AIC**, not AMP; the new check explicitly uses that actual residue name. Its nearest ligand–lipid heavy atom is 15.5597 Å away, so it is not another occurrence of replicate 2's quoted clash.

**Supported interpretation.** Replicate 2 is an unusually clear example of full correctness credit coexisting with a scientifically unusable final assembly, alongside honest disclosure of the failure. Replicate 3 instead illustrates full process credit with a final packing defect. A single molecular illustration could show one, but their different score mechanisms should not be merged.

### Task 11 temporary validation versus submitted structures

The exact artifact tested by the correctness verifier is `system.gro` with `topol.top` in the outputs directory, using:

```text
gmx grompp -f /tests/minim.mdp -c system.gro -p topol.top -o /tmp/rewardkit-topol.tpr -po /tmp/rewardkit-mdout.mdp -maxwarn 1
```

The frozen verifier MDP uses `pbc = xyz`, PME, and 1 nm cutoffs. A topology validated with a separately boxed coordinate file is therefore not evidence that this submitted-file command passes. Fresh direct reads give:
""")
    add_table(
        read("task11_delivered_boxes")[
            [
                "model",
                "replicate",
                "trial_name",
                "status",
                "atom_count",
                "box_nm",
                "usable_positive_box",
                "absent",
                "strict_pass",
            ]
        ]
    )
    add("""All six Sol/Astra outputs have 829 atoms and a zero box. The native trajectories identify the following separate validation coordinate files, while the submitted coordinate file remains `/app/outputs/system.gro`:

| Configuration | Replicate | Separate validation coordinate file |
| --- | ---: | --- |
| Sol | 1 | `/app/work/validate.gro` |
| Sol | 2 | `/app/validation/check.gro` |
| Sol | 3 | `/app/work/validation.gro` |
| Astra | 1 | `/app/validation/check.gro` |
| Astra | 2 | `/app/work/validation.gro` |
| Astra | 3 | `/app/work/validation.gro` |

For example, Astra replicate 2 writes `p[-1]='20.0 20.0 20.0'` to `/app/work/validation.gro`; Sol replicate 1 writes a 30 nm cube to `/app/work/validate.gro`. Sol replicate 2's native command tests `gmx grompp ... -c /app/validation/check.gro -p /app/outputs/topol.top`, not the delivered zero-box coordinates. Astra replicate 1 says in its final answer: “A temporary box was used only for validation. No minimization or reparameterization was performed.” Sol replicate 3 likewise explicitly discloses the source had no box.

This is not an accidental loss of original periodic data. The historical artifact check reads AMBER IFBOX=0, no BOX_DIMENSIONS flag, and exactly 3×829 coordinate numbers in the inpcrd, with no box/velocity tail. The original agent-visible instruction says “Convert the system to GROMACS format,” while the periodic preparation requirement comes from the verifier. Historical reviewers proposed box-related fairness corrections; the user explicitly retained the failures: “Box vectors required and not overlooked,” with a note that the instruction now says simulation-ready. This report preserves that grading decision and distinguishes it from a general claim that a faithful conversion of a boxless system is always scientifically invalid.

Sol's three final scores are 0.8333/1.0000; Astra's are 0.6667/1.0000, 0.8333/1.0000, and 0.8333/1.0000. All fail the weight-1 periodic `command_succeeds:gmx grompp ...` check. Astra replicate 1 additionally retains a weight-1 `nonuniform_14_scaling_preserved` zero; the audit disputed that detector, but the user retained it. The first Astra failure therefore cannot be attributed solely to the box.

Opus passes all three with delivered positive boxes: **(5.24298,5.00705,4.98624) nm** in repeats 1 and 2, and **(6.24298,6.00705,5.98624) nm** in repeat 3. Its reports disclose the added box. Gemini's repeat 2 (`Mmg8ESr`) passes, delivering a positive **(64.85953,60.14098,59.72475) nm** box. Repeats 1 and 3 are timeouts and lack the required output GRO. They are not delivered zero-box structures. GLM's first two attempts also pass with positive boxes, and its third attempt has no final GRO.

**Supported interpretation and accuracy.** Sol/Astra support a mismatch between validation target and submitted artifact under the actual periodic verifier. The current statement that Gemini also fails all three for that reason must be corrected. Full process credit in these conversion trials reflects their scientific reasoning and disclosure checklist, while the retained correctness penalty concerns a specific submitted-file requirement.

### Task 39 recognition and charge treatment

The task asks for a **single D3 ligand 11a complex leg**, supplied inputs, Boresch restraints, 12/11/21 lambda schedules, 44 five-stage windows, and compiled minimization TPRs. It does not ask for a computed binding free energy or production dynamics. The retained agent-visible prompts do **not explicitly require a co-alchemical counterion or a particular finite-size correction**. The original correctness and process criteria do require the specific counterion representation. Recognising a net-charge change is therefore different from satisfying the scored counterion implementation, and either is different from establishing a complete physically justified future ABFE protocol.

The finalized outcomes across all twelve repeated configurations are:
""")
    task39 = read("case_trial_inventory")
    task39 = task39[task39.task_id.str.startswith("39")]
    add_table(
        task39[["model", "replicate", "trial_name", "final_correctness", "final_process", "strict_pass", "status"]]
    )
    add("""**Strongest three, all nine repeats.** Every Sol/Astra/Opus attempt explicitly discloses the +1 ligand becoming a net −1 e endpoint after decoupling, compiles the requested setup, and leaves a charge correction/co-ion for later or states that none was applied. Representative exact final-answer statements are:

* Opus R1: “Ligand is +1 charged; no net-charge correction is applied.”
* Opus R3: “No charge correction or co-alchemical ion was applied.”
* Sol R2: “electrostatic/finite-size correction remains outside this setup task.”
* Astra R3: “Charge/finite-size corrections must be considered when a complete ABFE cycle is eventually analyzed; none were calculated here.”

All nine end at correctness 0.9/process 0.6. The retained weight-1 correctness failure is `alchemical_chloride_counterion_is_present_and_neutralized` (one of ten correctness checks). The two weight-1 process failures concern recognising **and implementing** the compensating counterion and updating/generating its index (two of five process checks). The truncated stored names start `did_the_agent_recognize_that_annihilatin` and `did_the_agent_update_or_generate_the_com`. Their wording is conjunctive: a zero does not imply the agent failed to notice the issue. The newer user verdict authorizes only “regrade the the boresch restraint thing as passing”; all non-Boresch charge/counterion/index values remain as originally scored. Exact original/final pairs and decisions are in the appendix.

**Gemini.** Repeat 2 (`fQzeTBN`) completes with 0.9/0.6. Its manifest explicitly states that the decoupled state is −1 and that `-maxwarn 2` was used when compiling the 44 enmin TPRs. Repeats 1 (`EZBnKRB`, 0.1/0.2 raw exported rewards) and 3 (`DZGSRd6`, 0.8/0.6) time out; their adjusted scores are zero and neither is a strict pass. R1 explicitly reasons about net-charge warnings and coupling schemes; R3 records those warnings and investigates ion order/coupling. The evidence supports concern being encountered, but not a completed charge treatment or a final deliberate deferral statement in every timed-out attempt. They should not be described as three completed examples equivalent to the strongest three.

**GLM's passing attempt.** Repeat 1 (`4YrjZUD`) says in `final_answer.txt`:

> -maxwarn 5; no co-alchemical ion added (no mdrun run).

Its manifest states:

> No co-alchemical ion was added (out of scope; no mdrun run).

The original score was 0.4/0.4. Original criteria found no co-alchemical chloride, no new ion index, and use of `couple-moltype`, alongside representation-specific Boresch/layout/lambda objections. The older v0.2 task review explicitly recommends awarding C1–C5/P3–P4 for valid alternative representations and **excluding C6/P2 because the instruction did not require the co-ion**. The final human-verified archive gives GLM 1.0/1.0, exactly as exported. Its no-output repeat 2 (`3xcJqpi`) remains 0/0; repeat 3 (`ucBvfBE`) times out and is adjusted to 0/0. The older review reverses these latter two repeat labels, so this report uses the manuscript's exported `attempt_index`, matching exact trial names rather than copying that prose ordering.

The same historical policy promotes Gemini 3.7 Flash, Opus-5, GPT-5.6 Sol/Terra, and Sonnet-5's completed setups to 3/3 on this task. This contrasts with the newer top three's retained counterion penalties. All twelve task outcomes are computed from finalized exports, but a capability claim based on that cross-cohort contrast is not supported by a uniform scoring rule.

**Interpretation and accuracy.** The strongest three support recognition without implementing the **particular scored** charge treatment. The draft should not turn that into a universal requirement that every scientifically valid charged-ligand setup must implement a co-alchemical chloride, nor claim all frontier attempts completed and uniformly deferred the same requirement. No new calculation here establishes the quantitative validity of an alternative electrostatic treatment. A clarified task specification and a documented consistent retrospective scoring policy would be needed before using Task 39 to compare cohorts causally; this report does not change either.

### Task 17 obtaining the answer without delivery

All three Gemini attempts were inspected. Repeat 1 (`c6z4Wh2`) completes with 1.0/1.0. Repeats 2 (`STe7b2G`) and 3 (`53mZX2z`) time out at the 900-second agent limit without `outputs/prolif_interactions.csv` or `final_answer.txt`. Each retains final exported correctness 0/process 0.75, adjusted to zero for both headline dimensions because of the execution error.

The relevant printed result occurs at normalized trajectory event **5** in repeat 2 and event **17** in repeat 3. The first prints twenty ranked interactions; the second prints all 31, with frame counts out of 26 and both precise and rounded percentages. Neither prints only a final top-ten deliverable, but their first ten interaction identities and occupancies are correct. The new check parses stdout, removes optional chain suffixes such as `.D` and `.HIT`, permits arbitrary order for tied occupancies, and compares the resulting top-ten set with `tests/correctness/expected_outputs/prolif_interactions.csv`. The maximum difference is 0.004615 percentage points, as expected from the reference's two-decimal rounding. This is validation against a saved reference, not an independent recomputation of interaction chemistry from the trajectory.
""")
    ranking = checks["task17_recorded_rankings"][0]
    add_table(pd.DataFrame(ranking["recorded_first_ten"]))
    add("""After obtaining the ranked values, repeat 2 records **22 further events**: inspecting ProLIF/MDAnalysis segment and residue identity, `TPRParser.parse`, `do_moltype`, `do_atoms`, `do_resinfo`, RDKit conversion attributes, packages, and the filesystem; it also reruns fingerprint calculations. Repeat 3 records **10 further events**, mainly extracting original residue numbers and inspecting parser/converter internals and DataFrame construction. Neither history contains the required successful CSV/final-summary write. Their output directories are empty in the saved artifact collection, and the verifier separately reports “Missing CSV file: /app/outputs/prolif_interactions.csv.”

The original process score in both was 0.5. The original weight-1 ranking criterion `did_the_agent_rank_interactions_by_avera` was zero because the agent printed exploratory results rather than a final top-ten report; the later case review grants only that ranking point, producing 0.75. The weight-1 delivery criterion `did_the_agent_write_prolif_interactions` remains zero. The scored correctness CSV-comparison criterion remains zero; file-existence and non-empty-summary diagnostics have zero weight and do not manufacture partial correctness. The execution error independently prevents strict success.

**Supported interpretation and accuracy.** This is a strong example of reaching the requested numerical answer without completing delivery, alongside excessive continued investigation. It does not show that investigating residue identity is inherently useless or that all Gemini attempts behave this way: the first repeat delivered successfully. The current specific two-trial claim is supported, with the qualification that correctness of the printed result was established by a reference comparison.

### Which scientific interpretations each case supports

| Interpretation | Supported evidence | Boundary |
| --- | --- | --- |
| High partial credit despite a consequential error | Task 25 R3: C=1/P=0.875 with displaced ligand; Task 29 R2: C=1/P=0.9375 with extreme clashes | Full correctness means the listed checks passed, not exhaustive physical validation |
| Intermediate validation followed by invalid final artifact | Task 25 R1/R3 retain a close intermediate ligand complex but mix coordinate frames at assembly; Task 11 validates another boxed file | Task 11 is also a specification/verifier issue for a boxless source, retained by user decision |
| Recognition without implementation | All nine strongest-three Task 39 setups disclose charge change but do not implement the scored co-ion | That co-ion was not explicit in the prompt and historical cohorts were rescored differently |
| Scientific answer without completed delivery | Gemini Task 17 R2/R3 stdout matches top-ten reference; required files absent at timeout | Reference-based numerical agreement is not an independent reanalysis of the raw MD trajectory |

## Correctness and process disagreement

The four completed-trial categories use final scores and the same full-credit threshold. Execution errors are an exclusive fifth category, even if a raw grader awarded one or both full dimensions. Every row sums to **150 selected trials**, and every error still contributes a failed strict pass.
""")
    add_table(counts)
    add("![Correctness and process outcomes](figures/correctness_process_disagreement.png)")
    add("""The requested 14/15/2 preliminary counts reproduce exactly. The two Opus full-correctness/incomplete-process cases are Task 25 replicate 3 and Task 29 replicate 2, audited above. Their original correctness checklists missed a final pose or packing defect; process grading identified a specific workflow/validation failure. The two opposite Opus disagreements are Task 29 replicate 3 and Task 32's failed repeat. For Sol/Astra, the audited Task 11 zero-box conversions and Task 25/29 packing failures show why full process credit need not certify the complete final artifact.

Process checks assess particular decisions and actions. The Task 29 global scan demonstrates an additional subtlety: a check can literally have been performed without establishing a safe final structure. The final Task 29 process zero is retained under the user's grading authority, even though an earlier reviewer proposed narrow credit for the act of checking. The report therefore distinguishes a fairness argument about one rubric item from scientific validity of the delivery.

The current partial-credit paragraph's conditional reward values do not reproduce from these finalized trials. Among completed trials, Gemini is **0.981842 correctness/0.987944 process (126 trials)**, rather than 0.9769/0.9803; GLM is **0.901834/0.921379 (137 trials)**, rather than 0.8790/0.9004. Adjusted values remain Gemini 0.824747/0.829873 and GLM 0.823675/0.841526, agreeing with headline exports. The draft's inference that lower rewards are therefore a harness artifact rather than a model issue is stronger than this conditional calculation establishes: conditioning on completion removes difficult failed deliveries and does not identify a cause.

## Comparison with the existing Section 3

| Existing statement or theme | Finding | Use in revision |
| --- | --- | --- |
| 18 configurations, 2100 trials, twelve repeated | Confirmed exactly | Retain denominators and distinguish historical cohort |
| Opus 94.7%, Sol/Astra 88%; Pass@3 49/46/46, Pass³ 46/43/43 | Confirmed against saved metrics | Discuss alongside the task-level distribution |
| Shared 12 hard tasks passed consistently | Confirmed; also 42 shared tasks overall | Supported additional finding; qualify finalized scoring and Task 35 adjudication |
| Progress on hard tasks demonstrates model improvement across batches | Hard-task numerical rates reproduce, but content/judge/scoring policies changed; Task 39 is a direct inconsistency | Avoid attributing all cross-batch differences to model capability without harmonization evidence |
| Membrane 12/15, 11/15, 5/15, 5/15 | Confirmed; several systems drive differences | Useful scientifically defined task-specific comparison; retain five-task uncertainty |
| Both displaced Opus Task 25 ligands fail correctness pose checks | Distances confirmed for repeats 1 and 3; pose loss is a process failure, and repeat 3 correctness is full | Correct which criterion/dimension detected the defect |
| Task 29 1.37 Å contact caused infinite force and failed checks | Contact confirmed in repeat 2; correctness is full; log points to another atom with a much closer lipid–lipid near-overlap | Describe observed clashes and minimization failure separately from unique-cause attribution and score mechanism |
| Gemini, Sol, Astra all fail all three Task 11 attempts for absent boxes | False for Gemini: one strict pass, two timeouts without final GRO; Sol/Astra zero boxes confirmed | Correct the Gemini outcomes and distinguish missing files from zero boxes |
| All frontier Task 39 attempts lack a treatment and defer it | Strongest-three completed setups support a narrowly worded observation; Gemini includes partial timeouts; GLM pass also lacks co-ion | State actual prompt/rubric scope and the different historical rescore policies |
| Gemini prints correct top ten then times out on two Task 17 repeats | Confirmed by text-only reference check across both repeats, with one successful repeat as contrast | Strong delivery example; say how printed correctness was established |
| Gemini has more timeouts than any other model | False over all twelve repeated configurations: DeepSeek V4.1 has 30, Gemini 24, Qwen 14, GLM 6 | Restrict a comparison to an explicitly named cohort or correct it |
| Reward conditional values imply harness rather than model failure | Quoted conditional values are stale; removing errors does not establish causality | Replace values if used and avoid the causal inference |
| Claude Opus-5 judged all repeated configurations | Saved Gemini remaining-batch config explicitly names a GPT-6.1 Sol Codex judge | Complete judge-provenance audit before making the universal statement |
| One Opus Task 32 timeout explains its failure | One selected strict failure is confirmed; selected trial has completed Harbor status | An internal-command timeout is possible; its detailed causal account was not part of these five case audits and needs targeted support |
| Family-wide behavioural conclusions | The examined attempts show specific repeated behaviours, but task, harness, model, and judge are not experimentally separated | Use bounded descriptions of observed trials, not lab-wide causal generalizations |

## Unresolved points and useful next decisions

* **No final score-pair discrepancy remains:** every finalized row is traced to raw records or the applicable saved review/export. The main unresolved scoring issue is **consistency of policy across cohorts**, especially Task 39, rather than whether the final CSV was read correctly. No score is changed here.
* **Criterion-level history for v0.2:** final numerical tables and task-specific decisions are available, but a complete per-trial final criterion JSON/exporter was not located. The appendix labels raw criterion failures as historical when later overridden. The inaccessible v0.2a intermediate prevents a complete replay of every earlier transformation from that directory alone.
* **Release identity:** connect the manuscript's v1.0 cohort and archival claim to an immutable released task tree before submission. Folder names and package-version strings alone do not establish it.
* **Judge history:** saved configs contradict a universal Opus-5 judge claim. A full per-trial judge manifest would clarify which process assessments came from which model, including later reviews. No grading needs to be repeated to document this.
* **Task 25:** the independent distances and frame mismatch are strong; no dynamics is needed to establish that a ligand tens of Å from the protein is not retaining its supplied binding pose. This review does not infer a quantitative binding free-energy consequence.
* **Task 29:** severe clashes, huge logged LJ energy, and non-finite forces are established. The new near-overlap involving the reported force atom is a stronger geometric association than the quoted ligand–lipid contact. A unique force-overflow cause is not claimed without an energy/force decomposition; none was run here.
* **Task 11:** the source is boxless and the frozen prompt did not explicitly demand a new periodic cell. The retained grade is authoritative for reported benchmark success, while interpretation should acknowledge the hidden periodic-preprocessing condition and the separate validation target.
* **Task 39:** document whether the intended scientific requirement is a specific co-ion implementation, a justified general charge-treatment plan, or a setup-only delivery. The evidence supports reviewing that specification and harmonization, without deciding a new grade in this report.
* **Task 17:** the saved printed ranking agrees with the saved reference; this review does not independently regenerate the reference from raw coordinates. That narrower claim is sufficient for the delivery example.

The heatmaps can support a concrete account of shared bounded competence and recurring task-specific weaknesses. The predefined membrane comparison is useful because it changes the interpretation of the overall ranking across several systems. The two Opus artifact failures and the Gemini delivery failures merit discussion precisely because their score dimensions expose different blind spots. The one-task quantum category, the one-task parameterization reversal, and tiny aggregate membrane margins should remain narrowly described. These are recommendations for using evidence, not a rewrite or proposed restructuring of the manuscript.

## Complete audited trial inventory

Original and final scores differ where an identified saved adjudication applies. The table prints exact UUIDs to make each case independently identifiable; replicate means the finalized export's `attempt_index`, not a possibly inconsistent label in an old report.
""")
    inventory = read("case_trial_inventory")
    add_table(
        inventory[
            [
                "model",
                "task_id",
                "replicate",
                "trial_name",
                "trial_id",
                "status",
                "final_correctness",
                "final_process",
                "strict_pass",
            ]
        ]
    )
    add("""## Detailed criterion and trajectory evidence

This appendix supplies the requested criterion names, weights, recorded explanations, original/final scores, artifact locations, and short trajectory/artifact excerpts for every audited trial. Long original explanations are shortened for readability; complete copied JSON fields remain in `evidence/case_evidence.json`. Positive-weight scoring failures are separated from zero-weight diagnostics. When no final per-criterion record exists, the failures below describe the original rubric, not newly alleged defects after human rescoring.
""")
    for case in cases:
        add(f"### {case['model']} task {case['number']:02d} replicate {case['replicate']} {case['trial_name']}")
        add(f"""UUID: `{case["trial_id"]}`. Status: `{case["status"]}`. Final correctness/process: **{case["final_correctness"]}/{case["final_process"]}**. Strict pass: **{case["strict_pass"]}**. Original recorded scores: **{case["original_scores"]}**.

Source trial: `{case["source_trial_dir"]}`.

Final numerical score authority: `{case.get("numerical_score_authority", "")}`.

Submitted-artifact root: `{case["artifact_root"]}`. Trajectory: `{case["trajectory_path"]}` ({case["trajectory_event_count"]} recorded events).
""")
        verdict = case.get("user_verdict", {})
        if verdict:
            policy = verdict.get("verdict", {})
            add(
                f"Final adjudication: {verdict.get('decision', 'recorded user decision')}. {verdict.get('outcome_note', '')}"
            )
            if policy.get("verbatim"):
                add(quote(policy["verbatim"]))
            changed = verdict.get("criterion_decisions", [])
            if changed:
                add_table(
                    pd.DataFrame(
                        [
                            {
                                k: r.get(k, "")
                                for k in [
                                    "criterion_id",
                                    "original_value",
                                    "applied_value",
                                    "weight",
                                    "action",
                                    "reason",
                                ]
                            }
                            for r in changed
                        ]
                    )
                )
        final_record = case["final_failed_criteria"]
        if not case.get("criteria_are_adjudicated") and str(case.get("numerical_score_authority", "")).endswith(
            "tables/trials.csv"
        ):
            add(
                "The final numeric score comes from the older human-verified table. The following criterion observations are **original**, may have been superseded by task-specific review, and must not be read as the final score's failed-check list."
            )
        scoring = [r for r in final_record if r["weight"] > 0]
        diagnostics = [r for r in final_record if r["weight"] <= 0]
        if scoring:
            add_table(
                pd.DataFrame(
                    [{k: r[k] for k in ["dimension", "name", "weight", "value", "description"]} for r in scoring]
                )
            )
            for criterion in scoring:
                if criterion["reasoning"]:
                    add(f"Recorded explanation for `{criterion['name']}`:")
                    add(quote(shortened(criterion["reasoning"])))
        else:
            add(
                "No positive-weight failures appear in the applicable retained criterion record. This statement is limited to that record and does not constitute an independent validation of the artifact."
            )
        if diagnostics:
            add("Zero-weight failed diagnostics: " + "; ".join(f"`{r['name']}`" for r in diagnostics) + ".")
        # Prior audits explicitly cite compact native excerpts with line locations.
        native = []
        for review in case.get("historical_assessment", {}).get("criterion_reviews", []):
            for evidence in review.get("evidence", []):
                if evidence.get("excerpt") and (
                    "transcript" in evidence.get("path", "")
                    or evidence.get("path", "").endswith((".py", ".md", ".txt"))
                ):
                    native.append(evidence)
        if native:
            add("Short preserved evidence excerpts (historical source locations):")
            seen = set()
            for evidence in native:
                value = evidence["excerpt"]
                if value in seen:
                    continue
                seen.add(value)
                add(f"`{evidence['path']}` lines {evidence.get('line_start', '?')}–{evidence.get('line_end', '?')}:")
                add(quote(shortened(value, 700)))
                if len(seen) >= 4:
                    break
        # Prefer explicit final scientific disclosure to duplicated grompp warnings.
        artifact_quotes = []
        pattern = {
            11: r"box|temporary|validation",
            17: r"occupanc|top.ten",
            25: r"pose|ligand|crystal",
            29: r"cannot be minim|not ready|clash|un.minim",
            39: r"no co.alchemical|no.*correction|finite.size|net.charge|charged.endpoint",
        }[case["number"]]
        for artifact in case["artifact_texts"]:
            for line in artifact["text"].splitlines():
                if re.search(pattern, line, re.I) and "WARNING 1 [file" not in line and len(line) < 1300:
                    artifact_quotes.append((artifact["path"], line))
        for path, line in artifact_quotes[:3]:
            add(f"Artifact `{path}`:")
            add(quote(line))
        if not native:
            selected = []
            for excerpt in case["trajectory_excerpts"]:
                if re.search(pattern, excerpt["text"], re.I) and "coulombtype" not in excerpt["text"]:
                    selected.append(excerpt)
            for excerpt in selected[-2:]:
                add(f"Trajectory event `{excerpt['event']}`:")
                add(quote(shortened(excerpt["text"], 900)))
    add("""## Reproduction and file inventory

Run from the manuscript repository with the existing analysis environment. All output paths resolve from the scripts; inputs outside this analysis directory are read-only.

```bash
MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/section3_review_2026-11-20/analyze_results.py
MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/section3_review_2026-11-20/collect_case_evidence.py
MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/section3_review_2026-11-20/check_artifacts.py
MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/section3_review_2026-11-20/audit_context.py
MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/section3_review_2026-11-20/make_report.py
```

The scripts reuse the manuscript's strict-pass and bootstrap functions. No dependency was installed for this analysis. The primary figure PDFs are standalone vector panels; PNGs are 300 dpi. `preservation_manifest.json` fingerprints the pre-analysis tracked manuscript files, and `preservation_check.json` records the end-of-review comparison. `input_manifest.json` fingerprints exact manuscript tables and relevant source exports/review notes. Geometry inputs and raw result files have additional hashes in the deterministic and provenance outputs.

Created files (Python cache files excluded):
""")
    files = sorted(str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for name in ["report.md", "created_files.csv", "preservation_check.json"]:
        if name not in files:
            files.append(name)
    add_table(pd.DataFrame({"file": sorted(files)}))
    pd.DataFrame({"file": sorted(files)}).to_csv(HERE / "created_files.csv", index=False)
    (HERE / "report.md").write_text("\n".join(sections))
    print("Wrote", HERE / "report.md")


if __name__ == "__main__":
    main()
