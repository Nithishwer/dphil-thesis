# Chapter 3 figure assets

## Figure 3.1: Sampling comparison

Figure 3.1 was imported from
`/biggin/b211/reub0138/Projects/orexin/figures/fig1`.

- `figures/combined_square_v3.svg` is an unchanged copy of the supplied figure,
  assembled in Inkscape. The thesis includes its vector PDF export,
  `figures/combined_square_v3.pdf`.
- `data/figure_3_1/` contains the four original per-repeat CSV datasets for no
  HREX, HREX, apo windows, and epsilon-HREX.
- `scripts/intermediates/figure_3_1/` contains the four original `_w_stats.csv`
  tables used to plot the per-ligand means and standard deviations.
- `scripts/s0_make_exp_v_abfe_df_w_stats.py` and
  `scripts/s1_plot_exp_v_abfe_v3_label.py` are the original preparation and
  plotting scripts, adapted to the chapter paths and noninteractive execution.
  MUE and RMSE use equivalent NumPy expressions in place of scikit-learn;
  plotting parameters and the TI-based aggregation are retained.

Run from the repository root in the thesis plotting environment:

```sh
chapter=chapters/Ch3-Benchmarking-and-System-preparation
uv run --locked python "$chapter/scripts/s0_make_exp_v_abfe_df_w_stats.py"
uv run --locked python "$chapter/scripts/s1_plot_exp_v_abfe_v3_label.py"
```

The preparation script regenerates the intermediate tables. The plotting script
writes four panel SVGs into `figures/`; the combined layout and panel letters
remain in the supplied Inkscape SVG. Its panel order is (a) no HREX, (b) HREX,
(c) apo windows, and (d) epsilon-HREX. Export that layout for pdfLaTeX with:

```sh
inkscape "$chapter/figures/combined_square_v3.svg" \
  --export-type=pdf --export-filename="$chapter/figures/combined_square_v3.pdf"
```

## Figure 3.2: Allosteric sodium

The figure is included in Chapter 3 as Figure 3.2. Source assets were copied from
`/biggin/b211/reub0138/Projects/orexin/figures/fig5`.

- `figures/allosteric_sodium/combined_v4_converged.svg` is the unchanged source
  figure, assembled in Inkscape from six plot panels.
- `figures/allosteric_sodium/combined_v4_converged.pdf` is the earlier vector PDF
  export, retained with its source SVG. The thesis now includes the exact
  publication asset as `figures/allosteric_sodium/paper_figure_5.pdf`, exported
  from the unchanged `figures_for_publication/fig5.svg`.
- `data/allosteric_sodium/` contains six repeat-level CSV files and the six
  `*_w_stats.csv` tables used to plot the figure. The tables reproduce the MUE
  and RMSE values displayed in all six panels.
- `scripts/s0_make_exp_v_abfe_df_w_stats_*.py` are the original data-preparation
  scripts. They group TI estimates by ligand, calculate means and sample standard
  deviations, and assign an experimental error of 1 kcal/mol.
- `scripts/s1_plot_exp_v_abfe_v3*.py` are the original panel plotting scripts.
  The later `v3a` scripts in the source directory postdate the supplied figure and
  were not imported.

The copied scripts retain their calculations and plotting settings. Paths were
adapted to the chapter folders, and the Python files were formatted with Ruff.
Regenerated tables and statistics go to
`scripts/intermediates/allosteric_sodium/`; panel SVGs go to
`figures/allosteric_sodium/`. Plotting uses the archived input tables in `data/`.
The combined figure's Inkscape layout is preserved in the supplied SVG; the panel
scripts do not assemble that layout.

From the repository root, regenerate all six panels using the thesis plotting
environment plus the original scripts' scikit-learn dependency:

```sh
chapter=chapters/Ch3-Benchmarking-and-System-preparation
for script in \
    s1_plot_exp_v_abfe_v3_deflorian_label.py \
    s1_plot_exp_v_abfe_v3_label_lenselink.py \
    s1_plot_exp_v_abfe_v3_label_minetti.py; do
    MPLBACKEND=Agg uv run --locked --with scikit-learn python "$chapter/scripts/$script"
done
```

