"""Data preparation and statistical aggregation for Task 3.

Two layers are handled here:

* Survey layer (the research question). The public Sharma et al. (2026) workbooks are coded,
  eligibility rules are applied, UPS totals are scored and audited, and the association between
  academic GenAI-use frequency and unintentional procrastination is estimated.
* Pipeline layer (engineering benchmark). Raw JSONL timings from ``src/collector.py`` are filtered
  for warm-up runs and aggregated into latency percentiles, bootstrap intervals and error rates.

Usage::

    python src/process_data.py --config configs/research.yaml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------------------
# Coding rules (documented in docs/DATA_DICTIONARY.md)
# --------------------------------------------------------------------------------------
FREQUENCY_CODES = {
    'rarely/ never': 0,
    'a few times a month': 1,
    'once a week': 2,
    'a few times a week': 3,
    'everyday': 4,
}
FREQUENCY_LABELS = {
    0: 'Rarely/never',
    1: 'Few times a month',
    2: 'Once a week',
    3: 'Few times a week',
    4: 'Every day',
}
UPS_CODES = {'do not agree': 1, 'agree slightly': 2, 'agree moderately': 3, 'agree very much': 4}
EDUCATION_CODES = {
    "graduate/ persuing bachelor's": 'bachelor_category',
    "post graduate/ persuing master's": 'master_category',
    'higher secondary': 'higher_secondary',
}
UPS_ITEMS = [f'ups_{i}' for i in range(1, 7)]
# Zero-based positions in both workbooks, with the header prefix each column must carry.
COLUMNS = {
    'consent': (0, 'I have read all the instructions'),
    'age': (2, 'Age'),
    'gender': (3, 'Gender'),
    'education': (4, 'Education Qualification'),
    'academic_ai_use': (6, 'Do you use Generative AI tools'),
    'ai_frequency_label': (7, 'Frequency of Generative AI tool usage'),
}
UPS_POSITIONS = list(range(27, 33))  # one-based columns 28-33
UPS_PREFIXES = ['I rarely begin tasks', 'Often I mean to be doing', 'I often seem to start things',
                'I intend to get things done', 'Often I will set myself a date', 'I really want to get things']
CODED_FIELDS = ['record_id', 'age', 'education', 'ai_frequency'] + UPS_ITEMS  # Task 2 schema


def load_config(path: str | Path) -> dict:
    import yaml
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    with p.open(encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    cfg['_config_path'] = str(p)
    cfg['_config_sha256'] = sha256_file(p)
    return cfg


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _norm(value) -> str:
    return re.sub(r'\s+', ' ', str(value)).strip().lower()


def parse_age(value):
    """Return (exact_age, lower_bound, ambiguous). '22 years' -> 22; '23+' -> (nan, 23, True)."""
    s = _norm(value)
    m = re.fullmatch(r'(\d{1,3})(?:\s*years?)?', s)
    if m:
        a = float(m.group(1))
        return a, a, False
    m = re.fullmatch(r'(\d{1,3})\s*\+', s)
    if m:
        return np.nan, float(m.group(1)), True
    return np.nan, np.nan, True


def _check_headers(df: pd.DataFrame) -> None:
    cols = list(df.columns)
    for name, (pos, prefix) in COLUMNS.items():
        if not str(cols[pos]).strip().startswith(prefix):
            raise ValueError(f'Unexpected header for {name} at column {pos + 1}: {cols[pos]!r}')
    for pos, prefix in zip(UPS_POSITIONS, UPS_PREFIXES):
        if not str(cols[pos]).strip().startswith(prefix):
            raise ValueError(f'Unexpected UPS header at column {pos + 1}: {cols[pos]!r}')


def _extract(df: pd.DataFrame) -> pd.DataFrame:
    _check_headers(df)
    out = pd.DataFrame({name: df.iloc[:, pos].values for name, (pos, _) in COLUMNS.items()})
    for item, pos in zip(UPS_ITEMS, UPS_POSITIONS):
        out[item] = df.iloc[:, pos].values
    return out


def code_ups(value):
    """Map a UPS response (text label or integer code) to 1-4; return NaN when invalid."""
    if isinstance(value, (int, np.integer, float, np.floating)) and not pd.isna(value):
        v = float(value)
        return v if v in (1.0, 2.0, 3.0, 4.0) else np.nan
    return float(UPS_CODES[_norm(value)]) if _norm(value) in UPS_CODES else np.nan


def code_frame(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Code one workbook into analysis variables. No initials or sensitive scales are kept."""
    df = df.dropna(how='all').reset_index(drop=True)
    x = _extract(df)
    coded = pd.DataFrame({'record_id': [f'{prefix}{i:03d}' for i in range(1, len(x) + 1)]})
    coded['consent'] = x['consent'].map(_norm).eq('yes')
    ages = x['age'].map(parse_age)
    coded['age'] = [a[0] for a in ages]
    coded['age_lower_bound'] = [a[1] for a in ages]
    coded['age_ambiguous'] = [a[2] for a in ages]
    coded['age_normalised'] = x['age'].map(lambda v: isinstance(v, str) and not v.strip().isdigit())
    coded['gender'] = x['gender'].map(_norm)
    coded['education'] = x['education'].map(lambda v: EDUCATION_CODES.get(_norm(v), 'unknown'))
    coded['academic_ai_use'] = x['academic_ai_use'].map(_norm)
    coded['ai_frequency'] = x['ai_frequency_label'].map(lambda v: FREQUENCY_CODES.get(_norm(v), np.nan))
    for item in UPS_ITEMS:
        coded[item] = x[item].map(code_ups)
    coded['ups_missing_items'] = coded[UPS_ITEMS].isna().sum(axis=1)
    coded['ups_total'] = coded[UPS_ITEMS].sum(axis=1, min_count=6)
    return coded


