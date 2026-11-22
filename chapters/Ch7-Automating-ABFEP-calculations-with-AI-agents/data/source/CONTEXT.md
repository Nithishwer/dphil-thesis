# MDArena: RSC Digital Discovery Communication

Last reviewed: 20 November 2026.

## Latest approved scoring update (20 November; reapplied after repository update)

The active score exports now include Wei-Tse's approved **Task 39 Policy B**,
reapplied against commit `b2f616bf8318c6cfa0d1c24804824f9bb6f8b6ad`. This
supersedes the earlier Task 39 aggregate scores below. C6, P2 and ion-specific P4
remain scored implemented-charge requirements; accepted non-charge decisions
are carried forward without independent artifact revalidation. All 26 completed
setups score correctness 0.9 and process 0.6; all 36 selected repeated Task 39
trials fail strict success. Original raw error grades and the completed empty
GLM trial are unchanged.

Current strict-pass totals are GPT-5.6 Sol 120/150, GPT-5.6 Terra 102/150,
Claude Opus-5 112/150, Gemini 3.7 Flash 104/150, Claude Sonnet-5 93/150 and
GLM-5.2 94/150. All other totals and the 18-configuration/2,100-trial selection
are unchanged. Approval and exact trial/criterion decisions are recorded in
`data/adjudications/task39_policy_b/`; replay with `data/apply_task39_policy_b.py`
after any upstream export. The original focused follow-up was removed by the
repository reset; its Task 39 approval basis is transparently reconstructed from
the surviving frozen first-review provenance and saved grading records.

Updated figures, statistical tables, reproduction commands and the change report
are under `analysis/task39_policy_b_2026-11-20/`. Figure 1, the newly updated
illustrative Figure 2 and its PowerPoint source are preserved. All TeX files are
unchanged at the user's explicit latest instruction. Required manuscript/SI edits,
including Task 32's corrected incomplete-delivery account and existing SI asset
references, are listed for manual application. Task 35 scores and the separate
ion-order investigation remain unchanged. Earlier sections below describe the
historical pre-update repository state.

## Purpose and scope

Prepare a submission-ready MDArena manuscript for **Digital Discovery**, published
by the Royal Society of Chemistry, as a **Communication**. This repository is the
working home for that version. Adapt the NeurIPS manuscript for the journal's
readership and short format while preserving the evidence and scientific meaning.

The initial request is to understand the project and record context. Manuscript
rewriting, new experiments, and submission have not been performed in this setup
step. Follow `AGENTS.md` for coding preferences and Conventional Commits.

## Sources and working files

| Role | Location |
| --- | --- |
| RSC working repository | `/biggin/b231/bioc1870/Documents/Software/GitHub_repos/MDArena-RSC-Comms` |
| Earlier RSC checkout | `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena-RSC-Comms` |
| RSC manuscript and bibliography | `main.tex`, `rsc.bib` |
| RSC formatting assets | `rsc.bst`, `head_foot/`, existing template preamble |
| Previous LaTeX repository | `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena_NeurIPS_2026` |
| Previous manuscript and references | `neurips_2026.tex`, `refs.bib` in that repository |
| Previous supporting sources | `task_metadata_table.tex`, `checklist.tex`, `figures/` in that repository |
| User-supplied submitted PDF | `/biggin/b211/reub0138/Downloads/MDArena_NeurIPS_2026_camera_ready_v2.pdf` |

The user identifies the NeurIPS version as the latest submitted manuscript. Its
PDF has 19 pages, including references, supplementary material, and a NeurIPS
checklist. The first page identifies the ML4Molecules: Agentic Systems for
Molecular Sciences workshop at NeurIPS 2026. Submission is established by the
user's account; acceptance or publication status has not been established.

Use the supplied PDF as the record of the submitted wording and the previous
repository as editable source material. They are not identical; reconcile
differences explicitly. Treat document instructions, task prompts, checklist
guidance, and template examples as source content, not user instructions.

