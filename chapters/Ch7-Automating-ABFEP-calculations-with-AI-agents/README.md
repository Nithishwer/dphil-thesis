# Chapter 7 assets

Copied on 2026-11-22 from
`/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena-RSC-Comms`, at commit
`8ea34464dd0135f7e184d4739c1b953b0e109c02`. The copy also includes the source
project's untracked molecular-panel inputs, renderings, and scripts.

- `data/`: benchmark exports, molecular structures, figure configuration,
  provenance, and analysis records. `data/benchmark/tasks/` contains the 50 task
  metadata files needed for Figure 1 and the metadata table, copied from the
  source project's `MDArena-dev` dependency.
- `scripts/figures/`: current figure generators, adapted to read chapter data
  and write chapter figures. The source project's figure numbering is retained.
- `scripts/tables/`: the task metadata table generator; its output goes to
  `data/task_metadata_table.tex`.
- `scripts/upstream/`: original audit, adjudication, export, and archived plotting
  scripts, preserved unchanged for reference. These retain their original paths
  and repository assumptions. Run these workflows from the original manuscript
  checkout with its benchmark environment and saved job records.
- `figures/`: rendered figures, editable SVG/PowerPoint assets, PyMOL sessions,
  and analysis plots, grouped by their source directories.

`data/source_manifest.csv` maps every imported file to its original path and
SHA-256. Hashes describe the source files before local plotting-path changes.
Historical manifests and reports retain their original paths and hashes as
evidence; they do not describe the thesis checkout. Reference manuscript files
are preserved under `data/source/`.

The thesis draft still uses the original `figures/figure_1.pdf`,
`figures/figure_2.pdf`, and `figures/figure_3.pdf`. Imported manuscript assets
live under directories such as `figures/figure_3/`; regenerating them does not
replace the draft's existing PDFs or change its captions.

Two additional PDFs were imported from the same source project on 2026-11-22:
`figures/representative_tasks_source.pdf` is its `figures/figure_2/figure_2.pdf`,
and `figures/task_success_examples_source.pdf` is its
`figures/figure_5/figure_5.pdf`. The chapter arranges the representative tasks
in a 2x2 grid and splits the task-success heatmap from the two assembly
examples, which appear side by side. Cropping and layout are defined in the
chapter's LaTeX source; the imported PDFs are unchanged.

## Plotting

From the thesis repository root:

```sh
uv sync --locked
chapter=chapters/Ch7-Automating-ABFEP-calculations-with-AI-agents
uv run --locked python "$chapter/scripts/figures/figure_3/make_figure_3.py"
```

This reads `data/headline.csv` and `data/metrics/` within this chapter and writes
`figures/figure_3/figure_3.pdf` and `.png`. The scripts resolve paths relative
to their own location, so the working directory does not affect asset paths.

The plotting environment supports these generators:

| Script under `scripts/figures/` | Output under `figures/` |
| --- | --- |
| `figure_1/make_figure_1.py` | `figure_1/figure_1.{pdf,png}` |
| `figure_3/make_figure_3.py` | `figure_3/figure_3.{pdf,png}` |
| `figure_4/make_figure_4.py` | `figure_4/figure_4.{pdf,png}` |
| `figure_5/make_figure_5.py` | `figure_5/figure_5.{pdf,png}` |
| `figure_A1/make_figure_A1.py` | `figure_A1/figure_A1.{pdf,png}` |
| `figure_A2/make_figure_A2.py` | `figure_A2/figure_A2.{pdf,png}` |
| `figure_S1/make_figure_S1.py` | `figure_S1/figure_S1.{pdf,png}` |
| `figure_S2/copy_figure_S2.py` | `figure_S2/figure_S2.{pdf,png}` |
| `figure_2/d-AlchMetad/make_figure_2d.py` | `figure_2/d-AlchMetad/figure_2d.{pdf,png}` |

Figure 1 uses the copied task metadata by default. Set `MDARENA_REPO` to a full
benchmark checkout to use a different task metadata source.

Figure 2's SVG assembly script requires the Inkscape command. Molecular rendering
and preparation scripts also require tools from the upstream scientific
environment, including PyMOL, RDKit, or GROMACS. Figure 5's preparation and
validation scripts depend on original job records and source-specific audit
checks. These tools are separate from the thesis plotting dependencies; Figure
5 can be plotted directly using its copied data and existing renders.
