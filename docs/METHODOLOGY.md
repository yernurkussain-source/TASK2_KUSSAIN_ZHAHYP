# Methodology Passport Card

**Title:** Academic Generative AI Use and Unintentional Procrastination: A Secondary Analysis of an Indian Higher-Education Survey

**Authors:** Kussain and Zhahyp

**Public GitHub URL:** https://github.com/yernurkussain-source/TASK2_KUSSAIN_ZHAHYP

## Design and Task 1 alignment

Quantitative, observational secondary analysis. This operationalizes the AI-use/procrastination strand of Task 1. It changes the empirical setting to India and the outcome to unintentional procrastination; Kazakhstan remains a discussion context. It does not directly test academic procrastination among Kazakhstani students. No new participants are recruited.

## Research question and hypotheses

Is frequency of academic GenAI use associated with unintentional procrastination in the selected sample?

H0: Spearman rho = 0. H1: Spearman rho != 0. Two-sided alpha = 0.05. This analysis plan is written after published source findings may have been encountered, and is not a prospective preregistration.

## Variables

| Role                           | Operational definition                                                                                                           |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Independent/predictor          | Reported academic AI-use frequency, ordered 1–4 from a few times a month to every day. Measured, not manipulated.                |
| Dependent                      | UPS sum of six responses scored 1–4, total 6–24. Higher scores indicate more unintentional procrastination.                      |
| Controlled analysis conditions | Source version, inclusion rules, scoring, complete-case rule, statistical procedure, Python/package versions, seed.              |
| Potential covariates           | Age, gender and education category for a separately specified supplementary analysis; they are not held constant experimentally. |

## Sample

The downloaded raw workbook contains 355 responses and the supplied cleaned workbook contains 300. All 300 cleaned responses were matched to the raw workbook using multiple fields, without publishing initials. Of the 55 excluded source records, 20 report no academic AI use and 35 report use. The authors' full exclusion rationale was not supplied.

Main sample: the 285 records in the supplied cleaned workbook with age >=18 and either bachelor's or master's education category. Exclude 15 Higher Secondary responses. Categories combine graduates and current students, so current enrolment cannot be established separately. All main-sample respondents report academic AI use; there is no non-user comparison group. Selection and convenience-sampling biases limit generalization.

## Metrics and baseline

Primary metric: Spearman rho between AI-use frequency and UPS total. Report n, two-sided asymptotic p-value and a 95% paired percentile-bootstrap CI. Use 10,000 bootstrap resamples in the research configuration; the smoke test uses 1,000. Seed: 20261007.

Statistical baseline: rho = 0, representing no monotonic association. This is a null reference, not a randomized control group. Reject H0 when p < 0.05, subject to data-quality checks. Otherwise do not reject H0; do not assert equivalence or absence of association.

Guardrails: zero invalid required values; zero missing UPS items in included rows; zero duplicate record IDs; all six UPS values in 1–4; computed totals in 6–24; exact agreement with supplied totals for the audited cleaned records; at least 95% valid bootstrap resamples. Record rejected cases in preprocessing rather than silently replacing missing values with zero. A constant variable stops the analysis. Runtime is a descriptive engineering measurement, not the scientific endpoint.

## Analysis plan

Validate and score first. Run the main association analysis only after finalizing preprocessing. Repeat on eligible raw records using explicit independent selection rules to assess sensitivity to the authors' unexplained exclusions. Specify any adjusted analysis before execution and label it supplementary. The supplied script implements scoring and unadjusted association; raw-workbook preprocessing and adjusted models remain subsequent tasks.

## Data and software

Source: Sharma et al. (2026), Mendeley Data V1, https://doi.org/10.17632/88pv88j8jb.1. Dataset license: CC BY 4.0. The public repository will contain original MIT-licensed code and ten synthetic rows. Exclude participant initials and unnecessary sensitive survey fields from any future derived data release.

Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. Parameters are stored in configs/sample.json. The pipeline produces scored.csv and results.json. No scientific result is reported from synthetic data. Docker build verification and the GitHub URL remain pending.

## Metric definitions and validity (SS5)

For respondent i, UPS_i = sum of the six coded item responses; each item is in {1, 2, 3, 4}, so UPS_i is in [6, 24]. No reverse coding is applied to the six supplied items.

Spearman rho is the Pearson correlation between the average ranks of AI-use frequency and UPS total. Average ranks handle tied values. The 95% percentile interval uses the 2.5th and 97.5th percentiles of valid paired-bootstrap correlations. Bootstrap validity rate = valid resamples / requested resamples; the required rate is at least 0.95.

Internal validity is limited by cross-sectional measurement, self-report, potential confounding and unexplained source exclusions. Fixed software and scoring improve computational reproducibility but do not eliminate these biases. Construct validity is limited by the distinction between unintentional and academic procrastination. External validity is limited by convenience recruitment in India and education labels that mix graduates with current students. Kazakhstan relevance will be discussed as a transferability question, not estimated as a local effect.

The scientific baseline is the null association. The engineering baseline is the fixed synthetic fixture with known UPS totals, checked by unit tests. There is no untreated participant group. Speed and memory are not research outcomes for this question; runtime is recorded for diagnostics. No unsupported resource threshold is imposed.
