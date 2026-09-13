"""Read completed selected trials; write audit artifacts only to this tmp folder."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/hyohyeon/Desktop/agent-research-commincation')
DATA = json.loads((OUT / 'audit-index.json').read_text())
ROWS = DATA['rows']
READ = {
    (2, 2): [2, 3, 4, 5], (2, 4): [2, 3, 4],
    (3, 1): [5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    (3, 3): [3, 4, 5, 6], (3, 5): [3, 4, 5],
    (4, 2): [2, 3, 4, 5, 6],
    (5, 3): [1, 2, 3, 4, 5, 6], (5, 4): [2, 3, 4],
    (6, 1): [3, 4, 5, 6], (6, 3): [4, 5, 6, 7],
    (6, 4): [4, 5, 6], (6, 5): [3, 4, 5, 6, 7],
}

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}

def independent_evaluate(problem, schedule):
    meetings = {m['id']: m['attendees'] for m in problem['meetings']}
    valid = set(schedule) == set(meetings)
    valid = valid and all(type(s) is int and 0 <= s < len(problem['slots']) for s in schedule.values())
    if not valid:
        return {'valid': False, 'score': None}
    valid = all(problem['people'][p]['availability'][schedule[m]] for m, people in meetings.items() for p in people)
    valid = valid and all(schedule[a] < schedule[b] for a, b in problem['precedence'])
    valid = valid and all(schedule[a] != schedule[b] or not (set(meetings[a]) & set(meetings[b]))
                          for a, b in itertools.combinations(meetings, 2))
    arithmetic = sum(problem['people'][p]['preferences'][schedule[m]] for m, people in meetings.items() for p in people)
    return {'valid': valid, 'score': arithmetic if valid else None, 'arithmetic_sum': arithmetic}

totals = {k: sum(r[k] for r in ROWS) for k in ('task_messages', 'all_phase_messages', 'correct_claims',
          'incorrect_claims', 'undetermined_claims', 'codec_errors', 'changed_proposals', 'explicit_revisions', 'questions')}
totals['protocol_rejections'] = sum(len(r['protocol_rejections']) for r in ROWS)
totals['question_messages'] = sum(bool(m['questions']) for r in ROWS for m in r['messages'])
totals['person_request_messages'] = sum(bool(m['requests']) for r in ROWS for m in r['messages'])
totals['raw_source_messages_read'] = sum(map(len, READ.values()))

candidate_checks, final_checks, held_checks, revision_events = [], [], [], []
reading_log, evidence = [], ['# 직접 대조한 송신 원문', '',
    '선별한 task 메시지의 sender_source를 원본에서 그대로 복사했다. 이 파일의 목록만 원문을 직접 읽었다고 보고한다. '
    '모든 110개 task 메시지를 수동 전수 검수한 기록은 아니다. 메시지 번호는 experiment/packet.params.sequence다.', '']
for r in ROWS:
    key = (r['stage'], r['trial'])
    source = Path(r['source'])
    manifest = json.loads((source.parent / 'manifest.json').read_text())
    problem = manifest['comparison_settings']['problem']
    events = [json.loads(line) for line in (source / 'events.jsonl').read_text().splitlines()]
    for m in r['messages']:
        if set(m['schedule']) == {'M1', 'M2', 'M3'}:
            ev = independent_evaluate(problem, m['schedule'])
            original = m['candidate_evaluation']
            assert ev['valid'] == original['valid'] and ev['score'] == original['score']
            candidate_checks.append({'stage': r['stage'], 'trial': r['trial'], 'message': m['message'],
                                     'kind': m['kind'], 'schedule': m['schedule'], 'independent': ev, 'matches': True})
    result = json.loads((source / 'result.json').read_text())
    assert result['submissions']['A'] == result['submissions']['B']
    final_ev = independent_evaluate(problem, result['submissions']['A'])
    assert final_ev['valid'] and final_ev['score'] == 20
    final_checks.append({'stage': r['stage'], 'trial': r['trial'], 'identical_submissions': True,
                         'schedule': result['submissions']['A'], 'independent': final_ev})
    for c in r['undetermined_details']:
        ev = independent_evaluate(problem, c['value']['schedule'])
        assert not ev['valid'] and ev['arithmetic_sum'] == c['arithmetic_sum']
        held_checks.append({'stage': r['stage'], 'trial': r['trial'], 'message': c['message'],
                            'schedule': c['value']['schedule'], 'asserted': c['value']['score'],
                            'arithmetic_sum': ev['arithmetic_sum'], 'arithmetic_matches': c['arithmetic_matches']})
    for e in events:
        if e['method'] == 'experiment/submissions_invalidated':
            revision_events.append({'stage': r['stage'], 'trial': r['trial'], **e['params']})
    selected = READ.get(key, [])
    reading_log.append({'stage': r['stage'], 'trial': r['trial'], 'source': str(source),
                        'automated_task_messages': r['task_messages'], 'raw_sender_source_read_in_full': selected,
                        'all_rejection_error_fields_read': True,
                        'full_rejection_responses_read': ([x['request_id'] for x in r['protocol_rejections']]
                                                         if key in ((6, 3), (6, 4), (6, 5)) else []),
                        'language_dictionary_read': key in ((6, 1), (6, 3), (6, 4), (6, 5))})
    if selected:
        evidence += [f'## 단계 {r["stage"]} · trial-{r["trial"]:02d}', '', f'원본: {source}/events.jsonl', '']
    for e in events:
        if e['method'] == 'experiment/packet' and e['params']['sequence'] in selected:
            p = e['params']
            assert p['phase'] == 'task'
            evidence += [f'### 메시지 {p["sequence"]} · {p["sender"]} → {p["receiver"]} · {p["request_id"]}',
                         '', '```text', p['sender_source'], '```', '']
    if key in ((6, 3), (6, 4), (6, 5)):
        evidence += ['### 직접 읽은 거절 원문', '']
        for x in r['protocol_rejections']:
            evidence += [f'{x["actor"]} · {x["request_id"]} · {x["error"]}', '',
                         '```json', json.dumps(x['raw_response'], ensure_ascii=False, indent=2), '```', '']
    if key in ((6, 1), (6, 3), (6, 4), (6, 5)):
        evidence += ['### 합의된 사전', '', '```json', (source / 'language.json').read_text().strip(), '```', '']

p = json.loads((Path(ROWS[0]['source']).parent / 'manifest.json').read_text())['comparison_settings']['problem']
all_ev = [(dict(zip(('M1', 'M2', 'M3'), t)), independent_evaluate(p, dict(zip(('M1', 'M2', 'M3'), t))))
          for t in itertools.product(range(12), repeat=3)]
feasible = [(s, e['score']) for s, e in all_ev if e['valid']]
best = max(score for _, score in feasible)
assert best == 20
summary_actual = sum(p['people'][person]['preferences'][2] for person in ('A1', 'A3'))
assert summary_actual == 0

unchanged = all(hashes(Path(folder)) == expected for folder, expected in DATA['protected_trial_hashes'].items())
code_maps = []
for stage in range(2, 7):
    base = ROOT / '.worktree' / DATA['plan_id'] / f'stage-{stage}'
    code_maps.append({name: hashlib.sha256((base / name).read_bytes()).hexdigest()
                      for name in DATA['evaluator_source_hashes']})
assert unchanged and all(x == DATA['evaluator_source_hashes'] for x in code_maps)
assert len(revision_events) == 17 and all(not e['cleared_agents'] for e in revision_events)

dump('source-reading-log.json', {'reviewer_kind': 'AI; independent targeted audit',
      'reviewer_agent': '/root/stages_3_4', 'automated_scope': '25 completed trials; all 110 task packets',
      'manual_scope': 'selected sender_source payloads, error metadata, selected rejected payloads and dictionaries only',
      'all_raw_messages_manually_reviewed': False, 'rows': reading_log})
dump('verification.json', {'totals': totals, 'comparison_groups': sorted({r['comparison_group'] for r in ROWS}),
     'review_policy_version': DATA['review_policy_version'], 'original_trial_files_unchanged': unchanged,
     'all_execution_sources_unchanged_and_equal': True, 'experiment_model_calls': 0,
     'candidate_checks': candidate_checks, 'final_checks': final_checks, 'held_arithmetic_checks': held_checks,
     'revision_events': revision_events, 'all_revisions_cleared_no_existing_submissions': True,
     'independent_enumeration': {'all_assignments': len(all_ev), 'feasible': len(feasible), 'best_score': best,
          'best_schedules': [s for s, score in feasible if score == best]},
     'independent_error_checks': {'A_M3_slot2_preference': summary_actual,
          'A1_slot0_available': p['people']['A1']['availability'][0],
          'A2_slot0_available': p['people']['A2']['availability'][0],
          'precedence': p['precedence']},
     'docs_metrics_sha256_at_audit': hashlib.sha256((ROOT / 'docs/metrics.md').read_bytes()).hexdigest()})
(OUT / 'selected-source-evidence.md').write_text('\n'.join(evidence) + '\n')

table = ['# 단계 2~6, trial-01~05 임시 관찰표', '',
    '이 표는 현재 실행 계획의 완료된 25회만 대상으로 한다. 방식별 30회 본실험의 최종 비교표가 아니다. '
    '관찰표는 고정된 평가기 write_trial_records로 별도 tmp 폴더에 생성했고 원본을 덮어쓰지 않았다.', '',
    '정/오/보류는 전달된 명시 주장 발생 횟수다. 첫 후보는 M1·M2·M3를 모두 담은 첫 propose 메시지다. '
    '불가 후보는 점수를 부여하지 않았다. 변경/수정은 제안 배치 변경 메시지/성공적으로 적용된 revise 이벤트이며, '
    '질문은 typed questions 항목 수다. ASK/requests의 개인 정보 요청은 질문 열에 포함하지 않는다.', '',
    '| 단계/회차 | task 메시지 | 정/오/보류 | 첫 전체 후보(M1,M2,M3) | 변경/revise | 질문 항목 | 문법 거절 | 임시 상세 관찰 |',
    '|---|---:|---:|---|---:|---:|---:|---|']
csv_rows = []
for r in ROWS:
    f = r['first_full_proposal']
    status = str(f['evaluation']['score']) + '점' if f['evaluation']['valid'] else '불가'
    schedule = ','.join(str(f['schedule'][m]) for m in ('M1', 'M2', 'M3'))
    observation = Path(r['output']) / 'observation.md'
    table.append(f'| {r["stage"]}/{r["trial"]:02d} | {r["task_messages"]} | '
        f'{r["correct_claims"]}/{r["incorrect_claims"]}/{r["undetermined_claims"]} | '
        f'm{f["message"]} {f["sender"]}: ({schedule}) {status} | '
        f'{r["changed_proposals"]}/{r["explicit_revisions"]} | {r["questions"]} | '
        f'{len(r["protocol_rejections"])} | [관찰]({observation}) |')
    csv_rows.append({k: r[k] for k in ('stage', 'trial', 'status', 'score', 'quality_gap', 'task_messages',
        'correct_claims', 'incorrect_claims', 'undetermined_claims', 'codec_errors', 'changed_proposals',
        'explicit_revisions', 'questions')} | {'protocol_rejections': len(r['protocol_rejections']),
        'first_full_schedule': schedule, 'first_full_valid': f['evaluation']['valid'],
        'first_full_score': f['evaluation']['score'], 'observation': str(observation), 'source': r['source']})
table += ['', '25회 최종 제출은 모두 A/B 일치·유효·20점이며 독립적인 원자료 검산도 일치했다. '
          '전체 110개 task 메시지에서 정답 주장 3650건, 오류 4건, 판정 보류 10건, 코덱 오류 0건이다. '
          '6단계 사전 합의 10개 메시지를 합한 전송 메시지는 120개이며 사전 합의는 task 주장 검수에 포함하지 않았다.', '',
          '배치 변경 및 적용 revise는 각각 17건, 문법 거절 16건, typed 질문 항목 1033개(해당 메시지 25개), '
          '개인 정보 요청을 포함한 메시지 10개다. 거절된 응답은 전달된 task 메시지와 주장 정오 집계에 포함하지 않는다.', '',
          f'[과정 검산과 사례]({OUT}/process-audit.md) · [읽은 원문 목록]({OUT}/source-reading-log.json) · '
          f'[원문 근거]({OUT}/selected-source-evidence.md) · [독립 검산 영수증]({OUT}/verification.json)', '']
(OUT / 'observation-table.md').write_text('\n'.join(table))
with (OUT / 'observation-table.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
    writer.writeheader()
    writer.writerows(csv_rows)
print(json.dumps({'totals': totals, 'candidate_checks': len(candidate_checks),
                  'originals_unchanged': unchanged, 'output': str(OUT)}, ensure_ascii=False))
