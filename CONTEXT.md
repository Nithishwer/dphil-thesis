# Project context

- Repository: https://github.com/Nithishwer/dphil-thesis
- Local project: `/biggin/b211/reub0138/Projects/thesis`
- Main branch: `main`; remote: `origin`.
- Commits use Conventional Commits: `type(optional-scope): description`.
  Examples: `feat(template): add Harvard Physics thesis template`,
  `fix(layout): correct caption spacing`, `docs: update thesis context`.
- The thesis uses Harvard Dissertate, with appearance adapted from Zhaoxi Xiong's
  2019 dissertation: https://arxiv.org/pdf/1906.02892.
- Use Latin Modern (`lmodern`) for text and mathematics, with T1 text encoding.
  Large chapter numbers retain the reference's crimson Palatino Bold.
- Body running headers and footers follow Tim Hempel's dissertation: chapter
  labels on even pages, titles on odd pages, and outer page numbers below short
  rules. Running headers and page numbers are 9 pt, matching Hempel's PDF.
  A4 paper uses 36.34 mm top and 52.4 mm bottom text-area margins, 18.9 pt
  `headsep`, 41.45 pt `footskip`, and `flushbottom`. Mirrored side margins are
  35 mm inside and 30 mm outside, reserving binding space while keeping each
  page's left margin within 30--35 mm. The class uses `twoside, openany`;
  chapter openings omit headers.
- Build with `sh scripts/build` (pdfLaTeX, BibTeX, and latexmk). The output is
  `dissertation.pdf`; generated LaTeX files and the compiled thesis PDF are not
  committed. Source figures, including PDFs, are versioned.
- Edit author and degree details in `frontmatter/personalize.tex`, chapter order
  in `dissertation.tex`, and formatting in `Dissertate.cls`.
- Each chapter and appendix has its own folder under `chapters/`, containing the
  matching `.tex` file and separate `data/`, `scripts/`, and `figures/`
  subfolders. Keep processing and plotting entry points directly in `scripts/`
  and working files in `scripts/intermediates/`, grouped by figure or workflow;
  do not nest `figures/`, `analysis/`, or `data/` folders inside `scripts/`.
  Figure paths are relative to the repository root; empty asset
  folders are preserved with `.gitkeep`. Root `scripts/build` is shared.
  Thesis Figure 7.9 is an exception to the script layout: its generator and
  rendered outputs are together in Chapter 7's `figures/figure_7_9/`, as requested.
- Chapter `data/` folders are local-only and ignored by Git. Keep their contents
  on disk; version thesis sources, Python scripts, and figures. Fresh clones
  require a separate data copy to regenerate plots. Back up data in other
  existing checkouts before pulling the commit that untracks these folders,
  because Git can remove their previously tracked files during that pull.
- `pyproject.toml` and `uv.lock` define the plotting-only uv project:
  Matplotlib, NumPy, pandas, SciPy, Pillow, Seaborn, and scikit-learn. Use `uv sync --locked`, then
  `uv run --locked python <chapter-script>`. `.venv/` is local and ignored.
- Chapter 7 assets were copied from
  `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena-RSC-Comms` on 2026-11-22
  (source commit `8ea34464dd0135f7e184d4739c1b953b0e109c02`, including untracked
  molecular-panel assets). Its `data/source_manifest.csv` records the source
  path, destination, and original SHA-256 for each retained imported file.
  Active scripts live directly in `scripts/` and use the chapter's data and
  figure folders; prepared coordinates, PyMOL sessions, generated tables, and
  validation records live in `scripts/intermediates/`. The original three flat PDF
  figure paths used by the thesis draft are retained. See the chapter README.
- The nine main-text figures of Anand et al. (JCTC 2026,
  DOI `10.1021/acs.jctc.6c01161`) were imported from
  `/biggin/b211/reub0138/Projects/orexin/figures` on 2026-11-22. Paper Figures
  1/5/6 are in Chapter 3, 2/3/4 in Chapter 4, and 7/8/9 in Chapter 5. Each chapter
  has `data/orexin_source_manifest.csv` with source paths, destinations, and
  original hashes, plus an asset README. Publication SVGs and existing Chapter 3
  figures are preserved; PDF exports are included in LaTeX with captions and
  CC BY attribution. Data and plotting scripts use chapter paths. Molecular
  sessions and prepared structures are in `scripts/intermediates/`. Chapter 4
  documents the archived TPR's incompatibility
  with MDAnalysis 2.11.0; the original prepared structures remain available.
- The same paper's 13 SI figures were imported on 2026-11-23 into Appendix A,
  in published S1–S13 order, with chapter references and CC BY attribution. The
  ten-panel S6/S7/S10/S11/S12 figures use `pdflscape` landscape pages. The appendix
  README maps the source directory names to the published numbering, and its
  `data/orexin_source_manifest.csv` records copies and reused Chapter 4 occupancy
  and Chapter 5 REUS inputs. Original figure sources and frozen data remain
  unchanged; the 16 scripts use local paths and write new plots separately from
  the publication figures. Scikit-learn supports the original clustering code.
- Chapters are numbered consecutively from 1 to 8, matching their filenames:
  Introduction; Theory and Methods; Benchmarking and System Preparation;
  Binding Pocket Resolvation; Apo-State Conformational Changes; ABFEs on Agonists;
  Automating ABFEs with AI Agents; Conclusion. Supporting Information is Appendix A.
- Chapters and the appendix retain placeholder prose, with published figures in
  Chapters 3–5. Chapter 7 preserves the existing AI-agents draft. Its layout
  follows the reference, with Latin Modern as the chosen font update.
- Preserve the repository's existing `LICENSE`; the upstream Dissertate license
  is retained separately in `LICENSE-Dissertate`.
