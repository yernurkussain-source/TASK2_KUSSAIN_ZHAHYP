# Academic GenAI Use and Unintentional Procrastination

Authors: Kussain and Zhahyp

## Overview

A reproducible secondary-analysis pipeline for an Indian higher-education survey. The research asks whether academic GenAI use frequency is associated with unintentional procrastination. This is an observational association study, not a causal experiment. Kazakhstan is a discussion context, not the origin of the observations.

This Task 2 package runs on ten explicitly synthetic records. It contains no research findings and no participant initials. The real-data analysis and raw-data sensitivity analysis are planned for the subsequent research stage.

## Research question and hypotheses

Is academic GenAI use frequency associated with unintentional procrastination in the selected sample?

H0: population Spearman correlation rho = 0.
H1: population Spearman correlation rho != 0.

The source is a convenience sample. Statistical inference is model-based and does not make it nationally representative.

## System requirements

Tested environments: Python 3.12.14 on Linux and Python 3.13.7 on Windows, both with NumPy 2.3.5 and SciPy 1.17.0. Package versions are pinned in requirements.txt. Internet is required for dependency installation; the sample benchmark runs offline.

A standard CPU computer is sufficient for the sample pipeline; no GPU is required. Use an isolated Python environment. Jupyter is optional and is not required to run the scripts. macOS execution has not been verified.

## Quickstart

From the repository root, using an activated virtual environment with Python 3.12.14 or 3.13.7:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/benchmark.py --config configs/sample.json
```

Outputs: `outputs/sample/results.json` and `outputs/sample/scored.csv`. The results include an input checksum, configuration checksum, package versions, seed, sample size, rho, asymptotic two-sided p-value, bootstrap interval, guardrail outcomes and runtime. Repeated runs reproduce statistical outputs; runtime may differ.

### Docker alternative

```bash
docker build -t task2-kussain-zhahyp .
docker run --rm task2-kussain-zhahyp
```

The result is printed to the console; container files are removed with the container. To retain them, use a bind mount, for example on macOS/Linux: `docker run --rm -v "$PWD/outputs:/app/outputs" task2-kussain-zhahyp`.
Docker build and container execution were successfully verified on Windows using Docker Desktop with Linux containers on 2026-10-11. The synthetic benchmark completed with exit code 0 using Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0.

## Structure

```text
configs/             Experiment parameters
src/benchmark.py     Validation, scoring and measurement
src/__init__.py      Package marker
data/sample/         Ten synthetic test records
data/processed/      Local research CSV destination (ignored)
docs/                Methodology, coding and validation notes
notebooks/           Optional exploratory work
tests/               Scoring and error-handling checks
requirements.txt     Exact package versions
Dockerfile           Container recipe
LICENSE              MIT license for original code
```

## Planned benchmarks

| Run                  | Input                                            | Measurement                                                | Status                   |
| -------------------- | ------------------------------------------------ | ---------------------------------------------------------- | ------------------------ |
| Smoke test           | 10 synthetic rows                                | Valid scoring and output generation                        | Implemented              |
| Validation tests     | Invalid and known-answer fixtures                | Reject invalid records, verify totals and rank correlation | Implemented              |
| Main analysis        | 285 eligible rows from supplied cleaned file     | Spearman rho, 95% CI, two-sided p                          | Planned                  |
| Sensitivity analysis | Raw responses under documented eligibility rules | Compare association and exclusions with main analysis      | Planned                  |
| Adjusted analysis    | Age, gender and education covariates             | Supplementary adjusted association                         | Planned; not implemented |

## Interpretation

Frequency codes are ordinal, not equal time intervals. UPS measures unintentional procrastination, not specifically academic procrastination. A statistically non-significant result does not prove no association. The p-value is an asymptotic approximation and is unsuitable for substantive conclusions from the ten-row smoke test. The 95% interval is a paired percentile bootstrap; degenerate resamples are counted and skipped, and the run fails if fewer than 95% are valid.

## Citation and data license

Sharma, P., Nandy, D., Ramchandani, G., James, A., Batra, M., & Dhanda, R. (2026). Datasheets for Role of Generative Artificial Intelligence Usage on Academic Dishonesty Among Indian Undergraduate and Postgraduate Students. Mendeley Data, V1. https://doi.org/10.17632/88pv88j8jb.1

Dataset: https://data.mendeley.com/datasets/88pv88j8jb/1 (CC BY 4.0, as stated by the repository). This is a published dataset; a corresponding peer-reviewed article has not been verified. Attribute the dataset separately when using it. The MIT license here covers our original code and synthetic fixture, not the source dataset or its questionnaire instruments.

## Team workflow and submission

Both authors should review the methodology and contribute actual changes under their own GitHub accounts. Suggested division: Kussain reviews code/configuration and execution; Zhahyp reviews data coding, source attribution and documentation. These are proposed roles, not claims of completed contributions. Keep descriptive commits and never manufacture a contribution history.

Public repository: https://github.com/yernurkussain-source/TASK2_KUSSAIN_ZHAHYP

Submit the current docs/METHODOLOGY.md file, or its PDF export, together with the public repository URL to LMS. Before submission, verify that the repository opens without signing in and that the submitted card matches the repository version.

## Expected smoke-test output (SS6)

The synthetic fixture has n = 10 and UPS totals `[10, 14, 16, 21, 16, 9, 14, 15, 21, 15]` in input order. With the supplied seed and 1,000 resamples, rho is approximately 0.477934 and the asymptotic p-value approximately 0.162379. These numbers are software checks only, not research evidence. Runtime is machine-dependent.

## Dataset citation (BibTeX)

```bibtex
@misc{sharma2026genai,
  author = {Sharma, Payal and Nandy, Debopriya and Ramchandani, Gungun and James, Ashlin and Batra, Megha and Dhanda, Rhythm},
  title = {Datasheets for Role of Generative Artificial Intelligence Usage on Academic Dishonesty Among Indian Undergraduate and Postgraduate Students},
  year = {2026},
  publisher = {Mendeley Data},
  version = {1},
  doi = {10.17632/88pv88j8jb.1},
  url = {https://doi.org/10.17632/88pv88j8jb.1}
}
```

## First GitHub publication

Create an empty public GitHub repository named `TASK2_KUSSAIN_ZHAHYP` without adding another README or license. From this folder, run the following after replacing YOUR_USERNAME with the actual owner account. Git must already be installed and authenticated.

```bash
git init -b main
git add .
git diff --cached --stat
git commit -m "Add methodology and tested synthetic analysis pipeline"
git remote add origin https://github.com/YOUR_USERNAME/TASK2_KUSSAIN_ZHAHYP.git
git push -u origin main
```

Before committing, inspect the staged list: no original survey workbooks, credentials, virtual environments or generated outputs should appear. Use each contributor's own account for their genuine changes. Add the teammate as a collaborator through the repository settings; sharing a login is unnecessary. Insert the actual repository URL into the methodology card and commit that update.

## Five-point submission audit

- [ ] The card contains the real public repository URL and the correct two authors.
- [ ] A fresh checkout runs the three Quickstart commands and writes both expected output files.
- [ ] The environment record states what was actually verified; if using Docker, its build and run have been verified.
- [ ] The repository includes configuration, tests, ten synthetic rows, attribution and license, with sensitive or generated files excluded.
- [ ] The public link opens without signing in, genuine contributions are visible, and the submitted card matches the repository version.
