# Figure 5

`figure_5.pdf` is the approved **185.9 × 73.3 mm** figure, promoted from
`figure_5_horizontal_headers` on 21 November 2026. `figure_5.png` is the 600 dpi
PNG, and `preview_at_manuscript_width.png` is the filtered 150 dpi viewing copy.
The earlier layout variants, backup outputs and exploration code have been
removed. There is one generator: `make_figure_5.py`.

Panel A is one continuous five-configuration × 50-task heatmap, with
configurations as rows and tasks as columns. Whole-word task-type headings
are horizontal on two levels. Task IDs are lightly bold; concise scientific
names are rotated vertically, and E/M/H difficulty has a separate labeled row.
The four colors encode 0–3 strict passes without cell numerals. The 3/3 teal
was lightened from `#277E73` to `#418D84` at the user’s request; the other three
colors and the shared-success strip are unchanged.
White matrix borders are 0.18 pt; task-type gutters are 0.824 mm wide.
`task_labels_and_values.csv` retains every original description, display label,
difficulty and strict-pass count. `task_success.csv` remains unchanged.

B and C occupy equal-height 36.65 mm bands at right. Panel titles are omitted.
Two-line task/model and score details sit next to the letters, with their tops
below the letter tops. Intermediate/Submitted labels are centered beneath the
protein representations using the projected protein Cα bounds. The 37.8 Å
label sits beside the dotted measurement line. B's receptor views retain
identical orientation and scale; C's overview and clash inset retain the exact
approved arrangement, with AMP702 and POPE808 below the molecule.

Liberation Sans is used throughout: 8.5 pt panel letters, 5.6 pt task names,
and 5.5 pt case details, state labels and inset titles. Labels are checked on a
300 dpi canvas. `layout.json` records all physical placements, crops and label
bounds. `selection_manifest.json` records the approved option's hashes;
`validation.json` confirms that the final PNG matches the approved palette
revision and that B/C remain pixel-identical to the original selection. The
palette update affects only 3/3 cells and their legend swatch; the verification
is recorded separately in `selection_manifest.json`. Raw renders, derived
coordinates, cameras, original provenance, scores, canonical tasks and TeX files
are unchanged.

The width is the RSC template's full text width: letter paper (215.9 mm) minus
15 mm on each side. At the same 185.9 mm width, the saved Figure 3 PDF is
73.284 mm high, so Figure 5 matches within 0.02 mm. Measurements use the saved
PDF page boxes, including Figure 3's tight export, rather than nominal canvases.
The twelve-configuration heatmap remains copied unchanged to `../figure_S2/`.
`caption.md` is proposed caption text only; manuscript TeX has not been edited.

## Reproduction

