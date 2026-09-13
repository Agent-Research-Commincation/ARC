"""Post-run review of exactly stages 2..6, trials 27..28. No model calls."""
import collections
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/hyohyeon/Desktop/agent-research-commincation')
PLAN = '20260912T170838Z-plan-22772406666b'
BASE = ROOT / '.worktree' / PLAN
sys.path.insert(0, str(BASE / 'stage-2'))
from experiment.records import write_trial_records
from experiment.evaluation import REVIEW_POLICY_VERSION
from experiment.protocols import source_frame
from experiment.problem import evaluate

def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}

def code_hashes(stage):
    base = BASE / f'stage-{stage}'
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((base / 'experiment').glob('*.py'))}

code = code_hashes(2)
assert all(code_hashes(s) == code for s in range(2, 7))
specs = []
protected = {}
for stage in range(2, 7):
    for number in range(27, 29):
        matches = list((BASE / f'stage-{stage}' / 'results/experiment').glob(f'*-stage{stage}-*/trial-{number:02d}'))
        assert len(matches) == 1
        folder = matches[0]
        result = json.loads((folder / 'result.json').read_text())
        assert result.get('finished_at') and result['status'] not in ('running', 'pending')
        specs.append((stage, number, folder, result))
        protected[str(folder)] = hashes(folder)

rows = []
for stage, number, folder, result in specs:
    manifest = json.loads((folder.parent / 'manifest.json').read_text())
    problem = manifest['comparison_settings']['problem']
    output = OUT / f'stage-{stage}' / f'trial-{number:02d}'
    review = write_trial_records(folder, problem, stage, output)
    events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
    language = json.loads((folder / 'language.json').read_text()) if (folder / 'language.json').exists() else None
    packets = [e['params'] for e in events if e['method'] == 'experiment/packet']
    applied = {e['params']['request_id']: e['params'] for e in events if e['method'] == 'experiment/applied'}
    rejected = {e['params']['request_id']: e['params'] for e in events if e['method'] == 'experiment/rejected'}
    controls, state = [], {}
    for event in events:
        if event['method'] != 'experiment/response_received':
            continue
        p = event['params']; request = p['request_id']
        try:
            action = json.loads(p['raw_response'])
        except (ValueError, TypeError):
            action = None
        before = dict(state)
        if request in applied:
            if applied[request]['action'] == 'submit':
                state[p['actor']] = {x['meeting']: x['slot'] for x in action['schedule']}
            elif applied[request]['action'] == 'revise':
                state = {}
        controls.append({'request_id': request, 'actor': p['actor'], 'phase': p['phase'],
                         'event_sequence': event['sequence'], 'raw_response': p['raw_response'],
                         'action': action, 'applied': applied.get(request), 'rejected': rejected.get(request),
                         'delivered_messages': [x['sequence'] for x in packets if x['request_id'] == request],
                         'submissions_before': before, 'submissions_after': dict(state)})
    assert state == result['submissions']
    messages, full = [], []
    for packet in packets:
        if packet['phase'] != 'task': continue
        frame = source_frame(stage, packet['sender_source'], language)
        m = {'message': packet['sequence'], 'sender': packet['sender'], 'receiver': packet['receiver'],
             'request_id': packet['request_id'], 'kind': frame['kind'], 'schedule': frame['schedule'],
             'fact_count': len(frame['facts']), 'summary_count': len(frame['summaries']),
             'questions': frame['questions'], 'requests': frame['requests'], 'evaluations': frame['evaluations'],
             'reasons': frame['reasons'], 'references': frame['references']}
        if set(frame['schedule']) == {'M1', 'M2', 'M3'}:
            m['candidate_evaluation'] = evaluate(problem, frame['schedule'])
            full.append({'message': packet['sequence'], 'sender': packet['sender'], 'kind': frame['kind'],
                         'schedule': frame['schedule'], 'evaluation': m['candidate_evaluation']})
        messages.append(m)
    claims = [c for m in review['messages'] for c in m['claims']]
    counts = collections.Counter(x['applied']['action'] for x in controls if x['applied'] and x['phase'] == 'task')
    rows.append({'stage': stage, 'trial': number, 'source': str(folder), 'output': str(output),
                 'comparison_group': manifest['comparison_group'], 'status': result['status'],
                 'operational_status': result['operational_status'], 'score': result['evaluation']['score'],
                 'quality_gap': result['quality_gap'], 'task_messages': review['task_messages'],
                 'all_phase_messages': len(packets),
                 **{k: review[k] for k in ('correct_claims','incorrect_claims','undetermined_claims','codec_errors')},
                 'first_full_candidate': full[0] if full else None,
                 'first_full_proposal': next((x for x in full if x['kind'] == 'propose'), None),
                 'full_candidates': full, 'changed_proposals': review['changed_proposal_messages'],
                 'explicit_revisions': review['explicit_revisions'],
                 'questions': sum(len(m['questions']) for m in messages),
                 'typed_claims': review['claim_counts_by_type'],
                 'incorrect_details': [c for c in claims if c['correct'] is False],
                 'undetermined_details': [c for c in claims if c['correct'] is None],
                 'messages': messages, 'protocol_rejections': list(rejected.values()),
                 'submissions': result['submissions'], 'control_sequence': controls,
                 'applied_task_controls': dict(counts), 'result_actions': result['actions'],
                 'wait_events': [e['params'] for e in events if e['method'] == 'experiment/wait_observed'],
                 'revision_events': [e['params'] for e in events if e['method'] == 'experiment/submissions_invalidated']})
    print(stage, number, review['correct_claims'], review['incorrect_claims'], review['undetermined_claims'],
          'score', result['evaluation']['score'], 'controls', dict(counts), flush=True)

assert all(hashes(Path(folder)) == expected for folder, expected in protected.items())
assert all(code_hashes(s) == code for s in range(2, 7))
(OUT / 'audit-index.json').write_text(json.dumps({'plan_id': PLAN, 'scope': 'stages 2..6, trials 27..28 only',
    'review_policy_version': REVIEW_POLICY_VERSION, 'rows': rows, 'protected_trial_hashes': protected,
    'evaluator_source_hashes': code, 'all_stage_evaluator_sources_equal': True,
    'original_trial_files_unchanged': True, 'execution_source_unchanged': True,
    'experiment_model_calls': 0}, ensure_ascii=False, indent=2) + '\n')