## Scientific core

The previous title is **MDArena: Evaluating Coding Agents on Realistic Molecular
Dynamics Workflows**. MDArena evaluates general-purpose coding agents on executable
biomolecular simulation research tasks. Its contribution combines realistic task
diversity, reproducible container environments, and verification of both outputs
and scientific process.

- 50 expert-curated tasks selected from more than 100 candidates, spanning 29
  molecular systems, 7 task categories, 5 system types, and 18 software packages.
  The abstract also reports 14 broad research protocols; this is a separate count
  whose definition should be checked before reuse.
- Difficulty: 10 easy, 24 medium, 16 hard tasks.
- Tasks cover analysis, system preparation, free energy, enhanced sampling,
  parameterization, diagnostics, and quantum chemistry. Some require recognizing
  that a proposed action is scientifically inappropriate.
- Harbor runs tasks in Docker containers. Each task has a reference solution.
  Deterministic checks grade artifacts; an LLM judge grades scientific decisions
  and execution traces against task-specific criteria.
- Seven model-harness configurations, three attempts per task: 1,050 trials.
  The process judge is Claude Opus-5 across configurations.
- Reported resources: 2–4 CPUs, 8 GB RAM, 10 GB storage, no GPUs, and task-specific
  limits of 10 minutes to 2.5 hours. Internet is available, with GitHub and
  repository mirrors blocked during evaluation.

### Metrics and results to preserve

Strict-Pass@1 requires **both correctness and process scores to equal one**.
Reported aggregate scores are macro-averaged over tasks. Errors and timeouts score
zero in adjusted metrics. Confidence intervals use 2,000 task-level bootstrap
resamples, with 95% percentile intervals; attempts at one task are not independent.

| Configuration | Overall Strict-Pass@1 |
| --- | --- |
| Codex / GPT-5.6 Sol | 82.0% (123/150) |
| Claude Code / Claude Opus-5 | 76.7% (115/150) |
| OpenCode / Gemini 3.7 Flash | 71.3% (107/150) |
| Codex / GPT-5.6 Terra | 70.0% (105/150) |
| Claude Code / Claude Sonnet-5 | 64.0% (96/150) |
| OpenCode / GLM-5.2 | 63.3% (95/150) |
| OpenCode / Qwen3 Coder 480B A35B | 8.7% (13/150) |

The six non-Qwen configurations achieve 90–100% on easy tasks. On hard tasks,
Claude Opus-5 reaches 52.1% (25/48) and GPT-5.6 Sol reaches 50.0% (24/48).
Higher partial-credit scores do not establish complete or repeatable success.
GPT-5.6 Sol passes 43/50 tasks at least once and 39/50 on all three attempts.

The supported framing is practical value on bounded tasks with supervision,
alongside fragility in long, complex research workflows. The current RSC draft's
suggestion of general production reliability with little supervision is an
editorial proposal that the benchmark does not establish. The deliberately
challenging, single-group task selection also prevents interpreting these rates
as estimates across all routine MD work. Preserve limitations concerning task
selection, LLM-judge dependence, and emphasis on setup and analysis rather than
long production simulations. Model names and results describe this evaluation;
they are not claims about today's best available models.

## Repository snapshot recorded on 13 November

This is historical context. The 19 November audit below supersedes the model
counts, manuscript status, and figure descriptions in this snapshot.

- `main.tex` retains the RSC two-column Communication template. It contains nine
  authors, affiliations, equal-contribution and corresponding-author notes, and
  an Author Contributions statement. Preserve these unless revising them is
  requested or a specific discrepancy is resolved.
- The title and abstract are provisional (including "Something like" wording).
  Most main text, example equations, figures, tables, conflict statement, data
  statement, and bibliography entries remain template examples or instructions.
  `README.txt` describes the template rather than this project's workflow.
