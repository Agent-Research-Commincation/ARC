"""Local-only post-run audit of stages2..6, trial23."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text());ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}=={(s,23) for s in range(2,7)}
READ={3:list(range(1,12)),6:[3,4,5]}
NOTES={2:'요약 교환·제안·제출',3:'거절8회; 최초후보20 유지; 추가요약1+1+14+2, A요약66/72키 수신',4:'A개인자료와 B요약 교환·제안·제출',5:'A제출→B wait→A wait→B제출; 새 메시지 없음',6:'종류누락은 추가수정, 잘못된 요약질문은 제거; 제안 유지'}


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
assert totals=={'task_messages':20,'all_phase_messages':22,'correct_claims':714,'incorrect_claims':0,'undetermined_claims':0,'codec_errors':0,'changed_proposals':0,'explicit_revisions':0,'questions':90,'result_actions':44}
controls=collections.Counter();types=collections.Counter();candidates=[];finals=[];claims=[];reading=[];rejections=[];waits=[];qchecks=[];observations={}
evidence=['# 선별 원문','','task14/20개(3단계 전11개·6단계 전3개), 거절10/10개 직접 독해. 나머지 task는 자동대조·정규화 검토.','']
timeline=['# 제어 흐름','','모든 response/applied/rejected 및 제출 상태 대조.','']
table=['# 2~6단계 trial23 관찰표','','최초 전체 후보·최종 모두 유효20점. C/I/U는 내용 주장 발생 수.','',
 '|단계|task|C/I/U|첫 후보|변경/revise|질문|wait|거절|과정|','|---|---:|---|---|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s=r['stage'];source=Path(r['source']);problem=json.loads((source.parent/'manifest.json').read_text())['comparison_settings']['problem']
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    o=json.loads((Path(r['output'])/'observation.json').read_text());observations[s]=o;controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and r['submissions']['A']==r['submissions']['B'] and not r['revision_events']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    finals.append({'stage':s,'trial':23,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert got['valid'] and got['score']==20
        assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidates.append({'stage':s,'trial':23,'message':c['message'],'schedule':c['schedule'],**got})
    for m in o['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c);assert c['correct'] is True;types[c['type']]+=1
            claims.append({'stage':s,'trial':23,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected})
    reading.append({'stage':s,'trial':23,'source':str(source),'task_messages_total':r['task_messages'],'full_task_sender_source_read':READ.get(s,[]),
      'all_normalized_task_messages_reviewed':True,'all_response_control_metadata_reviewed':True,'full_rejected_raw_response_read':[v['request_id'] for v in r['protocol_rejections']],
      'full_additional_control_responses_read':(['request-20','request-21'] if s==3 else (['request-3','request-4','request-5','request-6'] if s==5 else [])),
      'language_dictionary_read':s==6})
    if s in READ:evidence += [f'## stage{s} / trial23','','원본: `'+str(source)+'/events.jsonl`','']
    for seq in READ.get(s,[]):
        p=packets[seq];evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',p['sender_source'],'```','']
    timeline += [f'## stage{s} / trial23','','|request|주체/phase|action|결과|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        act=c['action']['action'] if c['action'] else 'parse-failed';status=c['rejected']['error'] if c['rejected'] else 'applied'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{act}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            nxt=next((v for v in r['control_sequence'][i+1:] if v['actor']==c['actor'] and v['applied']),None)
            rejections.append({'stage':s,'trial':23,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and act=='wait':
            assert s==5 and c['submissions_before']==c['submissions_after']=={'A':{'M1':1,'M2':6,'M3':10}}
            waits.append({'stage':s,'trial':23,**c})
    timeline.append('')
    for qm,am in {3:[(4,5),(6,7),(8,9),(10,11)],5:[(1,2)]}.get(s,[]):
        q=next(m for m in r['messages'] if m['message']==qm)['questions'];answer=next(m for m in o['messages'] if m['message']==am)['claims']
        qkeys={tuple(x) for x in q};akeys={(c['type'],*c['value'][:-1]) for c in answer if c['type']=='summary'};assert qkeys==akeys
        qchecks.append({'stage':s,'trial':23,'question_message':qm,'answer_message':am,'requested_keys':len(qkeys),'answer_keys':len(akeys),'exact_match':True})
    first=r['first_full_candidate'];table.append(f"|{s}|{r['task_messages']}|{r['correct_claims']}/0/0|m{first['message']} 20점|0/0|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[s]}|")
    csvrows.append({'stage':s,'trial':23,'source':str(source),'status':r['status'],'score':r['score'],**{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),'notes':NOTES[s]})

assert controls=={'send':20,'submit':10,'wait':2}
assert len(candidates)==5 and len(claims)==714 and len(rejections)==10 and len(waits)==2
assert sum(map(len,READ.values()))==14
def row(s):return next(r for r in ROWS if r['stage']==s)
def response(s,req):return next(c for c in row(s)['control_sequence'] if c['request_id']==req)
def payload(s,msg):return next(c for c in row(s)['control_sequence'] if msg in c['delivered_messages'])['action']['payload']
# Separate exact repeats, altered but still rejected requests, removed questions, and eventual spelling repair.
assert response(3,'request-1')['action']==response(3,'request-2')['action']
assert response(3,'request-2')['action']['payload'].replace('asksummmary','asksu mmary')==response(3,'request-3')['action']['payload']
assert response(3,'request-3')['action']['payload'].replace('asksu mmary','asks ummary')==response(3,'request-4')['action']['payload']
ainfo=response(3,'request-4')['action']['payload'].split('\nasks ummary')[0].split('\n')[1:]
assert payload(3,1).split('\n')[4:]==ainfo
assert payload(3,1).split('\n')[:4]==['request().','ask(B1).','ask(B2).','ask(B3).']
assert response(3,'request-6')['action']['payload'].replace('availability','available')==response(3,'request-7')['action']['payload']
assert response(3,'request-7')['action']['payload'].split('\naskSummary')[0]==payload(3,2)
assert response(3,'request-11')['action']['payload'].replace('askSummary','asksummary')==payload(3,4)
assert 'info().\n'+response(6,'request-3')['action']['payload']==payload(6,3)
assert response(6,'request-6')['action']['payload'].split('\nasksum')[0]==payload(6,5)
assert not row(3)['wait_events'] and not row(3)['revision_events'] and not row(3)['changed_proposals']
assert [c['action']['action'] for c in row(5)['control_sequence']]==['send','send','submit','wait','wait','submit']
assert not any(c['delivered_messages'] for c in row(5)['control_sequence'][2:])
# A's initial 48 keys are the explicitly available meeting-slots; later 18 keys are distinct additions.
initial=[c['value'] for m in observations[3]['messages'] if m['message']==1 for c in m['claims']]
all_a=[c['value'] for m in observations[3]['messages'] if m['sender']=='A' for c in m['claims'] if c['type']=='summary']
initial_keys={tuple(c[:-1]) for c in initial};all_keys={tuple(c[:-1]) for c in all_a}
assert len(initial)==len(initial_keys)==48 and len(all_a)==len(all_keys)==66 and len(all_keys-initial_keys)==18
all_possible={(typ,'A',m['id'],slot) for m in problem['meetings'] for slot in range(12) for typ in ['available','preference']}
missing=all_possible-all_keys
assert missing=={(typ,'A','M3',slot) for typ in ['available','preference'] for slot in [2,6,7]}
positive_keys={(typ,'A',m['id'],slot) for m in problem['meetings'] for slot in range(12) for typ in ['available','preference']
               if all(problem['people'][p]['availability'][slot] for p in m['attendees'] if problem['people'][p]['owner']=='A')}
assert initial_keys==positive_keys
enumerated=[(s,independent(problem,s)) for s in (dict(zip(['M1','M2','M3'],v)) for v in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']];best=max(v['score'] for s,v in valid);optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,'applied_task_controls':dict(controls),
 'protocol_rejections':10,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidates,'independent_final_checks':finals,'independent_claim_counts':dict(types),'independent_claim_checks_file':'independent-claim-checks.json',
 'question_response_checks':qchecks,'wait_events':waits,'stage3_A_initial_summary_keys':48,'stage3_A_additional_distinct_summary_keys':18,
 'stage3_A_final_distinct_summary_keys':66,'stage3_A_untransmitted_keys':[list(x) for x in sorted(missing)],
 'stage3_A_request1_and2_identical':True,'stage3_B_partial_argument_repair_still_rejected':True,'stage3_B_request11_spelling_repair_delivered':True,
 'stage3_no_candidate_change_revise_wait':True,'stage6_invalid_summary_question_removed':True,'stage5_waits_without_new_peer_packet':True,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claims);dump('rejection-followups.json',rejections)
dump('source-reading-log.json',{'method':'automatic all selected trials plus direct reading of selected originals; not manual exhaustive review','full_task_payloads_read':14,'task_payloads_total':20,'rejected_full_responses_read':10,'rows':reading})
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n');(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n');(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':len(ROWS),'totals':totals,'controls':dict(controls),'independent_claim_counts':dict(types),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
