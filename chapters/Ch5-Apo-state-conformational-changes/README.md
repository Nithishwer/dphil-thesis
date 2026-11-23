# Chapter 5 paper figures

Imported on 2026-11-22 from
`/biggin/b211/reub0138/Projects/orexin/figures` for Anand et al.,
*Improving ABFE Calculations for GPCRs by Addressing Errors in Apo-State
Representation*, [doi:10.1021/acs.jctc.6c01161](https://doi.org/10.1021/acs.jctc.6c01161).

| Thesis figure | Paper figure | Included PDF under `figures/` | Source workflow |
| --- | --- | --- | --- |
| 5.1 | 7 | `apo_state_correction/paper_figure_7.pdf` | `fig7/` |
| 5.2 | 8 | `compound_correction/paper_figure_8.pdf` | `fig8/` |
| 5.3 | 9 | `combined_correction/paper_figure_9.pdf` | `fig9/` |

The SVGs are unchanged copies from `figures_for_publication/`, exported to PDF
with Inkscape. Figure 9's PDF crops the empty page margins. Captions credit the
CC BY 4.0 paper. `data/orexin_source_manifest.csv` records the original paths,
destinations, and SHA-256 hashes; hashes for adapted scripts refer to their
upstream versions. The 13 SI figures were subsequently imported into Appendix A
on 2026-11-23; see the [appendix asset README](../appendixA/README.md). Its S12
plotting script reuses this chapter's compound REUS curves and intersection tables.

## Layout

- `data/compound_reus/`: five forward/reverse convergence curves and an
  intersection table for each of the ten ligands. Obsolete and shortened curve
  variants were excluded.
- `data/combined_reus/`: the equivalent curves and intersection table for the
  combined correction.
- `data/compound_correction/` and `data/combined_correction/`: frozen ABFE
  plotting inputs; the former also contains the compound-specific corrections.
- `data/reus_schematic/points.csv`: the original illustrative point export.
  The PCA schematic is synthetic, not a simulation PCA dataset.
- `scripts/`: original preparation and plotting scripts, with descriptive names,
  chapter-relative paths, noninteractive output, equivalent NumPy error metrics,
  and Ruff formatting.
- `scripts/intermediates/`: regenerated correction tables and schematic points.
- `figures/`: publication SVGs and PDFs, original schematic panels, and generated
  plots. Newly generated schematic panels use `reus_schematic/regenerated/`.

Figure 7's thermodynamic cycle, schematic arrangement, panel labels, and FES
panels were assembled manually in Inkscape. The SVG embeds its images and keeps
that layout editable; the scripts regenerate component panels. The schematic
generators retain the source's unseeded random point generation, so their new
points need not match the original illustration.

## Regeneration

After `uv sync --locked`, run from the repository root:

```sh
chapter=chapters/Ch5-Apo-state-conformational-changes
for script in \
    prepare_compound_corrections.py \
    plot_compound_reus.py \
    plot_compound_correction.py \
    plot_combined_reus.py \
    plot_combined_correction.py; do
    uv run --locked python "$chapter/scripts/$script"
done
```

The preparation script writes its correction table under
`scripts/intermediates/compound_correction/`. The plotting scripts read the
frozen publication inputs in `data/`, and write corrected tables under
`scripts/intermediates/`. The regenerated compound corrections and both corrected
ABFE tables were checked against the archived originals.

To generate new illustrative PCA panels:

```sh
uv run --locked python "$chapter/scripts/make_reus_ensemble_schematic.py"
uv run --locked python "$chapter/scripts/make_reus_cv_schematic.py"
```

Re-export the editable composites after changing their layout:

```sh
for item in apo_state_correction/7 compound_correction/8 combined_correction/9; do
    folder=${item%/*}
    number=${item#*/}
    area=--export-area-page
    if [ "$number" = 9 ]; then area=--export-area-drawing; fi
    inkscape "$chapter/figures/$folder/paper_figure_$number.svg" \
        "$area" --export-text-to-path \
        --export-filename="$chapter/figures/$folder/paper_figure_$number.pdf"
done
```

Build the thesis with `sh scripts/build`.
