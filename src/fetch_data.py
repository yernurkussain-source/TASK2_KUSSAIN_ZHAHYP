"""Download the two public source workbooks (Mendeley Data V1) and verify their SHA-256 hashes.

The workbooks are not committed to Git; they are written to data/raw/ (ignored). Re-running is safe:
files that already match the expected hash are left untouched.

Usage::

    python src/fetch_data.py --config configs/research.yaml
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_data  # noqa: E402

ROOT = process_data.ROOT
URL = 'https://data.mendeley.com/public-files/datasets/88pv88j8jb/files/{file_id}/file_downloaded'


def fetch(cfg: dict, base_url: str = URL, timeout: float = 60.0) -> list[Path]:
    written = []
    for key, spec in cfg['source']['files'].items():
        dest = ROOT / spec['path']
        if dest.exists() and process_data.sha256_file(dest) == spec['sha256']:
            print(f'{key}: already present and verified ({dest.relative_to(ROOT)})')
            continue
        url = base_url.format(file_id=spec['mendeley_file_id'])
        req = urllib.request.Request(url, headers={'User-Agent': 'task3-research-pipeline/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed public URL
            payload = resp.read()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != spec['sha256']:
            raise ValueError(f'{key}: SHA-256 mismatch ({digest}); the remote file is not Mendeley V1')
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + '.part')
        tmp.write_bytes(payload)
        tmp.replace(dest)
        print(f'{key}: downloaded {len(payload)} bytes, SHA-256 verified -> {dest.relative_to(ROOT)}')
        written.append(dest)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--config', default='configs/research.yaml')
    args = parser.parse_args(argv)
    try:
        fetch(process_data.load_config(args.config))
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}\nDownload manually from https://doi.org/10.17632/88pv88j8jb.1 into data/raw/ '
              'using the file names in configs/research.yaml.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
