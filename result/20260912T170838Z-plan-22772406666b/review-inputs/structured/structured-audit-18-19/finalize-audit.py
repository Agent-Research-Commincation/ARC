"""Local-only audit finalization for exactly stages 2..6, trials 18..19."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text());ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}==set(itertools.product(range(2,7),range(18,20)))
READ={(2,18):[1,2,3,4,5],(3,18):[1,2,3,4,5,6,7],(3,19):[1,2,3,4,5],(6,18):[3,4],(6,19):[3,4,5,6]}
NOTES={(2,18):'최적→불가→최적; 같은 payload revise가 B 제출 삭제, 재제출',
 (2,19):'제안 수락 후 양쪽 제출',(3,18):'술어 수정; 개인자료 10→72 요청; 제출→wait→accept→제출',
 (3,19):'질문 수정; 72개 질문에 108개 사실/요약 응답, A 전체요약 후속 요청',
 (4,18):'팀 요약 교환·제안 후 제출',(4,19):'개인 자료 교환·제안 후 제출',
 (5,18):'자료 교환·제안·수락 후 제출',(5,19):'요약 72개 질문·응답 및 제안',
 (6,18):'종류 누락·마침표 누락 수정',(6,19):'사전 수락/종류/질문 인수 수정; 제출 유지 중 wait·요약 반복'}

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
    else:raise AssertionError(t)
    assert value==expected==c['expected'] and c['correct'] is True
    return expected

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims',
 'undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals=={'task_messages':36,'all_phase_messages':40,'correct_claims':1572,'incorrect_claims':0,'undetermined_claims':0,
 'codec_errors':0,'changed_proposals':2,'explicit_revisions':2,'questions':442,'result_actions':76}
controls=collections.Counter();types=collections.Counter();candidates=[];finals=[];claims=[];reading=[];rejections=[];waits=[];revisions=[];qchecks=[]
evidence=['# 선별 원문','','task 23/36개 및 거절 응답 9/9개 직접 독해. 기타 task는 자동대조·정규화 결과 검토 범위다.','']
timeline=['# 제어 흐름','','모든 응답과 applied/rejected를 request ID로 연결하고 제출 상태를 재구성했다.','']
table=['# 2~6단계 trial18~19 관찰표','','10회 최종 유효·20점. 첫 전체 후보도 모두 최적이나 2/18은 중간에 불가 후보로 바뀌었다.','',
 '|단계/회차|task|C/I/U|첫 후보 점수|변경/revise|질문|wait|거절|과정|','|---|---:|---|---:|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial'];key=(s,t);source=Path(r['source'])
    problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    observed=json.loads((Path(r['output'])/'observation.json').read_text())
    controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    finals.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':t,'message':c['message'],'schedule':c['schedule'],**got})
    assert r['first_full_candidate']['evaluation']['score']==20
    for m in observed['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c);types[c['type']]+=1
            claims.append({'stage':s,'trial':t,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected})
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],
     'full_task_sender_source_read':READ.get(key,[]),'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,
     'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
     'full_control_responses_read':([c['request_id'] for c in r['control_sequence']] if key==(2,18) else
       (['request-8','request-9','request-10','request-11'] if key==(3,18) else
       (['request-3','request-10','request-11','request-12','request-14','request-15'] if key==(6,19) else []))),
     'language_dictionary_read':s==6})
    if key in READ:
        evidence += [f'## stage {s} / trial {t:02d}','',f'원본: `{source}/events.jsonl`','']
    for seq in READ.get(key,[]):
        p=packets[seq];evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',p['sender_source'],'```','']
    timeline += [f'## stage {s} / trial {t:02d}','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed';status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':t,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait':
            assert len(c['submissions_before'])==1 and c['submissions_before']==c['submissions_after']
            waits.append({'stage':s,'trial':t,**c})
        if c['applied'] and act=='revise':
            record=next(v for v in r['revision_events'] if v['request_id']==c['request_id'])
            assert sorted(c['submissions_before'])==record['cleared_agents'] and not c['submissions_after']
            revisions.append({'stage':s,'trial':t,'cleared_agents':record['cleared_agents'],**c})
    timeline.append('')
    pairs={(3,18):[(3,4),(5,6)],(3,19):[(1,2),(4,5)],(6,18):[(3,4)],(6,19):[(3,4)]}.get(key,[])
    for qm,am in pairs:
        q=next(m for m in r['messages'] if m['message']==qm)['questions']
        answer=next(m for m in observed['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys={(c['type'],*c['value'][:-1]) for c in answer if c['type'] in ['fact','summary']}
        assert qkeys<=akeys
        extra=akeys-qkeys
        assert len(extra)==(36 if (s,t,qm,am)==(3,19,1,2) else 0)
        qchecks.append({'stage':s,'trial':t,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),
                        'answer_keys':len(akeys),'missing_keys':[],'extra_keys':[list(x) for x in sorted(extra)]})
    table.append(f"|{s}/{t:02d}|{r['task_messages']}|{r['correct_claims']}/0/0|20|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},
                   'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[key]})

assert controls=={'send':34,'submit':21,'wait':6,'revise':2}
assert len(rejections)==9 and len(waits)==6 and len(revisions)==2 and len(candidates)==16 and len(claims)==1572
assert [(x['stage'],x['trial'],x['message']) for x in candidates if not x['valid']]==[(2,18,3)]
assert sum(map(len,READ.values()))==23
def row(s,t):return next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
def response(s,t,request):return next(c for c in row(s,t)['control_sequence'] if c['request_id']==request)
def message_payload(s,t,msg):return next(c for c in row(s,t)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
repairs=[]
for s,t,req,msg,changes in [(3,18,'request-1',1,{'teavailable':'teamavailable'}),
 (3,19,'request-2',1,{'askummary':'asksummary'}),(6,18,'request-5',4,{'prop()\n':'prop().\n'}),
 (6,19,'request-5',3,{'qs(av,':'qs(available,','qs(pref,':'qs(preference,'})]:
    old=response(s,t,req)['action']['payload'];new=message_payload(s,t,msg);replaced=old
    for a,b in changes.items():replaced=replaced.replace(a,b)
    assert replaced==new
    repairs.append({'stage':s,'trial':t,'rejected_request':req,'applied_message':msg,'only_changes':changes})
assert 'inf().\n'+response(6,18,'request-3')['action']['payload']==message_payload(6,18,3)
assert 'i().\n'+response(6,19,'request-4')['action']['payload']==response(6,19,'request-5')['action']['payload']
assert response(6,19,'request-7')['action']['payload'].split('\nprp().')[0]==message_payload(6,19,4)
# A repeats exactly the same peer payload via revise, invalidating B's correct submission.
same_payload=response(2,18,'request-4')['action']['payload']==response(2,18,'request-8')['action']['payload'];assert same_payload
clearing=response(2,18,'request-8');assert clearing['submissions_before']=={'B':{'M1':1,'M2':6,'M3':10}} and not clearing['submissions_after']
assert response(2,18,'request-5')['action']['schedule']==response(2,18,'request-9')['action']['schedule']
# All A team summaries in 6/19 m6 repeat m3, while B's existing submission is preserved.
r=row(6,19);o=json.loads((Path(r['output'])/'observation.json').read_text())
values=lambda seq:{tuple(c['value']) for m in o['messages'] if m['message']==seq for c in m['claims']}
assert values(3)==values(6) and len(values(6))==72
for req in ['request-11','request-12','request-13','request-14']:
    c=response(6,19,req);assert c['submissions_before']==c['submissions_after']=={'B':{'M1':1,'M2':6,'M3':10}}
enumerated=[(s,independent(problem,s)) for s in (dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']];best=max(v['score'] for s,v in valid);optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,
 'applied_task_controls':dict(controls),'protocol_rejections':9,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),
 'independent_claim_checks_file':'independent-claim-checks.json','question_response_checks':qchecks,'payload_repair_checks':repairs,
 'wait_events':waits,'revision_events':revisions,'stage2_trial18_identical_payload_revise_cleared_B':same_payload,
 'stage2_trial18_B_resubmitted_same_schedule':True,'stage6_trial19_72_summaries_repeated':True,'stage6_trial19_submission_preserved':True,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus selective direct raw reading; not manual exhaustive review',
 'full_task_payloads_read':23,'task_payloads_total':36,'rejected_full_responses_read':9,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n')
(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n')
(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'candidate_checks':len(candidates),
                  'independent_claim_counts':dict(types),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
