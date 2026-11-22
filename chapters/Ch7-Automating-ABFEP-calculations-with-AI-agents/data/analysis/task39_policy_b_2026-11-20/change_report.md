# Task 39 Policy B: redo against the updated checkout

Baseline commit: `b2f616bf8318c6cfa0d1c24804824f9bb6f8b6ad` (`Updated Figure 2`). The input scores match the surviving pre-update evidence baseline; no Policy A changes were present. Exactly 16 score pairs changed from 1/1 to 0.9/0.6. Ten newer completed setups already had these scores. All 36 selected repeated Task 39 trials now fail strict success. The nine error trials retain their raw grades and stay zero in adjusted metrics; the completed empty GLM trial stays zero. **Every TeX file is byte-identical to the updated checkout**, as explicitly requested in the latest instruction.

## Before/after aggregate metrics

Each affected configuration has 150 trials. C/P means are adjusted; CIs use the existing 2,000 task-clustered bootstrap resamples, seed 0, 95% percentile limits. Cost per strict pass uses the existing plotted mean cost divided by strict success; GLM retains the supplied-mean/token allocation assumption. Recorded costs/coverage are unchanged.

| Configuration | Passes before → after | After strict rate [95% CI] | Mean C before → after | Mean P before → after | USD per strict pass before → after |
|---|---|---|---|---|---|
| gpt-5.6-sol | 123 → 120 | 80.00% [69.33%, 89.33%] | 0.959426 → 0.957426 | 0.975152 → 0.967152 | 1.8360 → 1.8819 |
| opus-5 | 115 → 112 | 74.67% [64.00%, 84.02%] | 0.937607 → 0.935607 | 0.965455 → 0.957455 | 2.2274 → 2.2870 |
| gemini-3.7-flash | 107 → 104 | 69.33% [56.67%, 80.67%] | 0.905537 → 0.903537 | 0.916386 → 0.908386 | 1.3176 → 1.3556 |
| gpt-5.6-terra | 105 → 102 | 68.00% [56.67%, 78.67%] | 0.885365 → 0.883365 | 0.920017 → 0.912017 | 1.1187 → 1.1516 |
| sonnet-5 | 96 → 93 | 62.00% [50.67%, 74.00%] | 0.885216 → 0.883216 | 0.925115 → 0.917115 | 1.4012 → 1.4464 |
| glm-5.2 | 95 → 94 | 62.67% [50.67%, 73.33%] | 0.823675 → 0.823008 | 0.841526 → 0.838859 | 2.9634 → 2.9949 |


Repeatability changes (task counts out of 50; confidence intervals are in `repeatability_before_after.csv`):

| Configuration | Pass@3 tasks before → after | Pass³ tasks before → after |
|---|---|---|
| gpt-5.6-sol | 43 → 42 | 39 → 38 |
| opus-5 | 43 → 42 | 33 → 32 |
| gemini-3.7-flash | 37 → 36 | 34 → 33 |
| gpt-5.6-terra | 40 → 39 | 28 → 27 |
| sonnet-5 | 38 → 37 | 27 → 26 |
| glm-5.2 | 39 → 38 | 24 → 24 |


All other configurations' totals are unchanged. Full before/after correctness/process CIs, conditional means and costs are in `aggregate_before_after.csv`. Every difficulty/type metric and its task-bootstrap CI is in `breakdown_before_after.csv`.

## Exact changes and provenance

`data/adjudications/task39_policy_b/decision.json` verifies exact UUIDs, trial names, task checksums and replicate identities. The 390 scored criterion decisions for 26 completed setups are beside it. C6/P2/ion-specific P4 remain failures; non-charge decisions are carried forward without new artifact validation. The separate ion-order question is deferred. `trial_changes.csv` gives full source and prior final-grade paths.

