# Data dictionary and coding rules

## Source columns

Both workbooks share the first 38 columns. Positions are one-based; `src/process_data.py` checks every header prefix before coding and stops if the layout differs.

| Column | Variable | Coding |
|---|---|---|
| 1 | consent | "Yes" → included; anything else → excluded (`no_consent`) |
| 2 | initials | never read into derived files |
| 3 | age | integer; "22 years" → 22; "23+" → lower bound 23 (eligible, exact age missing) |
| 4 | gender | lower case: female, male |
| 5 | education | Graduate/Persuing Bachelor's → `bachelor_category`; Post Graduate/Persuing Master's → `master_category`; Higher Secondary → `higher_secondary` (excluded) |
| 7 | academic_ai_use | yes / no |
| 8 | ai_frequency | Rarely/Never = 0, A few times a month = 1, Once a week = 2, A few times a week = 3, Everyday = 4 |
| 28–33 | ups_1 to ups_6 | Do not agree = 1, Agree slightly = 2, Agree moderately = 3, Agree very much = 4 (case and spaces ignored; the cleaned workbook already stores 1 to 4) |
| 41 (cleaned only) | Procrastination | supplied UPS total, used only for the audit |

All six UPS items point in the same direction, so no item is reverse scored. The total is the sum of the six items, with no prorating and no zero imputation. The nine-item GenAI composite is not used as the predictor because one item measures daily hours while the others measure agreement.

## Derived files in `data/processed/`

| File | Rows | Content |
|---|---|---|
| `survey_main.csv` | 285 | record_id (C001…), age, gender, education, ai_frequency (1 to 4), ups_1 to ups_6, ups_total, supplied_ups_total |
| `survey_raw_coded.csv` | 355 | all raw records (R001…) with age_lower_bound, age_ambiguous, academic_ai_use, ai_frequency (0 to 4), UPS items and total, exclusion reasons and `in_sensitivity_a` / `in_sensitivity_b` flags |
| `exclusion_flow.csv` | 13 | sequential exclusion counts for each sample |
| `survey_association.csv` | 3 | ρ, CIs, p-values, Kruskal–Wallis per analysis |
| `survey_group_summary.csv` | 9 | per-level n, mean, SD, median, p25, p75, p95, p99 with bootstrap CIs |
| `survey_reference_comparisons.csv` | 7 | each level against the reference group |
| `pipeline_latency_summary.csv` | 12 | latency statistics and guardrails per implementation and workload |
| `pipeline_speedup.csv` | 6 | p50 speed-up of the vectorised implementation with bootstrap CI |
| `pipeline_warmup_effect.csv` | 12 | first warm-up run against the benchmark median |
| `metrics_summary.csv` | long format | every metric above in one table: layer, analysis, group, metric, estimate, ci95_low, ci95_high, n, unit |

Exclusion reasons are applied in this order, and the first failing rule is recorded: `no_consent`, `education_higher_secondary`, `age_below_18_or_unparsed`, `inconsistent_use_no_but_frequency`, `invalid_required_value`, `no_academic_ai_use` (Sensitivity A only), `frequency_rarely_never` (Sensitivity A only).

## Benchmark log `data/raw/test_run.jsonl`

One JSON object per line.

| Field | Meaning |
|---|---|
| schema_version, session_id, run_id | log version, collection session, sequential run number |
| timestamp_utc | ISO 8601 with microseconds, taken after the timed call |
| phase | `warmup` (discarded) or `benchmark` |
| implementation | `baseline_loop` (Task 2) or `vectorized` |
| n_records, rep, batch_seed | workload size, repetition index, seed for the workload and bootstrap |
| bootstrap_resamples | resamples per run (1,000) |
| edge_case | null, or the injected defect: `missing_item`, `out_of_range`, `duplicate_id`, `constant_exposure` |
| status | `ok`; `rejected` (invalid batch correctly refused); `error` (unexpected failure) |
| error_type, error_message | exception details, if any |
| latency_ns, latency_ms | duration of the target call only |
| rho, ci_low, ci_high, valid_resamples | estimates returned by the call (null when rejected) |

`test_run_meta.json` stores the CPU model, logical CPU count, RAM, OS, Python and package versions, git commit, and the input and configuration hashes.
