# GPCR paper Supporting Information figures

Imported on 2026-11-23 from
`/biggin/b211/reub0138/Projects/orexin/figures`, using
`/biggin/b211/reub0138/Downloads/ct6c01161_si_001.pdf` to identify the published
figure numbering and captions. These are the 13 SI figures of Anand et al.,
[Improving ABFE Calculations for GPCRs by Addressing Errors in Apo-State Representation](https://doi.org/10.1021/acs.jctc.6c01161).

Appendix Figures A.1–A.13 follow SI Figures S1–S13 in order. Chapters 3–5 refer
to the relevant appendix figures. S6, S7, S10, S11, and S12 use landscape pages
to keep their ten panels readable. Captions credit the paper under CC BY 4.0.

The historical directory names do **not** match the published SI numbering.
The table below records that mapping. Each figure is under
`figures/si_s<number>/si_figure_S<number>.{svg,pdf}`; S8 and S9 have original
PDFs rather than SVGs.

| Published SI figure | Subject | Source asset relative to the original `figures/` |
| --- | --- | --- |
| S1 | GCMC-like resolvation schematic | `figures_for_publication/si_fig2.svg` |
| S2 | Boresch setup and repeat variability | `figures_for_publication/si_fig1.svg` |
| S3 | Additional mGlu5 water-occupancy traces | `figures_for_publication/si_fig3.svg` |
| S4 | Water occupancy across four datasets | `si_fig9_solvation_for_all_datasets/si_fig9_vdw_solvation_for_all_datasets.svg` |
| S5 | Lenselink with GCMC-like resolvation | `si_fig14/exp_vs_pred_with_dg_shading_blue_lenselink_gcmc_exploratory_wstat_v3_label.svg` |
| S6 | PCA by simulation ensemble | `figures_for_publication/si_fig4.svg` |
| S7 | PCA by simulation time | `figures_for_publication/si_fig6.svg` |
| S8 | PCA overlap across four datasets | `si_fig12/si_fig12_pca_apo_vdw20_holo.pdf` |
| S9 | Deflorian PCA overlap | `si_fig13a/si_fig13a_pca_apo_vdw20_holo.pdf` |
| S10 | Cluster assignments | `figures_for_publication/si_fig5.svg` |
| S11 | Selected apo and endpoint PCA | `figures_for_publication/si_fig7.svg` |
| S12 | Compound-specific REUS surfaces | `figures_for_publication/si_fig8.svg` |
| S13 | Pooled A2A ABFE performance | `si_fig10_A2A_combined_plot/A2A_combined_exp_vs_pred_with_dg_shading.svg` |

## Data and scripts

`data/orexin_source_manifest.csv` records every retained or reused source file,
its destination relative to the thesis root, and its original SHA-256 hash.
Hashes refer to the original files before script path adaptations. Input data
and publication figure sources are unchanged. The original SI tables and the
unpublished Kumar GCMC figure were not part of this figure import.

- `data/si_s2/`: repeat-level Lenselink ABFE data.
- `data/si_s4/` and `data/si_s4_inputs/`: frozen occupancy plotting tables and
  the per-dataset inputs used to prepare them.
- `data/si_s5/`: frozen Lenselink GCMC plotting data and its original incremental
  batch summary. Preparation uses that fixed batch rather than choosing a new
  latest batch.
- `data/deflorian_pca/`: full PCA projections shared by S6, S7, and S10; original
  clustered projections for S10; and selected apo/endpoint projections for S11.
- `data/si_s8/` and `data/si_s9/`: pooled PCA projections, including the original
  input used to prepare the Deflorian table.
- `data/si_s13/`: the frozen pooled table and three input dataset tables.

S3 reuses the identical frozen water-occupancy inputs already in
`chapters/Ch4-Binding-pocket-resolvation/data/water_occupancy/`. S12 reuses the
curves and intersection tables in
`chapters/Ch5-Apo-state-conformational-changes/data/compound_reus/`. These reused
files are included in the appendix source manifest.

The original scripts live directly in `scripts/`, with names based on their
published SI figure. Paths resolve relative to the script, so execution does
not depend on the working directory. Scientific calculations and plotting
settings are retained, with noninteractive output and Ruff formatting. The
unused clustering helpers in the time-colouring script were omitted.

Preparation scripts write working tables under
`scripts/intermediates/si_s<number>/`. Plotting uses frozen publication inputs
in `data/`. The clustering script writes its refitted cluster tables under
`scripts/intermediates/si_s10/`, separately from its rendered panels. Original
cluster assignments remain in `data/deflorian_pca/clustered/`.

## Regeneration

From the repository root:

```sh
uv sync --locked
appendix=chapters/appendixA
for script in "$appendix"/scripts/*.py; do
    uv run --locked python "$script"
done
```

The plotting project includes scikit-learn for the original K-means clustering
and metric calculations. No original simulation directory is needed by the
adapted entry points. There is no numerical generator for the manually drawn
S1 schematic. Its PDF export crops the empty source-page margins.

Scripts write new composite renders to `figures/si_s<number>/regenerated/` and
component panels to `figures/si_s<number>/panels/`. The publication figures used
by LaTeX remain unchanged. The original Inkscape composites embed their images;
panel generators do not automatically assemble those manual layouts.

All 16 imported scripts were run from outside the repository. Regenerated
occupancy tables, PCA overlap metrics, pooled ABFE results, and cluster
assignments were checked against the archived inputs and outputs. For the
Lenselink GCMC table, the relocated `Source_Batch` path is provenance metadata;
the scientific columns are retained.

After editing a composite SVG, export its PDF with Inkscape:

```sh
for figure in "$appendix"/figures/si_s*/si_figure_S*.svg; do
    area=--export-area-page
    case "$figure" in */si_s1/*) area=--export-area-drawing ;; esac
    inkscape "$figure" "$area" --export-text-to-path \
        --export-filename="${figure%.svg}.pdf"
done
```

Build the thesis with `sh scripts/build`.
