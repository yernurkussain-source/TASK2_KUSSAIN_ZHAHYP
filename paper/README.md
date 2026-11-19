# IEEE conference paper

Four-page IEEE paper (`\documentclass[conference]{IEEEtran}`, IMRaD structure) built from the analysis outputs of this repository. The compiled PDF is [`KUSSAIN_ZHAKYP_IEEE_PAPER.pdf`](KUSSAIN_ZHAKYP_IEEE_PAPER.pdf).

## Files

```text
main.tex                      Preamble, title, abstract, keywords, \input of the sections, bibliography
sections/01_introduction.tex  Context, gap, research questions RQ1-RQ3, contributions, outline
sections/02_methodology.tex   Data and samples, estimators and baselines, pipeline and benchmark (Fig. 1, Table I)
sections/03_results.tex       Setup, RQ1-RQ3 results (Tables II-III, Figs. 2-3), discussion
sections/04_conclusion.tex    Threats to validity, conclusion and future work
references.bib                18 BibTeX entries checked against Crossref/DataCite, clutter fields removed
make_assets.py                Writes generated/ from reports/results.json and data/processed/
generated/                    values.tex, paper_values.tex (number macros), fig_effects.pdf, fig_latency.pdf
```

No number in the text is typed by hand: the sections use the macros in `generated/values.tex` (written by `src/build_report.py`) and `generated/paper_values.tex`.

## Build

From the repository root, after `python src/run_pipeline.py`:

```bash
python paper/make_assets.py
cd paper && latexmk -pdf main.tex
cp main.pdf KUSSAIN_ZHAKYP_IEEE_PAPER.pdf
```

TeX Live needs the `IEEEtran`, `cite`, `booktabs` and `pgf/tikz` packages (all in a full TeX Live installation and on Overleaf).

## Overleaf

Upload the contents of `paper/` (including `generated/`) as a new project and compile `main.tex` with pdfLaTeX. Zotero users can import `references.bib` (File > Import) and keep the same citation keys with Better BibTeX.