- At initial inspection, `data/` and `figures/` were present but entirely
  untracked. They predate this context-writing step. Do not delete or stage them
  incidentally. The latest commit was a revert of RSC figure inclusion; figure
  selection and placement remain unresolved.
- Existing assets include dataset composition (Figure 1), strict pass versus
  model release date (Figure 2), difficulty and cost (Figure 3), and supplementary
  outcome/category figures (A1/A2), each under `figures/figure_*/` with its Python
  generator. The previous three-panel overall figure is in `figures/figure_2_old/`.
- `data/` now contains ten models. The original seven retain the submitted
  headline rates above; GPT-6.1 Sol, GPT-6 Astra, and Claude Opus-5.5 add final
  user-adjudicated strict-pass rates of 88.0%, 88.0%, and 94.67%, respectively.
  All ten models have 150 trials across the same 50 task IDs. The separate
  `data/codex_regrade_human/` and `figures/codex_regrade_human/` variants are no
  longer present in the working tree.
- The three new models are exported by the sibling
  `MDArena_run_analysis_DD_regraded/export_rsc_data.py`, using the frozen DD
  qualifying-run selection and final user verdicts. Their selection excludes
  earlier infrastructure failures. Opus-5.5 costs are recovered from native
  Claude Code logs and represent recorded list-price costs; its mean is
  $0.8573 per trial. Task 35 passes were awarded by user decision, and Task 39
  corrections cover Boresch restraints only.
- Figures 2, 3, A1, and A2 read the corresponding CSVs under this repository's
  `data/` directory. Figure 3 uses the nine-model subset listed below.
  Figure 2 uses provider colours
  and three marker classes: Terra/Sonnet/Flash, Sol/Opus/GLM/Qwen, and Astra/Fable.
  The provider legend is below left and the class legend below right. GLM-5.2
  (about 753B total parameters) and Qwen3 Coder (480B total, 35B active) are
  assigned to Sol/Opus as an approximate size-based plotting convention, not a
  parameter-matched comparison with the closed models. The parameter sources
  and grouping rationale are recorded in the script.
  Its release dates and source URLs are recorded in `make_figure_2.py`; no live
  lookup is needed to regenerate it. OpenAI dates use the API release changelog,
  with an x-axis break between Qwen3 Coder's July 2025 release and the 2026
  releases. The narrower figure uses the same date scale in both visible
  windows and a shared y-axis. Model names accompany the points; vertical bars
  show the existing 95% task-bootstrap CIs.
  Fable names a class but has no score or point in the current dataset.
  Figure 2A includes both Gemini 3.7 Flash and Gemini 4 Argon, using Argon's
  13 October 2026 developer launch. Figure 2B and 2C use Argon in place of Flash.
  Figure 3 is restricted to GPT-5.6 Sol, GPT-6.1 Sol, GPT-6 Astra, Claude Opus-5,
  Claude Opus-5.5, Gemini 3.7 Flash, Gemini 4 Argon, GLM-5.2, and DeepSeek V4.1 Flash.
  DeepSeek costs use the exported trial token counts and Vertex AI list prices.
  The export yields a mean of USD 0.702 per trial. OpenCode logs differ for
  26 failed trials and yield a mean of USD 0.721 across the same 150 trials.
  Figure 3 uses the model colours defined in `make_figure_3.py` for the bars,
  scatter points, and legend markers.
  Scatter and legend markers are circles for GPT-5.6 Sol, Opus-5, Flash, GLM,
  and DeepSeek. GPT-6.1 Sol, Opus-5.5, and Argon use triangles, and Astra uses a star.
  Four columns beneath the panels group OpenAI, Claude, Gemini, and open models.
  The cost panel shows the key for striped bars.
  `main.tex` includes Figure 3 as a two-column `figure*` in Results and
  Discussion, with label `fig:difficulty_cost` and a matching text reference.
  A local `latexmk` build and visual check confirm Figure 3 spans both columns
  on page 4; the current draft remains four pages.
  A2 and the old overall figure retain the original model palette; A1 colours
  encode outcomes. Strict rates are calculated from both score dimensions;
  the legacy correctness-only `pass_rate` field is not used as a strict rate.
  Figure 1 checks the task selection and categories against all task-summary
  CSVs, then obtains system types and packages from `MDArena-dev/tasks/`.

