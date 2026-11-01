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
  Body text uses the class's 12 pt normal size; the copyright page's smaller
  font is scoped to that page. The default spacing factor remains 1.2.
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
- The current document contains editable sample content. Its layout follows the
  reference, with Latin Modern as the chosen font update. The sample compiles to
  70 pages; sample opening quotations report underfull boxes.
- Preserve the repository's existing `LICENSE`; the upstream Dissertate license
  is retained separately in `LICENSE-Dissertate`.
