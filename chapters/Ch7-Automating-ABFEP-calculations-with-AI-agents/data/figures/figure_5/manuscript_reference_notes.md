# Proposed manuscript-reference updates (not applied)

The approved Figure 5 places **A, the five-configuration task heatmap**, at left
and **B, Task 25 binding-pose loss**, above **C, Task 29 ligand–lipid clash**, at
right. Panel A uses horizontal task-type headings, concise scientific task names
and a separate E/M/H difficulty row. The underlying values and panel letters are
unchanged. Earlier layout alternatives have been removed.

The existing twelve-configuration task heatmap remains copied unchanged to
`figures/figure_S2/figure_S2.pdf` and `.png`. All `.tex` files remain unchanged.
The manuscript locations below refer to commit
`775e5c6c93e2da35a54b4fda196526a5e3fd54d3`.

Figure 5 is **185.9 × 73.3 mm**, matching the RSC template's full text width and
the scaled height of Figure 3 (73.284 mm at the same width). Use the canonical
`figures/figure_5/figure_5.pdf`; `caption.md` contains the updated proposed caption.

| Location | Required reference when editing manually |
|---|---|
| `main.tex:315`, shared successes and the twelve hard tasks | Figure 5A for the five selected configurations; S2 for all twelve |
| `main.tex:328`, task-level repeatability and differing task profiles | Figure 5A / Figure S2 for selected/all repeated configurations |
| `main.tex:353`, membrane-task performance comparison | Figure 5A / Figure S2 for task-level outcomes |
| `main.tex:353`, Task 25 submitted ligand displacement | Figure 5B; the illustrated trial is replicate 3, `5qy4iHm`, at 37.8 Å |
| `main.tex:353`, Task 29 ligand–lipid carbon contact | Figure 5C; replicate 2, `Z4DQoGB`, at 1.37 Å |
| Main figure inclusion, not yet present | `figures/figure_5/figure_5.pdf`, with the separate proposed `caption.md` |
| SI heatmap inclusion, not yet present | `figures/figure_S2/figure_S2.pdf`, with `../figure_S2/caption.md` |

The original A/B/C panel lettering is restored. References based on the
intermediate two-panel layout need **Task 25: 5A → 5B** and **Task 29: 5B → 5C**.
Figure S2 remains the unchanged **twelve**-configuration heatmap. The selected
layout is the only active Figure 5; all panel references use A/B/C as above.

No explicit Figure 5/5A/5B/5C references or Figure 5 inclusion were found in the
current `main.tex` or `SI.tex`; those files therefore need new references rather
than replacements of existing literal panel citations. The old local Figure 5
caption and README panel headings have been updated. The earlier analysis
reports, heatmap assets, task tables and molecular-provenance files are preserved.

## Existing S2 numbering conflict

`SI.tex:37` uses the automatic `S\arabic{figure}` numbering scheme. Its figure
blocks currently assign:

| Current number | Existing material | Location |
|---|---|---|
| S1 | Complementary difficulty/cost configurations | `SI.tex:239–244` |
| S2 | Legacy outcome plot, `figures/codex_regrade_human/figure_A1.pdf` | `SI.tex:251–256` |
| S3 | Legacy category plot, `figures/codex_regrade_human/figure_A2.pdf` | `SI.tex:258–266` |

The new named `figure_S2` assets do not overwrite any of those files or the
existing A1/A2 renderers/assets. To include the requested heatmap as S2, insert
it after S1 and manually renumber the existing outcome/category figures to
S3/S4, or explicitly resolve their retention/order. Their existing missing-asset
references and workshop descriptions are not silently repaired by this update.

## Interpretation checks accompanying the new references

The Task 25 illustration retains full correctness 1.000 and process 0.875;
the current statement that this trial failed correctness checks for the binding
pose would conflict with the figure. The Task 29 illustration retains correctness
1.000 and process 0.9375; the shown pair is not established as the unique cause
of the log's non-finite force. The proposed captions preserve these distinctions.
These wording notes have not been applied to the manuscript.
