# Harvard Physics thesis template

Project repository: [Nithishwer/dphil-thesis](https://github.com/Nithishwer/dphil-thesis).
Repository details and the Conventional Commits convention are recorded in
[CONTEXT.md](CONTEXT.md).

Harvard Dissertate, adjusted to the appearance of Zhaoxi Xiong's 2019 thesis,
[Classification and Construction of Topological Phases of Quantum Matter](https://arxiv.org/pdf/1906.02892).
The class is adapted directly from the [public LaTeX source](https://arxiv.org/src/1906.02892).
The underlying template is [suchow/Dissertate](https://github.com/suchow/Dissertate),
also linked by [Harvard Physics](https://www.physics.harvard.edu/academics/thesishelp).

## Build

From this directory, run:

```sh
sh scripts/build
```

Equivalent command:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error dissertation.tex
```

Output: `dissertation.pdf`. The build uses pdfLaTeX, BibTeX, and latexmk, matching
the reference's pdfLaTeX engine. Required LaTeX packages are available on this
machine; no external font installation is needed.

## Edit

- `dissertation.tex`: main document, chapter order, and appendix.
- `frontmatter/personalize.tex`: title, author, advisor, degree, and date.
- `frontmatter/`: abstract, previous publications, and acknowledgments.
- `chapters/`: sample chapters and appendix.
- `references.bib`: bibliography entries.
- `Dissertate.cls`: typography and page layout.

The department and field are Physics. Names, dates, and text remain editable
sample placeholders. The copyright year follows `degreeyear` automatically.
The reference's front matter includes lists of tables and figures and a previous
publications page. To omit the latter, remove the `\previousworks` call in the
class's `\frontmatter` definition. The dedication and illustrated colophon are
omitted from the compiled document, as in the reference.

## Appearance

The class uses the reference's Computer Modern text and mathematics, US Letter
paper, 1.2-inch margins, 1.2 line-spacing factor, crimson Palatino chapter numbers,
bold section headings, serif captions, and numbered citations in square brackets.
Chapter numbering starts at 1. Footnotes are numbered continuously; bibliography
entries use `unsrt` in citation order with compressed spacing.

Compatibility adjustments preserve the published appearance: the caption
justification option is corrected, unavailable bold small caps in the contents
use their actual upright bold substitute, and the title-page offset is calibrated
against the PDF. An emergency line-breaking allowance prevents overfull lines
in the Latin sample text.

Verification with identical text in a temporary document matched the published
title, abstract, and opening introduction excerpt to within 0.001 PDF points in
word positions. The delivered sample compiles to 57 pages with no LaTeX warnings,
undefined citations, missing glyphs, or overfull boxes. Its page count and line
breaks naturally depend on the sample content.

The repository's existing license is retained in `LICENSE`. The underlying
Dissertate AGPL license is included separately in `LICENSE-Dissertate`. Original
bundled font assets retain their own licenses; this appearance uses TeX's
standard fonts.