To regenerate the grouped tables separately:

```sh
for script in "$chapter"/scripts/s0_make_exp_v_abfe_df_w_stats_*.py; do
    uv run --locked python "$script"
done
```

Re-export the supplied composite after editing it in Inkscape:

```sh
inkscape "$chapter/figures/allosteric_sodium/combined_v4_converged.svg" \
    --export-area-page --export-text-to-path \
    --export-filename="$chapter/figures/allosteric_sodium/combined_v4_converged.pdf"
```

Build the thesis with `sh scripts/build`.

## Published-paper import

The nine main-text figures of Anand et al.,
[doi:10.1021/acs.jctc.6c01161](https://doi.org/10.1021/acs.jctc.6c01161),
were checked against the supplied paper on 2026-11-22. This chapter contains
paper Figures 1, 5, and 6 as thesis Figures 3.1, 3.2, and 3.3. All three captions
credit the CC BY 4.0 paper. Chapter 4 contains paper Figures 2–4; Chapter 5
contains paper Figures 7–9. The 13 SI figures were subsequently imported into
Appendix A on 2026-11-23; see the [appendix asset README](../appendixA/README.md).

The existing SVGs for Figures 3.1 and 3.3 exactly match the publication SVGs and
were reused with their existing scripts and data. Figure 3.3 uses the Kumar D3
inputs in `data/figure_3_3/`, its preparation and plotting scripts ending in
`_kumar.py`, and the composite under `figures/figure_3_3/`.
`data/orexin_source_manifest.csv` records the publication figure sources and the
existing script/data mappings, with original SHA-256 hashes. Existing adapted
scripts were retained.

Re-export the publication Figure 5 used in the thesis with:

```sh
inkscape "$chapter/figures/allosteric_sodium/paper_figure_5.svg" \
    --export-area-page --export-text-to-path \
    --export-filename="$chapter/figures/allosteric_sodium/paper_figure_5.pdf"
```


## Figure 3.5: Deflorian OX2 set 1 sodium comparison

- `data/figure_3_5/deflorian_set1_repeats.csv` snapshots the current repeat-level
  results for all 27 compounds, including estimator errors and source CSV paths.
  Missing estimates are written explicitly as `NA`.
- `scripts/prepare_figure_3_5.py` reads the `total` rows from current numbered
  `abfe_vanN_hrex_r1/analysis/abfe_results.csv` files in
  `/biggin/b211/reub0138/Projects/orexin/deflorian_set_1_j13_v1` (without Na)
  and `deflorian_set_1_j13_v2_na` (with Na). It excludes `abfe_old`.
  Experimental values match the with-Na experimental CSV and MIAMA inventory.
- `scripts/plot_figure_3_5.py` defaults to MBAR; `--method BAR` and `--method TI`
  use the other saved estimators. The plot is regenerated entirely from the
  local data snapshot. Re-run preparation to collect newly available results.
- `scripts/intermediates/figure_3_5/` contains per-compound means, sample SDs,
  repeat counts, and panel statistics. Wholly missing compounds remain `NA` in
  the summaries. A single repeat is plotted without a vertical error bar.
- `figures/figure_3_5/figure_3_5_MBAR.svg` and `.pdf` place without Na on the
  left and with Na on the right, following Figure 3.3's colors, bands, and
  labels. The panels share equal axis limits, expanded if needed to fit data.

The initial snapshot contains 93 without-Na repeats and 73 with-Na repeats,
covering 26 compounds in each panel. Compound 42922 has no current without-Na
result; compound 49599 has no with-Na result. All available current repeats are
included, including repeats 4–6 for five without-Na compounds. Results are not
filtered by convergence status, and each panel's statistics use its own
available compounds. Horizontal error bars are assigned 1 kcal/mol; vertical
error bars show repeat SD rather than estimator uncertainty.

From the repository root:

```sh
chapter=chapters/Ch3-Benchmarking-and-System-preparation
uv run --locked python "$chapter/scripts/prepare_figure_3_5.py"
uv run --locked python "$chapter/scripts/plot_figure_3_5.py"
```
