"""Post-run audit of stages 2..6, trials 27 and 28; separate authorized 3/07 value comparison."""
import collections
import csv
import hashlib
import itertools
import json
import re
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text()); ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,t) for s in range(2,7) for t in [27,28]}
READ={(2,28):[1,2,3,4,5,6],(3,27):[1,2,3,4,5],(3,28):[1,2,4],(4,27):[2,3],(4,28):[2,3,4],(6,27):[3,4,5,6],(6,28):[4,5,6,7,8]}
EXTRA={(2,28):['request-5','request-6','request-7','request-8'],(3,27):['request-10','request-11'],(3,28):['request-9','request-10'],(4,27):['request-3','request-4','request-5'],(4,28):['request-3','request-4','request-5','request-6'],(6,27):['request-1','request-2','request-7','request-8'],(6,28):['request-1','request-3','request-4','request-13','request-14']}
NOTES={(2,27):'자료·최적 제안·제출',(2,28):'추가 개인 정보 교환 뒤 최적→무효→최적; 명시 불가 사유',(3,27):'B M1 요약 오류 12회/11고유; 미교정·19점',(3,28):'개인 fact 질문에 팀 summary 응답; 질문 72개는 후속 전송',(4,27):'첫 무효 후보→최적; 명시 사유 없음',(4,28):'최적→무효→최적; A1 불가 사유',(5,27):'자료·최적 제안·수락·제출',(5,28):'후보 요약 6개 뒤 전체 72개 요청·응답',(6,27):'첫 무효 후보를 send로 교정; 명시 valid0·사유; score23 보류',(6,28):'같은 사전 재정의 뒤 합의; 문법·기호 교정; 후보 유지'}
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

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims','undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals=={'task_messages':42,'all_phase_messages':47,'correct_claims':1414,'incorrect_claims':12,'undetermined_claims':1,'codec_errors':0,'changed_proposals':6,'explicit_revisions':5,'questions':510,'result_actions':77}
controls=collections.Counter();types=collections.Counter();candidates=[];finals=[];claims=[];reading=[];rejections=[];observations={};held=[];errors=[];revisions=[];qchecks=[]
evidence=['# 선별 원문','','27~28회차 task 28/42개, 거절10/10개 직접 독해. 별도 승인된 3/07 m2 값 비교는 현재 회차 집계에서 제외.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial27~28 관찰표','','모두 유효 제출 성공. 3/27만 19점, 나머지는 최적20점. C/I/U는 내용 주장 발생 수.','', '|단계/회차|최종|task|C/I/U|첫 후보|변경/revise|질문|거절|과정|','|---|---:|---:|---|---|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial'];key=(s,t);source=Path(r['source']);problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text());observations[key]=o;controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['operational_status']=='normal' and r['submissions']['A']==r['submissions']['B'] and not r['wait_events']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==(19 if key==(3,27) else 20)
    assert r['score']==final['score'] and r['quality_gap']==20-r['score'];finals.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':t,'message':c['message'],'kind':c['kind'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        action=next(c for c in r['control_sequence'] if m['message'] in c['delivered_messages'])['action'];assert packets[m['message']]['sender_source']==action['payload']
        for c in m['claims']:
            types[c['type']]+=1
            if c['correct'] is None:
                assert key==(6,27) and c['type']=='schedule_score';iv=independent(problem,c['value']['schedule'])
                assert not iv['valid'] and c['expected'] is None and c['candidate_valid'] is False
                assert iv['arithmetic_sum']==c['value']['score']==c['arithmetic_sum']==23 and c['arithmetic_matches'] is True
                assert c['interpretation']=='legacy_infeasible_score_unspecified';expected=None;held.append({'stage':s,'trial':t,**c,'independent':iv})
            else:expected=claim_expected(problem,c)
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
        if c['applied'] and act=='revise':
            assert c['submissions_before']==c['submissions_after']=={};revisions.append({'stage':s,'trial':t,**c})
    timeline.append('')
    for qm,am in {(2,28):[(3,4)],(3,27):[(1,2),(3,4)],(3,28):[(1,2),(4,5)],(4,27):[(1,2)],(5,27):[(1,2)],(5,28):[(3,4)],(6,27):[(4,5)],(6,28):[(5,6),(6,7)]}.get(key,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions'];answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys=set()
        for c in answer:
            if c['type'] in ['fact','summary']:akeys.add((c['type'],*c['value'][:-1]))
            if c['type'] in ['schedule_score','schedule_valid']:akeys.add((c['type'].split('_')[1],*[c['value']['schedule'][m] for m in ['M1','M2','M3']]))
        exact_answered=qkeys&akeys
        if (s,t,qm)!=(3,28,1):assert qkeys<=akeys
        else:assert len(qkeys)==len(akeys)==72 and not exact_answered
        qchecks.append({'stage':s,'trial':t,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_requested_keys_answered':len(exact_answered),'extra_answer_keys':[list(x) for x in sorted(akeys-qkeys)],'unanswered_exact_keys':[list(x) for x in sorted(qkeys-akeys)],'value_correctness_scored_separately':True})
    first=r['first_full_candidate'];fl=f"m{first['message']} "+(f"{first['evaluation']['score']}점" if first['evaluation']['valid'] else '무효')
    table.append(f"|{s}/{t}|{r['score']}|{r['task_messages']}|{r['correct_claims']}/{r['incorrect_claims']}/{r['undetermined_claims']}|{fl}|{r['changed_proposals']}/{r['explicit_revisions']}|{r['questions']}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[key]})
assert controls=={'send':37,'submit':20,'revise':5}
assert len(candidates)==20 and len(claims)==1427 and len(errors)==12 and len(held)==1 and len(rejections)==10
assert sum(c['correct'] is True for c in claims)==1414 and sum(map(len,READ.values()))==28 and len(revisions)==5

def row(s,t):return next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
def response(s,t,req):return next(c for c in row(s,t)['control_sequence'] if c['request_id']==req)
def payload(s,t,msg):return next(c for c in row(s,t)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
def message(s,t,seq):return next(m for m in observations[s,t]['messages'] if m['message']==seq)

assert response(3,27,'request-1')['action']==response(3,27,'request-2')['action']
assert response(3,27,'request-1')['action']['payload'].endswith('\nasksumary')
assert response(3,27,'request-3')['action']['payload'].count('asksumary(')==72
assert response(3,27,'request-4')['action']['payload'].replace('asksumm ary','asksummary')==payload(3,27,1)
assert response(3,27,'request-1')['action']['payload'].split('\nasksumary')[0]==payload(3,27,3).split('\nasksummary')[0]
assert response(3,28,'request-1')['action']['payload'].count('asksummary(availability')==36
assert all(q[0]=='fact' for q in message(3,28,1)['questions'])
assert not message(3,28,2)['questions'] and all(c['type']=='summary' for c in message(3,28,2)['claims'])
assert response(3,28,'request-3')['action']['payload'].split('\nrequest().')[0]==payload(3,28,2)
assert 'request().'+response(3,28,'request-3')['action']['payload'].split('\nrequest().')[1]==payload(3,28,4)
# The same dictionary is returned with an invalid acceptance envelope, then redefined without value changes.
a1=response(6,28,'request-1')['action'];a2=response(6,28,'request-2')['action'];a3=response(6,28,'request-3')['action']
assert a1['language']==a2['language']==a3['language'] and {**a2,'action':'define_language'}==a3
assert response(6,28,'request-6')['action']['payload'].removeprefix('inf().\n')==response(6,28,'request-7')['action']['payload']
assert response(6,28,'request-7')['action']['payload'].replace('askvalid(','aval(').replace('askscore(','ascore(')==payload(6,28,5)
assert response(6,28,'request-9')['action']['payload'].replace('\nreq().','')==payload(6,28,6)
# Five explicit revises are pre-submission; one other counterproposal is a normal send before agreement/submission.
assert [c['action']['action'] for c in row(6,27)['control_sequence'][2:]]==['send','send','send','send','submit','submit']
assert row(6,27)['changed_proposals']==1 and not row(6,27)['revision_events']
assert message(6,27,6)['kinds']==['accept'] and message(6,27,6)['schedule']=={}
assert any(c['type']=='schedule_valid' and c['value']=={'schedule':{'M1':5,'M2':6,'M3':10},'valid':0} and c['correct'] for c in message(6,27,5)['claims'])
assert ['available','A2',5,0] in [c['value'] for c in message(6,27,3)['claims'] if c['type']=='fact']
assert not message(4,27,3)['claims']
assert ['available','B','M1',8,0] in [c['value'] for c in message(4,27,2)['claims'] if c['type']=='summary']
# 3/27 repeats the earlier incorrect preference once; no error has a later correction.
unique_errors={tuple(e['value'][:-1]) for e in errors};assert len(unique_errors)==11 and all((e['stage'],e['trial'],e['type'])==(3,27,'summary') for e in errors)
corrections=[]
for e in errors:
    later=[{'message':m['message'],**c} for m in observations[3,27]['messages'] if m['message']>e['message'] for c in m['claims'] if c['type']=='summary' and c['value'][:-1]==e['value'][:-1]]
    assert all(c['correct'] is False for c in later)
    corrections.append({'message':e['message'],'value':e['value'],'expected':e['expected'],'later_same_key_claims':later,'explicit_correction':False})
assert len(corrections[0]['later_same_key_claims'])==1 and all(not c['later_same_key_claims'] for c in corrections[1:])
# Information expansion, not a new candidate or corrections: six candidate keys repeat in later full summaries.
expansions=[]
for s,t,small,large in [(5,28,2,4),(6,28,5,7)]:
    aa=[c['value'] for c in message(s,t,small)['claims'] if c['type']=='summary'];bb=[c['value'] for c in message(s,t,large)['claims'] if c['type']=='summary']
    assert len(aa)==6 and len(bb)==72 and set(map(tuple,aa))<=set(map(tuple,bb))
    expansions.append({'stage':s,'trial':t,'early_message':small,'later_message':large,'summary_occurrences':78,'unique_keys':72,'repeated_keys':6})

all_schedules=[dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3)]
baseline=[independent(problem,s) for s in all_schedules];assert baseline==[counterfactual(problem,s,{}) for s in all_schedules]
base_valid={i:v['score'] for i,v in enumerate(baseline) if v['valid']};best=max(base_valid.values());optimal=[all_schedules[i] for i,score in base_valid.items() if score==best]
assert len(base_valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
cfs=[]
for e in errors:
    value=e['value'];overrides={tuple(value[:-1]):value[-1]};after=[counterfactual(problem,s,overrides) for s in all_schedules];av={i:v['score'] for i,v in enumerate(after) if v['valid']};ab=max(av.values());ao=[all_schedules[i] for i,v in av.items() if v==ab]
    submitted=row(3,27)['submissions']['A'];before_sub=independent(problem,submitted);after_sub=counterfactual(problem,submitted,overrides)
    effects={'feasible_set_changed':set(av)!=set(base_valid),'schedule_scores_changed':av!=base_valid,'optimal_score_before':best,'optimal_score_after':ab,'optimal_schedules_changed':optimal!=ao,'submitted_schedule_affected':before_sub!=after_sub}
    for k,v in effects.items():assert e['impact'][k]==v
    cfs.append({'message':e['message'],'value':value,'expected':e['expected'],'method':'independent isolated team-summary override','valid_before':len(base_valid),'valid_after':len(av),'optimal_schedules_after':ao,'submitted_before':before_sub,'submitted_after':after_sub,**effects})
combined_overrides={tuple(e['value'][:-1]):e['value'][-1] for e in errors};cv=[counterfactual(problem,s,combined_overrides) for s in all_schedules];valid_cv={i:v['score'] for i,v in enumerate(cv) if v['valid']};cb=max(valid_cv.values());co=[all_schedules[i] for i,v in valid_cv.items() if v==cb]
combined={'stage':3,'trial':27,'method':'all 11 distinct transmitted summary errors applied; not a causal experiment','valid_count':len(valid_cv),'optimal_score':cb,'optimal_schedules':co,'submitted_original':independent(problem,row(3,27)['submissions']['A']),'submitted_counterfactual':counterfactual(problem,row(3,27)['submissions']['A'],combined_overrides),'submitted_is_counterfactual_optimum':row(3,27)['submissions']['A'] in co,'actual_belief_or_cause_inferred':False}
assert combined['submitted_is_counterfactual_optimum'] and cb==21

# Secondary authorized comparison: independent regex extraction from the two raw packets, then direct participant arithmetic.
secondary=json.loads((OUT/'trial07-secondary-source-hashes.json').read_text());src07=Path(secondary['source']);src27=Path(row(3,27)['source'])
assert json.loads((src07.parent/'manifest.json').read_text())['comparison_settings']['problem']==problem
pat=re.compile(r'^team(available|preference)\(B,(M[123]),(\d+),(\d+)\)\.$')
def extract(folder,seq):
    p=next(e['params'] for e in map(json.loads,(folder/'events.jsonl').read_text().splitlines()) if e['method']=='experiment/packet' and e['params']['sequence']==seq)
    return p,{(m.group(1),m.group(2),int(m.group(3))):int(m.group(4)) for line in p['sender_source'].splitlines() if (m:=pat.fullmatch(line))}
p07,x=extract(src07,2);p27,y=extract(src27,4)
def m1(v):return {(ty,slot):value for (ty,meeting,slot),value in v.items() if meeting=='M1'}
assert m1(x)==m1(y) and len(m1(x))==24
assert all(v[(ty,'M1',slot)]==v[(ty,'M2',slot)] for v in [x,y] for ty in ['available','preference'] for slot in range(12))
subset_checks=[]
for n in range(1,4):
    for ppl in itertools.combinations(['B1','B2','B3'],n):
        vals={(ty,slot):int(all(problem['people'][p]['availability'][slot] for p in ppl)) if ty=='available' else sum(problem['people'][p]['preferences'][slot] for p in ppl) for ty in ['available','preference'] for slot in range(12)}
        subset_checks.append({'people':list(ppl),'matching_cells':sum(vals[k]==m1(x)[k] for k in vals),'all_24_match':vals==m1(x)})
assert [c['people'] for c in subset_checks if c['all_24_match']]==[['B1','B2']]
assert [p for m in problem['meetings'] if m['id']=='M1' for p in m['attendees'] if problem['people'][p]['owner']=='B']==['B1']
value_table=[{'type':ty,'slot':sl,'trial07_M1':x[ty,'M1',sl],'trial27_M1':y[ty,'M1',sl],'true_M1_B1':int(problem['people']['B1']['availability'][sl]) if ty=='available' else problem['people']['B1']['preferences'][sl],'B1_plus_B2':int(all(problem['people'][p]['availability'][sl] for p in ['B1','B2'])) if ty=='available' else sum(problem['people'][p]['preferences'][sl] for p in ['B1','B2'])} for ty in ['available','preference'] for sl in range(12)]
pattern={'scope':'secondary value-only comparison; trial07 excluded from current 10-trial counts','sources':[{'trial':7,'message':2,'path':str(src07/'events.jsonl')},{'trial':27,'message':4,'path':str(src27/'events.jsonl')}],'raw_M1_24_values_equal':True,'M1_equals_M2_in_each_packet':True,'actual_M1_B_attendees':['B1'],'matching_subsets':subset_checks,'value_table':value_table,'inferred_internal_reasoning':False}
evidence += ['## 별도 값 비교: stage3 / trial07 m2','','현재 27~28회차 집계에서 제외한 읽기 전용 추가 근거. 원본: `'+str(src07/'events.jsonl')+'`','','```text',p07['sender_source'],'```','']
dump('pattern-comparison-3-07-27.json',pattern)

unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items());secondary_unchanged=hashes(src07)==secondary['hashes']
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged and secondary_unchanged

dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'statuses':{'success':10},'final_score_counts':{'20':9,'19':1},'applied_task_controls':dict(controls),'protocol_rejections':10,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_checks_file':'independent-claim-checks.json','held_score_checks':held,'independent_error_counterfactuals':cfs,'combined_stage3_trial27_errors':combined,'error_unique_keys':11,'error_occurrences':12,'correction_checks':corrections,'question_response_checks':qchecks,'summary_expansions':expansions,'revise_events':revisions,'all_five_revises_before_any_submission':True,'stage6_trial27_counterproposal_via_send_before_agreement_and_submission':True,'stage6_trial28_same_dictionary_redefined':True,'stage3_trial28_person_questions_answered_with_team_summaries':True,'stage3_trial28_removed_questions_sent_later_unchanged':True,'pattern_comparison_file':'pattern-comparison-3-07-27.json','independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},'original_trial_files_unchanged':unchanged,'secondary_trial07_files_unchanged':secondary_unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':28,'task_payloads_total':42,'rejected_full_responses_read':10,'secondary_value_only_read':{'stage':3,'trial':7,'message':2,'not_counted_in_primary_totals':True},'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'claim_types':dict(types),'combined':combined,'subset_matches':subset_checks,'original_unchanged':unchanged,'secondary_unchanged':secondary_unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
