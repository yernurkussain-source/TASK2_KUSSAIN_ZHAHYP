# Validation record

Entries are in date order. Each one states what was run, where, and what it does not cover.

## Task 2

### 2026-10-07, preparation environment (Linux)

* Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0 (packages already installed).
* Seven unit tests passed: known UPS totals, invalid and missing items, duplicate IDs, education eligibility, constant variables, a known negative rank correlation and seed repeatability.
* The ten-row synthetic benchmark wrote `scored.csv` and `results.json`; all 1,000 bootstrap resamples were valid; runtime was about 0.4 s.
* Docker was not available in this environment on this date (see 2026-10-11).

### 2026-10-08, Windows (Ernur Kussain)

* Python 3.13.7 in a fresh virtual environment; dependencies installed from `requirements.txt`.
* All seven unit tests passed and the synthetic benchmark completed (0.423 s) with zero invalid records, missing values or duplicate IDs.

### 2026-10-11, Docker Desktop on Windows (Linux containers)

* Docker CLI 29.8.2; the image built, including the unit-test step.
* Container: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0; ten synthetic records; 1,000 valid resamples; exit code 0; runtime 0.6274 s.

These checks covered the software pipeline only. No research hypothesis was tested in Task 2.

## Task 3: data collection and analysis

### 2026-10-28, source data

* Both workbooks were downloaded from Mendeley Data V1. SHA-256 hashes match the values Mendeley publishes for the files: raw `a8fdc7e5…0883` (98,483 bytes, 355 responses) and cleaned `dac25b20…1593` (145,416 bytes, 300 responses).
* The public download URL redirects to Mendeley's public S3 bucket and returns the same bytes without a login, so `src/fetch_data.py` needs only internet access.
* Coding audit: all 300 computed UPS totals equal the supplied `Procrastination` column; main sample n = 285, Sensitivity A n = 303, Sensitivity B n = 327. Four raw age entries were normalised ("22 years", "21 years", "23+", "21+").

### 2026-10-28, benchmark collection (preparation environment)

* Linux container, Intel Xeon @ 2.80 GHz, 2 logical CPUs, 7.84 GB RAM, Python 3.12.3, NumPy 2.3.5, SciPy 1.17.0, pandas 2.3.3; not inside Docker.
* `python src/collector.py` wrote 420 records in 121.6 s: 60 warm-up and 360 benchmark records; 25 invalid batches were injected (50 timed records, one per implementation) and all were rejected; 0 unexpected errors.
* On the 155 paired runs with identical inputs, both implementations returned the same ρ and interval limits (largest absolute difference 2.2 × 10⁻¹⁶).
* The committed log comes from this environment. Re-running the collector on another machine changes the latency values but should not change the guardrail results.

### 2026-10-28, analysis, notebook and figures

* 24 unit tests passed on Python 3.12.3 and on Python 3.13.18 (Linux). Without the source workbooks one test is skipped by design (the re-coding check).
* Fresh-checkout test: the tracked files were cloned into an empty folder, `requirements.txt` was installed into a new Python 3.13 virtual environment, and the three Quickstart commands ran without errors in 9.1 s (peak memory 343 MB). Every CSV and figure was byte-identical to the committed files; only the Python version line in `reports/results.json` differed.
* `requirements-lock.txt` installed into a new Python 3.12 environment; tests and pipeline passed and reproduced all committed outputs exactly.
* `notebooks/01_data_analysis.ipynb` was executed top to bottom with nbconvert on Python 3.12 (with workbooks) and on Python 3.13 (without workbooks): execution counts 1 to 12 in order, no errors.
* All five figures exist as PDF and 300 DPI PNG and were inspected visually for axis units, uncertainty display, legend placement and grayscale-distinguishable markers. The seaborn colour-blind colours used were checked with a palette validator (CVD separation passed).
* Not verified here: `docker build`, because Docker Hub is not reachable from the preparation environment. The Dockerfile now installs `requirements-lock.txt` and runs `src/run_pipeline.py`, so it has to be rebuilt and run on a machine with Docker before the final submission. Windows execution of the Task 3 scripts has not been verified yet either.

