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
  subfolders. Figure paths are relative to the repository root; empty asset
  folders are preserved with `.gitkeep`. Root `scripts/build` is shared.
- Chapter 7 assets were copied from
  `/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena-RSC-Comms` on 2026-11-22
  (source commit `8ea34464dd0135f7e184d4739c1b953b0e109c02`, including untracked
  molecular-panel assets). Its `data/source_manifest.csv` records the source
  path, destination, and original SHA-256 for each imported file. Active plotting
  scripts use the chapter's data and figure folders; original audit/export
  scripts are preserved under `scripts/upstream/`. The original three flat PDF
  figure paths used by the thesis draft are retained. See the chapter README.
- Chapters are numbered consecutively from 1 to 8, matching their filenames:
  Introduction; Theory and Methods; Benchmarking and System Preparation;
  Binding Pocket Resolvation; Apo-State Conformational Changes; ABFEs on Agonists;
  Automating ABFEs with AI Agents; Conclusion. Supporting Information is Appendix A.
- Chapters and the appendix are minimal templates with titles, labels, and TODOs,
  except Chapter 7, which preserves the existing AI-agents draft. Its layout
  follows the reference, with Latin Modern as the chosen font update.
- Preserve the repository's existing `LICENSE`; the upstream Dissertate license
  is retained separately in `LICENSE-Dissertate`.