Regenerate all PNG and PDF figures from this repository with the existing
analysis environment:

```bash
for script in figures/figure_*/make_figure_*.py; do
    ../MDArena-dev/.venv/bin/python "$script"
done
```

Paths to data and outputs resolve from each script, so execution also works
from other directories. Figure 1 discovers the sibling benchmark checkout;
`MDARENA_REPO` can select a different checkout explicitly.

## Current state and trial-source audit: 19 November

The main text now contains the Introduction, Methods, Results and Discussion,
Author Contributions, and a draft data-availability statement. The abstract is
still a placeholder and the conflict statement still contains template guidance.
`SI.tex` is a separate supplementary document. The RSC preamble is retained.

The exported data contain **18 configurations and 2100 selected trials**:
six v0.1 configurations with 50 trials each, seven v0.2 configurations with
150 each, and five configurations called v1.0 in the manuscript with 150 each.
Each configuration covers 50 tasks. Version labels in
`figures/benchmark_versions.py` identify these manuscript cohorts; run-folder
names such as `MDArena_v3_runs` and `MDArena_v4_runs` are not release labels.
The sibling benchmark checkout still documents an unreleased v0.3.0 and has
package version 0.2.0; the manuscript's v1.0.0 archival claim therefore remains
to be checked against the intended release before submission.

`data/trial_sources.csv` gives one row per selected trial, including model,
cohort, harness, task, attempt, exact analysis directory, current source
directory, and the selection map/audit/collection manifest where applicable.
All **2100 analysis result paths and 2100 source result paths were checked to
exist**, and their result IDs match pairwise. Regenerate the index with
`python data/make_trial_sources.py`.
The script reads saved results and selection records without modifying them.

For the compact directory map below:

- `E` = `/biggin/b231/bioc1870/Documents/Software/GitHub_repos/MDArena_eval/v0.2`
- `B` = `/biggin/b211/reub0138/Projects/LLMsxFEP`
- Every directory listed contains run subdirectories and then individual trials,
  except the timestamped GPT-5.6 directories, which directly contain trials.
- `jobs_rep{1,2,3}` means three separate replicate roots.

| Configuration | Cohort / selected trials | Current source roots |
| --- | --- | --- |
| GPT-5.5 Medium | v0.1 / 50 | `B/MDArena_evals/run_v1_codex_GPT55_medium/jobs` |
| GPT-5.5 XHigh | v0.1 / 50 | `B/MDArena_evals/run_v1_codex_GPT55_xhigh/jobs` |
| Gemini 3.5 Flash | v0.1 / 50 | `B/MDArena_evals/run_v1_opencode_Gemini_Flash3.5/jobs` |
| Gemini 3.1 Pro Preview | v0.1 / 50 | `B/MDArena_evals/run_v1_opencode_Gemini_Pro3.1/jobs` |
| DeepSeek V3.2 | v0.1 / 50 | `B/MDArena_evals/run_v1_opencode_Deepseek/jobs` |
| Qwen3 Instruct 235B A22B | v0.1 / 50 | `B/MDArena_evals/run_v1_opencode_Qwen/jobs` |
| GPT-5.6 Sol | v0.2 / 150 | `B/MDArena_v2_runs/jobs/2026-08-25__00-04-29` (149); `B/MDArena_v2_runs/jobs/2026-08-27__15-17-31` (1) |
| GPT-5.6 Terra | v0.2 / 150 | `B/MDArena_v2_runs/jobs/2026-08-25__23-45-27` (149); `B/MDArena_v2_runs/jobs/2026-08-27__15-15-22` (1) |
| Claude Opus-5 | v0.2 / 150 | `E/Claude/Opus-5/jobs` |
| Claude Sonnet-5 | v0.2 / 150 | `E/Claude/Sonnet-5/jobs` |
| Gemini 3.7 Flash | v0.2 / 150 | `E/Gemini/3.7-flash/jobs` |
| GLM-5.2 | v0.2 / 150 | `E/GLM/5.2/jobs_rep{1,2,3}` |
| Qwen3 Coder 480B A35B | v0.2 / 150 | `E/Qwen/Coder-480B/jobs_rep{1,2,3}` |
| GPT-6 Astra | v1.0 / 150 | `B/MDArena_v3_runs/jobs` (four selected batches; exact trials in the index) |
| GPT-6.1 Sol | v1.0 / 150 | `B/MDArena_v4_runs/gpt-6.1-sol/jobs` |
| Claude Opus-5.5 | v1.0 / 150 | `B/MDArena_v4_runs/opus/jobs` |
| Gemini 4 Argon | v1.0 / 150 | `B/MDArena_v4_runs/gemini-4-argon/jobs` (includes imported v3 trials) |
| DeepSeek V4.1 Flash | v1.0 / 150 | `B/MDArena_v4_runs/deepseek-v4/jobs` |

