import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import collector  # noqa: E402
import process_data as pdp  # noqa: E402

CFG = pdp.load_config('configs/research.yaml')


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.pool = collector.load_rows(pdp.ROOT / CFG['benchmark']['input_path'])

    def test_workload_has_unique_ids_and_task2_schema(self):
        rows = collector.make_workload(self.pool, 40, np.random.default_rng(1))
        self.assertEqual(len({r['record_id'] for r in rows}), 40)
        self.assertEqual(list(rows[0]), pdp.CODED_FIELDS)

    def test_every_edge_case_is_rejected_by_both_implementations(self):
        for kind in CFG['benchmark']['edge_cases']:
            rows = collector.inject_edge_case(collector.make_workload(self.pool, 30, np.random.default_rng(2)),
                                              kind, np.random.default_rng(3))
            for impl in CFG['benchmark']['implementations']:
                with self.subTest(kind=kind, impl=impl), self.assertRaises(ValueError):
                    collector.target(rows, impl, 100, 1)

    def test_small_collection_writes_valid_jsonl(self):
        cfg = copy.deepcopy(CFG)
        cfg['benchmark']['edge_case_rate'] = 0.5
        cfg['benchmark']['bootstrap_resamples'] = 100
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run.jsonl'
            records = collector.collect(cfg, out_path=out, workloads=[30], warmup=2, runs=6)
            lines = [json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]
            meta = json.loads((Path(tmp) / Path(CFG['benchmark']['meta_path']).name).read_text())
        self.assertEqual(len(lines), len(records))
        self.assertEqual(sum(r['phase'] == 'warmup' for r in lines), 4)  # 2 runs x 2 implementations
        self.assertEqual(sum(r['status'] == 'error' for r in lines), 0)
        injected = [r for r in lines if r['edge_case']]
        self.assertTrue(all(r['status'] == 'rejected' for r in injected))
        self.assertTrue(all(r['latency_ms'] > 0 for r in lines))
        self.assertIn('cpu_count_logical', meta['environment'])


if __name__ == '__main__':
    unittest.main()