## Task 3: domain model and report

### 2026-11-02, domain model, results section and report (preparation environment)

* `docs/domain_model.md`: all 137 LaTeX expressions (display and inline) parse with KaTeX 0.16.11 without errors; the Mermaid C4 diagram renders with Mermaid CLI 11.16.0 and is exported to `reports/figures/domain_c4_container.pdf` and `.png`.
* `src/build_report.py` fills `reports/paper_section_4.md` and the LaTeX inputs from `reports/results.json` and `data/processed/`; no placeholder remains, and the tests check that the reported primary estimate equals the value in `results.json`.
* `reports/latex/task3_report.tex` compiles with `latexmk -pdf` (pdfTeX, TeX Live) without errors, overfull boxes or undefined references: 9 pages, all fonts embedded. The compiled file is `reports/TASK3_KUSSAIN_ZHAKYP_REPORT.pdf`.
* The figure titles no longer carry their own numbers, so the captions in the report and in `paper_section_4.md` do the numbering. Figure 6 (four panels, (a) to (d)) was added; all six figures exist as PDF and 300 DPI PNG.
* 29 unit tests passed on Python 3.12.3 and 3.13.18 (Linux). In a fresh clone with Python 3.13, the pipeline, the notebook (13 code cells, in order, no errors) and the LaTeX build all ran; the figures, the results section and the LaTeX inputs were identical to the committed versions. The processed CSVs differed only in the last floating-point digits between machines.
* Not verified in this environment: `docker build` and `docker run` (see the next entry).

### 2026-11-02, Windows and Docker Desktop (Ernur Kussain)

* Windows, Python 3.13.7 virtual environment: all 29 unit tests passed in 7.2 s with the source workbooks present, so the re-coding check ran as well.
* `docker build -t task3-kussain-zhakyp .` completed on Docker Desktop (Linux containers) from `python:3.12.14-slim` (digest `f77ac9e4…e51f`), with dependencies installed from `requirements-lock.txt` and the unit-test step passing inside the image.
* `docker run --rm task3-kussain-zhakyp` ran the pipeline from the committed processed CSVs and benchmark log in 10.3 s: n = 285, ρ = 0.2829, 95% CI [0.1771, 0.3835], p = 1.211 × 10⁻⁶, identical to `reports/results.json`. It wrote all six figures (PDF and PNG), `reports/paper_section_4.md` and the LaTeX inputs inside the container.
* The workbooks are excluded by `.dockerignore`, so the container does not re-code the survey data; that step is covered by the Windows test run above.

### 2026-11-03, check of the tagged release (preparation environment)

* The tag `v1.0-task3` was cloned from GitHub into an empty folder; the 29 tests passed and the pipeline ran. The check found three problems, now fixed:
  * Figure 4 showed an empty box instead of the subscript in "H₀" when rendered on macOS, because seaborn picks Arial where it is installed and Arial has no subscript zero. `src/visualize.py` now uses DejaVu Sans, which ships with Matplotlib, so the figures look the same on Windows, macOS, Linux and in Docker. A new test renders Figure 4 and fails on any missing-glyph warning.
  * In Figure 6(b) the legend covered the upper end of the main interval; it now sits between the rows.
  * `reports/results.json` still held the hash of an earlier `configs/research.yaml` (the file had changed only in a comment). It was regenerated, and `config_sha256` now matches the committed config.
* The notebook had been executed with Python 3.14.2 and its output contained the font warnings and a local path; it was executed again (13 code cells, in order, no errors or warnings).
* After the fixes, 30 unit tests passed (Python 3.13.18, Linux, workbooks present). All six figures were regenerated and checked visually, and the report was recompiled (9 pages, no warnings, all fonts embedded). The reported results are unchanged; the processed CSVs differ from the previous version only in the last floating-point digits.
