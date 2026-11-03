import json
import re
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import build_report  # noqa: E402
import process_data as pdp  # noqa: E402
import visualize  # noqa: E402

CFG = pdp.load_config('configs/research.yaml')


class BuildReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_report.load(CFG)
        cls.values = build_report.values(cls.data)

    def test_values_match_results_json(self):
        a = self.data['res']['survey']['association'][0]
        self.assertEqual(self.values['rhoMain'], f"{a['spearman_rho']:.3f}")
        self.assertEqual(self.values['nMain'], 285)
        self.assertEqual(self.values['nInjected'], 25)

    def test_template_has_no_unfilled_placeholders(self):
        template = (pdp.ROOT / 'reports/templates/paper_section_4.template.md').read_text(encoding='utf-8')
        keys = set(re.findall(r'\{\{(\w+)\}\}', template))
        available = set(self.values) | set(build_report.md_tables(self.data))
        self.assertEqual(keys - available, set())

    def test_latex_tables_are_booktabs_without_vertical_rules(self):
        tex = build_report.tex_tables(self.data)
        self.assertIn('\\toprule', tex)
        self.assertIn('\\bottomrule', tex)
        for spec in re.findall(r'\\begin\{tabular\}\{([^}]*)\}', tex):
            self.assertNotIn('|', spec)

    def test_latex_macro_names_are_letters_only(self):
        for name in self.values:
            self.assertRegex(name, r'^[A-Za-z]+$')


class SummaryFigureTests(unittest.TestCase):
    def test_four_panel_figure_written_as_pdf_and_300_dpi_png(self):
        from PIL import Image
        proc = pdp.ROOT / CFG['processed']['dir']
        res = json.loads((pdp.ROOT / CFG['reports']['results_json']).read_text(encoding='utf-8'))
        visualize.set_style()
        with tempfile.TemporaryDirectory() as tmp:
            paths = visualize.fig_summary_panels(
                pd.read_csv(proc / 'survey_group_summary.csv'), res['survey']['association'],
                res['survey']['models_main'], pd.read_csv(proc / 'pipeline_latency_summary.csv'),
                pd.read_csv(proc / 'pipeline_speedup.csv'), Path(tmp), 300)
            self.assertEqual(sorted(p.suffix for p in paths), ['.pdf', '.png'])
            with Image.open(paths[1]) as png:
                self.assertGreaterEqual(round(png.info['dpi'][0]), 300)

    def test_figure_text_has_no_missing_glyphs(self):
        res = json.loads((pdp.ROOT / CFG['reports']['results_json']).read_text(encoding='utf-8'))
        visualize.set_style()
        with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            visualize.fig_effect_forest(res['survey']['association'], res['survey']['models_main'],
                                        Path(tmp), 100)
        self.assertEqual([str(w.message) for w in caught if 'missing from font' in str(w.message)], [])


if __name__ == '__main__':
    unittest.main()
