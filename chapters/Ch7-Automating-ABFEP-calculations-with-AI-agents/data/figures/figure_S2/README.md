# Figure S2: unchanged twelve-configuration task heatmap

`figure_S2.pdf` and `figure_S2.png` are **byte-identical copies** of:

```text
analysis/task39_policy_b_2026-11-20/current/figures/task_heatmap_all_twelve.pdf
analysis/task39_policy_b_2026-11-20/current/figures/task_heatmap_all_twelve.png
```

No plotting, grading, style, label, task-order or data changes are made.
`copy_manifest.json` records source/destination paths and SHA256 checksums.
`caption.md` contains a proposed caption. Reproduce from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python figures/figure_S2/copy_figure_S2.py
```

The script refuses to replace existing destination files with different content.

**Numbering conflict:** `SI.tex` currently numbers its second figure (the legacy
outcome plot at `figures/codex_regrade_human/figure_A1.pdf`) as S2 through the
automatic S-prefixed counter. That figure, its counterpart A2, their scripts,
and all TeX files remain untouched. The new `figure_S2` directory did not exist.
Before including this heatmap as S2, manually move the existing outcome/category
figures to S3/S4 or otherwise resolve their numbering. See
`../figure_5/manuscript_reference_notes.md` for all required reference updates.