| Configuration | R | Exact trial | UUID | C/P before → after |
|---|---|---|---|---|
| gemini-3.7-flash | 1 | 39_fep_gmx_d3_abfe__CKEGmoX | c50efe53-23c4-43e8-be4d-c9ce742544c9 | 1/1 → 0.9/0.6 |
| gemini-3.7-flash | 2 | 39_fep_gmx_d3_abfe__4HWkD87 | 1296634c-4437-4e0d-8a58-371b641b1dfe | 1/1 → 0.9/0.6 |
| gemini-3.7-flash | 3 | 39_fep_gmx_d3_abfe__BqJHXzN | 40de7db2-1829-439a-a915-040e30e68729 | 1/1 → 0.9/0.6 |
| glm-5.2 | 1 | 39_fep_gmx_d3_abfe__4YrjZUD | 943151f3-b4e8-4b74-94fc-38d24d406c4d | 1/1 → 0.9/0.6 |
| gpt-5.6-sol | 1 | 39_fep_gmx_d3_abfe__yrN5FwS | 7b09b08f-ddcc-43cc-bf68-b91fc90d96c6 | 1/1 → 0.9/0.6 |
| gpt-5.6-sol | 2 | 39_fep_gmx_d3_abfe__zfF3nS2 | fa535758-a572-403a-81d3-5ff7297e9fee | 1/1 → 0.9/0.6 |
| gpt-5.6-sol | 3 | 39_fep_gmx_d3_abfe__vWd96Zu | 5d51332c-bc2a-4233-9ad1-c2c7e5f82040 | 1/1 → 0.9/0.6 |
| gpt-5.6-terra | 1 | 39_fep_gmx_d3_abfe__uRvxxD7 | 0e8ca4ab-02eb-419b-9f24-19404399b41e | 1/1 → 0.9/0.6 |
| gpt-5.6-terra | 2 | 39_fep_gmx_d3_abfe__D3nGCqN | d7b9d65f-57dd-47e8-9540-44214d00e7c7 | 1/1 → 0.9/0.6 |
| gpt-5.6-terra | 3 | 39_fep_gmx_d3_abfe__7zptP4A | de0dde71-86e6-4da5-be49-ea5505768040 | 1/1 → 0.9/0.6 |
| opus-5 | 1 | 39_fep_gmx_d3_abfe__dXtpePB | 59d8832f-596c-4e09-87ec-ff31253fdefa | 1/1 → 0.9/0.6 |
| opus-5 | 2 | 39_fep_gmx_d3_abfe__N2e4GKf | 24d0d1aa-6ea5-4352-8536-e48fad2b88f1 | 1/1 → 0.9/0.6 |
| opus-5 | 3 | 39_fep_gmx_d3_abfe__aqbZ7Ng | c52d0fe0-342b-4d62-ab30-4f409e6f0f11 | 1/1 → 0.9/0.6 |
| sonnet-5 | 1 | 39_fep_gmx_d3_abfe__BsQAhC2 | ff50b8e4-97a1-40fb-b0a0-01b28201bb74 | 1/1 → 0.9/0.6 |
| sonnet-5 | 2 | 39_fep_gmx_d3_abfe__ni6AoQs | 869987d7-8525-4f74-bd8d-6690f8422cf0 | 1/1 → 0.9/0.6 |
| sonnet-5 | 3 | 39_fep_gmx_d3_abfe__oJsf7kJ | 2b1cf47b-2028-49a9-9459-79d4a995d9cf | 1/1 → 0.9/0.6 |


The reset removed the untracked focused follow-up. Its required Task 39 basis was reconstructed transparently from `analysis/section3_review_2026-11-20/tables/score_provenance.csv`, the first review's exact case UUIDs, and saved original/final criterion records. The reconstructed report/1,404-row worksheet are in `analysis/section3_followup_2026-11-20/`; they are labelled as a reconstruction, not a verbatim restoration. Missing older finalized per-criterion values remain `not reconstructable`; no unobserved value is claimed as a recovered observation. Original grades are untouched.

## Regenerated figures and tables