From the repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=/tmp/mdarena-matplotlib
MDARENA_FIGURE_PYTHON=/biggin/b231/bioc1870/miniconda3/bin/python
"$MDARENA_FIGURE_PYTHON" figures/figure_5/make_figure_5.py
"$MDARENA_FIGURE_PYTHON" figures/figure_5/validate_figure_5.py
```

The saved coordinate copies, raw renders and PyMOL sessions are already supplied.
The original preparation, rendering candidates and source measurements remain
preserved for review; regenerating the composition does not rerender molecules
or change their cameras. `created_files.csv` inventories the final assets and
the unchanged S2 copy.

## Panel A: task-level strict success

The selected five-configuration table keeps its existing type-grouped task
order. Figure S2 is the unchanged twelve-configuration analysis PDF/PNG.

Source: `analysis/task39_policy_b_2026-11-20/current/tables/task_success_matrix.csv`,
with `task_metadata.csv` beside it. Every cell is independently checked against
the active selected `data/trials/{configuration}.csv` files for Opus-5.5,
GPT-6.1 Sol, GPT-6 Astra, Gemini 4 Argon and GLM-5.2: exactly three trials per
task and 150 per configuration. Completion and both full score dimensions
are required (existing threshold 0.999); the legacy `pass_rate` is never used.
The top-three intersection is recomputed, giving **42 tasks / 12 hard tasks**.
Task 39 is **0/3 in all five rows** after Policy B. The ordering is exactly the
existing type-grouped, task-number order; no overlap-based sorting is applied.
`task_success.csv` retains every plotted value, description and shared-set flag.
The heatmap, type headings, difficulty row and molecular annotations are vector
elements in the PDF; only molecular images are rasterized.

## Panel B: Task 25, intermediate versus submitted assembly

- Configuration: Claude Opus-5.5; replicate **3**.
- Exact trial: `25_mglu5_membrane_setup__5qy4iHm`.
- UUID: `8fab37cd-775f-4f91-b5bf-d4953037bb87`.
- Final exported scores: correctness **1.000**, process **0.875**, strict fail.
- Artifact directory:
  `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena_v4_runs/opus/jobs/2026-11-08__15-49-30/25_mglu5_membrane_setup__5qy4iHm/artifacts/app/outputs/`.
- Intermediate: `complex_oriented.pdb`; submitted: `system.gro`.
- Ligand covalent connectivity: saved `lig_openff_sage221.top`.
- Prior evidence: `analysis/section3_review_2026-11-20/report.md` and
  `deterministic_checks/artifact_results.json` in that review directory.

The fresh periodic KD-tree search covers every LIG atom and every amino-acid
protein atom, excluding ACE/NME caps. It is independently checked by the exact
minimum-image displacement of the resulting pair. The minimum is
**37.813362717431 Å** between **LIG267 Cl, global GRO row 4275**
at **(4.329, 4.928, 5.395) nm** and **LYS117 HZ2, global row 1873**
at **(11.299, 7.806, 7.281) nm**. The unmodified intermediate minimum is
**1.757868595772 Å**. The displayed 37.8 Å joins these actual atom centers;
it is not a center-of-mass distance or the heavy-atom-only minimum.

Coordinate transformations (row-vector convention, all lengths in Å):

1. Convert saved GRO nm to Å exactly once. The receptor is already continuous;
   no atomwise wrapping or protein repair is performed.
2. Translate the **entire submitted ligand** by **(+85.38, 0, 0) Å**, one x-box
   vector of the **(85.38, 85.38, 100.29) Å** orthorhombic box. The receptor is
   not moved separately to shorten the displayed gap. This is precisely the
   nearest periodic image selected by the all-atom minimum calculation.
3. Match **264 protein Cα atoms** by ordered sequence and the constant residue
   offset (intermediate residue = submitted residue + 567). Normalize CYX/CYS
   and HIE/HIS names only for correspondence checks; atom coordinates are not
   changed to alter chemistry. Fit the submitted protein to the centered
   intermediate protein with a proper Kabsch rotation (Cα RMSD **0.004942 Å**).
   Apply that same transform to the entire submitted structure, including the
   already imaged ligand. **The ligand is never independently fitted.**
4. Intermediate translation: **(+14.22095833, +15.63989394, +1.44783712) Å**.
   Submitted translation after the Kabsch rotation:
   **(−86.61753779, −84.79979732, −97.97774804) Å**.
   The nearly identity rotation is recorded at full precision as
   `task25.row_vector_rotation` in `verified_geometry.json`.
5. Apply one shared rigid camera rotation to both complete derived views.
   Selected camera: candidate 2, yaw −25°, tilt +12° relative to the documented
   displacement/z-axis basis. Both main views have identical view, origin,
   clipping planes and orthographic scale. The pocket inset is explicitly
   magnified; it uses the same molecular orientation.

Hydrogens are hidden except the measured Lys117 HZ2 and its side-chain sticks.
Solvent, ions and membrane are hidden. The source geometry is not minimized,
repaired or repositioned to create the illustration. Intermediate pocket
cartoons are transparent so the retained ligand remains visible. Full correctness
credit did **not** detect the final displacement; its process pose criterion failed.

## Panel C: Task 29, submitted ligand–lipid clash

- Configuration: Claude Opus-5.5; replicate **2**.
- Exact trial: `29_pept2_beta_lactam_membrane_se__Z4DQoGB`.
- UUID: `f9f2a3e2-0910-4868-9578-a54e42e53d5c`.
- Final exported scores: correctness **1.000**, process **0.9375**, strict fail.
- Submitted artifact:
  `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena_v4_runs/opus/jobs/2026-11-08__02-25-59/29_pept2_beta_lactam_membrane_se__Z4DQoGB/artifacts/app/outputs/system.gro`.
- Connectivity and molecule identities: `AMP.itp`, `POPE.itp`, `topol.top`
  in the same directory. Log: `em_test_mdrun.log`.

Fresh all-ligand-carbon/all-lipid-carbon search verifies **1.368612436010 Å**:

| Atom | Global GRO row | Saved position (nm) |
|---|---:|---|
| AMP702 C6 | 7575 | (5.246, 7.258, 5.184) |
| POPE808 C316 | 20845 | (5.301, 7.267, 5.309) |

These are separate AMP and POPE molecules. The topology declares no
intermolecular-interaction section. Their covalent graphs are read from the saved
ITP files into **separate PyMOL objects**; no proximity bond is inferred between
the clashing carbons. The carbon–carbon separation lies in the camera plane.
The transparent spheres use the ordinary PyMOL carbon van der Waals radius
(1.7 Å), without modifying atom centers or chemical connectivity.

The pair already shares a continuous nearest image, so **no periodic imaging is
needed**. All coordinates receive only the global translation
**(−52.735, −72.625, −52.465) Å**, followed by a rigid camera rotation.
The complete ligand and offending lipid have continuous saved covalent geometry
(maximum bond lengths checked below 2.2 Å); no atomwise wrapping is used.
The selected angle is candidate 2: +30° around the carbon-contact axis followed
by a −12° image-plane roll. Only protein residues within 12 Å of the ligand
provide faint cartoon context. POPE is written as `PPE` in the derived PDB
solely to fit the PDB three-letter residue field; the original identity remains
POPE808 in all evidence and labels.

**Interpretation limit:** the log reports `Maximum force = inf on atom 44170`,
not either atom illustrated here. The audit found POPG994 H4X (44170) only
**0.054772256 Å** from POPE889 C34 (31014). No force calculation was rerun;
the 1.37 Å ligand–lipid clash is not assigned as the unique cause of that log.

## Files, resolution and preservation

- `prepare_figure_5.py`: read-only source checks, independent distances,
  correspondence and derived PDBs under `derived/`.
- `render_structures.py`: PyMOL rendering and saved cameras/PSE sessions;
  `renders/candidates/` retains the inspected alternatives.
- `make_figure_5.py`: approved heatmap, aspect-preserving crops, vector annotations,
  and assembly in Liberation Sans; also exports the complete display table.
- `validate_figure_5.py`: preservation, coordinate, resolution and PDF checks.
- `source_manifest.json`: exact input paths/hashes and protected local files;
  original manuscript baseline commit **6ff0003be4237c693a4f4e3ab9e240b5ee1c1527**,
  preserved as historical provenance rather than rewritten after later TeX edits.
- `layout_revision_manifest.json`: current preservation baseline at commit
  **775e5c6c93e2da35a54b4fda196526a5e3fd54d3**. It protects the current TeX,
  evaluation exports, original coordinate copies/renders/cameras and all unrelated
  tracked files while permitting the specifically requested figure revisions.
- `verified_geometry.json`: numerical measurements, trial identities, all
  transforms and original atom records. Derived PDB precision is 0.001 Å;
  measurements are made on the original coordinates at their saved precision.
- `validation.json`: final checks and software versions; camera candidate
  contact sheets are supplementary viewing copies.

Raw B renders are 1404 × 1800 pixels, C is 1800 × 1800, and the insets
1250 × 1000 / 1650 × 1100. B uses identical 1292 × 1629-pixel crops at
23.4 mm width. C uses a 1620 × 1521-pixel crop at 28 mm width, trimming the
upper white margin at original image fraction 0.90; no molecule or contact
point is removed. The pocket and contact insets are 12 and 23 mm wide.
All molecular images exceed **600 effective dpi** at their actual PDF placements
(verified using `pdfimages -list`). The PDF retains the original cropped molecular
pixels; PNG reductions are filtered. No source
coordinates, grades or scores are rewritten. No new agent evaluations, LLM
grading, minimization or other simulation is invoked. The separate caption
preserves the distinction between observed geometry and what grading detected.

`manuscript_reference_notes.md` maps the old lettering to the new panels and
flags the existing implicit S2 numbering conflict in `SI.tex`. No manuscript
reference changes have been applied.
