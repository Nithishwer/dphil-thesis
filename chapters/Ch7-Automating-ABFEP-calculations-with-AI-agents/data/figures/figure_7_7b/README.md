# Figure 7.7B source data

The inputs are unchanged copies of the submitted PepT2--ampicillin membrane
assembly from Task 29, Claude Opus-5.5, replicate 2, trial
`29_pept2_beta_lactam_membrane_se__Z4DQoGB`.
`source_manifest.json` records the original paths and SHA-256 hashes.

- `system.gro`: the complete submitted structure, including protein, AMP702,
  237 POPE molecules, 79 POPG molecules, water and ions.
- `protein.itp`, `AMP.itp`, `POPE.itp`, `POPG.itp`: explicit atom order and
  covalent bonds used to make separate molecular objects in PyMOL.
- `topol.top`: the original molecule inventory.
- `geometry.json`: the verified AMP702 C6--POPE808 C316 contact and shared
  display translation, copied from the original Figure 5 geometry audit.

The preparation script reads these bundled coordinates and topologies. The
original job directory is recorded only as provenance; it is not needed to
reproduce the figure. Protein coordinates and all 316 lipids are retained.
The contact remains 1.368612436 Å; no geometry is minimized or repositioned.

## Reproduction

Use Python with PyMOL (`pymol2` and `chempy`), NumPy, SciPy, Matplotlib and
Pillow. Rendering was checked with PyMOL 3.2.0a. From the repository root:

```sh
export MPLCONFIGDIR=/tmp/thesis-matplotlib
chapter=chapters/Ch7-Automating-ABFEP-calculations-with-AI-agents
python "$chapter/scripts/prepare_figure_7_7b_session.py"
python "$chapter/scripts/make_figure_7_7b.py"
```

Both scripts resolve inputs relative to their own location. Preparation writes
the editable full-membrane session and its verification record under
`scripts/intermediates/figure_7_7b/`. The figure script writes the editable
`renders/task29_selected_views.pse` session there, with `overview` and `closeup`
scenes, and the selected cameras in `task29_selected_views.json`.

The full-membrane preview, molecular renders and final PDF/PNG live under
`figures/figure_7_7b/`. The final labels are composed in `assemble_panel()` in
the figure script. The chapter includes `figure_7_7b.pdf` as Figure 7.7B.
