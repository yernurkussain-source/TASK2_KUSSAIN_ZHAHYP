"""Week 7 measurement harness for the Task 2 analysis pipeline.

The target function is the Task 2 pipeline itself: validate records, score UPS, then estimate the
Spearman correlation with a percentile-bootstrap interval. Two implementations are timed on
identical inputs and identical bootstrap resamples:

* ``baseline_loop``: the unchanged Task 2 code (``benchmark.association``), one SciPy call per resample;
* ``vectorized``: ``process_data.spearman_bootstrap``, which ranks all resamples in blocks.

Design rules (see docs/METHODOLOGY.md, Task 3 addendum):

* Each (implementation, workload) condition starts with ``warmup_runs`` labelled ``phase="warmup"``;
  they are written to the log but excluded from every summary statistic.
* Only the target call is inside the timer (``time.perf_counter_ns``). Workload generation,
  error handling and JSON serialisation happen outside it; records are buffered and written at the end.
* Workloads are drawn with replacement from the 285 real main-sample records (empirical distribution,
  not a uniform ``randint`` generator).
* A fixed share of benchmark runs receives an invalid batch (edge case). Those runs must be rejected;
  any other exception is logged as an unexpected error. Nothing is silently dropped.
* The order of the two implementations alternates between repetitions (ABBA) to spread drift.

Usage::

    python src/collector.py --config configs/research.yaml
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark  # noqa: E402  (Task 2 module, unchanged)
import process_data  # noqa: E402

ROOT = process_data.ROOT
SCHEMA_VERSION = 1


def load_rows(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return [{k: r[k] for k in process_data.CODED_FIELDS} for r in rows]


def make_workload(pool: list[dict], n: int, rng: np.random.Generator) -> list[dict]:
    idx = rng.integers(0, len(pool), n)
    out = []
    for i, j in enumerate(idx, 1):
        r = dict(pool[j])
        r['record_id'] = f'W{i:05d}'
        out.append(r)
    return out


def inject_edge_case(rows: list[dict], kind: str, rng: np.random.Generator) -> list[dict]:
    rows = [dict(r) for r in rows]
    i = int(rng.integers(0, len(rows)))
    if kind == 'missing_item':
        rows[i]['ups_3'] = ''
    elif kind == 'out_of_range':
        rows[i]['ups_2'] = '5'
    elif kind == 'duplicate_id':
        rows[i]['record_id'] = rows[(i + 1) % len(rows)]['record_id']
    elif kind == 'constant_exposure':
        for r in rows:
            r['ai_frequency'] = '3'
    else:
        raise ValueError(f'Unknown edge case {kind}')
    return rows


def target(rows: list[dict], implementation: str, resamples: int, seed: int) -> dict:
    """The measured unit of work: validate -> score -> association with bootstrap CI."""
    benchmark.validate(rows)
    x, y = benchmark.score(rows)
    if implementation == 'baseline_loop':
        return benchmark.association(x, y, {'seed': seed, 'bootstrap_resamples': resamples,
                                            'minimum_valid_bootstrap_fraction': 0.95})
    if implementation == 'vectorized':
        res = process_data.spearman_bootstrap(x, y, resamples, seed, 0.95)
        res.pop('_bootstrap_estimates')
        return res
    raise ValueError(f'Unknown implementation {implementation}')


def environment_metadata() -> dict:
    meta = {
        'python': platform.python_version(), 'implementation': platform.python_implementation(),
        'os': platform.platform(), 'machine': platform.machine(), 'cpu_count_logical': os.cpu_count(),
        'cpu_model': _cpu_model(), 'ram_total_gb': _ram_gb(),
        'packages': process_data.versions(),
        'docker': Path('/.dockerenv').exists(),
    }
    try:
        meta['git_commit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True,
                                            text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        meta['git_commit'] = None
    return meta


def _cpu_model() -> str | None:
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.lower().startswith('model name'):
                return line.split(':', 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or None


def _ram_gb() -> float | None:
    try:
        return round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30, 2)
    except (ValueError, OSError, AttributeError):
        pass
    try:  # Windows
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('sullAvailExtendedVirtual', ctypes.c_ulonglong)]
        stat = MemoryStatus()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return round(stat.ullTotalPhys / 2**30, 2)
    except Exception:  # noqa: BLE001 - metadata is best effort
        return None


def collect(cfg: dict, out_path: Path | None = None, workloads=None, warmup=None, runs=None) -> list[dict]:
    b = cfg['benchmark']
    workloads = workloads or b['workloads_n_records']
    warmup = b['warmup_runs'] if warmup is None else warmup
    runs = b['benchmark_runs'] if runs is None else runs
    impls = list(b['implementations'])
    pool = load_rows(ROOT / b['input_path'])
    edge_rng = np.random.default_rng(cfg['seed'] + 1)
    session = uuid.uuid4().hex[:12]
    records = []
    run_id = 0
    for n in workloads:
        for rep in range(warmup + runs):
            phase = 'warmup' if rep < warmup else 'benchmark'
            batch_seed = int(cfg['seed'] + 1000 * n + rep)
            rows = make_workload(pool, n, np.random.default_rng(batch_seed))
            edge = None
            if phase == 'benchmark' and edge_rng.random() < b['edge_case_rate']:
                edge = str(edge_rng.choice(b['edge_cases']))
                rows = inject_edge_case(rows, edge, edge_rng)
            order = impls if rep % 2 == 0 else impls[::-1]
            for impl in order:
                run_id += 1
                status, err_type, err_msg, res = 'ok', None, None, None
                t0 = time.perf_counter_ns()
                try:
                    res = target(rows, impl, b['bootstrap_resamples'], batch_seed)
                except ValueError as exc:
                    t1 = time.perf_counter_ns()
                    status = 'rejected' if edge else 'error'
                    err_type, err_msg = 'validation_error', str(exc)
                except Exception as exc:  # noqa: BLE001 - every failure is logged, never dropped
                    t1 = time.perf_counter_ns()
                    status, err_type, err_msg = 'error', type(exc).__name__, str(exc)
                else:
                    t1 = time.perf_counter_ns()
                    if edge:  # an invalid batch that passed validation is a guardrail failure
                        status, err_type, err_msg = 'error', 'invalid_batch_accepted', edge
                records.append({
                    'schema_version': SCHEMA_VERSION, 'session_id': session, 'run_id': run_id,
                    'timestamp_utc': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                    'phase': phase, 'implementation': impl, 'n_records': n, 'rep': rep,
                    'batch_seed': batch_seed, 'bootstrap_resamples': b['bootstrap_resamples'],
                    'edge_case': edge, 'status': status, 'error_type': err_type, 'error_message': err_msg,
                    'latency_ns': t1 - t0, 'latency_ms': (t1 - t0) / 1e6,
                    'rho': None if res is None else res['spearman_rho'],
                    'ci_low': None if res is None else res['ci95_percentile_bootstrap'][0],
                    'ci_high': None if res is None else res['ci95_percentile_bootstrap'][1],
                    'valid_resamples': None if res is None else res['valid_bootstrap_resamples'],
                })
    out_path = out_path or ROOT / b['log_path']
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8', newline='\n') as f:
        for r in records:
            f.write(json.dumps(r, allow_nan=False) + '\n')
    meta = {'session_id': session, 'config_sha256': cfg['_config_sha256'],
            'input_sha256': process_data.sha256_file(ROOT / b['input_path']),
            'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'records': len(records), 'environment': environment_metadata(),
            'design': {k: b[k] for k in ('warmup_runs', 'benchmark_runs', 'bootstrap_resamples',
                                         'workloads_n_records', 'implementations', 'edge_case_rate', 'edge_cases')},
            'recommended_isolation': 'docker run --rm --cpus=2 --memory=2g ...; close background applications'}
    meta_path = out_path.with_name(Path(b['meta_path']).name) if out_path != ROOT / b['log_path'] else ROOT / b['meta_path']
    meta_path.write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8', newline='\n')
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description='Collect warm-up and benchmark timings as JSONL.')
    parser.add_argument('--config', default='configs/research.yaml')
    args = parser.parse_args(argv)
    cfg = process_data.load_config(args.config)
    started = time.perf_counter()
    records = collect(cfg)
    bench = [r for r in records if r['phase'] == 'benchmark']
    print(f"wrote {len(records)} records ({len(records) - len(bench)} warm-up) to {cfg['benchmark']['log_path']} "
          f"in {time.perf_counter() - started:.1f} s; unexpected errors: {sum(r['status'] == 'error' for r in bench)}")


if __name__ == '__main__':
    main()