- Main Figure 3 (18 configurations, timeline plus five reward panels), Figure 4 (nine difficulty/cost configurations), S1 (complementary nine), A1 (ten outcomes) and A2 (same ten, task types): PDF and PNG using existing generators/designs/selections. Fixed stale Figure 3/4 output stems and S1's renderer import so the intended filenames are regenerated. No changes to Figure 1, the latest illustrative Figure 2 PNG/PowerPoint or archived figures.
- Six affected trial/task/category/metric CSVs plus `data/headline.csv` (25 active data files). Costs and unrelated fields are preserved; legacy correctness-only `pass_rate` retains its existing meaning.
- `current/figures/`: five-model/all-twelve task heatmaps, repeatability counts, correctness–process disagreement (each PDF/PNG). `current/tables/` contains task matrices, 0/3–3/3 counts, Pass@1/@3/Pass³, shared success, never/inconsistent tasks, workflow/membrane and paired differences, trial classifications, quadrant counts, and complete score provenance. The surviving original review remains frozen.
- `overlap_before_after.csv`: strongest-three shared 3/3 remains 42 tasks/12 hard; five-main intersections stay unchanged. Older-five shared 3/3 falls 21→20; older-six at-least-one falls 32→31. All other task vectors/row order are preserved.

## TeX updates for manual application (not applied)

The latest instruction explicitly prohibits all TeX edits. Your new representative-task caption/label, citations and section headings therefore remain intact. The following list replaces the previous task's requested direct text edits:

| File:line | Action | Required update |
|---|---|---|
| main.tex:340 | Replace the Task 39/32 paragraph | Task 39 concerns the complex leg for one +1 ligand (11a), not a set of ligands. All 36 repeated trials fail strict success under Policy B. The nine strongest-three completed trials acknowledge the charge change but do not implement the scored ion/index treatment and receive C=0.9/P=0.6. Recognition/deferred plans are insufficient; co-alchemical ions are not the only scientifically possible charge-treatment strategy. Task 32 failed through incomplete delivery after a charging/network-planning command continued in the background: the agent ended its turn and verification began without the required outputs. No Harbor agent timeout was recorded; grades stay unchanged. |
| main.tex:279 | Document harmonization in Methods | Retrospectively apply C6, P2 and ion-specific P4 consistently across the twelve repeated configurations; preserve accepted method-independent corrections and original run records. Do not describe the ion-order question as independently revalidated. The broader claim that all cohort criteria are comparable remains outside this specific approval. |
| main.tex:318 | Update adjusted and conditional means | Gemini 4 Argon: correctness 82.47% adjusted / 98.18% conditional; process 82.99% / 98.79%. GLM: correctness 82.30% / 90.11%; process 83.89% / 91.85%. The old conditional values were already stale before Policy B. Conditioning on completion does not identify model versus harness causes. |
| main.tex:320 | Correct GLM repeatability | 38/50 tasks at least once, 24/50 on all three (previously 39/50 and 24/50). |
| main.tex:348 | Correct Gemini cost-comparison success rate | Gemini 3.7 Flash rises from its revised 69.3% to Gemini 4 Argon's unchanged 76.7%, rather than 71.3% to 76.7%. Recorded costs are unchanged. Cost-panel references should point to Figure 4B, not 3B. |
| main.tex:144 | Correct the commented abstract population | 18 configurations, 2,100 trials: twelve repeated configurations contribute 1,800 and six historical configurations contribute 300. The live abstract and conclusion placeholders are otherwise unchanged. |
| SI.tex:114 | Correct Task 39 scientific requirement wording | The scored requirement is implemented charge compensation through the co-alchemical chloride and associated index; recognition or an unimplemented plan is insufficient. Do not claim this is the only scientifically valid strategy. Accept valid explicit B states or couple-moltype for the ligand pathway. |
| SI.tex:117 | Describe the actual harmonized assessment | Ten equally weighted correctness criteria and five equally weighted process criteria. Preserve the accepted representation corrections. Across 26 completed setups, C=9/10 and P=3/5. Nine errors retain raw grades but adjusted scores are zero; the completed empty GLM trial stays zero. The 16 changed passes are three each for Sol-5.6, Terra, Opus-5, Flash-3.7 and Sonnet-5, plus one GLM trial. |
| SI.tex:242 | Correct S1 reference | S1 complements current main-text Figure 4 (difficulty/cost), not Figure 3 (timeline/rewards). |
| SI.tex:253 | Update outcome asset and caption manually | Use figures/figure_A1/figure_A1.pdf; its existing renderer selects ten configurations, not the seven described in the current legacy caption. The selection/design were preserved during regeneration. |
| SI.tex:260 | Update task-type asset and caption manually | Use figures/figure_A2/figure_A2.pdf with the same ten selected configurations. The current TeX references a missing historical asset; no alias was inserted that would silently contradict its seven-model caption. |