def prepare_cleaned(path: Path) -> tuple[pd.DataFrame, dict]:
    """Main sample: supplied cleaned workbook, excluding Higher Secondary and age < 18."""
    df = pd.read_excel(path, engine='openpyxl').dropna(how='all').reset_index(drop=True)
    coded = code_frame(df, 'C')
    supplied = pd.to_numeric(df['Procrastination'], errors='coerce').to_numpy()
    coded['supplied_ups_total'] = supplied
    agree = int(np.sum(coded['ups_total'].to_numpy() == supplied))
    reasons = []
    for _, r in coded.iterrows():
        if r['education'] not in ('bachelor_category', 'master_category'):
            reasons.append('education_higher_secondary')
        elif not (r['age'] >= 18):
            reasons.append('age_below_18_or_unparsed')
        elif r['ups_missing_items'] > 0 or pd.isna(r['ai_frequency']):
            reasons.append('invalid_required_value')
        else:
            reasons.append('')
    coded['exclusion_reason'] = reasons
    audit = {'cleaned_records': int(len(coded)),
             'supplied_total_agreement': agree,
             'supplied_total_disagreement': int(len(coded) - agree)}
    return coded, audit


def prepare_raw(path: Path) -> pd.DataFrame:
    """Raw workbook with independent, sequential eligibility rules (first failing rule recorded)."""
    df = pd.read_excel(path, engine='openpyxl').dropna(how='all').reset_index(drop=True)
    coded = code_frame(df, 'R')
    reasons_a, reasons_b = [], []
    for _, r in coded.iterrows():
        checks = [
            ('no_consent', not r['consent']),
            ('education_higher_secondary', r['education'] not in ('bachelor_category', 'master_category')),
            ('age_below_18_or_unparsed', not (r['age_lower_bound'] >= 18)),
            ('inconsistent_use_no_but_frequency', r['academic_ai_use'] == 'no' and r['ai_frequency'] >= 1),
            ('invalid_required_value', r['ups_missing_items'] > 0 or pd.isna(r['ai_frequency'])),
        ]
        first = next((name for name, failed in checks if failed), '')
        # Sensitivity A mirrors the main-sample population: academic users with a use frequency.
        if first:
            reason_a = first
        elif r['academic_ai_use'] != 'yes':
            reason_a = 'no_academic_ai_use'
        elif r['ai_frequency'] == 0:
            reason_a = 'frequency_rarely_never'
        else:
            reason_a = ''
        reasons_a.append(reason_a)
        reasons_b.append(first)  # Sensitivity B keeps Rarely/never as the low-use reference level
    coded['exclusion_reason_a'] = reasons_a
    coded['exclusion_reason_b'] = reasons_b
    coded['in_sensitivity_a'] = coded['exclusion_reason_a'].eq('')
    coded['in_sensitivity_b'] = coded['exclusion_reason_b'].eq('')
    return coded


RULE_ORDER = ['no_consent', 'education_higher_secondary', 'age_below_18_or_unparsed',
              'inconsistent_use_no_but_frequency', 'invalid_required_value', 'no_academic_ai_use',
              'frequency_rarely_never']