The historical six use `analysis/task_job_map.csv` in each run folder to select
one trial per task. Do not rediscover an arbitrary first attempt from their jobs
trees. Their metadata were exported from the frozen v0.1.0 commit
`d50547af07a4de9720c95ae42450ee3d49b8ae14`, preserving `15_grompp_tcoup` and
11/23/16 easy/medium/hard tasks, compared with 10/24/16 for the later cohorts.

The seven v0.2 analysis copies are under
`B/MDArena_v2_runs/reduced_outputs`, with `runs.toml` and per-model
`collect-manifest.json` files linking them to the raw roots above. Those manifests
predate the move of the local raw runs into `MDArena_eval/v0.2`; their old raw
paths omit the `v0.2` component. The trial index records the current locations.
Regrade and replacement batches are included in the exported selection.

GPT-6 Astra, GPT-6.1 Sol, and Opus-5.5 use
`B/MDArena_run_analysis_DD/inputs/{astra,sol-6.1,opus-5.5}`. Its
`input-audit.json` freezes 450 qualifying trials and records 249 excluded earlier
attempts. Final exported scores incorporate user adjudications in
`B/MDArena_run_analysis_DD_regraded`; the original result scores need not equal
the final manuscript scores. Preserve that selection and adjudication history.

Other saved work exists in both `MDArena-dev/jobs` trees, local
`MDArena_eval/v0.3` (Opus-5.5/Fable and smoke tests), local v0.2 DeepSeek/Kimi
smoke runs, `B/MDArena_v2_runs/jobs_backup` and `jobs_rep2`, earlier batches in
`B/MDArena_v3_runs`, `B/MDArena_evals/jobs` and its testing folders,
`B/mdarena_og/jobs`, and `B/testing_mdarena/jobs`. These are not additional
selected manuscript trials. The old
`B/MDArena_v2_runs/analysis/analysis_v0.2a_human_regraded` directory is not readable
under the current filesystem permissions; it was unnecessary for resolving the
selected analysis and source result paths.

### Figures after this audit

- Figure 1 is one row with the task-type pie beside the package bars, labelled A
  and B. Its metadata consistency check uses the twelve v0.2/v1.0 configurations, excluding
  the historical v0.1 task replacement rather than changing historical metadata.
- Figure 2 annotates all seven v0.2 names with superscript stars, including GLM
  in the reward panels. The six v0.1 names retain superscript daggers. Unmarked
  configurations are the manuscript's v1.0 cohort.
- Figure 3 retains its nine configurations and all numerical analyses, adding
  the version stars to the legend. Its renderer also produces Figure S1.
