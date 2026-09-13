"""Finalize exactly the 15 completed structured trials 12..14; local files only."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
D = json.loads((OUT / 'audit-index.json').read_text())
ROWS = D['rows']
assert {(r['stage'], r['trial']) for r in ROWS} == set(itertools.product(range(2, 7), range(12, 15)))
BASE = Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree') / D['plan_id']
FULL_READ = {(2,13): [2,3], (2,14): [1,2], (3,12): [2,3,4], (3,13): [1,2,3],
             (3,14): [2,3], (4,13): [2,3,4,5,6], (4,14): [1,2],
             (5,12): [2,3,4,5,6,7,8], (6,13): [4,5,6]}

def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def digest(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}

def independent(problem, schedule):
    meetings = {m['id']: m['attendees'] for m in problem['meetings']}
    assert set(schedule) == set(meetings)
    valid = all(problem['people'][p]['availability'][schedule[m]]
                for m, people in meetings.items() for p in people)
    valid = valid and all(schedule[a] < schedule[b] for a, b in problem['precedence'])
    valid = valid and all(schedule[a] != schedule[b] or not(set(meetings[a]) & set(meetings[b]))
                          for a,b in itertools.combinations(meetings, 2))
    total = sum(problem['people'][p]['preferences'][schedule[m]]
                for m, people in meetings.items() for p in people)
    return {'valid': valid, 'score': total if valid else None, 'arithmetic_sum': total}

def compact(schedule):
    return '(' + ','.join(str(schedule[m]) for m in ['M1','M2','M3']) + ')'

def frame_label(candidate):
    e = candidate['evaluation']
    return f"m{candidate['message']} {candidate['sender']} {compact(candidate['schedule'])} " + (str(e['score']) if e['valid'] else '불가')

totals = {k: sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims',
          'incorrect_claims','undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals == {'task_messages':52,'all_phase_messages':58,'correct_claims':2108,'incorrect_claims':5,
                  'undetermined_claims':1,'codec_errors':0,'changed_proposals':9,'explicit_revisions':10,
                  'questions':479,'result_actions':96}
controls = collections.Counter()
candidate_checks, final_checks, claim_checks, reading, rejected = [], [], [], [], []
evidence = ['# 선별 원문 근거', '', '명시한 task payload 29/52개와 거절 응답 8/8개를 직접 읽었다. 나머지 task payload는 정규화 결과 자동대조 범위다.', '']
timeline = ['# 제어 흐름', '', '실제 response/applied/rejected 및 제출 상태 재구성. `m`은 packet 번호이고 request 번호와 다르다.', '']
table = ['# 2~6단계 trial12~14 관찰표', '', '15회 모두 최종 유효·20점. C/I/U는 내용 주장 정답/오류/보류 발생 수이며 질문과 후보 자체는 주장 수에 넣지 않는다.', '',
         '|단계/회차|task 메시지|C/I/U|첫 전체 후보|제안 변경/명시 revise|질문|문법 거절|내용·과정 메모|',
         '|---|---:|---|---|---:|---:|---:|---|']
notes = {(2,12):'내용 오류 없음', (2,13):'후보 수정; 별개 B/M3/9 요약 오류 미정정',
         (2,14):'A/M3 선호도 2건 미정정', (3,12):'요약 요청 오타 반복; 유효성·점수 응답 후 제출',
         (3,13):'질문 타입 availability→available 수정 후 전달', (3,14):'자체 불가 요약과 충돌한 후보를 상대가 수정',
         (4,12):'내용 오류 없음', (4,13):'정확한 원자료와 후속 요약 충돌; 상대 명시 반박 후 후보 수락',
         (4,14):'A/M1/9 가용성 오류 미정정', (5,12):'불가 후보 반복; 점수 23은 보류; 명시 불가 응답 후 수락',
         (5,13):'내용 오류 없음', (5,14):'내용 오류 없음', (6,12):'내용 오류 없음',
         (6,13):'종류 중복 거절 후 후보만 전달; 요청받아 요약 후속 전달', (6,14):'기호 길이 거절 후 사전 수정·수락'}
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial']; key=(s,t)
    source=Path(r['source'])
    manifest=json.loads((source.parent/'manifest.json').read_text())
    problem=manifest['comparison_settings']['problem']
    result=json.loads((source/'result.json').read_text())
    events=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()]
    packets=[e['params'] for e in events if e['method']=='experiment/packet']
    observed=json.loads((Path(r['output'])/'observation.json').read_text())
    controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0
    for c in r['full_candidates']:
        got=independent(problem,c['schedule'])
        assert (got['valid'],got['score']) == (c['evaluation']['valid'],c['evaluation']['score'])
        candidate_checks.append({'stage':s,'trial':t,'message':c['message'],'schedule':c['schedule'],**got})
    assert r['submissions']['A']==r['submissions']['B']
    got=independent(problem,r['submissions']['A'])
    assert got['valid'] and got['score']==20
    final_checks.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**got})
    for c in r['incorrect_details']:
        assert c['type']=='summary'
        typ,team,meeting,slot,value=c['value']
        people=[p for m in problem['meetings'] if m['id']==meeting for p in m['attendees'] if problem['people'][p]['owner']==team]
        expected=(int(all(problem['people'][p]['availability'][slot] for p in people)) if typ=='available'
                  else sum(problem['people'][p]['preferences'][slot] for p in people))
        assert expected==c['expected'] and expected!=value
        later=[{'message':m['message'],'sender':m['sender'],'claim':cc}
               for m in observed['messages'] if m['message']>c['message'] for cc in m['claims']
               if cc['type']=='summary' and cc['value'][:-1]==c['value'][:-1]]
        claim_checks.append({'stage':s,'trial':t,'message':c['message'],'raw_value':c['value'],
                             'independent_expected':expected,'attendees':people,'later_same_key_summary_claims':later})
    for c in r['undetermined_details']:
        assert (s,t,c['message'])==(5,12,6)
        got=independent(problem,c['value']['schedule'])
        assert not got['valid'] and got['arithmetic_sum']==c['value']['score']==23
        claim_checks.append({'stage':s,'trial':t,'message':6,'raw_value':c['value'],**got,'judgment':'undetermined'})
    selected=FULL_READ.get(key,[])
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],
                    'full_task_sender_source_read':selected,'all_normalized_task_messages_reviewed':True,
                    'all_response_control_metadata_reviewed':True,
                    'full_rejected_raw_response_read':[x['request_id'] for x in r['protocol_rejections']],
                    'setup_success_raw_response_read':['request-2','request-3'] if key==(6,14) else []})
    if selected or r['protocol_rejections']:
        evidence += [f'## stage {s} / trial {t:02d}', '', f'원본: `{source}/events.jsonl`', '']
    for p in packets:
        if p['phase']=='task' and p['sequence'] in selected:
            payload=p['sender_source']
            evidence += [f"### m{p['sequence']} {p['sender']} ({p['request_id']})", '',
                         '```text', payload if isinstance(payload,str) else json.dumps(payload,ensure_ascii=False), '```','']
    timeline += [f'## stage {s} / trial {t:02d}', '', '|request|주체/phase|action|결과|m|제출 상태 전→후|', '|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed'
        status='거절: '+c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            follow=r['control_sequence'][i+1:]
            nxt=next((x for x in follow if x['applied']),None)
            nxt_same=next((x for x in follow if x['actor']==c['actor'] and x['applied']),None)
            rejected.append({'stage':s,'trial':t,'request_id':c['request_id'],'error':c['rejected']['error'],
                             'phase':c['phase'],'actor':c['actor'],'raw_response':c['raw_response'],
                             'next_applied':nxt,'next_same_actor_applied':nxt_same})
            evidence += [f"### 거절 {c['request_id']}: {c['rejected']['error']}", '', '```json', c['raw_response'], '```','']
    timeline += ['', '실제 revise의 cleared_agents: '+json.dumps([v['cleared_agents'] for v in r['revision_events']])+'.','']
    first=r['first_full_candidate']; label=frame_label(first)
    table.append(f"|{s}/{t:02d}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/{r['undetermined_claims']}|{label}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['protocol_rejections'])}|{notes[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],
                    **{k:r[k] for k in totals if k!='result_actions'},'protocol_rejections':len(r['protocol_rejections']),
                    'first_candidate':label,'notes':notes[key]})

assert controls=={'send':42,'submit':30,'revise':10}
assert all(not r['wait_events'] for r in ROWS)
assert all(not v['cleared_agents'] for r in ROWS for v in r['revision_events'])
assert all(not c.get('later_same_key_summary_claims') for c in claim_checks)
assert len(rejected)==8
assert sum(len(v) for v in FULL_READ.values())==29
bad_first=[{'stage':r['stage'],'trial':r['trial'],'candidate':r['first_full_candidate']}
           for r in ROWS if not r['first_full_candidate']['evaluation']['valid']]
assert len(bad_first)==4
enumerated=[(sch, independent(problem,sch)) for sch in
            (dict(zip(['M1','M2','M3'],slots)) for slots in itertools.product(range(len(problem['slots'])),repeat=3))]
valid=[(sch,v) for sch,v in enumerated if v['valid']]
best=max(v['score'] for sch,v in valid)
optimal=[sch for sch,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(digest(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes']
                   for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],
     'totals':totals,'applied_task_controls':dict(controls),'protocol_rejections':8,
     'rejections_by_phase':dict(collections.Counter(r['phase'] for r in rejected)),
     'independent_candidate_checks':candidate_checks,'independent_final_checks':final_checks,
     'independent_flagged_claim_checks':claim_checks,'initial_invalid_candidates':bad_first,
     'independent_enumeration':{'assignments':len(enumerated),'valid':len(valid),'optimal_score':best,'optimal_schedules':optimal},
     'all_revisions_before_any_submission':True,'all_revisions_cleared_agents_empty':True,
     'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,
     'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('source-reading-log.json',{'method':'automatic all selected trials plus selective direct raw reading; not manual exhaustive review',
     'full_task_payloads_read':29,'task_payloads_total':52,'rejected_full_responses_read':8,'rows':reading})
dump('rejection-followups.json',rejected)
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n')
(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n')
(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'candidate_checks':len(candidate_checks),
                  'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