def exclusion_flow(cleaned: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample, frame, col in [('main_cleaned', cleaned, 'exclusion_reason'),
                               ('sensitivity_a_raw', raw, 'exclusion_reason_a'),
                               ('sensitivity_b_raw_five_level', raw, 'exclusion_reason_b')]:
        remaining = len(frame)
        rows.append({'sample': sample, 'step': 'records_in_source', 'excluded': 0, 'remaining': remaining})
        present = set(r for r in frame[col] if r)
        for reason in [r for r in RULE_ORDER if r in present] + sorted(present - set(RULE_ORDER)):
            k = int((frame[col] == reason).sum())
            remaining -= k
            rows.append({'sample': sample, 'step': reason, 'excluded': k, 'remaining': remaining})
        rows.append({'sample': sample, 'step': 'analysed', 'excluded': 0, 'remaining': int((frame[col] == '').sum())})
    return pd.DataFrame(rows)


def prepare(cfg: dict) -> dict:
    """Code both workbooks and write minimal, de-identified CSVs to data/processed/."""
    files = cfg['source']['files']
    for key in ('raw', 'cleaned'):
        p = ROOT / files[key]['path']
        if not p.exists():
            raise FileNotFoundError(f'{p} not found; run python src/fetch_data.py first')
        if sha256_file(p) != files[key]['sha256']:
            raise ValueError(f'SHA-256 mismatch for {p}; the source file differs from Mendeley V1')
    cleaned, audit = prepare_cleaned(ROOT / files['cleaned']['path'])
    raw = prepare_raw(ROOT / files['raw']['path'])
    out = ROOT / cfg['processed']['dir']
    out.mkdir(parents=True, exist_ok=True)
    main = cleaned[cleaned['exclusion_reason'] == ''].copy()
    main_cols = ['record_id', 'age', 'gender', 'education', 'ai_frequency'] + UPS_ITEMS + ['ups_total', 'supplied_ups_total']
    main = main[main_cols].astype({c: int for c in ['age', 'ai_frequency', 'ups_total', 'supplied_ups_total'] + UPS_ITEMS})
    main.to_csv(ROOT / cfg['processed']['main'], index=False, lineterminator='\n')
    raw_cols = ['record_id', 'age', 'age_lower_bound', 'age_ambiguous', 'gender', 'education', 'academic_ai_use',
                'ai_frequency'] + UPS_ITEMS + ['ups_total', 'exclusion_reason_a', 'exclusion_reason_b',
                                              'in_sensitivity_a', 'in_sensitivity_b']
    raw[raw_cols].to_csv(ROOT / cfg['processed']['raw_coded'], index=False, lineterminator='\n')
    flow = exclusion_flow(cleaned, raw)
    flow.to_csv(out / 'exclusion_flow.csv', index=False, lineterminator='\n')
    audit.update({'main_n': int(len(main)),
                  'sensitivity_a_n': int(raw['in_sensitivity_a'].sum()),
                  'sensitivity_b_n': int(raw['in_sensitivity_b'].sum()),
                  'raw_records': int(len(raw)),
                  'raw_age_values_normalised': int(raw['age_normalised'].sum()),
                  'raw_age_values_lower_bound_only': int(raw['age_ambiguous'].sum())})
    return audit


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def _row_pearson(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean(axis=1, keepdims=True)
    den = np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1))
    with np.errstate(invalid='ignore', divide='ignore'):
        return (a * b).sum(axis=1) / den


def bootstrap_indices(n: int, resamples: int, seed: int) -> np.ndarray:
    """Draw resample indices with the same call sequence as the Task 2 loop (identical resamples)."""
    rng = np.random.default_rng(seed)
    return np.stack([rng.integers(0, n, n) for _ in range(resamples)])


