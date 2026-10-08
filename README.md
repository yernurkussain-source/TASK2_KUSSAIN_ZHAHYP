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
Python 3.12.14; NumPy 2.3.5; SciPy 1.17.0. Internet is required to install dependencies, but the benchmark runs offline. Dependencies and their transitive runtime dependency (NumPy for SciPy) are pinned in requirements.txt. Use an isolated environment if your system already has Python packages installed.

Supported target: a standard CPU computer with Python 3.12.14 on Linux, macOS or Windows; no GPU is required. Direct execution was checked in the preparation Linux environment. Hardware-specific performance claims are not made. Jupyter is optional and is not needed by this command-line pipeline.

## Quickstart
From the extracted repository root, with Python 3.12.14 available:

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
Docker was unavailable in the preparation environment, so the container build is not yet verified. The test and benchmark commands were tested directly with the exact installed versions; fresh dependency installation was not tested. The Python image tag pins the interpreter release; a base-image digest should be recorded after the first successful build for stricter container reproducibility.

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
| Run | Input | Measurement | Status |
| --- | --- | --- | --- |
| Smoke test | 10 synthetic rows | Valid scoring and output generation | Implemented |
| Validation tests | Invalid and known-answer fixtures | Reject invalid records, verify totals and rank correlation | Implemented |
| Main analysis | 285 eligible rows from supplied cleaned file | Spearman rho, 95% CI, two-sided p | Planned |
| Sensitivity analysis | Raw responses under documented eligibility rules | Compare association and exclusions with main analysis | Planned |
| Adjusted analysis | Age, gender and education covariates | Supplementary adjusted association | Planned; not implemented |

## Interpretation
Frequency codes are ordinal, not equal time intervals. UPS measures unintentional procrastination, not specifically academic procrastination. A statistically non-significant result does not prove no association. The p-value is an asymptotic approximation and is unsuitable for substantive conclusions from the ten-row smoke test. The 95% interval is a paired percentile bootstrap; degenerate resamples are counted and skipped, and the run fails if fewer than 95% are valid.

## Citation and data license
Sharma, P., Nandy, D., Ramchandani, G., James, A., Batra, M., & Dhanda, R. (2026). Datasheets for Role of Generative Artificial Intelligence Usage on Academic Dishonesty Among Indian Undergraduate and Postgraduate Students. Mendeley Data, V1. https://doi.org/10.17632/88pv88j8jb.1

Dataset: https://data.mendeley.com/datasets/88pv88j8jb/1 (CC BY 4.0, as stated by the repository). This is a published dataset; a corresponding peer-reviewed article has not been verified. Attribute the dataset separately when using it. The MIT license here covers our original code and synthetic fixture, not the source dataset or its questionnaire instruments.

## Team workflow and submission
Both authors should review the methodology and contribute actual changes under their own GitHub accounts. Suggested division: Kussain reviews code/configuration and execution; Zhahyp reviews data coding, source attribution and documentation. These are proposed roles, not claims of completed contributions. Keep descriptive commits and never manufacture a contribution history.

Create a public repository named `TASK2_KUSSAIN_ZHAHYP`, upload these files including dotfiles, add its actual URL to docs/METHODOLOGY.md, and verify the Quickstart from a fresh download. Submit that Markdown card and the public repository URL to LMS. GitHub publication and the final URL are pending.

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
