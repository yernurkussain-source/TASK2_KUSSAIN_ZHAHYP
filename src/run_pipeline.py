"""One-command entry point for Task 3.

Default: re-code the source workbooks if they are in data/raw/ (otherwise use the committed
data/processed/ CSVs), aggregate statistics, and render all figures.

    python src/run_pipeline.py                 # analysis + figures (about 10 s)
    python src/run_pipeline.py --fetch         # download and verify the public workbooks first
    python src/run_pipeline.py --collect       # also re-run the Week 7 benchmark (about 2-3 min)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import collector  # noqa: E402
import fetch_data  # noqa: E402
import process_data  # noqa: E402
import visualize  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run the Task 3 pipeline.')
    parser.add_argument('--config', default='configs/research.yaml')
    parser.add_argument('--fetch', action='store_true', help='download the source workbooks (internet required)')
    parser.add_argument('--collect', action='store_true', help='re-collect data/raw/test_run.jsonl before analysis')
    args = parser.parse_args(argv)
    started = time.perf_counter()
    cfg = process_data.load_config(args.config)
    if args.fetch:
        fetch_data.fetch(cfg)
    if args.collect:
        collector.main(['--config', args.config])
    process_data.main(['--config', args.config])
    visualize.main(['--config', args.config])
    print(f'pipeline finished in {time.perf_counter() - started:.1f} s')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
