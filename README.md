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
- `chapters/`: one folder per chapter and appendix, each containing its `.tex`
  source and separate `data/`, `scripts/`, and `figures/` folders.
- `references.bib`: bibliography entries.
- `Dissertate.cls`: typography and page layout.

For example, Chapter 1 is organized as:

```text
chapters/Ch1-Introduction/
├── Ch1-Introduction.tex
├── data/
├── scripts/
└── figures/
```

Keep input data in `data/`, processing and plotting scripts directly in
`scripts/`, and figure outputs in `figures/` within the relevant chapter.
Keep working files (prepared structures, sessions, generated tables, and
validation records) in `scripts/intermediates/`, grouped by figure or workflow.
Do not recreate `figures/`, `analysis/`, or `data/` trees inside `scripts/`.
Figure paths in LaTeX are
relative to the repository root, for example
`chapters/Ch1-Introduction/figures/example.pdf`. Empty asset folders contain a
`.gitkeep` file so Git preserves them. The root `scripts/build` remains the
shared thesis build command.

## Plotting

The repository has a uv project for plotting, with Matplotlib, NumPy, pandas,
SciPy, and Pillow. Install the locked environment from the repository root:

```sh
uv sync --locked
```

Run a chapter script in that environment, for example:

```sh
chapter=chapters/Ch7-Automating-ABFEP-calculations-with-AI-agents
uv run --locked python "$chapter/scripts/make_figure_3.py"
```

Alternatively, activate it with `source .venv/bin/activate`. The environment is
local and ignored by Git; `pyproject.toml` and `uv.lock` record the dependencies.

Chapter 7's data, scripts, and figure assets were copied from
`/biggin/b211/reub0138/Projects/LLMsxFEP/MDArena-RSC-Comms`. Its
[asset README](chapters/Ch7-Automating-ABFEP-calculations-with-AI-agents/README.md)
describes the imported layout, plotting commands, and upstream tools that need
their original scientific environment.

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
Chapter filenames and headings follow this order:

1. Introduction
2. Theory and Methods
3. Benchmarking and System Preparation
4. Binding Pocket Resolvation
5. Apo-State Conformational Changes
6. ABFEs on Agonists
7. Automating ABFEs with AI Agents
8. Conclusion

Chapters are minimal templates with a title, label, and content TODO, except for
Chapter 7, which retains the existing AI-agents draft. Supporting Information
follows as Appendix A. The page count and line breaks depend on the content.

The repository's existing license is retained in `LICENSE`. The underlying
Dissertate AGPL license is included separately in `LICENSE-Dissertate`. Original
bundled font assets retain their own licenses; this appearance uses TeX's
standard fonts.
