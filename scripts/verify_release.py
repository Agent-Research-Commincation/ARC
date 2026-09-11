"""Verify a portable release and replay its selected reviews and numeric analysis.

Usage: python3 scripts/verify_release.py --bundle . --output /tmp/new-replay
Only Python 3.9+ is required. No Codex login, network or model calls are used.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay_review import hashes, inside, read_json, verify_seal


def check_bundle_path(root, relative):
    path = (root/relative).resolve()
    if Path(relative).is_absolute() or not inside(path, root):
        raise ValueError('Operational paths must stay within the bundle: ' + relative)
    return path


def compare_data(expected, actual, at='root'):
    """All historical data values must match; only location/time metadata differs."""
    metadata = {'generated_at', 'selected_collection', 'source', 'review', 'readable', 'transcript', 'source_events'}
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ValueError('Type differs at ' + at)
        for key, value in expected.items():
            if key in metadata:
                continue
            if key not in actual:
                raise ValueError('Missing value at ' + at + '.' + key)
            compare_data(value, actual[key], at + '.' + key)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError('List differs at ' + at)
        for i, (a, b) in enumerate(zip(expected, actual)):
            compare_data(a, b, at + '[' + str(i) + ']')
    elif isinstance(expected, float):
        if type(actual) not in (int, float) or not math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-10):
            raise ValueError('Numeric value differs at ' + at)
    elif type(expected) is not type(actual) or expected != actual:
        raise ValueError('Value differs at ' + at)


def check_links(root):
    files = [root/'README.md', *sorted((root/'docs').glob('*.md'))]
    files += sorted((root/'results/readable').rglob('*.md'))
    files += sorted((root/'results/analysis').rglob('*.md'))
    count = 0
    for path in files:
        if any(part in ('source', 'evaluation-source', 'selected-review') for part in path.parts):
            continue
        for target in re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)', path.read_text()):
            target = unquote(target.strip().strip('<>'))
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            target = target.split('#')[0]
            resolved = (path.parent/target).resolve()
            if Path(target).is_absolute() or not inside(resolved, root) or not resolved.exists():
                raise ValueError('Nonportable reader link: ' + str(path.relative_to(root)) + ' -> ' + target)
            count += 1
    return count


def run_python(root, script, arguments, cwd):
    result = subprocess.run([sys.executable, '-I', '-B', str(root/'scripts'/script), *map(str, arguments)],
                            cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(script + ' failed:\n' + result.stdout + result.stderr)
    return result.stdout


def verify(bundle, output):
    root, output = Path(bundle).resolve(), Path(output).resolve()
    if output.exists() or inside(output, root):
        raise ValueError('Choose a new replay output outside the bundle')
    expected = read_json(root/'checksums.json')['files']
    before = hashes(root)
    actual = dict(before)
    actual.pop('checksums.json', None)
    if actual != expected:
        raise ValueError('Bundle checksums do not match')
    manifest = read_json(root/'release.json')
    collection = read_json(check_bundle_path(root, manifest['collection']))
    output.mkdir(parents=True)
    summaries = []
    for record in collection['records']:
        source = check_bundle_path(root, record['source'])
        review = check_bundle_path(root, record['review'])
        readable = check_bundle_path(root, record['readable'])
        verify_seal(source)
        verify_seal(review)
        verify_seal(readable)
        text = run_python(root, 'replay_review.py', ['--source', source, '--review', review,
                          '--output', output/('stage-' + str(record['stage']))], output)
        summaries.append(json.loads(text))
        print('선택한 평가 재현: %d단계 · %d회 일치' % (record['stage'], summaries[-1]['trials']), flush=True)
    run_python(root, 'derive_release.py', ['--root', root, '--output', output/'analysis'], output)
    for name in ('comparison.json', 'trials.json', 'case-evidence.json'):
        compare_data(read_json(root/'reference/analysis'/name), read_json(output/'analysis'/name), name)
        compare_data(read_json(root/manifest['analysis']/name), read_json(output/'analysis'/name), 'published.' + name)
    # Report assertions also bind the headline conclusions to the replayed data.
    trials = read_json(output/'analysis/trials.json')
    headline = {'trials':len(trials), 'successes':sum(t['success'] for t in trials),
                'optimal':sum(t['optimal'] for t in trials),
                'runner_turns':sum(t['actions'] for t in trials),
                'model_cost_estimate_usd':sum(t['model_cost_estimate_usd'] for t in trials),
                'incorrect_claims':sum(t['incorrect_claims'] for t in trials),
                'undetermined_claims':sum(t['undetermined_claims'] for t in trials)}
    compare_data(manifest['expected_results'], headline, 'expected_results')
    links = check_links(root)
    if before != hashes(root):
        raise ValueError('Verification modified the bundle')
    result = {'verified':True, 'release_id':manifest['release_id'], **headline,
              'review_trials_replayed':sum(s['trials'] for s in summaries),
              'reader_links_checked':links, 'bundle_files_checked':len(expected),
              'historical_numeric_and_case_data_match':True, 'bundle_unchanged':True,
              'new_model_calls':0,
              'isolation':'Fresh -I -B Python processes; evaluator/analysis audit guards allow bundled inputs and stdlib only; network and process launch denied in workers.',
              'natural_language_scope':'Replays selected AI annotations; independent human interpretation remains unmeasured.'}
    (output/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.bundle, args.output)