- `figures/figure_S1/` contains the complementary nine configurations: GPT-5.5
  Medium/XHigh, GPT-5.6 Terra, Sonnet-5, Gemini 3.5 Flash/3.1 Pro Preview,
  DeepSeek V3.2, and both Qwen configurations. It uses the same strict-pass
  calculation, 2000 task-bootstrap resamples, axes, and provider hues as Figure 3.
  Stars/daggers distinguish v0.2/v0.1. `SI.tex` includes it as Figure S1 and
  preserves historical difficulty labels and the cross-version qualification.
- Qwen3 Coder records no billed cost in the exported tables or trajectory
  summary; a checked native OpenCode database also records zero costs. The
  **supplied historical mean is GBP 0.14 per trial**, recorded in the sibling
  `MDArena_NeurIPS_2026/figures/figure_3/make_figure_3.py` (also present under `B`).
  All 150 trial identities and token counts match the current manuscript tables.
  S1 reuses the workshop conversion (1 GBP = 1.36 USD; mean USD 0.1904) and
  token allocation (uncached input:cached input:output = 1:0.1:4), with striped
  bars and an explicit caption. The exchange rate and difficulty allocation are
  assumptions, not recovered trial billing records. Source CSV costs remain blank.
- `SI.tex` still has two older missing-asset placeholders after S1, referencing
  `figures/codex_regrade_human/`. Updating those legacy figures is outstanding.
- Updated figure PDFs/600-dpi PNGs were regenerated and visually checked. The
  current environment has no LaTeX compiler; full manuscript/SI pagination must
  be checked where TeX is available.

## Differences and decisions to resolve during adaptation

- The local NeurIPS introduction says the strongest configuration solves "fewer
  than half of the tasks"; the PDF correctly refers to about half of **hard-task
  attempts**. Preserve the denominator and distinguish tasks from attempts.
- The PDF gives the benchmark URL as `https://github.com/weitse-hsu/MDArena` and
  describes version v0.2.0. The local source still links an anonymized repository.
  Confirm the public release and archival details before finalizing availability
  wording; external availability has not been verified in this setup step.
- Both versions introduce "two representative tasks" but present three: modified
  residue parameterization, a charged-ligand absolute binding free-energy setup,
  and assessing a PCA-derived collective variable. Decide which examples belong
  in the Communication and which in supplementary information.
- Select the central claim, final title, and minimum figures needed for a short
  chemistry-facing narrative. Retain the scientific limitations when condensing.
- Reconcile individual numerical claims with the selected data variant before
  reuse, including cost estimates and the membrane-preparation failure subset.
- Confirm final conflict, funding, author-contribution, and release information
  from the authors and source evidence. Import relevant scientific references
  from `refs.bib` into `rsc.bib` as the text is adapted.

## Journal guidance

Checked 7 November 2026 against the official
[Digital Discovery author guidelines](https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/digital-discovery).

- Communications normally occupy at most four printed pages. The submission
  needs a justification for urgent publication and significance to this readership.
- Use a single-paragraph abstract, around 50–250 words. Preserve RSC formatting
  and numbered superscript references. The template's Chemical Communications
  heading prohibition is not established here as a Digital Discovery requirement.
- Include conflicts and data availability statements; identify accessible data
  and code. Author contributions are encouraged. Acknowledge funding and AI use.
- Submit manuscript source and PDF, figures, cover letter, and supplementary
  material. Prepare reproducible code/data for review.
- A graphical table-of-contents entry is required at revision: up to 8 × 4 cm,
  TIFF at least 600 dpi, with 1–2 sentences totaling at most 250 characters.

Recheck guidance before submission. Decide the four-page allocation through
rendered layout review rather than assuming which components can be excluded.

## Next work

First settle the narrative and figure/data selection, then adapt `main.tex` and
`rsc.bib`, separate supporting detail into supplementary material, and replace all
template examples. Compile and inspect the final PDF for page count, legibility,
references, and figure placement. Prepare the remaining submission materials
against the confirmed journal requirements. Compilation and final layout review
have not been performed as part of this context-only change.