In particular, the SI still points to the two missing `figures/codex_regrade_human/` PDFs and describes seven configurations; the regenerated A1/A2 assets retain their existing ten-configuration selection. No compatibility aliases were added that would silently change the meaning of those captions. This remains a manual TeX task.

## Task 32 and remaining evidence limits

Task 32 `32_fep_openfe_rbfe_dhodh__Y9ZuSSz` retains C=0/P=1 and completed status with no Harbor exception. All five scored correctness criteria fail because the required final ligand SDF, mapped network, transformations and summary were absent; only the 58,830-byte uncharged intermediate survived. Ligand preparation completed in 11.508 s. The later command `time python scripts/plan_rbfe_network.py 2>&1 | grep -v -i warn | tail -40` exceeded a 120-second native tool wait and continued in the background. The agent scheduled a 1,200-second wakeup but ended its turn; Harbor verification began before that wakeup, with the required outputs absent. This supports incomplete delivery, not the draft's slow-alignment/Harbor-timeout account. The unique lifecycle cause remains unresolved. Saved evidence is copied read-only in `validation/task32_evidence.md` and runtime timestamps in `validation/task32_runtime.json`. No grades changed.

Other pre-existing text needing separate review remains untouched: Task 11/Gemini outcome wording; Task 25/29 correctness/process and force-causality descriptions; the universal highest-timeout claim; the universal Opus-5 judge claim; the unverified v1.0 archive claim; and abstract/conclusion/bibliography placeholders. Task 35 and the separate ion-order investigation were not expanded.

## Validation/reproduction

Nine panels were rendered for visual inspection. Static TeX environment checks pass; existing unresolved assets are recorded rather than changed. No TeX compiler is installed, so no manuscript/SI compilation or pagination claim is made. All TeX bytes, original run/grade records, canonical tasks, historical v0.1 exports, costs and unrelated task scores are preserved. The overlay replays without changing active CSV bytes.


```json
{
  "baseline_commit": "b2f616bf8318c6cfa0d1c24804824f9bb6f8b6ad",
  "n_configurations": 18,
  "n_trials": 2100,
  "changed_trials": 16,
  "task39_completed_setups_at_09_06": 26,
  "task39_repeated_strict_passes": 0,
  "policy_A_previously_applied": false,
  "tex_files_checked": 2,
  "all_tex_files_byte_identical": true,
  "original_record_files_checked": 6248,
  "original_records_unchanged": true,
  "canonical_task_files_checked": 250,
  "canonical_task_files_unchanged": true,
  "historical_v01_exports_byte_identical": true,
  "unrelated_trial_fields_costs_and_Task32_Task35_scores_unchanged": true,
  "latest_Figure2_PNG_PPTX_unchanged": true,
  "original_frozen_review_unchanged": true,
  "overlay_replay_byte_identical": true,
  "figure_panels_rendered": 9,
  "tex_compiler": null,
  "compiled": false,
  "existing_unresolved_tex_assets": [
    {
      "tex_file": "SI.tex",
      "asset": "figures/codex_regrade_human/figure_A1.pdf"
    },
    {
      "tex_file": "SI.tex",
      "asset": "figures/codex_regrade_human/figure_A2.pdf"
    }
  ],
  "duplicate_tex_labels": {
    "main.tex": [],
    "SI.tex": []
  }
}
```


```bash
PYTHONDONTWRITEBYTECODE=1 ../MDArena-dev/.venv/bin/python data/apply_task39_policy_b.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/task39_policy_b_2026-11-20/regenerate.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/task39_policy_b_2026-11-20/verify_and_report.py
```

No agents, LLM judges, simulations or canonical-task edits are invoked. No TeX is written. Committing/pushing are left to the user. `file_changes.csv` lists every new/modified deliverable, including pre-update CSV snapshots.
