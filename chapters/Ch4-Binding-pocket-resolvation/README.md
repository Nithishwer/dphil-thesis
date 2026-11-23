# Chapter 4 paper figures

Imported on 2026-11-22 from
`/biggin/b211/reub0138/Projects/orexin/figures` for Anand et al.,
*Improving ABFE Calculations for GPCRs by Addressing Errors in Apo-State
Representation*, JCTC 2026, 22, 10428–10444,
[doi:10.1021/acs.jctc.6c01161](https://doi.org/10.1021/acs.jctc.6c01161).
The supplied publication PDF was used to identify the nine main-text figures.
The 13 Supporting Information figures were subsequently imported into Appendix A
on 2026-11-23; see the [appendix asset README](../appendixA/README.md). Its S3
plotting scripts reuse the identical water-occupancy inputs in this chapter.

| Thesis figure | Paper figure | Included PDF under `figures/` | Source workflow |
| --- | --- | --- | --- |
| 4.1 | 2 | `binding_pocket/paper_figure_2.pdf` | `fig2/` |
| 4.2 | 3 | `mglu5_solvation/paper_figure_3.pdf` | `fig3_nd_4/` |
| 4.3 | 4 | `mglu5_solvation/paper_figure_4.pdf` | `fig3_nd_4/` |

Each included PDF is an Inkscape export of the unchanged matching SVG from
`figures_for_publication/`. Figure 2's PDF crops the empty SVG page margins.
Captions describe the original panels and credit the CC BY 4.0 paper.
`data/orexin_source_manifest.csv` records source paths, destinations, and original
SHA-256 hashes. Script hashes describe the source before local adaptations.

## Layout

- `data/binding_pocket/`: the original receptor structure and input GRO file.
- `data/mglu5_abfe/`: repeat-level free energies and frozen plotting tables.
- `data/water_occupancy/`: frozen cumulative occupancy and apo reference tables,
  plus the per-compound occupancy inputs and configurations used to prepare them.
- `data/solvation_structures/`: the apo snapshot and compound 6 ABFE coordinates
  and topology used by the molecular preparation script.
- `scripts/`: the original processing and plotting entry points, renamed by
  purpose and adapted to chapter paths. NumPy expressions replace the original
  scikit-learn error metrics without changing their definitions. Scripts use
  noninteractive plotting and are formatted with Ruff.
- `scripts/intermediates/`: prepared structures, PyMOL (`.pse`) and ChimeraX
  (`.cxs`) sessions, regenerated tables, and per-figure working files.
- `figures/`: editable publication composites, PDF exports, original molecular
  panels, and regenerated plot panels.

The publication composites were assembled manually in Inkscape. Plotting scripts
regenerate individual panels; they do not rebuild the composite layouts or the
manually configured molecular views. The imported SVGs embed their images.

## Regeneration

Run from the repository root after `uv sync --locked`:

```sh
chapter=chapters/Ch4-Binding-pocket-resolvation
for script in \
    prepare_mglu5_abfe_data.py \
    prepare_water_occupancy_initial.py \
    prepare_water_occupancy_solvated.py \
    plot_mglu5_abfe.py \
    plot_water_occupancy_initial.py \
    plot_water_occupancy_solvated.py; do
    uv run --locked python "$chapter/scripts/$script"
done
```

Preparation writes tables under `scripts/intermediates/`. Plotting reads the
frozen publication inputs under `data/` so that rerunning a preparation script
does not silently change a published panel. Both grouped ABFE tables and both
cumulative occupancy tables were regenerated and checked against those inputs.

Molecular preparation uses the separate MDAnalysis environment:

```sh
uv run --locked --with MDAnalysis python "$chapter/scripts/prepare_binding_pocket_structure.py"
uv run --locked --with MDAnalysis python "$chapter/scripts/prepare_solvation_structures.py"
```

The binding-pocket preparation was verified with MDAnalysis 2.11.0. That version
cannot parse the archived, PLUMED-enabled GROMACS 2020.6 TPR used by
`prepare_solvation_structures.py` (it raises `EOFError`). The original TPR,
coordinates, prepared PDBs, molecular renderings, and PyMOL session are retained;
repeating that preparation requires a compatible scientific environment.
PyMOL and ChimeraX are needed to edit their respective saved views.

To export a composite after editing its SVG:

```sh
inkscape "$chapter/figures/binding_pocket/paper_figure_2.svg" \
    --export-area-drawing --export-text-to-path \
    --export-filename="$chapter/figures/binding_pocket/paper_figure_2.pdf"
for number in 3 4; do
    inkscape "$chapter/figures/mglu5_solvation/paper_figure_$number.svg" \
        --export-area-page --export-text-to-path \
        --export-filename="$chapter/figures/mglu5_solvation/paper_figure_$number.pdf"
done
```

Build the thesis with `sh scripts/build`.