def spearman_bootstrap(x, y, resamples: int, seed: int, min_valid_fraction: float = 0.95,
                       chunk: int = 2000) -> dict:
    """Vectorised equivalent of ``benchmark.association``: same estimates, fewer Python calls."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        raise ValueError('Correlation is undefined for a constant variable')
    res = stats.spearmanr(x, y)
    idx = bootstrap_indices(len(x), resamples, seed)
    estimates = []
    for start in range(0, resamples, chunk):
        block = idx[start:start + chunk]
        xb, yb = x[block], y[block]
        ok = (xb.max(axis=1) > xb.min(axis=1)) & (yb.max(axis=1) > yb.min(axis=1))
        rx = stats.rankdata(xb[ok], axis=1)
        ry = stats.rankdata(yb[ok], axis=1)
        estimates.append(_row_pearson(rx, ry))
    est = np.concatenate(estimates) if estimates else np.array([])
    fraction = len(est) / resamples
    if fraction < min_valid_fraction:
        raise ValueError('Too many degenerate bootstrap resamples')
    lo, hi = np.quantile(est, [0.025, 0.975])
    return {'spearman_rho': float(res.statistic), 'p_value_asymptotic_two_sided': float(res.pvalue),
            'ci95_percentile_bootstrap': [float(lo), float(hi)],
            'valid_bootstrap_resamples': int(len(est)),
            'skipped_bootstrap_resamples': int(resamples - len(est)),
            '_bootstrap_estimates': est}


def permutation_p_spearman(x, y, resamples: int, seed: int) -> float:
    """Two-sided Monte Carlo permutation p-value, (k + 1) / (B + 1)."""
    rng = np.random.default_rng(seed)
    rx = stats.rankdata(x)
    ry = stats.rankdata(y)
    observed = abs(stats.pearsonr(rx, ry).statistic)
    perms = np.stack([rng.permutation(ry) for _ in range(resamples)])
    null = np.abs(_row_pearson(np.broadcast_to(rx, perms.shape), perms))
    return float((np.sum(null >= observed - 1e-12) + 1) / (resamples + 1))


def bootstrap_ci(values, func, resamples: int, rng: np.random.Generator, level: float = 0.95):
    v = np.asarray(values, dtype=float)
    idx = rng.integers(0, len(v), (resamples, len(v)))
    est = func(v[idx], axis=1)
    a = (1 - level) / 2
    lo, hi = np.quantile(est, [a, 1 - a])
    return float(lo), float(hi)


def cliffs_delta(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.sign(a[:, None] - b[None, :]).mean())


def cliffs_delta_bootstrap(a, b, resamples: int, rng: np.random.Generator, level: float = 0.95):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ia = rng.integers(0, len(a), (resamples, len(a)))
    ib = rng.integers(0, len(b), (resamples, len(b)))
    combined = np.concatenate([a[ia], b[ib]], axis=1)
    ranks = stats.rankdata(combined, axis=1)
    u = ranks[:, :len(a)].sum(axis=1) - len(a) * (len(a) + 1) / 2
    delta = 2 * u / (len(a) * len(b)) - 1
    q = (1 - level) / 2
    lo, hi = np.quantile(delta, [q, 1 - q])
    return float(lo), float(hi)


def holm(pvalues) -> list[float]:
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adjusted[i] = running
    return adjusted.tolist()


def cronbach_alpha(items: np.ndarray) -> float:
    items = np.asarray(items, dtype=float)
    k = items.shape[1]
    return float(k / (k - 1) * (1 - items.var(axis=0, ddof=1).sum() / items.sum(axis=1).var(ddof=1)))


def group_summary(df: pd.DataFrame, resamples: int, seed: int, sample: str) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for level, g in df.groupby('ai_frequency'):
        v = g['ups_total'].to_numpy(dtype=float)
        mlo, mhi = bootstrap_ci(v, np.median, resamples, rng)
        alo, ahi = bootstrap_ci(v, np.mean, resamples, rng)
        rows.append({'sample': sample, 'ai_frequency': int(level), 'label': FREQUENCY_LABELS[int(level)],
                     'n': int(len(v)), 'mean': v.mean(), 'sd': v.std(ddof=1),
                     'mean_ci_low': alo, 'mean_ci_high': ahi,
                     'median': float(np.median(v)), 'median_ci_low': mlo, 'median_ci_high': mhi,
                     'p25': float(np.percentile(v, 25)), 'p75': float(np.percentile(v, 75)),
                     'p95': float(np.percentile(v, 95)), 'p99': float(np.percentile(v, 99)),
                     'min': float(v.min()), 'max': float(v.max())})
    return pd.DataFrame(rows)


def reference_comparisons(df: pd.DataFrame, reference: int, resamples: int, seed: int, sample: str) -> pd.DataFrame:
    """Each use level against the lowest-use reference group (baseline group)."""
    rng = np.random.default_rng(seed)
    ref = df.loc[df['ai_frequency'] == reference, 'ups_total'].to_numpy(dtype=float)
    rows = []
    for level, g in df.groupby('ai_frequency'):
        if level == reference:
            continue
        v = g['ups_total'].to_numpy(dtype=float)
        ir = rng.integers(0, len(ref), (resamples, len(ref)))
        iv = rng.integers(0, len(v), (resamples, len(v)))
        med_diff = np.median(v[iv], axis=1) - np.median(ref[ir], axis=1)
        mean_diff = v[iv].mean(axis=1) - ref[ir].mean(axis=1)
        dlo, dhi = cliffs_delta_bootstrap(v, ref, resamples, rng)
        mw = stats.mannwhitneyu(v, ref, alternative='two-sided')
        rows.append({'sample': sample, 'ai_frequency': int(level), 'label': FREQUENCY_LABELS[int(level)],
                     'reference_level': int(reference), 'reference_label': FREQUENCY_LABELS[int(reference)],
                     'n': int(len(v)), 'n_reference': int(len(ref)),
                     'median_difference': float(np.median(v) - np.median(ref)),
                     'median_difference_ci_low': float(np.quantile(med_diff, 0.025)),
                     'median_difference_ci_high': float(np.quantile(med_diff, 0.975)),
                     'mean_difference': float(v.mean() - ref.mean()),
                     'mean_difference_ci_low': float(np.quantile(mean_diff, 0.025)),
                     'mean_difference_ci_high': float(np.quantile(mean_diff, 0.975)),
                     'cliffs_delta': cliffs_delta(v, ref), 'cliffs_delta_ci_low': dlo, 'cliffs_delta_ci_high': dhi,
                     'mann_whitney_u': float(mw.statistic), 'p_value': float(mw.pvalue)})
    out = pd.DataFrame(rows)
    out['p_value_holm'] = holm(out['p_value'])
    return out


def ols_models(df: pd.DataFrame, covariates: list[str]) -> dict:
    """Baseline model (covariates only) versus proposed model (covariates + AI-use frequency)."""
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    terms = []
    for c in covariates:
        terms.append(f'C({c})' if df[c].dtype == object else c)
    base_formula = 'ups_total ~ ' + ' + '.join(terms)
    prop_formula = base_formula + ' + ai_frequency'
    cat_formula = base_formula + ' + C(ai_frequency, Treatment(1))'
    base = smf.ols(base_formula, data=df).fit()
    prop = smf.ols(prop_formula, data=df).fit()
    cat = smf.ols(cat_formula, data=df).fit()
    prop_hc3 = smf.ols(prop_formula, data=df).fit(cov_type='HC3')
    nested = anova_lm(base, prop)
    nested_cat = anova_lm(base, cat)
    z = df.assign(ups_z=(df['ups_total'] - df['ups_total'].mean()) / df['ups_total'].std(ddof=1),
                  freq_z=(df['ai_frequency'] - df['ai_frequency'].mean()) / df['ai_frequency'].std(ddof=1))
    std = smf.ols('ups_z ~ ' + ' + '.join(terms) + ' + freq_z', data=z).fit(cov_type='HC3')
    ci = prop_hc3.conf_int().loc['ai_frequency']
    sci = std.conf_int().loc['freq_z']
    resid = prop.resid
    return {
        'n': int(prop.nobs),
        'baseline': {'formula': base_formula, 'r2': float(base.rsquared), 'adj_r2': float(base.rsquared_adj),
                     'aic': float(base.aic), 'bic': float(base.bic)},
        'proposed': {'formula': prop_formula, 'r2': float(prop.rsquared), 'adj_r2': float(prop.rsquared_adj),
                     'aic': float(prop.aic), 'bic': float(prop.bic),
                     'beta_ai_frequency': float(prop_hc3.params['ai_frequency']),
                     'beta_ci95_hc3': [float(ci[0]), float(ci[1])],
                     'beta_p_hc3': float(prop_hc3.pvalues['ai_frequency']),
                     'standardised_beta': float(std.params['freq_z']),
                     'standardised_beta_ci95_hc3': [float(sci[0]), float(sci[1])]},
        'delta_r2': float(prop.rsquared - base.rsquared),
        'nested_f': float(nested['F'].iloc[1]), 'nested_f_p': float(nested['Pr(>F)'].iloc[1]),
        'categorical_robustness': {'formula': cat_formula, 'r2': float(cat.rsquared),
                                   'delta_r2': float(cat.rsquared - base.rsquared),
                                   'nested_f': float(nested_cat['F'].iloc[1]),
                                   'nested_f_p': float(nested_cat['Pr(>F)'].iloc[1])},
        'residual_diagnostics': {'shapiro_p': float(stats.shapiro(resid).pvalue),
                                 'breusch_pagan_p': float(_breusch_pagan(prop))},
    }


def _breusch_pagan(model) -> float:
    from statsmodels.stats.diagnostic import het_breuschpagan
    return het_breuschpagan(model.resid, model.model.exog)[1]


def association_block(df: pd.DataFrame, cfg: dict, label: str, permutation: bool = True) -> dict:
    a = cfg['analysis']
    res = spearman_bootstrap(df['ai_frequency'], df['ups_total'], a['bootstrap_resamples'], cfg['seed'],
                             a['minimum_valid_bootstrap_fraction'])
    est = res.pop('_bootstrap_estimates')
    out = {'analysis': label, 'n': int(len(df)), **res,
           'bootstrap_valid_fraction': res['valid_bootstrap_resamples'] / a['bootstrap_resamples'],
           'bootstrap_sd': float(est.std(ddof=1))}
    if permutation:
        out['p_value_permutation_two_sided'] = permutation_p_spearman(
            df['ai_frequency'].to_numpy(), df['ups_total'].to_numpy(), a['permutation_resamples'], cfg['seed'])
    kw = stats.kruskal(*[g['ups_total'].to_numpy() for _, g in df.groupby('ai_frequency')])
    out['kruskal_h'] = float(kw.statistic)
    out['kruskal_p'] = float(kw.pvalue)
    out['kruskal_epsilon_squared'] = float(kw.statistic / (len(df) - 1))
    out['decision'] = 'reject_H0' if res['p_value_asymptotic_two_sided'] < cfg['alpha'] else 'do_not_reject_H0'
    return out, est


# --------------------------------------------------------------------------------------
# Benchmark (pipeline layer) aggregation
# --------------------------------------------------------------------------------------
def load_jsonl(path: str | Path) -> pd.DataFrame:
    records = []
    with Path(path).open(encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f'{path}:{line_no}: malformed JSON line') from exc
    df = pd.DataFrame.from_records(records)
    required = {'run_id', 'phase', 'implementation', 'n_records', 'status', 'latency_ms'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'JSONL schema is missing fields: {sorted(missing)}')
    return df


def filter_warmup(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (benchmark_runs, warmup_runs). Warm-up runs never enter the summary statistics."""
    if not set(df['phase']).issubset({'warmup', 'benchmark'}):
        raise ValueError(f'Unknown phase labels: {sorted(set(df["phase"]))}')
    return df[df['phase'] == 'benchmark'].copy(), df[df['phase'] == 'warmup'].copy()


