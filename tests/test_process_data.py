import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import benchmark  # noqa: E402
import process_data as pdp  # noqa: E402

CFG = pdp.load_config('configs/research.yaml')
RAW_PRESENT = all((pdp.ROOT / f['path']).exists() for f in CFG['source']['files'].values())


class CodingTests(unittest.TestCase):
    def test_parse_age(self):
        self.assertEqual(pdp.parse_age(22), (22.0, 22.0, False))
        self.assertEqual(pdp.parse_age('22 years '), (22.0, 22.0, False))
        exact, lower, ambiguous = pdp.parse_age('23+')
        self.assertTrue(np.isnan(exact))
        self.assertEqual((lower, ambiguous), (23.0, True))
        self.assertTrue(np.isnan(pdp.parse_age('unknown')[1]))

    def test_code_ups_text_and_numbers(self):
        self.assertEqual(pdp.code_ups(' Agree slightly'), 2.0)
        self.assertEqual(pdp.code_ups('Agree Very Much'), 4.0)
        self.assertEqual(pdp.code_ups(3), 3.0)
        self.assertTrue(np.isnan(pdp.code_ups(5)))
        self.assertTrue(np.isnan(pdp.code_ups('')))

    @unittest.skipUnless(RAW_PRESENT, 'source workbooks not downloaded (python src/fetch_data.py)')
    def test_prepare_counts_match_documented_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = json.loads(json.dumps(CFG))
            cfg['processed'] = {'dir': tmp, 'main': f'{tmp}/main.csv', 'raw_coded': f'{tmp}/raw.csv',
                                'metrics_summary': f'{tmp}/m.csv'}
            audit = pdp.prepare(cfg)
            committed = pd.read_csv(pdp.ROOT / CFG['processed']['main'])
            regenerated = pd.read_csv(f'{tmp}/main.csv')
        self.assertEqual(audit['main_n'], 285)
        self.assertEqual(audit['sensitivity_a_n'], 303)
        self.assertEqual(audit['sensitivity_b_n'], 327)
        self.assertEqual(audit['supplied_total_agreement'], 300)
        pd.testing.assert_frame_equal(committed, regenerated)


class StatisticsTests(unittest.TestCase):
    def test_vectorised_bootstrap_equals_task2_loop(self):
        rng = np.random.default_rng(3)
        x = rng.integers(1, 5, 120)
        y = rng.integers(6, 25, 120)
        loop = benchmark.association(x, y, {'seed': 11, 'bootstrap_resamples': 400,
                                            'minimum_valid_bootstrap_fraction': 0.95})
        vec = pdp.spearman_bootstrap(x, y, 400, 11)
        vec.pop('_bootstrap_estimates')
        self.assertEqual(loop['valid_bootstrap_resamples'], vec['valid_bootstrap_resamples'])
        self.assertAlmostEqual(loop['spearman_rho'], vec['spearman_rho'], places=12)
        np.testing.assert_allclose(loop['ci95_percentile_bootstrap'], vec['ci95_percentile_bootstrap'], atol=1e-12)

    def test_degenerate_resamples_are_skipped_like_task2(self):
        x = np.array([1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
        y = np.arange(10)
        loop = benchmark.association(x, y, {'seed': 5, 'bootstrap_resamples': 300,
                                            'minimum_valid_bootstrap_fraction': 0.5})
        vec = pdp.spearman_bootstrap(x, y, 300, 5, 0.5)
        self.assertGreater(vec['skipped_bootstrap_resamples'], 0)
        self.assertEqual(loop['skipped_bootstrap_resamples'], vec['skipped_bootstrap_resamples'])

    def test_constant_variable_rejected(self):
        with self.assertRaises(ValueError):
            pdp.spearman_bootstrap(np.ones(10), np.arange(10), 100, 1)

    def test_holm_known_values(self):
        self.assertEqual(pdp.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_cronbach_alpha_perfectly_parallel_items(self):
        base = np.arange(1, 11, dtype=float)
        self.assertAlmostEqual(pdp.cronbach_alpha(np.column_stack([base, base, base])), 1.0)

    def test_cliffs_delta_bounds(self):
        self.assertEqual(pdp.cliffs_delta([5, 6, 7], [1, 2, 3]), 1.0)
        self.assertEqual(pdp.cliffs_delta([1, 2], [1, 2]), 0.0)


class BenchmarkAggregationTests(unittest.TestCase):
    def _log(self):
        rows = []
        for impl in ['baseline_loop', 'vectorized']:
            for rep in range(8):
                phase = 'warmup' if rep < 2 else 'benchmark'
                latency = 1000.0 if rep == 0 else 10.0 + rep
                edge = 'missing_item' if rep == 7 else None
                rows.append({'run_id': len(rows) + 1, 'phase': phase, 'implementation': impl, 'n_records': 50,
                             'rep': rep, 'status': 'rejected' if edge else 'ok', 'edge_case': edge,
                             'latency_ms': latency, 'rho': 0.3, 'ci_low': 0.1, 'ci_high': 0.5})
        return pd.DataFrame(rows)

    def test_warmup_is_excluded(self):
        bench, warm = pdp.filter_warmup(self._log())
        self.assertEqual(len(warm), 4)
        self.assertTrue((bench['latency_ms'] < 1000).all())

    def test_unknown_phase_raises(self):
        log = self._log()
        log.loc[0, 'phase'] = 'cold'
        with self.assertRaises(ValueError):
            pdp.filter_warmup(log)

    def test_latency_summary_and_guardrails(self):
        bench, _ = pdp.filter_warmup(self._log())
        s = pdp.latency_summary(bench, 200, 1).set_index('implementation')
        self.assertEqual(s.loc['vectorized', 'ok_runs'], 5)
        self.assertEqual(s.loc['vectorized', 'p50_ms'], 14.0)
        self.assertEqual(s.loc['vectorized', 'rejection_detection_rate'], 1.0)
        self.assertEqual(s.loc['vectorized', 'unexpected_error_rate'], 0.0)
        self.assertLessEqual(s.loc['vectorized', 'p50_ci_low'], 14.0)

    def test_outlier_flag_is_non_destructive(self):
        values = pd.Series([10.0, 11, 12, 11, 10, 95])
        flags = pdp.flag_outliers_iqr(values)
        self.assertEqual(int(flags.sum()), 1)
        self.assertEqual(len(values), 6)

    def test_malformed_jsonl_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad.jsonl'
            p.write_text('{"run_id": 1}\n{not json}\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                pdp.load_jsonl(p)


if __name__ == '__main__':
    unittest.main()
