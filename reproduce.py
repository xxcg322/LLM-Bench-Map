"""Reproduce published analyses from local data, without network or model calls."""
from __future__ import annotations
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from integrity import digest, verify_release

ROOT = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'code/extended'/f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def require_equal(actual, expected, name):
    if actual != expected:
        raise ValueError(f'Reproduction mismatch: {name}')


def reproduce(work):
    inputs = work/'inputs'
    shutil.copytree(ROOT/'data/inputs', inputs)
    (inputs/'results.json').write_bytes(gzip.decompress((inputs/'results.json.gz').read_bytes()))
    output = work/'base'
    subprocess.run([sys.executable, '-B', str(ROOT/'data/code/run.py'),
                    '--input-dir', str(inputs), '--output', str(output)], check=True)
    compared = []
    for pattern in ('tables/*.csv', 'figures/*_data.csv'):
        for expected in sorted((ROOT/'data').glob(pattern)):
            name = expected.relative_to(ROOT/'data')
            require_equal(digest(output/name), digest(expected), str(name))
            compared.append(str(name))
    for name in ('papers.csv', 'design_analysis.json', 'roles.json', 'flow.json', 'validation.json'):
        require_equal(digest(output/name), digest(ROOT/'data'/name), name)
        compared.append(name)
    # Text and code integrity is checked separately from statistical reproduction.
    for expected in sorted((ROOT/'data').glob('*.md')):
        require_equal(digest(output/expected.name), digest(expected), expected.name)
    require_equal(digest(output/'claim_ledger.csv'), digest(ROOT/'data/claim_ledger.csv'), 'claim_ledger.csv')
    windows = module('time_windows')
    windows.ROOT, windows.BASE = ROOT, ROOT/'data'
    previous_argv = sys.argv[:]
    try:
        sys.argv = ['time_windows.py', '--output', str(work/'time_windows')]
        windows.main()
    finally:
        sys.argv = previous_argv
    require_equal(digest(work/'time_windows/analysis.json'),
                  digest(ROOT/'expected/time_windows/analysis.json'), 'time_windows/analysis.json')
    errors = module('error_sensitivity')
    errors.ROOT, errors.BASE = ROOT, ROOT/'diagnostics'
    errors.DATA, errors.OUT = ROOT/'data', work/'error_sensitivity'
    errors.main()
    require_equal(digest(work/'error_sensitivity/scenarios.csv'),
                  digest(ROOT/'expected/error_sensitivity/scenarios.csv'), 'error_sensitivity/scenarios.csv')
    result = dict(status='passed', base_numeric_files=len(compared),
                  time_window_analysis_matched=True, error_scenarios_matched=True,
                  documentation_matched=True, semantic_accuracy_validated=False)
    (work/'reproduction_check.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


def main():
    if not __debug__:
        raise SystemExit('Run without -O: numerical assertions must remain enabled.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Keep regenerated files in a new directory')
    parser.add_argument('--verify-only', action='store_true', help='Check packaged file integrity only')
    args = parser.parse_args()
    manifest = verify_release(ROOT)
    print(f'Release integrity verified: {len(manifest["files"])} files', flush=True)
    if args.verify_only:
        return
    if args.output:
        work = args.output.resolve()
        if work.exists():
            raise SystemExit('Choose a new output directory; existing files are never overwritten.')
        if work == ROOT or ROOT.is_relative_to(work):
            raise SystemExit('The output must not contain the release directory.')
        work.mkdir(parents=True)
        reproduce(work)
        print(f'Regenerated files retained in: {work}')
    else:
        with tempfile.TemporaryDirectory(prefix='llm-bench-map-') as directory:
            reproduce(Path(directory))


if __name__ == '__main__':
    main()
