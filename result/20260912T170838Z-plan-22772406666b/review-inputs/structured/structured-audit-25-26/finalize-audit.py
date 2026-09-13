"""Local-only post-run audit of stages 2..6, trials 25 and 26."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text()); ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,t) for s in range(2,7) for t in [25,26]}
READ={(2,25):[1],(2,26):[1,2,3,4],(3,26):[2],(5,25):[1,2,3,4],(5,26):[2,3],(6,25):[3,4,5,6],(6,26):[5]}
EXTRA={(2,26):['request-3','request-4','request-5','request-6'],(4,25):['request-3','request-4','request-5','request-6'],(5,25):['request-3','request-4','request-5','request-6'],(5,26):['request-4','request-5'],(6,25):['request-2','request-3','request-6','request-8','request-9','request-10','request-11','request-12'],(6,26):['request-1','request-2','request-6','request-7']}
NOTES={(2,25):'중복 JSON 키 제거 후 전달',(2,26):'최적→무효→최적; 불가 사유 명시; 별도 요약 오류 미교정',(3,25):'요약·최적 제안·제출',(3,26):'선호도 요약 1개 미교정',(4,25):'A 제출 뒤 B/A wait; 새 peer 메시지 없음',(4,26):'B 요약·A 개인 자료 교환',(5,25):'최적→무효→최적; 불가 사유 명시; 무효 점수 보류',(5,26):'선호도 요약 1개 미교정',(6,25):'가용성 2개 오류; 무효 제안·수락·양쪽 제출; 교정 없음',(6,26):'마지막 유효성·점수 질문은 peer 답변 없이 제출'}
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
assert totals=={'task_messages':29,'all_phase_messages':33,'correct_claims':1439,'incorrect_claims':6,'undetermined_claims':2,'codec_errors':0,'changed_proposals':4,'explicit_revisions':4,'questions':148,'result_actions':60}
controls=collections.Counter(); types=collections.Counter(); candidates=[]; finals=[]; claims=[]; reading=[]; rejections=[]; observations={}; held=[]; errors=[]; waits=[]; revisions=[]; qchecks=[]
evidence=['# 선별 원문','','task 17/29개, 거절 5/5개 직접 독해. 상세 범위는 source-reading-log.json. 나머지 task는 자동대조·정규화 검토.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial25~26 관찰표','','C/I/U는 내용 주장 발생 수. 무효 일정의 공식 점수는 미정의이며 0점으로 치환하지 않았다.','', '|단계/회차|상태/점수|task|C/I/U|첫 후보|변경/revise|질문|wait|거절|과정|','|---|---|---:|---|---|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial']; key=(s,t); source=Path(r['source']); problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text()); observations[key]=o; controls.update(r['applied_task_controls'])
    assert r['operational_status']=='normal' and r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A'])
    assert (final['valid'],final['score'])==((False,None) if key==(6,25) else (True,20))
    assert r['status']==('failed' if key==(6,25) else 'success') and r['score']==final['score']
    finals.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']); assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':t,'message':c['message'],'kind':c['kind'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        action=next(c for c in r['control_sequence'] if m['message'] in c['delivered_messages'])['action']
        assert packets[m['message']]['sender_source']==action['payload']
        for c in m['claims']:
            types[c['type']]+=1
            if c['correct'] is None:
                assert c['type']=='schedule_score'
                independent_value=independent(problem,c['value']['schedule'])
                assert not independent_value['valid'] and c['expected'] is None and c['candidate_valid'] is False
                assert independent_value['arithmetic_sum']==c['value']['score']==c['arithmetic_sum']==25 and c['arithmetic_matches'] is True
                assert c['interpretation']=='legacy_infeasible_score_unspecified'; expected=None
                held.append({'stage':s,'trial':t,**c,'independent':independent_value})
            else: expected=claim_expected(problem,c)
            check={'stage':s,'trial':t,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected,'correct':c['correct']}
            claims.append(check)
            if c['correct'] is False: errors.append({'stage':s,'trial':t,**c})
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(key,[]),
      'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
      'full_additional_control_responses_read':EXTRA.get(key,[]),'language_dictionary_read':s==6,
      'stage6_trial25_task_original_read_via_action_payload_and_matched_sender_source':key==(6,25)})
    if key in READ: evidence += [f'## stage{s} / trial{t}','','원본: `'+str(source)+'/events.jsonl`','']
    for seq in READ.get(key,[]):
        p=packets[seq]; evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'', '```text',p['sender_source'],'```','']
    timeline += [f'## stage{s} / trial{t}','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed'; status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':t,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait': waits.append({'stage':s,'trial':t,**c})
        if c['applied'] and act=='revise':
            assert c['submissions_before']==c['submissions_after']=={}
            revisions.append({'stage':s,'trial':t,**c})
    timeline.append('')
    for qm,am in {(4,25):[(1,2)],(6,26):[(3,4)]}.get(key,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions']; answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q}; akeys={(c['type'],*c['value'][:-1]) for c in answer if c['type']=='summary'}
        assert qkeys==akeys
        qchecks.append({'stage':s,'trial':t,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_match':True})
    first=r['first_full_candidate']; first_label=f"m{first['message']} "+('20점' if first['evaluation']['valid'] else '무효')
    outcome='성공/20' if r['status']=='success' else '실패/미정의'
    table.append(f"|{s}/{t}|{outcome}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/{r['undetermined_claims']}|{first_label}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[key]})
assert controls=={'send':25,'submit':20,'revise':4,'wait':2}
assert len(candidates)==17 and len(claims)==1447 and len(errors)==6 and len(held)==2 and len(rejections)==5
assert sum(c['correct'] is True for c in claims)==1439 and sum(map(len,READ.values()))==17
assert len(revisions)==4 and len(waits)==2

def row(s,t): return next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
def response(s,t,req): return next(c for c in row(s,t)['control_sequence'] if c['request_id']==req)
def payload(s,t,msg): return next(c for c in row(s,t)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
def message(s,t,seq): return next(m for m in observations[s,t]['messages'] if m['message']==seq)

bad_json=response(2,25,'request-1')['action']['payload']
assert bad_json.count('"summaries":')==2 and bad_json.replace(',"summaries":[]','',1)==payload(2,25,1)
assert response(2,25,'request-1')['rejected']['error']=='Duplicate JSON key: summaries'
# Separate dictionary repair, vocabulary repair, and dropped incompatible kinds/requests.
lbad={v['meaning']:v['symbol'] for v in response(6,25,'request-1')['action']['language']}
lgood={v['meaning']:v['symbol'] for v in response(6,25,'request-2')['action']['language']}
assert lbad['teamavailable']=='teamavail' and len(lbad['teamavailable'])==9
assert {**lbad,'teamavailable':'tavail'}==lgood
assert response(6,25,'request-4')['action']['payload'].replace('tpref(','teampref(')==response(6,25,'request-5')['action']['payload']
assert response(6,25,'request-5')['action']['payload'].split('\nrequest().')[0]==payload(6,25,3)
assert response(6,25,'request-5')['action']['payload'].count('asksum(')==72 and not message(6,25,3)['questions']
assert response(6,25,'request-7')['action']['payload'].split('\npropose().')[0]==payload(6,25,4)
assert response(6,25,'request-7')['action']['payload'].split('\npropose().')[1]=='\nat(M1,8).\nat(M2,6).\nat(M3,10).'
assert not response(6,25,'request-7')['delivered_messages']
assert 'tavail(B,M1,8,1).' in payload(6,25,4) and 'tavail(B,M2,8,1).' in payload(6,25,4)
assert row(6,25)['first_full_candidate']['message']==5 and not row(6,25)['changed_proposals']
assert all(c['schedule']=={'M1':8,'M2':6,'M3':10} for c in row(6,25)['full_candidates'])
# Both recovering trials had truthful availability information before the invalid counterproposal.
assert ['available','B','M1',8,0] in json.loads(payload(2,26,1))['summaries']
assert 'AV B1 8 0' in payload(5,25,2)
for s,t in [(2,26),(5,25)]:
    assert [c['schedule'] for c in row(s,t)['full_candidates']]==[{'M1':1,'M2':6,'M3':10},{'M1':8,'M2':6,'M3':10},{'M1':1,'M2':6,'M3':10}]
    assert [c['action']['action'] for c in row(s,t)['control_sequence']]==['send','send','revise','revise','submit','submit']
    assert all(not c['cleared_agents'] for c in row(s,t)['revision_events'])
    assert any(c['type']=='reason' and c['value']==['unavailable','M1','B1',8] and c['correct'] for c in message(s,t,4)['claims'])
assert message(2,26,4)['questions']==[['summary','available','B','M1',8],['valid',8,6,10]]
assert message(2,26,4)['references']==[1,3]
assert not any(c['delivered_messages'] for c in row(2,26)['control_sequence'][4:])
assert [c['action']['action'] for c in row(4,25)['control_sequence']]==['send','send','submit','wait','wait','submit']
assert all(w['submissions_before']==w['submissions_after']=={'A':{'M1':1,'M2':6,'M3':10}} for w in waits)
assert not any(c['delivered_messages'] for c in row(4,25)['control_sequence'][2:])
assert message(6,26,5)['questions']==[['score',1,6,10],['valid',1,6,10]] and not message(6,26,5)['claims']
assert not any(c['delivered_messages'] for c in row(6,26)['control_sequence'][5:])
# Summary errors have no later explicit update to the same key. The false validity claim is contradicted by the peer's reason.
corrections=[]
for e in errors:
    s,t=e['stage'],e['trial']
    if e['type']=='summary':
        later=[c for m in observations[s,t]['messages'] if m['message']>e['message'] for c in m['claims'] if c['type']=='summary' and c['value'][:-1]==e['value'][:-1]]
        assert not later
        corrections.append({'stage':s,'trial':t,'message':e['message'],'type':e['type'],'value':e['value'],'later_same_key_claims':[],'explicit_correction':False})
    else:
        assert (s,t,e['type'])==(2,26,'schedule_valid')
        corrections.append({'stage':s,'trial':t,'message':e['message'],'type':e['type'],'value':e['value'],'later_peer_contradiction_message':4,'later_peer_reason':['unavailable','M1','B1',8],'explicit_valid_zero_restatement':False,'candidate_returned_to_valid':True})

# Independent team-summary override evaluator; it does not alter an individual's other meeting summaries.
def counterfactual(problem,schedule,overrides):
    meetings={m['id']:m['attendees'] for m in problem['meetings']}
    valid=all(schedule[a]<schedule[b] for a,b in problem['precedence'])
    valid=valid and all(schedule[a]!=schedule[b] or not(set(meetings[a])&set(meetings[b])) for a,b in itertools.combinations(meetings,2))
    total=0
    for m,ps in meetings.items():
        slot=schedule[m]
        for team in ['A','B']:
            ppl=[p for p in ps if problem['people'][p]['owner']==team]
            available=overrides.get(('available',team,m,slot),int(all(problem['people'][p]['availability'][slot] for p in ppl)))
            preference=overrides.get(('preference',team,m,slot),sum(problem['people'][p]['preferences'][slot] for p in ppl))
            valid=valid and bool(available); total+=preference
    return {'valid':bool(valid),'score':total if valid else None,'arithmetic_sum':total}

all_schedules=[dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3)]
baseline=[independent(problem,s) for s in all_schedules]
assert baseline==[counterfactual(problem,s,{}) for s in all_schedules]
base_valid={i:v['score'] for i,v in enumerate(baseline) if v['valid']}; best=max(base_valid.values()); optimal=[all_schedules[i] for i,score in base_valid.items() if score==best]
assert len(base_valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
cfs=[]
for e in [x for x in errors if x['type']=='summary']:
    value=e['value']; overrides={tuple(value[:-1]):value[-1]}
    after=[counterfactual(problem,s,overrides) for s in all_schedules]; av={i:v['score'] for i,v in enumerate(after) if v['valid']}; ab=max(av.values()); ao=[all_schedules[i] for i,v in av.items() if v==ab]
    submitted=row(e['stage'],e['trial'])['submissions']['A']; before_sub=independent(problem,submitted); after_sub=counterfactual(problem,submitted,overrides)
    effects={'feasible_set_changed':set(av)!=set(base_valid),'schedule_scores_changed':av!=base_valid,'optimal_score_before':best,'optimal_score_after':ab,'optimal_schedules_changed':optimal!=ao,'submitted_schedule_affected':before_sub!=after_sub}
    for k,v in effects.items(): assert e['impact'][k]==v
    cfs.append({'stage':e['stage'],'trial':e['trial'],'message':e['message'],'value':value,'expected':e['expected'],'method':'independent isolated team-summary override','valid_before':len(base_valid),'valid_after':len(av),'optimal_schedules_after':ao,'submitted_before':before_sub,'submitted_after':after_sub,**effects})
combined_overrides={tuple(e['value'][:-1]):e['value'][-1] for e in errors if (e['stage'],e['trial'])==(6,25)}
combined_values=[counterfactual(problem,s,combined_overrides) for s in all_schedules]
combined_valid={i:v['score'] for i,v in enumerate(combined_values) if v['valid']}; combined_best=max(combined_valid.values()); combined_opt=[all_schedules[i] for i,v in combined_valid.items() if v==combined_best]
assert combined_best==25 and row(6,25)['submissions']['A'] in combined_opt
combined={'stage':6,'trial':25,'method':'both transmitted summary errors applied together; not a causal experiment','valid_count':len(combined_valid),'optimal_score':combined_best,'optimal_schedules':combined_opt,'submitted_schedule_is_counterfactual_optimum':True,'actual_belief_or_cause_inferred':False}
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged

dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'statuses':dict(collections.Counter(r['status'] for r in ROWS)),'applied_task_controls':dict(controls),
 'protocol_rejections':5,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_checks_file':'independent-claim-checks.json',
 'held_score_checks':held,'independent_error_counterfactuals':cfs,'combined_stage6_trial25_errors':combined,'correction_checks':corrections,
 'question_response_checks':qchecks,'wait_events':waits,'revise_events':revisions,'all_four_revises_before_any_submission':True,
 'stage2_trial25_duplicate_empty_summaries_field_removed':True,'stage6_trial25_dictionary_single_symbol_shortened':True,
 'stage6_trial25_A_vocabulary_repaired_then_all_72_questions_removed':True,'stage6_trial25_B_rejected_invalid_proposal_removed_before_delivery':True,
 'stage6_trial25_delivered_invalid_candidate_uncorrected':True,'stage2_trial26_final_two_questions_have_no_peer_answer':True,'stage6_trial26_final_two_questions_have_no_peer_answer':True,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':17,'task_payloads_total':29,'rejected_full_responses_read':5,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'claim_types':dict(types),'counterfactuals':cfs,'combined':combined,'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
