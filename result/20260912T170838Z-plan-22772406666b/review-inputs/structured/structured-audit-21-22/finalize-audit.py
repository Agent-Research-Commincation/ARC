"""Read-only post-run audit for exactly stages 2..6, trials21..22; outputs in tmp."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text());ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}==set(itertools.product(range(2,7),[21,22]))
READ={(2,22):[1,2],(3,21):[1,2,3],(3,22):[1,2,3],(6,21):[3,4,5],(6,22):[3,4,5,6]}
NOTES={(2,21):'요약 교환·제안·제출',(2,22):'A/M3/3 선호도2→정답1, 미정정',(3,21):'종류중복 거절 뒤 정보만 전달; 후보19→20 revise',(3,22):'질문 오타 거절2회 뒤 요약만 전달, 상대요약+제안 수신',(4,21):'요약72개 요청·응답 및 제안',(4,22):'요약 교환·제안·제출',(5,21):'요약 교환·제안·제출',(5,22):'요약72개 요청·응답 및 제안',(6,21):'A 제출→B wait→A 유효성·점수 답변/accept→B 제출',(6,22):'B/M3/4 선호도3→정답0, 미정정'}


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
    assert expected==c['expected'] and (value==expected)==c['correct']
    return expected

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims','undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals=={'task_messages':25,'all_phase_messages':29,'correct_claims':1440,'incorrect_claims':2,'undetermined_claims':0,'codec_errors':0,'changed_proposals':1,'explicit_revisions':1,'questions':290,'result_actions':53}
controls=collections.Counter();types=collections.Counter();verdicts=collections.Counter();candidates=[];finals=[];claims=[];errors=[];reading=[];rejections=[];waits=[];revisions=[];qchecks=[]
evidence=['# 선별 원문','','task 15/25개 및 거절 응답3/3개 직접 독해. 다른 task는 자동대조·정규화 검토 범위다.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태를 대조했다.','']
table=['# 2~6단계 trial21~22 관찰표','','최종 모두 유효·20점. C/I/U는 내용 주장 정답/오류/보류 발생 수.','',
 '|단계/회차|task|C/I/U|첫 후보점수|변경/revise|질문|wait|거절|과정|','|---|---:|---|---:|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial'];key=(s,t);source=Path(r['source'])
    problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text())
    controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    finals.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':t,'message':c['message'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c);types[c['type']]+=1;verdicts[str(c['correct'])]+=1
            claims.append({'stage':s,'trial':t,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected,'correct':c['correct']})
            if not c['correct']:
                assert c['type']=='summary' and c['value'][0]=='preference'
                typ,team,meeting,slot,value=c['value']
                people=[p for mm in problem['meetings'] if mm['id']==meeting for p in mm['attendees'] if problem['people'][p]['owner']==team]
                later=[{'message':mm['message'],'claim':cc} for mm in o['messages'] if mm['message']>m['message']
                       for cc in mm['claims'] if cc['type']=='summary' and cc['value'][:-1]==c['value'][:-1]]
                assert not later
                unavailable=[p for p in people if not problem['people'][p]['availability'][slot]]
                assert unavailable
                same_message_availability=[cc['value'] for cc in m['claims'] if cc['type']=='summary' and cc['value'][:4]==['available',team,meeting,slot]]
                assert same_message_availability==[['available',team,meeting,slot,0]]
                errors.append({'stage':s,'trial':t,'message':m['message'],'sender':m['sender'],'value':c['value'],'expected':expected,
                  'attendee_preferences':{p:problem['people'][p]['preferences'][slot] for p in people},'unavailable_attendees':unavailable,
                  'same_message_correct_unavailability':same_message_availability,'later_same_key_claims':later,'explicit_correction_observed':False,'impact':c['impact']})
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(key,[]),
      'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,
      'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
      'full_additional_control_responses_read':(['request-4'] if key==(3,21) else (['request-5','request-6','request-7','request-8'] if key==(6,21) else [])),
      'language_dictionary_read':s==6})
    if key in READ:evidence += [f'## stage {s} / trial {t}','','원본: `'+str(source)+'/events.jsonl`','']
    for seq in READ.get(key,[]):
        p=packets[seq];evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',p['sender_source'],'```','']
    timeline += [f'## stage {s} / trial {t}','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed';status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':t,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait':
            assert key==(6,21) and c['submissions_before']==c['submissions_after']=={'A':{'M1':1,'M2':6,'M3':10}}
            waits.append({'stage':s,'trial':t,**c})
        if c['applied'] and act=='revise':
            record=next(v for v in r['revision_events'] if v['request_id']==c['request_id'])
            assert key==(3,21) and not c['submissions_before'] and not c['submissions_after'] and not record['cleared_agents']
            revisions.append({'stage':s,'trial':t,'cleared_agents':[],**c})
    timeline.append('')
    for qm,am in {(4,21):[(1,2)],(5,22):[(1,2)],(6,21):[(3,4)],(6,22):[(3,4)]}.get(key,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions'];answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys={(c['type'],*c['value'][:-1]) for c in answer if c['type']=='summary'}
        assert qkeys==akeys
        qchecks.append({'stage':s,'trial':t,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_match':True})
    score=r['first_full_candidate']['evaluation']['score']
    table.append(f"|{s}/{t}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/0|{score}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},
      'first_candidate_score':score,'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[key]})

assert controls=={'send':24,'submit':20,'wait':1,'revise':1}
assert len(candidates)==13 and len(claims)==1442 and len(errors)==2 and len(rejections)==3 and len(waits)==1 and len(revisions)==1
assert verdicts=={'True':1440,'False':2}
assert all(c['valid'] for c in candidates)
assert [(c['stage'],c['trial'],c['message'],c['score']) for c in candidates if c['score']<20]==[(3,21,2,19)]
assert sum(map(len,READ.values()))==15
def row(s,t):return next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
def response(s,t,req):return next(c for c in row(s,t)['control_sequence'] if c['request_id']==req)
def payload(s,t,msg):return next(c for c in row(s,t)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
assert response(3,21,'request-1')['action']['payload'].split('\nrequest().')[0]==payload(3,21,1)
assert not any(m['questions'] for m in row(3,22)['messages'])
assert [c['action']['action'] for c in row(6,21)['control_sequence'][-4:]]==['submit','wait','send','submit']
reply=next(m for m in row(6,21)['messages'] if m['message']==5)
assert reply['kind']=='accept' and reply['schedule']=={} and set(map(tuple,reply['evaluations']))=={('valid',1,6,10,1),('score',1,6,10,20)}
assert response(6,21,'request-7')['submissions_before']==response(6,21,'request-7')['submissions_after']=={'A':{'M1':1,'M2':6,'M3':10}}
enumerated=[(s,independent(problem,s)) for s in (dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']];best=max(v['score'] for s,v in valid);optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
for e in errors:
    meeting,slot=e['value'][2:4]
    assert not any(s[meeting]==slot for s,v in valid)
    e['no_valid_schedule_uses_error_slot']=True
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'applied_task_controls':dict(controls),
 'protocol_rejections':3,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_verdicts':dict(verdicts),
 'independent_claim_checks_file':'independent-claim-checks.json','errors_and_correction_checks':errors,'question_response_checks':qchecks,'wait_events':waits,'revision_events':revisions,
 'stage3_trial21_only_information_retained_after_rejection':True,'stage3_trial22_no_questions_delivered':True,
 'stage6_trial21_evaluation_response_after_own_submission':True,'stage6_trial21_accept_has_no_schedule_fields':True,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':15,'task_payloads_total':25,'rejected_full_responses_read':3,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'independent_claim_counts':dict(types),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
