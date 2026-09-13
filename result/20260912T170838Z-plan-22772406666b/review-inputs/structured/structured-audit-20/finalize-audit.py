"""Post-run local-only audit of exactly stages 2..6, trial20."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text());ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,20) for s in range(2,7)}
READ={2:[1,2,3,4],3:[1,2,3,4,5],5:[1,2],6:[3,4,5,6,7,8,9,10,11]}
NOTES={2:'첫 불가 후보를 사유와 대안으로 수정, 수락·평가 응답',3:'질문 타입 수정; 요약 교환·제안·일정 없는 accept',4:'요약 72개 질문·응답 뒤 제출',5:'B 제출→A wait→B wait→A 제출; 새 peer 메시지 없음',6:'setup 2 + task 9; 사전 합의 무거절, task 거절 5; 자료 1→6→72, 후보16→20'}


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def hashes(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}

def independent(problem,schedule):
    meetings={m['id']:m['attendees'] for m in problem['meetings']};assert set(schedule)==set(meetings)
    valid=all(problem['people'][p]['availability'][schedule[m]] for m,ps in meetings.items() for p in ps)
    valid=valid and all(schedule[a]<schedule[b] for a,b in problem['precedence'])
    valid=valid and all(schedule[a]!=schedule[b] or not(set(meetings[a])&set(meetings[b])) for a,b in itertools.combinations(meetings,2))
    total=sum(problem['people'][p]['preferences'][schedule[m]] for m,ps in meetings.items() for p in ps)
    return {'valid':valid,'score':total if valid else None,'arithmetic_sum':total}

def claim_expected(problem,c):
    t,v=c['type'],c['value']
    if t=='fact':
        typ,p,slot,value=v
        expected=int(problem['people'][p]['availability'][slot]) if typ=='available' else problem['people'][p]['preferences'][slot]
    elif t=='summary':
        typ,team,meeting,slot,value=v
        people=[p for m in problem['meetings'] if m['id']==meeting for p in m['attendees'] if problem['people'][p]['owner']==team]
        expected=int(all(problem['people'][p]['availability'][slot] for p in people)) if typ=='available' else sum(problem['people'][p]['preferences'][slot] for p in people)
    elif t=='reason':
        typ,meeting,person,slot=v;assert typ=='unavailable'
        expected=any(m['id']==meeting and person in m['attendees'] for m in problem['meetings']) and not problem['people'][person]['availability'][slot]
        value=True
    elif t in ['schedule_score','schedule_valid']:
        field='score' if t=='schedule_score' else 'valid'
        value=v[field];expected=independent(problem,v['schedule'])[field]
        if field=='valid':expected=int(expected)
    else:raise AssertionError(t)
    assert value==expected==c['expected'] and c['correct'] is True
    return expected

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims','undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals=={'task_messages':22,'all_phase_messages':24,'correct_claims':730,'incorrect_claims':0,'undetermined_claims':0,'codec_errors':0,'changed_proposals':2,'explicit_revisions':1,'questions':371,'result_actions':42}
controls=collections.Counter();types=collections.Counter();candidates=[];finals=[];claims=[];reading=[];rejections=[];waits=[];revisions=[];qchecks=[];observations={}
evidence=['# 선별 원문','','task 20/22개와 거절 응답 6/6개 직접 독해. 단계4의 두 task는 자동대조·정규화 검토 범위다.','']
timeline=['# 제어 흐름','','전체 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial20 관찰표','','최종 모두 유효·20점. C/I/U는 내용 주장 정답/오류/보류 발생 수.','',
 '|단계|task/setup|C/I/U|첫 전체 후보|변경/revise|질문|wait|거절|과정|','|---|---|---|---|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s=r['stage'];source=Path(r['source'])
    problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text());observations[s]=o
    controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    finals.append({'stage':s,'trial':20,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':20,'message':c['message'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c);types[c['type']]+=1
            claims.append({'stage':s,'trial':20,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected})
    reading.append({'stage':s,'trial':20,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(s,[]),
      'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,
      'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
      'full_additional_control_responses_read':(['request-1','request-2','request-16','request-17','request-18'] if s==6 else
                                               (['request-3','request-4','request-5','request-6'] if s==5 else [])),
      'language_dictionary_read':s==6})
    if s in READ:evidence += [f'## stage {s} / trial20','',f'원본: `{source}/events.jsonl`','']
    for seq in READ.get(s,[]):
        p=packets[seq];evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',p['sender_source'],'```','']
    timeline += [f'## stage {s} / trial20','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed';status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':20,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait':
            assert c['submissions_before']==c['submissions_after']=={'B':{'M1':1,'M2':6,'M3':10}}
            waits.append({'stage':s,'trial':20,**c})
        if c['applied'] and act=='revise':
            record=next(v for v in r['revision_events'] if v['request_id']==c['request_id'])
            assert not c['submissions_before'] and not c['submissions_after'] and not record['cleared_agents']
            revisions.append({'stage':s,'trial':20,'cleared_agents':[],**c})
    timeline.append('')
    pairs={3:[(1,2),(2,3)],4:[(1,2)],5:[(1,2)],6:[(5,6),(7,8),(9,10)]}.get(s,[])
    for qm,am in pairs:
        q=next(m for m in r['messages'] if m['message']==qm)['questions']
        answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys={(c['type'],*c['value'][:-1]) for c in answer if c['type'] in ['fact','summary']}
        assert qkeys==akeys
        qchecks.append({'stage':s,'trial':20,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_match':True})
    first=r['first_full_candidate'];score=first['evaluation']['score'];label='불가' if not first['evaluation']['valid'] else str(score)
    table.append(f"|{s}|{r['task_messages']}/{r['all_phase_messages']-r['task_messages']}|{r['correct_claims']}/0/0|m{first['message']} {first['schedule']} {label}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[s]}|")
    csvrows.append({'stage':s,'trial':20,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},
      'first_candidate_score':score,'first_candidate_valid':first['evaluation']['valid'],'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[s]})

assert controls=={'send':21,'submit':10,'wait':2,'revise':1}
assert len(candidates)==8 and len(claims)==730 and len(rejections)==6 and len(waits)==2 and len(revisions)==1
assert [(c['stage'],c['message']) for c in candidates if not c['valid']]==[(2,2)]
assert [(c['stage'],c['message'],c['score']) for c in candidates if c['valid'] and c['score']<20]==[(6,4,16)]
assert sum(map(len,READ.values()))==20
def row(s):return next(r for r in ROWS if r['stage']==s)
def response(s,req):return next(c for c in row(s)['control_sequence'] if c['request_id']==req)
def payload(s,msg):return next(c for c in row(s)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
# Exact language and message-use differences; rejected data did not reach peers.
assert response(3,'request-1')['action']['payload'].replace('availability','available')==payload(3,1)
old=response(6,'request-4')['action']['payload'];info,propose=old.split('\nprop().')
assert 'prop().'+propose==payload(6,4) and info==payload(6,10)
assert response(6,'request-8')['action']['payload'].replace('ask().','req().')==payload(6,5)
assert response(6,'request-9')['action']['payload'].replace('ask().','req().').replace('askfact(avail,','askfact(available,')==payload(6,5)
assert response(6,'request-7')['action']['payload'].replace('ask().','req().')==payload(6,7)
assert all(response(6,req)['action']['payload'].startswith('ask().\n') for req in ['request-6','request-7','request-8','request-9'])
obs=lambda s,seq:next(m for m in observations[s]['messages'] if m['message']==seq)
summary=lambda seq:{tuple(c['value']) for c in obs(6,seq)['claims'] if c['type']=='summary'}
assert len(summary(8))==6 and len(summary(10))==72 and summary(8)<=summary(10)
assert not any(c['type'] in ['schedule_valid','schedule_score','schedule_optimal'] for m in observations[6]['messages'] for c in m['claims'])
# 2/20 asks about an invalid schedule; the reply gives a correct reason and new proposal, not an explicit score answer for the old schedule.
assert obs(2,2)['questions'] and not obs(2,2)['claims'][-1]['type'].startswith('schedule_')
assert obs(2,3)['claims'][0]['type']=='reason'
assert {c['type'] for c in obs(2,4)['claims']}=={'schedule_valid','schedule_score'}
# 5/20 waits twice without any new peer packet between the proposal and final submissions.
assert [c['action']['action'] for c in row(5)['control_sequence']]==['send','send','submit','wait','wait','submit']
assert not any(c['delivered_messages'] for c in row(5)['control_sequence'][2:])
enumerated=[(s,independent(problem,s)) for s in (dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']];best=max(v['score'] for s,v in valid);optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'applied_task_controls':dict(controls),
 'protocol_rejections':6,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),
 'independent_claim_checks_file':'independent-claim-checks.json','question_response_checks':qchecks,'wait_events':waits,'revision_events':revisions,
 'stage6_setup_applied_without_rejection':True,'stage6_task_messages':9,'stage6_all_phase_messages':11,'stage6_rejections':5,
 'stage6_rejected_information_later_delivered_identically':True,'stage6_partial_summaries_repeated_in_full_set':6,
 'stage6_initial_candidate':{'schedule':{'M1':1,'M2':2,'M3':10},'valid':True,'independently_evaluated_score':16},
 'stage6_final_candidate':{'schedule':{'M1':1,'M2':6,'M3':10},'valid':True,'independently_evaluated_score':20},
 'stage6_no_explicit_candidate_score_or_validity_claims':True,'stage5_waited_twice_without_new_peer_packet':True,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review',
 'full_task_payloads_read':20,'task_payloads_total':22,'rejected_full_responses_read':6,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'independent_claim_counts':dict(types),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
