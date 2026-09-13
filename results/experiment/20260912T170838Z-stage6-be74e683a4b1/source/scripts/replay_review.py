"""Replay an archived evaluator and its selected annotations, without model calls.

This file is copied into standalone history exports. It depends only on Python's
standard library and the evaluator archived in the selected review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def hashes(folder):
    folder = Path(folder)
    found = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks are not supported in replay inputs: ' + str(path))
        if path.is_file():
            found[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def verify_seal(folder):
    expected = read_json(Path(folder)/'seal.json')['files']
    actual = hashes(folder)
    actual.pop('seal.json', None)
    if actual != expected:
        raise ValueError('Seal mismatch: ' + str(folder))


def inside(path, root):
    return path == root or root in path.parents


def restrict_io(read_roots, write_root):
    """Fail closed on Python file access outside inputs/output/stdlib.

    This is a Python audit guard, not an operating-system sandbox. Network and
    process launch are disallowed during frozen evaluator execution.
    """
    read_roots = [Path(p).resolve() for p in read_roots]
    read_roots += [Path(sys.base_prefix).resolve(), Path(sys.prefix).resolve()]
    write_root = Path(write_root).resolve()

    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec') or event.startswith('socket.'):
            raise PermissionError('Replay cannot launch processes or use the network: ' + event)
        if event != 'open' or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        mode = args[1] if len(args) > 1 and isinstance(args[1], str) else ''
        writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)) or any(c in mode for c in 'wax+')
        if writing:
            if not inside(path, write_root):
                raise PermissionError('Replay write outside output: ' + str(path))
        elif not any(inside(path, root) for root in read_roots + [write_root]):
            raise PermissionError('Replay read outside bundle/stdlib: ' + str(path))

    sys.addaudithook(audit)


def replay(source, review, output, exported=False):
    source, review, output = (Path(p).resolve() for p in (source, review, output))
    if output.exists() or inside(output, source) or inside(output, review):
        raise ValueError('Choose a new output directory outside the archived inputs')
    verify_seal(source)
    verify_seal(review)
    manifest = read_json(source/'manifest.json')
    selected = read_json(review/'manifest.json')
    code = review/'evaluation-source'
    if hashes(code) != selected.get('evaluation_source_files'):
        raise ValueError('The exact selected evaluator sources are required')
    original_hashes = selected['source_files']
    if exported:
        receipt = read_json(source/'export.json')
        if receipt.get('source_hashes') != original_hashes or receipt.get('review_hashes') != hashes(review):
            raise ValueError('Export does not bind the selected review to its source')
        # The readable root overlays observations; these raw artifacts must match.
        for relative, digest in original_hashes.items():
            if relative.startswith('source/') or Path(relative).name in ('events.jsonl', 'result.json', 'manifest.json', 'language.json'):
                if hashlib.sha256((source/relative).read_bytes()).hexdigest() != digest:
                    raise ValueError('Export changed original input: ' + relative)
    elif hashes(source) != original_hashes:
        raise ValueError('Review belongs to a different original run')
    for trial, digest in selected.get('manual_input_hashes', {}).items():
        if hashlib.sha256((review/trial/'manual-review.json').read_bytes()).hexdigest() != digest:
            raise ValueError('Selected natural-language annotation changed: ' + trial)
    before = hashes(source), hashes(review)
    output.mkdir(parents=True)
    sys.dont_write_bytecode = True
    restrict_io([source, review, Path(__file__).parent], output)
    # A CLI subprocess ensures no currently installed experiment package is reused.
    if any(name == 'experiment' or name.startswith('experiment.') for name in sys.modules):
        raise RuntimeError('Replay must start in a fresh Python process')
    sys.path.insert(0, str(code))
    from experiment.records import write_trial_records
    from experiment.evaluation import REVIEW_POLICY_VERSION
    if REVIEW_POLICY_VERSION != selected['review_policy_version']:
        raise ValueError('Selected policy version does not match archived code')
    rows = []
    for result_path in sorted(source.glob('trial-*/result.json')):
        trial = result_path.parent.name
        annotation = review/trial/'manual-review.json'
        row = write_trial_records(result_path.parent, manifest['comparison_settings']['problem'],
                                  manifest['stage'], output/trial,
                                  annotation if annotation.exists() else None)
        if row != read_json(review/trial/'observation.json'):
            raise ValueError('Replayed observation differs from selected review: ' + trial)
        rows.append(row)
    summary = {'trials':len(rows), 'pending':sum(r['content_review_status']=='pending' for r in rows),
               'review_policy_version':REVIEW_POLICY_VERSION}
    for key in ('correct_claims', 'incorrect_claims', 'undetermined_claims'):
        summary[key] = sum(r[key] for r in rows) if all(r[key] is not None for r in rows) else None
    if summary != read_json(review/'summary.json'):
        raise ValueError('Replayed review summary differs')
    if before != (hashes(source), hashes(review)):
        raise ValueError('Replay modified archived inputs')
    result = {'matched':True, 'trials':len(rows), 'review_id':selected['review_id'],
              'policy':REVIEW_POLICY_VERSION, 'new_model_calls':0,
              'scope':'Reuses selected source-anchored annotations; not an independent re-annotation.',
              'io_guard':'Python file-access audit guard; network/process launch denied',
              'summary':summary}
    (output/'replay.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, help='Standalone readable export containing selected-review/')
    parser.add_argument('--source', type=Path, help='Original sealed experiment run')
    parser.add_argument('--review', type=Path, help='Exact sealed post-run review')
    parser.add_argument('--output', type=Path, required=True, help='New replay output directory')
    args = parser.parse_args()
    if args.export:
        if args.source or args.review:
            parser.error('Use --export OR --source with --review')
        source, review = args.export, args.export/'selected-review'
    else:
        if not args.source or not args.review:
            parser.error('--source and --review are required without --export')
        source, review = args.source, args.review
    print(json.dumps(replay(source, review, args.output, bool(args.export)), ensure_ascii=False))


if __name__ == '__main__':
    main()
