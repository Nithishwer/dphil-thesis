# Project context

- Repository: https://github.com/Nithishwer/dphil-thesis
- Local project: `/biggin/b211/reub0138/Projects/thesis`
- Main branch: `main`; remote: `origin`.
- Commits use Conventional Commits: `type(optional-scope): description`.
  Examples: `feat(template): add Harvard Physics thesis template`,
  `fix(layout): correct caption spacing`, `docs: update thesis context`.
- The thesis uses Harvard Dissertate, with appearance adapted from Zhaoxi Xiong's
  2019 dissertation: https://arxiv.org/pdf/1906.02892.
- Build with `sh scripts/build` (pdfLaTeX, BibTeX, and latexmk). The output is
  `dissertation.pdf`; generated LaTeX files and the compiled thesis PDF are not
  committed. Source figures, including PDFs, are versioned.
- Edit author and degree details in `frontmatter/personalize.tex`, chapter order
  in `dissertation.tex`, and formatting in `Dissertate.cls`.
- The current document contains editable sample content. Reference-layout
  checks matched identical title, abstract, and introduction text within
  0.001 PDF points. The sample compiles to 57 pages without LaTeX warnings.
- Preserve the repository's existing `LICENSE`; the upstream Dissertate license
  is retained separately in `LICENSE-Dissertate`.
