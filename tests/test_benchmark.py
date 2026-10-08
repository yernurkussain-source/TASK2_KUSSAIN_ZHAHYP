import csv
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from benchmark import validate, score, association, ROOT

class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        with (ROOT/'data/sample/survey_sample.csv').open() as f:
            self.rows=list(csv.DictReader(f))
    def test_known_totals(self):
        validate(self.rows)
        self.assertEqual(score(self.rows)[1].tolist(), [10,14,16,21,16,9,14,15,21,15])
    def test_bad_item(self):
        self.rows[0]['ups_1']='0'
        with self.assertRaises(ValueError): validate(self.rows)
    def test_missing(self):
        self.rows[0]['ups_1']=''
        with self.assertRaises(ValueError): validate(self.rows)
    def test_duplicate(self):
        self.rows[1]['record_id']=self.rows[0]['record_id']
        with self.assertRaises(ValueError): validate(self.rows)
    def test_ineligible(self):
        self.rows[0]['education']='higher_secondary'
        with self.assertRaises(ValueError): validate(self.rows)
    def test_constant(self):
        with self.assertRaises(ValueError): association(np.ones(10), np.arange(10), {})
    def test_known_correlation_and_repeatability(self):
        cfg={'seed':7,'bootstrap_resamples':100,'minimum_valid_bootstrap_fraction':0.95}
        x=np.arange(10);y=-x
        a=association(x,y,cfg);b=association(x,y,cfg)
        self.assertAlmostEqual(a['spearman_rho'],-1)
        self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
