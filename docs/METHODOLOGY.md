# Methodology Passport Card (version 2, Task 3)

**Title:** Academic Generative AI Use and Unintentional Procrastination: A Secondary Analysis of an Indian Higher-Education Survey

**Authors:** Ernur Kussain and Zhanassyl Zhakyp

**Public GitHub URL:** https://github.com/yernurkussain-source/TASK2_KUSSAIN_ZHAHYP

Version 1 of this card was submitted for Task 2. Version 2 corrects the author names, adds explicit reference groups and a baseline model, and records the Task 3 measurement design. The Task 2 hypotheses, variables and primary metric are unchanged.

## Design and Task 1 alignment

Quantitative, observational secondary analysis of public survey data. It operationalises the AI-use and procrastination strand (RQ2) of Task 1. The empirical setting is India and the outcome is unintentional procrastination; Kazakhstan remains a discussion context. The study does not directly test academic procrastination among Kazakhstani students, and no new participants are recruited.

## Research question and hypotheses

Is the frequency of academic GenAI use associated with unintentional procrastination in the selected sample?

H₀: Spearman ρ = 0. H₁: Spearman ρ ≠ 0. Two-sided α = 0.05. The plan was written after published findings from the source may have been seen, so it is not a prospective preregistration. The Task 3 parameters were fixed in `configs/research.yaml` before the main association was computed.

## Variables

| Role | Operational definition |
|---|---|
| Independent (predictor) | Academic AI-use frequency, ordinal: 1 = a few times a month, 2 = once a week, 3 = a few times a week, 4 = every day; 0 = rarely/never in Sensitivity B only. Measured, not manipulated. |
| Dependent | UPS total: sum of six items scored 1 to 4, range 6 to 24. Higher scores mean more unintentional procrastination. |
| Controlled analysis conditions | Source version and SHA-256 hashes, eligibility rules, scoring, complete-case rule, statistical procedures, seed 20261007, Python and package versions. |
| Covariates (supplementary model) | Age, gender, education category. They are adjusted for statistically, not held constant. |
| Pipeline benchmark (engineering) | Independent: implementation (Task 2 loop vs vectorised) and workload (50 to 2,000 records). Dependent: latency per run (ms). Controlled: bootstrap resamples (1,000), seed per run, warm-up count, machine. |

## Samples

| Sample | Source | Rule | n |
|---|---|---|---|
| Main | supplied cleaned workbook (300) | bachelor's or master's category, age ≥ 18 (15 Higher Secondary excluded) | 285 |
| Sensitivity A | raw workbook (355) | independent rules (consent, education, age ≥ 18, academic use = yes, frequency recorded, complete UPS; 3 inconsistent "no use but monthly frequency" answers excluded) | 303 |
| Sensitivity B | raw workbook (355) | as A, with rarely/never respondents kept as level 0 | 327 |

The categories combine graduates and current students, so current enrolment cannot be established. Convenience sampling and online recruitment limit generalisation.

## Metrics, baselines and guardrails

Primary metric: Spearman ρ between AI-use frequency and UPS total, with n, asymptotic two-sided p, a 10,000-permutation p and a 95% percentile bootstrap CI (10,000 resamples, seed 20261007).

Secondary metrics: Kruskal–Wallis H and ε²; per-level median, p25, p75, p95, p99 and mean ± SD with bootstrap CIs; median difference and Cliff's δ against the reference group with Holm-adjusted Mann–Whitney p.

Baselines:

1. Statistical null, ρ = 0.
2. Reference group: the lowest-use level (a few times a month in the main sample; rarely/never in Sensitivity B). This answers the Task 2 feedback that the card had no reference group.
3. Baseline model: OLS of UPS on age, gender and education, compared with the proposed model that adds AI-use frequency (R², ΔR², nested F test, HC3 standard errors).
4. Literature reference: Abbas et al. (2024), β = 0.309 for ChatGPT use and general procrastination (different scale, so used only as a rough comparison).
5. Engineering baseline: the unchanged Task 2 loop bootstrap, compared with the vectorised implementation on identical inputs.

Decision rule: reject H₀ when p < 0.05 and every guardrail passes. A non-rejection would not be read as evidence of no association.

Survey guardrails: zero invalid or missing required values, zero duplicate IDs, all totals within 6 to 24, exact agreement of computed and supplied totals (300 of 300), at least 95% valid bootstrap resamples, no constant variable. Any failure stops the analysis.

Pipeline guardrails: unexpected error rate = 0; every injected invalid batch rejected; identical estimates from both implementations (tolerance 10⁻⁹). Warm-up runs are excluded, and IQR outliers are flagged but kept.

## Analysis plan

1. Download and hash-check both workbooks (`src/fetch_data.py`).
2. Code, apply eligibility rules and audit totals (`src/process_data.py`, `prepare`).
3. Collect benchmark timings with warm-up and benchmark phases (`src/collector.py`).
4. Aggregate statistics, write `data/processed/metrics_summary.csv` and `reports/results.json` (`src/process_data.py`, `run_analysis`).
5. Render figures (`src/visualize.py`) and execute `notebooks/01_data_analysis.ipynb`.

## Validity

Internal validity is limited by cross-sectional self-report, possible confounding (for example workload) and reverse causation. Construct validity is limited because UPS measures unintentional procrastination rather than academic procrastination. External validity is limited by convenience recruitment in India. The two raw-file sensitivity analyses address the authors' unexplained exclusions. Fixed software, hashes and seeds give computational reproducibility but do not remove these biases. Relevance to Kazakhstan is treated as a transferability question.

## Data and software

Source: Sharma et al. (2026), Mendeley Data V1, https://doi.org/10.17632/88pv88j8jb.1, CC BY 4.0. Original code is MIT licensed. Derived files keep only analysis variables and exclude initials, academic-dishonesty items and domicile.

Exact package pins are in `requirements.txt` and `requirements-lock.txt`. Execution checks are recorded in `docs/VALIDATION.md`.
