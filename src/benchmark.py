"""Validate survey records, score UPS and estimate a rank association."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
import scipy
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['record_id', 'age', 'education', 'ai_frequency'] + [f'ups_{i}' for i in range(1, 7)]

def validate(rows):
    seen = set()
    for line, r in enumerate(rows, 2):
        if not r['record_id'] or r['record_id'] in seen:
            raise ValueError(f'Line {line}: missing or duplicate record ID')
        seen.add(r['record_id'])
        try:
            age = float(r['age'])
            values = [int(r[k]) for k in FIELDS[3:]]
        except (ValueError, TypeError):
            raise ValueError(f'Line {line}: missing or invalid numeric value')
        if not np.isfinite(age) or not 18 <= age <= 120:
            raise ValueError(f'Line {line}: age outside eligibility range')
        if r['education'] not in ['bachelor_category', 'master_category']:
            raise ValueError(f'Line {line}: ineligible education category')
        if any(v < 1 or v > 4 for v in values):
            raise ValueError(f'Line {line}: frequency and UPS items must be integers 1–4')
    if len(rows) < 5:
        raise ValueError('At least five eligible records are required')

def score(rows):
    return (np.array([int(r['ai_frequency']) for r in rows]),
            np.array([sum(int(r[f'ups_{i}']) for i in range(1, 7)) for r in rows]))

def association(x, y, cfg):
    if len(set(x)) < 2 or len(set(y)) < 2:
        raise ValueError('Correlation is undefined for a constant variable')
    rho, p = spearmanr(x, y)
    rng = np.random.default_rng(cfg['seed'])
    estimates = []
    for _ in range(cfg['bootstrap_resamples']):
        idx = rng.integers(0, len(x), len(x))
        if len(set(x[idx])) > 1 and len(set(y[idx])) > 1:
            estimates.append(float(spearmanr(x[idx], y[idx]).statistic))
    fraction = len(estimates) / cfg['bootstrap_resamples']
    if fraction < cfg['minimum_valid_bootstrap_fraction']:
        raise ValueError('Too many degenerate bootstrap resamples')
    lo, hi = np.quantile(estimates, [0.025, 0.975])
    return {'spearman_rho': float(rho), 'p_value_asymptotic_two_sided': float(p),
            'ci95_percentile_bootstrap': [float(lo), float(hi)],
            'valid_bootstrap_resamples': len(estimates),
            'skipped_bootstrap_resamples': cfg['bootstrap_resamples'] - len(estimates)}

def run(config_path):
    started = time.perf_counter()
    cfg = json.loads(config_path.read_text())
    if cfg['mode'] not in ['synthetic_smoke_test', 'research']:
        raise ValueError('Unknown mode')
    if type(cfg['bootstrap_resamples']) is not int or cfg['bootstrap_resamples'] < 100:
        raise ValueError('At least 100 bootstrap resamples required')
    if not 0 < cfg['alpha'] < 1 or not 0 < cfg['minimum_valid_bootstrap_fraction'] <= 1:
        raise ValueError('Invalid analysis thresholds')
    data_path = ROOT / cfg['data_path']
    with data_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected CSV schema; use the documented field order')
        rows = list(reader)
    validate(rows)
    x, y = score(rows)
    stats = association(x, y, cfg)
    result = {'mode': cfg['mode'], 'n': len(rows), 'statistics': stats,
              'interpretation': 'Synthetic test only. No research conclusion.' if cfg['mode']=='synthetic_smoke_test'
              else ('Reject H0 at the specified alpha; association does not establish causation.' if stats['p_value_asymptotic_two_sided'] < cfg['alpha'] else 'Do not reject H0; this does not establish absence of association.'),
              'alpha': cfg['alpha'], 'seed': cfg['seed'],
              'data_sha256': hashlib.sha256(data_path.read_bytes()).hexdigest(),
              'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
              'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
              'guardrails': {'invalid_records': 0, 'missing_required_values': 0, 'duplicate_ids': 0},
              'runtime_seconds': round(time.perf_counter()-started, 4)}
    dest = ROOT / cfg['output_dir']; dest.mkdir(parents=True, exist_ok=True)
    with (dest/'scored.csv').open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['record_id','ai_frequency','ups_total'])
        w.writerows((r['record_id'], int(a), int(b)) for r,a,b in zip(rows,x,y))
    (dest/'results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config', default='configs/sample.json')
    args=parser.parse_args()
    try:
        p=Path(args.config);run(p if p.is_absolute() else ROOT/p)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr);sys.exit(1)