def flag_outliers_iqr(values: pd.Series, k: float = 1.5) -> pd.Series:
    """Non-destructive Tukey flag; flagged runs are kept in every statistic."""
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (values < q1 - k * iqr) | (values > q3 + k * iqr)


def latency_summary(bench: pd.DataFrame, resamples: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for (impl, n), g in bench.groupby(['implementation', 'n_records']):
        ok = g[g['status'] == 'ok']
        v = ok['latency_ms'].to_numpy(dtype=float)
        p50lo, p50hi = bootstrap_ci(v, np.median, resamples, rng)
        p95lo, p95hi = bootstrap_ci(v, lambda a, axis: np.percentile(a, 95, axis=axis), resamples, rng)
        mlo, mhi = bootstrap_ci(v, np.mean, resamples, rng)
        rejected = g[g['status'] == 'rejected']
        injected = g[g['edge_case'].notna()]
        rows.append({
            'implementation': impl, 'n_records': int(n), 'runs': int(len(g)), 'ok_runs': int(len(ok)),
            'unexpected_errors': int((g['status'] == 'error').sum()),
            'unexpected_error_rate': float((g['status'] == 'error').mean()),
            'injected_invalid_batches': int(len(injected)),
            'rejected_batches': int(len(rejected)),
            'rejection_detection_rate': float(len(rejected) / len(injected)) if len(injected) else np.nan,
            'mean_ms': float(v.mean()), 'sd_ms': float(v.std(ddof=1)), 'mean_ci_low': mlo, 'mean_ci_high': mhi,
            'p25_ms': float(np.percentile(v, 25)), 'p50_ms': float(np.median(v)),
            'p50_ci_low': p50lo, 'p50_ci_high': p50hi,
            'p75_ms': float(np.percentile(v, 75)),
            'p95_ms': float(np.percentile(v, 95)), 'p95_ci_low': p95lo, 'p95_ci_high': p95hi,
            'p99_ms': float(np.percentile(v, 99)),
            'max_ms': float(v.max()),
            'p95_all_runs_ms': float(np.percentile(g['latency_ms'], 95)),
            'iqr_flagged_runs': int(flag_outliers_iqr(ok['latency_ms']).sum()),
            'throughput_records_per_s_median': float(np.median(n / (v / 1000.0))),
        })
    return pd.DataFrame(rows)


def speedup_table(bench: pd.DataFrame, resamples: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    ok = bench[bench['status'] == 'ok']
    for n, g in ok.groupby('n_records'):
        b = g.loc[g['implementation'] == 'baseline_loop', 'latency_ms'].to_numpy()
        v = g.loc[g['implementation'] == 'vectorized', 'latency_ms'].to_numpy()
        ib = rng.integers(0, len(b), (resamples, len(b)))
        iv = rng.integers(0, len(v), (resamples, len(v)))
        ratio = np.median(b[ib], axis=1) / np.median(v[iv], axis=1)
        rows.append({'n_records': int(n), 'baseline_p50_ms': float(np.median(b)), 'vectorized_p50_ms': float(np.median(v)),
                     'speedup_p50': float(np.median(b) / np.median(v)),
                     'speedup_ci_low': float(np.quantile(ratio, 0.025)), 'speedup_ci_high': float(np.quantile(ratio, 0.975)),
                     'mann_whitney_p': float(stats.mannwhitneyu(b, v, alternative='two-sided').pvalue)})
    return pd.DataFrame(rows)


def estimate_agreement(bench: pd.DataFrame) -> dict:
    """Correctness guardrail: both implementations must return identical estimates on identical input."""
    ok = bench[bench['status'] == 'ok']
    keys = ['n_records', 'rep']
    piv = ok.pivot_table(index=keys, columns='implementation', values=['rho', 'ci_low', 'ci_high'])
    diffs = {}
    for metric in ['rho', 'ci_low', 'ci_high']:
        d = (piv[(metric, 'baseline_loop')] - piv[(metric, 'vectorized')]).abs()
        diffs[metric] = float(d.max())
    mismatches = int(sum((piv[(m, 'baseline_loop')] - piv[(m, 'vectorized')]).abs().gt(1e-9).sum() for m in ['rho', 'ci_low', 'ci_high']))
    return {'paired_runs_compared': int(len(piv)), 'max_abs_difference': diffs, 'mismatches_over_1e-9': mismatches}


def warmup_effect(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (impl, n), g in df[df['status'] == 'ok'].groupby(['implementation', 'n_records']):
        w = g[g['phase'] == 'warmup']['latency_ms']
        b = g[g['phase'] == 'benchmark']['latency_ms']
        rows.append({'implementation': impl, 'n_records': int(n), 'first_warmup_ms': float(w.iloc[0]),
                     'warmup_median_ms': float(w.median()), 'benchmark_median_ms': float(b.median()),
                     'first_run_to_benchmark_median_ratio': float(w.iloc[0] / b.median())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def metrics_long(assoc: list[dict], groups: pd.DataFrame, refs: pd.DataFrame, models: dict,
                 latency: pd.DataFrame, speed: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(layer, analysis, group, metric, estimate, lo=np.nan, hi=np.nan, n=np.nan, unit=''):
        rows.append({'layer': layer, 'analysis': analysis, 'group': group, 'metric': metric,
                     'estimate': estimate, 'ci95_low': lo, 'ci95_high': hi, 'n': n, 'unit': unit})

    for a in assoc:
        add('survey', a['analysis'], 'all', 'spearman_rho', a['spearman_rho'], *a['ci95_percentile_bootstrap'], a['n'], 'dimensionless')
        add('survey', a['analysis'], 'all', 'p_value_asymptotic', a['p_value_asymptotic_two_sided'], n=a['n'])
        if 'p_value_permutation_two_sided' in a:
            add('survey', a['analysis'], 'all', 'p_value_permutation', a['p_value_permutation_two_sided'], n=a['n'])
        add('survey', a['analysis'], 'all', 'kruskal_epsilon_squared', a['kruskal_epsilon_squared'], n=a['n'])
        add('survey', a['analysis'], 'all', 'bootstrap_valid_fraction', a['bootstrap_valid_fraction'], n=a['n'], unit='proportion')
    for _, g in groups.iterrows():
        grp = f"{g['ai_frequency']}:{g['label']}"
        add('survey', g['sample'], grp, 'ups_median', g['median'], g['median_ci_low'], g['median_ci_high'], g['n'], 'UPS points')
        add('survey', g['sample'], grp, 'ups_mean', g['mean'], g['mean_ci_low'], g['mean_ci_high'], g['n'], 'UPS points')
        add('survey', g['sample'], grp, 'ups_sd', g['sd'], n=g['n'], unit='UPS points')
        for p in ['p25', 'p75', 'p95', 'p99']:
            add('survey', g['sample'], grp, f'ups_{p}', g[p], n=g['n'], unit='UPS points')
    for _, r in refs.iterrows():
        grp = f"{r['ai_frequency']} vs {r['reference_level']}"
        add('survey', r['sample'], grp, 'median_difference', r['median_difference'], r['median_difference_ci_low'], r['median_difference_ci_high'], r['n'], 'UPS points')
        add('survey', r['sample'], grp, 'cliffs_delta', r['cliffs_delta'], r['cliffs_delta_ci_low'], r['cliffs_delta_ci_high'], r['n'], 'dimensionless')
        add('survey', r['sample'], grp, 'p_value_holm', r['p_value_holm'], n=r['n'])
    add('survey', 'models_main', 'baseline_covariates', 'r2', models['baseline']['r2'], n=models['n'], unit='proportion')
    add('survey', 'models_main', 'proposed_plus_frequency', 'r2', models['proposed']['r2'], n=models['n'], unit='proportion')
    add('survey', 'models_main', 'proposed_minus_baseline', 'delta_r2', models['delta_r2'], n=models['n'], unit='proportion')
    add('survey', 'models_main', 'proposed_plus_frequency', 'beta_ai_frequency', models['proposed']['beta_ai_frequency'],
        *models['proposed']['beta_ci95_hc3'], models['n'], 'UPS points per frequency level')
    for _, r in latency.iterrows():
        grp = f"{r['implementation']}|n={r['n_records']}"
        add('pipeline', 'latency', grp, 'p50_ms', r['p50_ms'], r['p50_ci_low'], r['p50_ci_high'], r['ok_runs'], 'ms')
        add('pipeline', 'latency', grp, 'p95_ms', r['p95_ms'], r['p95_ci_low'], r['p95_ci_high'], r['ok_runs'], 'ms')
        add('pipeline', 'latency', grp, 'p99_ms', r['p99_ms'], n=r['ok_runs'], unit='ms')
        add('pipeline', 'latency', grp, 'mean_ms', r['mean_ms'], r['mean_ci_low'], r['mean_ci_high'], r['ok_runs'], 'ms')
        add('pipeline', 'latency', grp, 'sd_ms', r['sd_ms'], n=r['ok_runs'], unit='ms')
        add('pipeline', 'guardrail', grp, 'unexpected_error_rate', r['unexpected_error_rate'], n=r['runs'], unit='proportion')
        add('pipeline', 'guardrail', grp, 'rejection_detection_rate', r['rejection_detection_rate'], n=r['injected_invalid_batches'], unit='proportion')
    for _, r in speed.iterrows():
        add('pipeline', 'speedup', f"n={r['n_records']}", 'speedup_p50', r['speedup_p50'], r['speedup_ci_low'], r['speedup_ci_high'], unit='ratio')
    return pd.DataFrame(rows)


def run_analysis(cfg: dict) -> dict:
    a = cfg['analysis']
    proc = ROOT / cfg['processed']['dir']
    main = pd.read_csv(ROOT / cfg['processed']['main'])
    raw = pd.read_csv(ROOT / cfg['processed']['raw_coded'])
    guard = survey_guardrails(main)
    sens_a = raw[raw['in_sensitivity_a']].copy()
    sens_b = raw[raw['in_sensitivity_b']].copy()
    for frame in (sens_a, sens_b):
        frame['ai_frequency'] = frame['ai_frequency'].astype(int)
        frame['ups_total'] = frame['ups_total'].astype(int)
    assoc_main, est_main = association_block(main, cfg, 'main_cleaned_n285')
    assoc_a, est_a = association_block(sens_a, cfg, 'sensitivity_a_raw_independent')
    assoc_b, est_b = association_block(sens_b, cfg, 'sensitivity_b_raw_five_level')
    groups = pd.concat([group_summary(main, a['bootstrap_resamples'], cfg['seed'], 'main_cleaned_n285'),
                        group_summary(sens_b, a['bootstrap_resamples'], cfg['seed'], 'sensitivity_b_raw_five_level')])
    refs = pd.concat([reference_comparisons(main, a['reference_level_main'], a['bootstrap_resamples'], cfg['seed'], 'main_cleaned_n285'),
                      reference_comparisons(sens_b, a['reference_level_five_level'], a['bootstrap_resamples'], cfg['seed'], 'sensitivity_b_raw_five_level')])
    models = ols_models(main, a['covariates'])
    groups.to_csv(proc / 'survey_group_summary.csv', index=False, lineterminator='\n')
    refs.to_csv(proc / 'survey_reference_comparisons.csv', index=False, lineterminator='\n')
    pd.DataFrame([assoc_main, assoc_a, assoc_b]).to_csv(proc / 'survey_association.csv', index=False, lineterminator='\n')

    b = cfg['benchmark']
    log = load_jsonl(ROOT / b['log_path'])
    bench, warm = filter_warmup(log)
    latency = latency_summary(bench, a['bootstrap_resamples'], cfg['seed'])
    speed = speedup_table(bench, a['bootstrap_resamples'], cfg['seed'])
    agree = estimate_agreement(bench)
    warm_tbl = warmup_effect(log)
    latency.to_csv(proc / 'pipeline_latency_summary.csv', index=False, lineterminator='\n')
    speed.to_csv(proc / 'pipeline_speedup.csv', index=False, lineterminator='\n')
    warm_tbl.to_csv(proc / 'pipeline_warmup_effect.csv', index=False, lineterminator='\n')
    metrics = metrics_long([assoc_main, assoc_a, assoc_b], groups, refs, models, latency, speed)
    metrics.to_csv(ROOT / cfg['processed']['metrics_summary'], index=False, lineterminator='\n')

    results = {
        'config_sha256': cfg['_config_sha256'], 'seed': cfg['seed'], 'alpha': cfg['alpha'],
        'survey': {'guardrails': guard, 'association': [assoc_main, assoc_a, assoc_b], 'models_main': models,
                   'ups_cronbach_alpha_main': cronbach_alpha(main[UPS_ITEMS].to_numpy()),
                   'input_sha256': {'main': sha256_file(ROOT / cfg['processed']['main']),
                                    'raw_coded': sha256_file(ROOT / cfg['processed']['raw_coded'])}},
        'pipeline': {'log_sha256': sha256_file(ROOT / b['log_path']), 'records_total': int(len(log)),
                     'warmup_records_discarded': int(len(warm)), 'benchmark_records': int(len(bench)),
                     'estimate_agreement': agree,
                     'unexpected_error_rate_overall': float((bench['status'] == 'error').mean()),
                     'rejection_detection_rate_overall': float((bench['status'] == 'rejected').sum()
                                                               / max(1, bench['edge_case'].notna().sum()))},
        'versions': versions(),
    }
    out = ROOT / cfg['reports']['results_json']
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, allow_nan=False, default=float) + '\n', encoding='utf-8', newline='\n')
    return results


def survey_guardrails(main: pd.DataFrame) -> dict:
    items = main[UPS_ITEMS]
    out = {
        'n': int(len(main)),
        'invalid_required_values': int((~items.isin([1, 2, 3, 4])).sum().sum() + (~main['ai_frequency'].isin([1, 2, 3, 4])).sum()),
        'missing_ups_items': int(items.isna().sum().sum()),
        'duplicate_record_ids': int(main['record_id'].duplicated().sum()),
        'ups_totals_out_of_range': int((~main['ups_total'].between(6, 24)).sum()),
        'computed_vs_supplied_total_mismatches': int((main['ups_total'] != main['supplied_ups_total']).sum()),
        'constant_variable': bool(main['ai_frequency'].nunique() < 2 or main['ups_total'].nunique() < 2),
    }
    failed = [k for k, v in out.items() if k != 'n' and v not in (0, False)]
    if failed:
        raise ValueError(f'Survey guardrails failed: {failed}')
    return out


def versions() -> dict:
    import platform
    import scipy
    out = {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
           'pandas': pd.__version__}
    for mod in ('statsmodels', 'matplotlib', 'seaborn'):
        try:
            out[mod] = __import__(mod).__version__
        except ImportError:
            pass
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--config', default='configs/research.yaml')
    parser.add_argument('--skip-prepare', action='store_true',
                        help='use the committed data/processed CSVs instead of re-coding the workbooks')
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    raw_present = all((ROOT / f['path']).exists() for f in cfg['source']['files'].values())
    if not args.skip_prepare and raw_present:
        audit = prepare(cfg)
        print('prepared:', json.dumps(audit))
    else:
        print('using committed data/processed CSVs (source workbooks not re-coded)')
    res = run_analysis(cfg)
    m = res['survey']['association'][0]
    print(f"main: n={m['n']} rho={m['spearman_rho']:.4f} CI95=[{m['ci95_percentile_bootstrap'][0]:.4f}, "
          f"{m['ci95_percentile_bootstrap'][1]:.4f}] p={m['p_value_asymptotic_two_sided']:.4g}")
    print('wrote', cfg['processed']['metrics_summary'], 'and', cfg['reports']['results_json'])
    return res


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
