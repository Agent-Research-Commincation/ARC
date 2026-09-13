"""Local-only final post-run audit of stages 2..6, trials 29 and 30."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text());ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,t) for s in range(2,7) for t in [29,30]}
READ={(2,29):[1],(3,29):[1,2,3,4,5,6],(3,30):[1,2,3,4,5],(5,29):[1,2,3],(6,29):[3,5,6],(6,30):[4,5,6]}
EXTRA={(2,29):['request-4','request-5'],(3,29):['request-13','request-14','request-15','request-16'],(3,30):['request-10','request-11'],(5,29):['request-4','request-5','request-6'],(6,29):['request-1','request-2','request-8','request-9'],(6,30):['request-1','request-2','request-8','request-9']}
NOTES={(2,29):'중복 summaries 빈 필드 삭제',(2,30):'자료·최적 제안·제출',(3,29):'거절7회; B제출→A wait→B수락 전송→A제출',(3,30):'거절4회; 질문과 정보를 분리 전송',(4,29):'자료·최적 제안·수락·제출',(4,30):'자료·최적 제안·제출',(5,29):'첫 무효 후보를 B1 불가 사유·revise로 교정',(5,30):'요약54개 질문에72개 응답',(6,29):'빠진 info 종류만 추가; 빈 일정 수락',(6,30):'빠진 info 종류만 추가; 빈 일정 수락'}
waits=[]
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
assert totals=={'task_messages':33,'all_phase_messages':37,'correct_claims':1453,'incorrect_claims':0,'undetermined_claims':0,'codec_errors':0,'changed_proposals':1,'explicit_revisions':1,'questions':415,'result_actions':73}
controls=collections.Counter();types=collections.Counter();candidates=[];finals=[];claims=[];reading=[];rejections=[];observations={};held=[];errors=[];revisions=[];qchecks=[]
evidence=['# 선별 원문','','29~30회차 task 21/33개, 거절15/15개 직접 독해. 나머지는 자동대조·정규화 검토.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial29~30 관찰표','','모두 유효 제출·최적20점. C/I/U는 내용 주장 발생 수.','', '|단계/회차|최종|task|C/I/U|첫 후보|변경/revise|질문|거절|과정|','|---|---:|---:|---|---|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial'];key=(s,t);source=Path(r['source']);problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text());observations[key]=o;controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['operational_status']=='normal' and r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    assert r['score']==final['score'] and r['quality_gap']==20-r['score'];finals.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':t,'message':c['message'],'kind':c['kind'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        action=next(c for c in r['control_sequence'] if m['message'] in c['delivered_messages'])['action'];assert packets[m['message']]['sender_source']==action['payload']
        for c in m['claims']:
            types[c['type']]+=1
            expected=claim_expected(problem,c);assert c['correct'] is True
            claims.append({'stage':s,'trial':t,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected,'correct':c['correct']})
            if c['correct'] is False:errors.append({'stage':s,'trial':t,**c})
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(key,[]),'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],'full_additional_control_responses_read':EXTRA.get(key,[]),'language_dictionary_read':s==6,'action_payload_reads_matched_sender_source':True})
    if key in READ:evidence += [f'## stage{s} / trial{t}','','원본: `'+str(source)+'/events.jsonl`','']
    for seq in READ.get(key,[]):
        p=packets[seq];evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',p['sender_source'],'```','']
    timeline += [f'## stage{s} / trial{t}','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed';status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':t,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait':waits.append({'stage':s,'trial':t,**c})
        if c['applied'] and act=='revise':
            assert c['submissions_before']==c['submissions_after']=={};revisions.append({'stage':s,'trial':t,**c})
    timeline.append('')
    for qm,am in {(3,29):[(1,2),(4,5)],(3,30):[(1,2)],(4,29):[(1,2)],(4,30):[(1,2)],(5,30):[(1,2)],(6,30):[(3,4)]}.get(key,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions'];answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys=set()
        for c in answer:
            if c['type'] in ['fact','summary']:akeys.add((c['type'],*c['value'][:-1]))
            if c['type'] in ['schedule_score','schedule_valid']:akeys.add((c['type'].split('_')[1],*[c['value']['schedule'][m] for m in ['M1','M2','M3']]))
        exact_answered=qkeys&akeys
        assert qkeys<=akeys
        qchecks.append({'stage':s,'trial':t,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_requested_keys_answered':len(exact_answered),'extra_answer_keys':[list(x) for x in sorted(akeys-qkeys)],'unanswered_exact_keys':[list(x) for x in sorted(qkeys-akeys)],'value_correctness_scored_separately':True})
    first=r['first_full_candidate'];fl=f"m{first['message']} "+(f"{first['evaluation']['score']}점" if first['evaluation']['valid'] else '무효')
    table.append(f"|{s}/{t}|{r['score']}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/{r['undetermined_claims']}|{fl}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[key]})
assert controls=={'send':32,'submit':20,'revise':1,'wait':1}
assert len(candidates)==14 and len(claims)==1453 and len(errors)==len(held)==0 and len(rejections)==15
assert sum(c['correct'] is True for c in claims)==1453 and sum(map(len,READ.values()))==21 and len(revisions)==1 and len(waits)==1

def row(s,t):return next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
def response(s,t,req):return next(c for c in row(s,t)['control_sequence'] if c['request_id']==req)
def payload(s,t,msg):return next(c for c in row(s,t)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
def message(s,t,seq):return next(m for m in observations[s,t]['messages'] if m['message']==seq)

# 3/29: initial repeated invalid summary requests are replaced with one fact request, then richer information follows.
assert response(3,29,'request-1')['action']==response(3,29,'request-3')['action']==response(3,29,'request-4')['action']
assert response(3,29,'request-2')['action']['payload']=='request().\nasks ummary'
assert payload(3,29,1)=='request().\naskfact(available,B1,0).'
assert response(3,29,'request-6')['action']['payload'].split('\nteamsummary')[0]=='\n'.join(payload(3,29,2).splitlines()[:3])
assert len(message(3,29,2)['claims'])==74
assert response(3,29,'request-9')['action']['payload']=='request().\nasks ummary'
assert response(3,29,'request-10')['action']['payload'].replace('asks ummary','asksummary')=='\n'.join(payload(3,29,4).splitlines()[:2])
assert len(message(3,29,4)['questions'])==72
assert [c['action']['action'] for c in row(3,29)['control_sequence'][-4:]]==['submit','wait','send','submit']
assert response(3,29,'request-15')['delivered_messages']==[6] and message(3,29,6)['kinds']==['accept']
assert response(3,29,'request-13')['submissions_after']==waits[0]['submissions_before']==waits[0]['submissions_after']==response(3,29,'request-15')['submissions_after']=={'B':{'M1':1,'M2':6,'M3':10}}
# 3/30: first split the rejected mixed message; then correct one predicate but remove an unrelated invalid request after its repeat.
bad=response(3,30,'request-1')['action']['payload']
assert bad.split('\nrequest().')[0]==payload(3,30,3)
assert 'request().'+bad.split('\nrequest().')[1]==payload(3,30,1)
assert response(3,30,'request-3')['action']['payload'].replace('te amavailable','teamavailable')==response(3,30,'request-4')['action']['payload']
assert response(3,30,'request-4')['action']==response(3,30,'request-5')['action']
assert response(3,30,'request-5')['action']['payload'].split('\nask summary')[0]==payload(3,30,2)
assert not any(m['questions'] for m in row(3,30)['messages'] if m['sender']=='A')
# Exact low-level repairs elsewhere; contents retained.
bad=response(2,29,'request-1')['action']['payload'];assert bad.count('"summaries":')==2
assert bad.replace(',"summaries":[]','',1)==payload(2,29,1)
bad=response(5,29,'request-1')['action']['payload']
assert bad.replace('KIND inform','KIND request',1).replace('\nKIND request','',1)==payload(5,29,1)
assert 'AV B1 8 0' in payload(5,29,2) and 'WHY_UNAVAILABLE M1 B1 8' in payload(5,29,3)
assert [c['schedule'] for c in row(5,29)['full_candidates']]==[{'M1':8,'M2':6,'M3':10},{'M1':1,'M2':6,'M3':10}]
assert not row(5,29)['revision_events'][0]['cleared_agents']
for t,req,m in [(29,'request-3',3),(30,'request-4',4)]:
    assert 'info().\n'+response(6,t,req)['action']['payload']==payload(6,t,m)
    assert message(6,t,6)['kinds']==['accept'] and message(6,t,6)['schedule']=={}
aa={tuple(c['value']) for c in message(3,29,3)['claims'] if c['type']=='summary'};bb={tuple(c['value']) for c in message(3,29,5)['claims'] if c['type']=='summary'}
assert len(aa)==6 and len(bb)==72 and aa<=bb
# The 54 stage5 questions cover B-feasible meeting-slots; the answer contains all 72 A summary fields.
q={tuple(x) for x in message(5,30,1)['questions']}
expected_q={('summary',ty,'A',m['id'],sl) for m in problem['meetings'] for sl in range(12) for ty in ['available','preference'] if all(problem['people'][p]['availability'][sl] for p in m['attendees'] if problem['people'][p]['owner']=='B')}
assert q==expected_q and len(q)==54 and len(message(5,30,2)['claims'])==72
all_schedules=[dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3)];values=[independent(problem,s) for s in all_schedules]
valid={i:v['score'] for i,v in enumerate(values) if v['valid']};best=max(valid.values());optimal=[all_schedules[i] for i,score in valid.items() if score==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged

dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'statuses':{'success':10},'final_score_counts':{'20':10},'applied_task_controls':dict(controls),'protocol_rejections':15,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_checks_file':'independent-claim-checks.json','question_response_checks':qchecks,'revise_events':revisions,'wait_events':waits,'stage3_trial29_B_submission_then_A_wait_then_B_peer_accept_then_A_submission':True,'stage3_trial29_B_submission_preserved':True,'stage3_trial29_A_summary_occurrences':78,'stage3_trial29_A_summary_unique_keys':72,'stage3_trial30_B_rejected_mixed_message_split_into_two_later_packets':True,'stage3_trial30_A_invalid_question_removed_not_retransmitted':True,'stage5_trial29_invalid_first_candidate_explicitly_corrected':True,'stage5_trial30_54_question_keys_match_B_feasible_meeting_slots':True,'stage6_both_missing_kinds_added_without_content_change':True,'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':21,'task_payloads_total':33,'rejected_full_responses_read':15,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'claim_types':dict(types),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
