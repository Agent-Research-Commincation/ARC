"""Tmp-only post-run audit formatting and independent arithmetic checks."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=Path('/Users/hyohyeon/Desktop/agent-research-commincation')
DATA=json.loads((OUT/'audit-index.json').read_text()); ROWS=DATA['rows']
READ={(3,9):[2,3,4],(3,10):[2,3,4,5,6,7],(4,11):[1,2,3],(5,9):[1,2],(6,10):[5,6],(6,11):[5]}
EXCERPTS={(3,10):[1],(4,10):[1],(5,11):[1]}

def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def hashes(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}

def independent(problem,schedule):
    meetings={m['id']:m['attendees'] for m in problem['meetings']}
    assert set(schedule)==set(meetings)
    valid=all(problem['people'][p]['availability'][schedule[m]] for m,people in meetings.items() for p in people)
    valid=valid and all(schedule[a]<schedule[b] for a,b in problem['precedence'])
    valid=valid and all(schedule[a]!=schedule[b] or not(set(meetings[a])&set(meetings[b])) for a,b in itertools.combinations(meetings,2))
    total=sum(problem['people'][p]['preferences'][schedule[m]] for m,people in meetings.items() for p in people)
    return {'valid':valid,'score':total if valid else None,'arithmetic_sum':total}

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims',
    'undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
totals['applied_task_controls']=dict(sum((collections.Counter(r['applied_task_controls']) for r in ROWS),collections.Counter()))
totals['rejections_by_phase']=dict(collections.Counter(e['phase'] for r in ROWS for e in r['protocol_rejections']))
totals['applied_setup_controls']=sum(bool(c['applied']) and c['phase']=='setup' for r in ROWS for c in r['control_sequence'])
totals['attempted_stop']=sum(c['action'].get('action')=='stop' for r in ROWS for c in r['control_sequence'] if isinstance(c['action'],dict))
totals['full_task_sources_read']=sum(map(len,READ.values()))
totals['question_messages']=sum(bool(m['questions']) for r in ROWS for m in r['messages'])
totals['person_request_messages']=sum(bool(m['requests']) for r in ROWS for m in r['messages'])
candidate_checks=[]; final_checks=[]; error_checks=[]; special={}; scope=[]; rejection_followups=[]
evidence=['# 선별 원문 근거','','전체 자동 대조와 선별 원문 검토를 구분한다. 직접 읽은 task 송신 원문은 17개이며 나머지는 발췌/자동 검산 범위다. '
          '거절 원문 전체의 저장은 전체를 직접 읽었다는 뜻이 아니다. source-reading-log.json을 함께 본다.','']
timeline=['# 제어 요청·적용·거절 순서','','87개 제어 응답을 자동 연결했다. 제출 상태는 적용 사건으로 복원하여 최종 result와 대조했다. '
          '상대 Agent에게 공개된 상태라는 뜻은 아니다.','']
for r in ROWS:
    key=(r['stage'],r['trial']);source=Path(r['source'])
    problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=[json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
    for m in r['messages']:
        if set(m['schedule'])=={'M1','M2','M3'}:
            ev=independent(problem,m['schedule']); original=m['candidate_evaluation']
            assert (ev['valid'],ev['score'])==(original['valid'],original['score'])
            candidate_checks.append({'stage':r['stage'],'trial':r['trial'],'message':m['message'],
                                    'kind':m['kind'],'schedule':m['schedule'],'independent':ev,'matches':True})
    assert r['submissions']['A']==r['submissions']['B']
    ev=independent(problem,r['submissions']['A']);assert ev['valid'] and ev['score']==r['score']==20
    final_checks.append({'stage':r['stage'],'trial':r['trial'],'schedule':r['submissions']['A'],'independent':ev,'identical':True})
    for c in r['incorrect_details']:
        assert c['type']=='summary'
        relation,team,meeting,slot,value=c['value']
        people=[p for m in problem['meetings'] if m['id']==meeting for p in m['attendees'] if problem['people'][p]['owner']==team]
        expected=int(all(problem['people'][p]['availability'][slot] for p in people)) if relation=='available' else sum(problem['people'][p]['preferences'][slot] for p in people)
        assert expected==c['expected'] and expected!=value
        error_checks.append({'stage':r['stage'],'trial':r['trial'],'message':c['message'],'claim':c['value'],
                             'expected':expected,'team_attendees':people,'matches':True})
    scope.append({'stage':r['stage'],'trial':r['trial'],'source':str(source),'automated_task_messages':r['task_messages'],
      'full_sender_sources_read':READ.get(key,[]),'sender_source_excerpts_read':EXCERPTS.get(key,[]),
      'source_excerpt_range':'first 200 and last 250 characters' if key in EXCERPTS else None,
      'all_control_action_apply_reject_fields_read':True,
      'full_control_responses_read':[3,4,5,6] if key==(4,11) else [],
      'full_rejected_responses_read':[4] if key==(3,9) else [],
      'rejection_excerpt_scope':('first/last 180 characters; all Q-prefixed lines' if key in [(5,9),(5,11)] else
         'first/last 180 characters and exact parser-error vicinity' if key in [(3,10),(4,10)] else None),
      'extra_inputs_read':[4,5,6] if key==(4,11) else [],'language_dictionary_read':key in [(6,10),(6,11)]})
    evidence += [f'## {r["stage"]}단계 trial-{r["trial"]:02d}','','원본: '+str(source/'events.jsonl'),'']
    for event in events:
        p=event['params']
        if event['method']=='experiment/packet' and p['sequence'] in READ.get(key,[]):
            assert p['phase']=='task'
            evidence += [f'### m{p["sequence"]} {p["sender"]} → {p["receiver"]} / {p["request_id"]}',
                         '','```text',p['sender_source'],'```','']
        if event['method']=='experiment/packet' and p['sequence'] in EXCERPTS.get(key,[]):
            evidence += [f'### m{p["sequence"]} 발췌: 처음 200 / 끝 250문자','','```text',p['sender_source'][:200],
                         '```','','```text',p['sender_source'][-250:],'```','']
        if key==(4,11) and event['method'] in ['experiment/input','experiment/response_received','experiment/applied']:
            ids=range(4,7) if event['method']=='experiment/input' else range(3,7)
            if p.get('request_id') in [f'request-{x}' for x in ids]:
                evidence += [event['method']+' '+p['request_id'],'','```json',json.dumps(p,ensure_ascii=False,indent=2),'```','']
    if r['protocol_rejections']:
        evidence += ['### 거절 원문 보존: 직접 읽은 범위는 별도 로그','','```json',json.dumps(r['protocol_rejections'],ensure_ascii=False,indent=2),'```','']
    if key in [(6,10),(6,11)]:evidence += ['### 합의 사전','','```json',(source/'language.json').read_text().strip(),'```','']
    timeline += [f'## {r["stage"]}단계 trial-{r["trial"]:02d}','','| 요청 | Agent | phase | action | 적용/거절 | 전달 m | 제출자 전 → 후 |',
                 '|---|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        action=c['action'].get('action') if isinstance(c['action'],dict) else 'parse failure'
        outcome='applied' if c['applied'] else 'rejected: '+c['rejected']['error']
        timeline += [f'| {c["request_id"]} | {c["actor"]} | {c["phase"]} | {action} | {outcome} | {c["delivered_messages"]} | '
                     f'{list(c["submissions_before"])} → {list(c["submissions_after"])} |']
        if c['rejected']:
            next_c=r['control_sequence'][i+1] if i+1<len(r['control_sequence']) else None
            next_applied=next((x for x in r['control_sequence'][i+1:] if x['applied']),None)
            def extract(x):
                return {k:x[k] for k in ['request_id','actor','action','applied','rejected','delivered_messages']} if x else None
            rejection_followups.append({'stage':r['stage'],'trial':r['trial'],'rejected_request':c['request_id'],
                'error':c['rejected']['error'],'next_response':extract(next_c),'next_applied':extract(next_applied)})
    timeline.append('')
    if key==(3,9):
        rejected=r['protocol_rejections'][0]['raw_response']['payload']; delivered=next(c['action']['payload'] for c in r['control_sequence'] if c['request_id']=='request-5')
        assert rejected.replace('revise().','propose().',1)==delivered
        special['stage3_trial09_revise_payload_only_first_line_changed']=True
    if key==(5,11):
        rejected=r['protocol_rejections'][0]['raw_response']['payload'];delivered=next(c['action']['payload'] for c in r['control_sequence'] if c['request_id']=='request-2')
        assert rejected.replace('QSUMMARY availability ','QSUMMARY available ')==delivered
        special['stage5_trial11_only_36_relation_names_corrected']=rejected.count('QSUMMARY availability ')==36
    if key==(5,9):
        obs=json.loads((Path(r['output'])/'observation.json').read_text())
        asked={(q[0],)+tuple(q[1:]) for q in obs['messages'][0]['questions']}
        answered={(c['type'],)+tuple(c['value'][:-1]) for c in obs['messages'][1]['claims']}
        assert asked==answered and len(asked)==53
        special['stage5_trial09_53_requested_keys_exactly_answered']=True

problem=json.loads((Path(ROWS[0]['source']).parent/'manifest.json').read_text())['comparison_settings']['problem']
all_schedules=[dict(zip(('M1','M2','M3'),x)) for x in itertools.product(range(12),repeat=3)]
feasible=[(s,independent(problem,s)['score']) for s in all_schedules if independent(problem,s)['valid']]
assert max(score for _,score in feasible)==20
assert all(hashes(Path(folder))==expected for folder,expected in DATA['protected_trial_hashes'].items())
for stage in range(2,7):
    base=ROOT/'.worktree'/DATA['plan_id']/f'stage-{stage}'
    assert {name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in DATA['evaluator_source_hashes']}==DATA['evaluator_source_hashes']
dump('verification.json',{'totals':totals,'candidate_checks':candidate_checks,'final_checks':final_checks,'error_checks':error_checks,
  'selected_case_checks':special,'original_trial_files_unchanged':True,'execution_sources_unchanged_and_equal':True,
  'experiment_model_calls':0,'review_policy_version':DATA['review_policy_version'],
  'comparison_groups':sorted({r['comparison_group'] for r in ROWS}),
  'independent_enumeration':{'assignments':1728,'feasible':len(feasible),'best_score':20,'best_schedules':[s for s,score in feasible if score==20]}})
dump('source-reading-log.json',{'reviewer_kind':'AI; targeted independent review','reviewer_agent':'/root/stages_3_4',
    'all_task_sources_manually_reviewed':False,'full_task_sources_read':sum(map(len,READ.values())),'rows':scope})
dump('rejection-followups.json',rejection_followups)
(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n')
(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
table=['# 2~6단계 trial-09~11 임시 관찰표','','완료된 15회만의 사후 관찰이다. 정/오/보류는 전달된 명시 주장 발생 횟수다. '
       '첫 후보는 완전한 첫 propose이다. 제안 변경과 적용 revise, 질문 항목과 대화 횟수, 거절과 실제 전달을 구분한다.','',
       '| 단계/회차 | task 메시지 | 정/오/보류 | 첫 전체 후보 | 최종 | 변경/revise | 질문 | wait | 거절 | 상세 |',
       '|---|---:|---:|---|---:|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    f=r['first_full_proposal'];s=','.join(str(f['schedule'][m]) for m in ['M1','M2','M3'])
    first=f'm{f["message"]} {f["sender"]} ({s}) '+(str(f['evaluation']['score'])+'점' if f['evaluation']['valid'] else '불가')
    wait=r['applied_task_controls'].get('wait',0);rejected=len(r['protocol_rejections']);obs=Path(r['output'])/'observation.md'
    table += [f'| {r["stage"]}/{r["trial"]:02d} | {r["task_messages"]} | {r["correct_claims"]}/{r["incorrect_claims"]}/{r["undetermined_claims"]} | '
              f'{first} | {r["score"]} | {r["changed_proposals"]}/{r["explicit_revisions"]} | {r["questions"]} | {wait} | {rejected} | [관찰]({obs}) |']
    csvrows.append({k:r[k] for k in ['stage','trial','status','score','quality_gap','task_messages','correct_claims','incorrect_claims',
         'undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions']} |
         {'wait':wait,'protocol_rejections':rejected,'first_candidate':first,'source':r['source'],'observation':str(obs)})
table += ['', '최종 15회 모두 양쪽 일치·유효·최적 20점. 44개 task 메시지는 정답 주장 2122건, 오류 1건, 보류 0건, 코덱 오류 0건이다. '
          '사전 합의 6개 패킷을 포함한 실제 전달은 50개다. 최초 후보는 14회 20점, 3단계 trial-09만 19점이며 이후 20점으로 개선된다.', '',
          '87개 제어 응답: task 적용 send 43, revise 1, submit 30, wait 1, stop 0회; setup 적용 6회; 거절 6회(모두 task). '
          '질문 533개는 11개 메시지의 항목 수다.', '',
          f'[과정 감사]({OUT}/process-audit.md) · [제어 순서]({OUT}/control-timeline.md) · [거절 후속 행동]({OUT}/rejection-followups.json) · '
          f'[원문]({OUT}/selected-source-evidence.md) · [읽은 범위]({OUT}/source-reading-log.json) · [검산]({OUT}/verification.json)','']
(OUT/'observation-table.md').write_text('\n'.join(table))
with (OUT/'observation-table.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(csvrows[0]));writer.writeheader();writer.writerows(csvrows)
print(json.dumps({'totals':totals,'candidate_checks':len(candidate_checks),'output':str(OUT)},ensure_ascii=False))
