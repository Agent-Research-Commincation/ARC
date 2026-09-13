"""Produce tmp-only observation artifacts from an already generated audit index."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/hyohyeon/Desktop/agent-research-commincation')
DATA = json.loads((OUT/'audit-index.json').read_text())
ROWS = DATA['rows']
READ = {(2,6):[2,3,4], (3,7):[1,2], (3,8):[2,3], (4,6):[2,3,4,5,6],
        (4,7):[1,3,5], (5,6):[1,2], (5,7):[2], (6,6):[3,4,5], (6,8):[5,6]}

def dump(name, value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def hashes(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}

def independent(problem, schedule):
    meetings = {m['id']:m['attendees'] for m in problem['meetings']}
    assert set(schedule)==set(meetings)
    valid = all(problem['people'][p]['availability'][schedule[m]] for m, people in meetings.items() for p in people)
    valid = valid and all(schedule[a]<schedule[b] for a,b in problem['precedence'])
    valid = valid and all(schedule[a]!=schedule[b] or not(set(meetings[a])&set(meetings[b]))
                          for a,b in itertools.combinations(meetings,2))
    total = sum(problem['people'][p]['preferences'][schedule[m]] for m,people in meetings.items() for p in people)
    return {'valid':valid,'score':total if valid else None,'arithmetic_sum':total}

totals = {k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims',
          'incorrect_claims','undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
totals['applied_task_controls'] = dict(sum((collections.Counter(r['applied_task_controls']) for r in ROWS),collections.Counter()))
totals['rejections_by_phase'] = dict(collections.Counter(e['phase'] for r in ROWS for e in r['protocol_rejections']))
totals['rejections_by_category'] = dict(collections.Counter(e['category'] for r in ROWS for e in r['protocol_rejections']))
totals['applied_setup_controls'] = sum(bool(c['applied']) and c['phase']=='setup' for r in ROWS for c in r['control_sequence'])
totals['attempted_stop'] = sum(c['action'].get('action')=='stop' for r in ROWS for c in r['control_sequence'] if isinstance(c['action'],dict))
totals['raw_source_messages_read_in_full'] = sum(map(len,READ.values()))
totals['question_messages'] = sum(bool(m['questions']) for r in ROWS for m in r['messages'])
totals['request_messages'] = sum(bool(m['requests']) for r in ROWS for m in r['messages'])

candidate_checks, final_checks, error_checks, reading, held = [], [], [], [], []
evidence = ['# 선별 원문과 제어 기록', '',
    '23개 task 송신 원문을 직접 읽었다. 46개 전체 task 메시지는 자동 검산 범위이며 수동 전수 검수라고 표현하지 않는다. '
    'm번호는 패킷 sequence, request 번호는 실행기 요청이다. 거절 원문은 전체를 저장하되 직접 읽은 범위는 source-reading-log.json에 별도 표시한다.', '']
timeline = ['# 제어 요청·적용·제출 상태', '',
    '96개 응답의 action과 applied/rejected/packet을 자동 연결했다. 제출 상태는 적용 사건으로 복원했으며 회차별 최종 result.submissions와 일치했다. '
    '이는 상대 Agent에게 공개된 상태가 아니다. send/submit/wait/revise/stop의 payload와 동작을 구분한다.', '']
rejection_rows = []
for r in ROWS:
    key = (r['stage'],r['trial']); source=Path(r['source'])
    problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=[json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
    for m in r['messages']:
        if set(m['schedule'])=={'M1','M2','M3'}:
            ev=independent(problem,m['schedule']); original=m['candidate_evaluation']
            assert ev['valid']==original['valid'] and ev['score']==original['score']
            candidate_checks.append({'stage':r['stage'],'trial':r['trial'],'message':m['message'],
                'kind':m['kind'],'schedule':m['schedule'],'independent':ev,'matches':True})
    assert r['submissions']['A']==r['submissions']['B']
    ev=independent(problem,r['submissions']['A']); assert ev['valid'] and ev['score']==r['score']
    final_checks.append({'stage':r['stage'],'trial':r['trial'],'identical':True,'schedule':r['submissions']['A'],
                         'independent':ev,'gap':20-ev['score']})
    for c in r['incorrect_details']:
        assert c['type']=='summary'
        relation,team,meeting,slot,value=c['value']
        people=[p for m in problem['meetings'] if m['id']==meeting for p in m['attendees'] if problem['people'][p]['owner']==team]
        expected=(int(all(problem['people'][p]['availability'][slot] for p in people)) if relation=='available'
                  else sum(problem['people'][p]['preferences'][slot] for p in people))
        assert expected==c['expected'] and expected!=value
        error_checks.append({'stage':r['stage'],'trial':r['trial'],'message':c['message'],
                            'claim':c['value'],'expected':expected,'team_attendees':people,'matches':True})
    for c in r['undetermined_details']:
        ev=independent(problem,c['value']['schedule']); assert not ev['valid'] and ev['arithmetic_sum']==c['arithmetic_sum']
        held.append({'stage':r['stage'],'trial':r['trial'],'message':c['message'],'asserted':c['value']['score'],
                     'independent':ev,'arithmetic_matches':c['arithmetic_matches']})
    selected=READ.get(key,[])
    reading.append({'stage':r['stage'],'trial':r['trial'],'source':str(source),
       'automated_task_messages':r['task_messages'],'raw_sender_source_read_in_full':selected,
       'raw_sender_source_excerpt_only':({'message':4,'range':'first 240 characters'} if key==(6,8) else None),
       'all_control_action_fields_and_apply_reject_metadata_read':True,
       'full_control_response_requests_read':([3,4,5,6] if key==(5,7) else [1,2,3,7,8,9,10] if key==(6,6)
                                             else [1,2,3,4,5] if key==(6,8) else []),
       'full_rejected_response_requests_read':([1] if key==(5,6) else [1] if key==(6,6) else [1,3] if key==(6,8) else []),
       'rejected_payload_excerpt_read':'first/last 250 chars and message-kind lines for remaining rejected task payloads',
       'extra_input_requests_read':([3,4,5,6] if key==(5,7) else [7,8,9,10] if key==(6,6) else []),
       'language_dictionary_read':key in [(6,6),(6,8)]})
    evidence += [f'## {r["stage"]}단계 / trial-{r["trial"]:02d}', '',f'원본: {source}/events.jsonl','']
    for e in events:
        if e['method']=='experiment/packet' and e['params']['sequence'] in selected:
            p=e['params']; assert p['phase']=='task'
            evidence += [f'### m{p["sequence"]} {p["sender"]} → {p["receiver"]} · {p["request_id"]}',
                         '', '```text',p['sender_source'],'```','']
        if e['method']=='experiment/packet' and key==(6,8) and e['params']['sequence']==4:
            evidence += ['### m4 발췌: 처음 240문자', '', '```text',e['params']['sender_source'][:240],'```','']
    if key in [(5,7),(6,6)]:
        evidence += ['### wait 전후 원본 제어 응답과 입력', '']
        ids=([3,4,5,6] if key==(5,7) else [7,8,9,10])
        for e in events:
            p=e['params']
            if e['method'] in ('experiment/input','experiment/response_received','experiment/applied') and p.get('request_id') in [f'request-{x}' for x in ids]:
                evidence += [f'{e["method"]} · {p["request_id"]}', '', '```json',json.dumps(p,ensure_ascii=False,indent=2),'```','']
    if r['protocol_rejections']:
        evidence += ['### 거절 원문 보존 (직접 읽은 범위는 별도 로그)', '']
        for e in r['protocol_rejections']:
            evidence += ['```json',json.dumps(e,ensure_ascii=False,indent=2),'```','']
    if key in [(6,6),(6,8)]:
        evidence += ['### 사전 합의 제어 응답', '']
        for c in r['control_sequence']:
            if c['phase']=='setup':evidence += [c['request_id'],'','```json',c['raw_response'],'```','']
        evidence += ['### 최종 합의 사전','','```json',(source/'language.json').read_text().strip(),'```','']
    timeline += [f'## {r["stage"]}단계 / trial-{r["trial"]:02d}', '',
       '| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 적용 전 제출자 → 적용 후 |',
       '|---|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        a=c['action'].get('action') if isinstance(c['action'],dict) else 'parse failed'
        outcome='applied' if c['applied'] else 'rejected: '+c['rejected']['error'] if c['rejected'] else 'unknown'
        timeline.append(f'| {c["request_id"]} | {c["actor"]} | {c["phase"]} | {a} | {outcome} | '
                        f'{c["delivered_messages"]} | {list(c["submissions_before"])} → {list(c["submissions_after"])} |')
        if c['rejected']:
            next_c=r['control_sequence'][i+1] if i+1<len(r['control_sequence']) else None
            next_ok=next((x for x in r['control_sequence'][i+1:] if x['applied']),None)
            rejection_rows.append({'stage':r['stage'],'trial':r['trial'],'request':c['request_id'],'actor':c['actor'],
               'phase':c['phase'],'category':c['rejected']['category'],'error':c['rejected']['error'],
               'next_response':({k:next_c[k] for k in ['request_id','actor','action','applied','rejected','delivered_messages']} if next_c else None),
               'next_applied':({k:next_ok[k] for k in ['request_id','actor','action','delivered_messages']} if next_ok else None)})
    timeline.append('')

problem=json.loads((Path(ROWS[0]['source']).parent/'manifest.json').read_text())['comparison_settings']['problem']
all_schedules=[dict(zip(('M1','M2','M3'),t)) for t in itertools.product(range(12),repeat=3)]
feasible=[(s,independent(problem,s)['score']) for s in all_schedules if independent(problem,s)['valid']]
best=max(score for _,score in feasible); assert best==20
error_trial=next(r for r in ROWS if (r['stage'],r['trial'])==(3,7))
observation=json.loads((Path(error_trial['output'])/'observation.json').read_text())
claim_values=[c['value'] for m in observation['messages'] if m['message']==2 for c in m['claims'] if c['type']=='summary']
m1={(rel,slot):val for rel,team,meeting,slot,val in claim_values if team=='B' and meeting=='M1'}
m2={(rel,slot):val for rel,team,meeting,slot,val in claim_values if team=='B' and meeting=='M2'}
assert len(m1)==24 and m1==m2
unchanged=all(hashes(Path(folder))==expected for folder,expected in DATA['protected_trial_hashes'].items())
for stage in range(2,7):
    base=ROOT/'.worktree'/DATA['plan_id']/f'stage-{stage}'
    assert {name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in DATA['evaluator_source_hashes']}==DATA['evaluator_source_hashes']
assert unchanged
dump('verification.json',{'totals':totals,'original_trial_files_unchanged':True,'execution_sources_unchanged_and_equal':True,
     'review_policy_version':DATA['review_policy_version'],'experiment_model_calls':0,
     'comparison_groups':sorted({r['comparison_group'] for r in ROWS}),
     'candidate_checks':candidate_checks,'final_checks':final_checks,'error_checks':error_checks,'held_checks':held,
     'independent_enumeration':{'assignments':1728,'feasible':len(feasible),'best_score':20,
         'best_schedules':[s for s,score in feasible if score==20]},
     'stage3_trial07_B_M1_equals_B_M2_in_all_24_transmitted_summary_fields':True,
     'docs_metrics_sha256':hashlib.sha256((ROOT/'docs/metrics.md').read_bytes()).hexdigest()})
dump('source-reading-log.json',{'reviewer_kind':'AI; independent targeted review','reviewer_agent':'/root/stages_3_4',
     'manual_full_task_payloads':sum(map(len,READ.values())),'all_task_payloads_manually_reviewed':False,'rows':reading})
dump('rejection-followups.json',rejection_rows)
(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n')
(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')

table=['# 2~6단계 trial-06~08 임시 관찰표','','종료된 15회만 사후 자동 대조했다. 현재 계획 전체의 최종 비교표가 아니다. '
       '정/오/보류는 전달된 명시 주장 발생 횟수다. 첫 후보는 완전한 첫 propose이며, '
       '제안 변경은 propose끼리의 배치 변경, revise는 실제 적용 사건이다. 질문 항목 수는 대화 횟수와 다르다.','',
       '| 단계/회차 | task 메시지 | 정/오/보류 | 첫 전체 후보 | 최종점수 | 변경/revise | 질문 | wait | 거절(task/setup) | 상세 |',
       '|---|---:|---:|---|---:|---:|---:|---:|---:|---|']
csv_rows=[]
for r in ROWS:
    f=r['first_full_proposal']; score=f['evaluation']['score']; schedule=','.join(str(f['schedule'][m]) for m in ('M1','M2','M3'))
    first=f'm{f["message"]} {f["sender"]} ({schedule}) '+(str(score)+'점' if f['evaluation']['valid'] else '불가')
    phase=collections.Counter(e['phase'] for e in r['protocol_rejections']); wait=r['applied_task_controls'].get('wait',0)
    obs=Path(r['output'])/'observation.md'
    table.append(f'| {r["stage"]}/{r["trial"]:02d} | {r["task_messages"]} | {r["correct_claims"]}/{r["incorrect_claims"]}/{r["undetermined_claims"]} | '
       f'{first} | {r["score"]} | {r["changed_proposals"]}/{r["explicit_revisions"]} | {r["questions"]} | {wait} | '
       f'{phase["task"]}/{phase["setup"]} | [관찰]({obs}) |')
    csv_rows.append({k:r[k] for k in ['stage','trial','status','score','quality_gap','task_messages','correct_claims','incorrect_claims',
          'undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions']} |
          {'wait':wait,'task_rejections':phase['task'],'setup_rejections':phase['setup'],'first_candidate':first,'source':r['source'],'observation':str(obs)})
table += ['', '15회 모두 양쪽 submit으로 완료되었다. 14회는 최적 20점, 3단계 trial-07은 유효한 19점(격차 1)이다. '
          '46개 task 메시지: 정답 2167건, 오류 11건, 보류 1건, 코덱 오류 0건. 사전 합의 7개 패킷을 포함하면 전체 전달 메시지는 53개다.',
          '', '96개 제어 응답 중 task에 적용된 동작은 send 45, revise 1, submit 30, wait 3, stop 0회다. '
          'setup 적용 7회와 거절 10회(task 7, setup 3)가 별도로 있다. 모든 거절 응답은 채널에 전달되지 않았다.', '',
          f'[과정 감사]({OUT}/process-audit.md) · [제어 전체 순서]({OUT}/control-timeline.md) · '
          f'[거절 후속 행동]({OUT}/rejection-followups.json) · [읽은 범위]({OUT}/source-reading-log.json) · '
          f'[원문 근거]({OUT}/selected-source-evidence.md) · [검산]({OUT}/verification.json)', '']
(OUT/'observation-table.md').write_text('\n'.join(table))
with (OUT/'observation-table.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
print(json.dumps({'totals':totals,'candidate_checks':len(candidate_checks),'final_checks':len(final_checks),
                  'output':str(OUT)},ensure_ascii=False))
