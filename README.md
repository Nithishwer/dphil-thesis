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

The class uses Latin Modern text and mathematics with T1 text encoding, A4
paper, mirrored 35 mm inner and 30 mm outer margins, a 1.2 line-spacing factor,
crimson Palatino chapter numbers,
bold section headings, serif captions, and numbered citations in square brackets.
Chapter numbering starts at 1. Footnotes are numbered continuously; bibliography
entries use `unsrt` in citation order with compressed spacing.

Running headers and footers follow Tim Hempel's dissertation: even pages show
"Chapter N" at the upper left, odd pages show the chapter title at the upper
right, and page numbers sit below a short rule at the outer bottom corners.
Running headers and page numbers use 9-point text. Vertical spacing follows the
measured reference: 36.34 mm above the text area and 52.4 mm below it, with an
18.9 pt header separation and a 41.45 pt footer offset. Full text pages align
at the bottom of the text area.
Chapter-opening pages omit the running header. The layout is two-sided, with
chapters allowed to start on either page; appendices use "Appendix A", etc.
The wider inner margin reserves room for binding: it is on the left of odd
pages and the right of even pages. Both page types retain a left margin within
the quoted 30--35 mm requirement.

Compatibility adjustments preserve the published appearance: the caption
justification option is corrected, unavailable bold small caps in the contents
use their actual upright bold substitute, and the title-page offset is calibrated
against the PDF. An emergency line-breaking allowance prevents overfull lines
in the Latin sample text.

Latin Modern is the chosen update to the reference's Computer Modern typography.
The delivered sample compiles to 61 pages with no undefined citations, missing
glyphs, or overfull boxes. Sample opening quotations report underfull boxes.
Its page count and line breaks naturally depend on the sample content.

The repository's existing license is retained in `LICENSE`. The underlying
Dissertate AGPL license is included separately in `LICENSE-Dissertate`. Original
bundled font assets retain their own licenses; this appearance uses TeX's
standard fonts.
