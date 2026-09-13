"""Local-only post-run audit of stages 2..6, trial 24."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text()); ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,24) for s in range(2,7)}
READ={3:list(range(1,7)),6:[3,4,5]}
NOTES={2:'요약 교환·제안·제출',3:'동일 문법 실패 5회 후 교정; 후보 유지; A 요약 6+54개(54고유)',4:'요약 질문·응답·제안·제출',5:'요약 질문·응답·제안·제출',6:'가용성 오류 1개 미교정; 제안 속 점수·유효성 질문은 peer 응답 없이 제출'}
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
assert totals=={'task_messages':16,'all_phase_messages':18,'correct_claims':711,'incorrect_claims':1,'undetermined_claims':0,'codec_errors':0,'changed_proposals':0,'explicit_revisions':0,'questions':280,'result_actions':33}
controls=collections.Counter(); types=collections.Counter(); candidates=[]; finals=[]; claims=[]; reading=[]; rejections=[]; observations={}; qchecks=[]
evidence=['# 선별 원문','','task 9/16개(3단계 전6개·6단계 전3개), 거절 5/5개 직접 독해. 나머지 task는 자동대조·정규화 검토.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial24 관찰표','','최초 전체 후보·최종 모두 유효20점. C/I/U는 내용 주장 발생 수.','', '|단계|task|C/I/U|첫 후보|변경/revise|질문|wait|거절|과정|','|---|---:|---|---|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s=r['stage']; source=Path(r['source']); problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text()); observations[s]=o; controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and r['submissions']['A']==r['submissions']['B']
    assert not r['revision_events'] and not r['wait_events'] and not r['changed_proposals']
    final=independent(problem,r['submissions']['A']); assert final['valid'] and final['score']==20
    finals.append({'stage':s,'trial':24,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']); assert got['valid'] and got['score']==20
        assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':24,'message':c['message'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c); types[c['type']]+=1
            claims.append({'stage':s,'trial':24,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected,'correct':c['correct']})
    reading.append({'stage':s,'trial':24,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(s,[]),
      'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
      'full_additional_control_responses_read':(['request-12','request-13'] if s==3 else (['request-1','request-2','request-6','request-7'] if s==6 else [])),
      'language_dictionary_read':s==6})
    if s in READ: evidence += [f'## stage{s} / trial24','','원본: `'+str(source)+'/events.jsonl`','']
    for seq in READ.get(s,[]):
        p=packets[seq]; evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'', '```text',p['sender_source'],'```','']
    timeline += [f'## stage{s} / trial24','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed'; status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':24,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
    timeline.append('')
    for qm,am in {3:[(3,4),(5,6)],4:[(1,2)],5:[(1,2)],6:[(3,4)]}.get(s,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions']; answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q}; akeys=set()
        for c in answer:
            if c['type']=='summary': akeys.add((c['type'],*c['value'][:-1]))
            if c['type'] in ['schedule_valid','schedule_score']:
                akeys.add((c['type'].split('_')[1],*[c['value']['schedule'][m] for m in ['M1','M2','M3']]))
        assert qkeys<=akeys
        qchecks.append({'stage':s,'trial':24,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'all_requested_keys_answered':True,'extra_answer_keys':[list(x) for x in sorted(akeys-qkeys)]})
    first=r['first_full_candidate']; table.append(f"|{s}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/{r['undetermined_claims']}|m{first['message']} 20점|0/0|{r['questions']}|0|{len(r['protocol_rejections'])}|{NOTES[s]}|")
    csvrows.append({'stage':s,'trial':24,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[s]})
assert controls=={'send':16,'submit':10}
assert len(candidates)==5 and len(claims)==712 and len(rejections)==5
assert sum(c['correct'] is True for c in claims)==711 and sum(c['correct'] is False for c in claims)==1
assert sum(map(len,READ.values()))==9

def row(s): return next(r for r in ROWS if r['stage']==s)
def response(s,req): return next(c for c in row(s)['control_sequence'] if c['request_id']==req)
def payload(s,msg): return next(c for c in row(s)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
def message(s,seq): return next(m for m in observations[s]['messages'] if m['message']==seq)

# Five identical rejected actions precede a complete syntactic repair in the next applied message.
failed=[response(3,f'request-{i}') for i in range(3,8)]
assert all(c['action']==failed[0]['action'] for c in failed)
assert all(c['rejected']['error']=='Unknown predicate or invalid syntax: ask summary' and not c['delivered_messages'] for c in failed)
assert failed[0]['action']['payload']=='request().\naskvalid(1,6,10).\naskscore(1,6,10).\nask summary'
assert payload(3,3).splitlines()[:3]==failed[0]['action']['payload'].splitlines()[:3]
assert len(payload(3,3).splitlines()[3:])==6 and all(x.startswith('asksummary(') for x in payload(3,3).splitlines()[3:])
assert response(3,'request-8')['delivered_messages']==[3]
assert not message(3,6)['schedule'] and message(3,6)['kinds']==['accept']
# The later 54 summary keys include all six candidate keys already answered, rather than 54 new keys.
initial_keys={tuple(c['value'][:-1]) for c in message(3,4)['claims'] if c['type']=='summary'}
later_keys={tuple(c['value'][:-1]) for c in message(3,6)['claims'] if c['type']=='summary'}
assert len(initial_keys)==6 and len(later_keys)==54 and initial_keys<=later_keys
assert len(later_keys-initial_keys)==48
all_possible={(typ,'A',m['id'],slot) for m in problem['meetings'] for slot in range(12) for typ in ['available','preference']}
missing=all_possible-later_keys
assert missing=={(typ,'A',m,slot) for typ in ['available','preference'] for m,slots in {'M1':[3,8],'M2':[1,3,8,9],'M3':[1,4,9]}.items() for slot in slots}
b_feasible={(typ,'A',m['id'],slot) for m in problem['meetings'] for slot in range(12) for typ in ['available','preference'] if all(problem['people'][p]['availability'][slot] for p in m['attendees'] if problem['people'][p]['owner']=='B')}
assert later_keys==b_feasible
# Error values are preserved as stated, with independently calculated expected values kept separate.
error=row(6)['incorrect_details'][0]
assert error['value']==['available','B','M1',9,0] and error['expected']==1
assert 'teamavl(B,M1,9,0).' in payload(6,3)
assert [p for m in problem['meetings'] if m['id']=='M1' for p in m['attendees'] if problem['people'][p]['owner']=='B']==['B1']
assert problem['people']['B1']['availability'][9] is True
later_same_key=[c for m in observations[6]['messages'] if m['message']>3 for c in m['claims'] if c['type']=='summary' and c['value'][:-1]==error['value'][:-1]]
assert not later_same_key
assert message(6,5)['questions']==[['score',1,6,10],['valid',1,6,10]] and not message(6,5)['claims']
assert [c['action']['action'] for c in row(6)['control_sequence']]==['define_language','accept_language','send','send','send','submit','submit']
assert not any(c['delivered_messages'] for c in row(6)['control_sequence'][5:])

enumerated=[(s,independent(problem,s)) for s in (dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']]; best=max(v['score'] for s,v in valid); optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
# Isolated summary counterfactual: only B/M1/slot9 availability becomes 0; not B1's availability in other meetings.
after=[(s,v) for s,v in valid if s['M1']!=9]; removed=[s for s,v in valid if s['M1']==9]
after_best=max(v['score'] for s,v in after); after_optimal=[s for s,v in after if v['score']==after_best]
assert removed and after_best==20 and after_optimal==optimal and row(6)['submissions']['A']['M1']!=9
cf={'method':'independent isolated summary counterfactual, availability(B,M1,9)=0 only','valid_before':len(valid),'valid_after':len(after),'removed_valid_schedules':removed,'optimal_score_before':best,'optimal_score_after':after_best,'optimal_schedules_unchanged':True,'submitted_schedule_affected':False,'actual_agent_belief_or_causation_inferred':False}
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged

dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'applied_task_controls':dict(controls),
 'protocol_rejections':5,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_checks_file':'independent-claim-checks.json',
 'question_response_checks':qchecks,'stage3_five_identical_rejected_actions':True,'stage3_next_applied_repair_request_id':'request-8',
 'stage3_A_summary_occurrences':60,'stage3_A_distinct_summary_keys':54,'stage3_A_repeated_summary_keys':6,'stage3_A_additional_distinct_summary_keys':48,
 'stage3_A_untransmitted_keys':[list(x) for x in sorted(missing)],'stage3_later_summary_keys_match_B_feasible_meeting_slots':True,
 'stage3_accept_has_no_at_schedule':True,'stage6_content_error':error,'stage6_error_explicitly_corrected':False,
 'stage6_final_two_questions_have_no_peer_answer':True,'independent_error_counterfactual':cf,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims); dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':9,'task_payloads_total':16,'rejected_full_responses_read':5,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n'); (OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n'); (OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0])); w.writeheader(); w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'independent_claim_counts':dict(types),'counterfactual':cf,'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
