# Chapter 3 figure assets

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
