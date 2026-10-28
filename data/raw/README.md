# Raw data

* `test_run.jsonl` and `test_run_meta.json`: the Week 7 benchmark log written by `python src/collector.py` (committed).
* `sharma2026_raw.xlsx` and `sharma2026_cleaned.xlsx`: the public source workbooks. They are not committed; `python src/fetch_data.py` downloads them here and verifies the SHA-256 hashes listed in `configs/research.yaml`.
