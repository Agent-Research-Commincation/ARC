"""Local post-run verification and evidence files for 2..6, trials 15..17 only."""
import collections
import csv
import hashlib
import itertools
import json
import re
from pathlib import Path

OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'audit-index.json').read_text())
ROWS=D['rows']
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/D['plan_id']
assert {(r['stage'],r['trial']) for r in ROWS}==set(itertools.product(range(2,7),range(15,18)))
READ={(2,16):[3],(5,15):[3],(3,15):[2,3,4,5,6],(3,16):[2,3,4],(3,17):[1,2,3,4],
      (4,16):[2,3,4],(6,15):[3,4],(6,16):[5,6],(6,17):[5,6]}
NOTES={(2,15):'제안·수락 후 양쪽 제출',(2,16):'B 제출→A wait→B accept→A 제출',
       (2,17):'제안 뒤 양쪽 제출',(3,15):'요약질문 오타 4회 거절→개인자료 10개→72개 요청·응답',
       (3,16):'질문 타입 수정; B 가용 슬롯의 A 요약 54개 수신',
       (3,17):'종류 중복·질문 타입·비ASCII 술어 3회 거절 후 수정',
       (4,15):'요약 72개 질문·응답 후 수락',(4,16):'후보 슬롯 요약 6개→전체 72개 추가 요청·응답',
       (4,17):'제안 뒤 양쪽 제출',(5,15):'A 제출→B wait→A accept→B 제출',
       (5,16):'개인자료 수신·제안 수락',(5,17):'요약 72개 질문·응답 및 제안',
       (6,15):'accept_language 사전 필드 제거; 질문 타입 수정',
       (6,16):'기본 술어를 합의 기호로 수정; 유효성·점수 확인',
       (6,17):'기본 술어를 합의 기호로 수정; 유효성·점수 확인'}

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def hashes(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}

def independent(problem,schedule):
    meetings={m['id']:m['attendees'] for m in problem['meetings']}
    assert set(schedule)==set(meetings)
    valid=all(problem['people'][p]['availability'][schedule[m]] for m,ps in meetings.items() for p in ps)
    valid=valid and all(schedule[a]<schedule[b] for a,b in problem['precedence'])
    valid=valid and all(schedule[a]!=schedule[b] or not(set(meetings[a])&set(meetings[b]))
                        for a,b in itertools.combinations(meetings,2))
    total=sum(problem['people'][p]['preferences'][schedule[m]] for m,ps in meetings.items() for p in ps)
    return {'valid':valid,'score':total if valid else None,'arithmetic_sum':total}

def claim_expected(problem,claim):
    t,v=claim['type'],claim['value']
    if t=='fact':
        typ,person,slot,value=v
        expected=int(problem['people'][person]['availability'][slot]) if typ=='available' else problem['people'][person]['preferences'][slot]
    elif t=='summary':
        typ,team,meeting,slot,value=v
        people=[p for m in problem['meetings'] if m['id']==meeting for p in m['attendees'] if problem['people'][p]['owner']==team]
        expected=int(all(problem['people'][p]['availability'][slot] for p in people)) if typ=='available' else sum(problem['people'][p]['preferences'][slot] for p in people)
    elif t in ['schedule_score','schedule_valid']:
        field='score' if t=='schedule_score' else 'valid'
        value=v[field];expected=independent(problem,v['schedule'])[field]
        if field=='valid':expected=int(expected)
    else:
        raise AssertionError(t)
    assert value==expected==claim['expected'] and claim['correct'] is True
    return expected

totals={k:sum(r[k] for r in ROWS) for k in ['task_messages','all_phase_messages','correct_claims','incorrect_claims',
        'undetermined_claims','codec_errors','changed_proposals','explicit_revisions','questions','result_actions']}
assert totals=={'task_messages':49,'all_phase_messages':55,'correct_claims':2163,'incorrect_claims':0,
                'undetermined_claims':0,'codec_errors':0,'changed_proposals':0,'explicit_revisions':0,
                'questions':572,'result_actions':99}
controls=collections.Counter();claimtypes=collections.Counter()
candidatechecks=[];finalchecks=[];claimchecks=[];reading=[];rejections=[];followchecks=[];waitchecks=[]
evidence=['# 선별 원문', '', 'Task 원문 23/49개, 거절 응답 12/12개 직접 독해. 원본 경로와 메시지 번호를 아래에 보존한다.','']
timeline=['# 제어 흐름', '', 'response/applied/rejected와 제출 상태를 전체 재구성했다.','']
table=['# 2~6단계 trial15~17 관찰표','','모두 최종 유효·20점. C/I/U는 내용 주장 정답/오류/보류 발생 수다.','',
       '|단계/회차|task 메시지|C/I/U|첫 전체 후보|변경/revise|질문|wait|거절|과정|',
       '|---|---:|---|---|---:|---:|---:|---:|---|']
csvrows=[]
for r in ROWS:
    s,t=r['stage'],r['trial'];key=(s,t);source=Path(r['source'])
    manifest=json.loads((source.parent/'manifest.json').read_text());problem=manifest['comparison_settings']['problem']
    result=json.loads((source/'result.json').read_text())
    events=list(map(json.loads,(source/'events.jsonl').read_text().splitlines()))
    packets={e['params']['sequence']:e['params'] for e in events if e['method']=='experiment/packet'}
    observed=json.loads((Path(r['output'])/'observation.json').read_text())
    controls.update(r['applied_task_controls'])
    assert r['status']=='success' and r['quality_gap']==0 and not r['revision_events']
    assert r['submissions']['A']==r['submissions']['B']
    final=independent(problem,r['submissions']['A']);assert final['valid'] and final['score']==20
    finalchecks.append({'stage':s,'trial':t,'schedule':r['submissions']['A'],**final})
    for c in r['full_candidates']:
        got=independent(problem,c['schedule']);assert got['valid'] and got['score']==20
        assert (got['valid'],got['score'])==(c['evaluation']['valid'],c['evaluation']['score'])
        candidatechecks.append({'stage':s,'trial':t,'message':c['message'],**got})
    for m in observed['messages']:
        assert m['codec_preserved'] is True and m['framing_preserved'] is True and not m['decode_error']
        for c in m['claims']:
            expected=claim_expected(problem,c);claimtypes[c['type']]+=1
            claimchecks.append({'stage':s,'trial':t,'message':m['message'],'type':c['type'],'value':c['value'],'expected':expected})
    selected=READ.get(key,[])
    reading.append({'stage':s,'trial':t,'source':str(source),'task_messages_total':r['task_messages'],
                    'full_task_sender_source_read':selected,'all_normalized_task_messages_reviewed':True,
                    'all_response_control_metadata_reviewed':True,'full_rejected_raw_response_read':[x['request_id'] for x in r['protocol_rejections']],
                    'full_success_control_responses_read':['request-3','request-4','request-5','request-6'] if key in [(2,16),(5,15)] else (['request-3'] if key==(6,15) else []),
                    'language_dictionary_read':s==6})
    if selected or r['protocol_rejections']:
        evidence += [f'## stage {s} / trial {t:02d}','',f'원본: `{source}/events.jsonl`','']
    for seq in selected:
        p=packets[seq];payload=p['sender_source']
        evidence += [f"### m{seq} {p['sender']} ({p['request_id']})",'','```text',payload if isinstance(payload,str) else json.dumps(payload,ensure_ascii=False),'```','']
    timeline += [f'## stage {s} / trial {t:02d}','','|request|주체/phase|action|적용/거절|m|제출 상태 전→후|','|---|---|---|---|---|---|']
    for i,c in enumerate(r['control_sequence']):
        status=c['rejected']['error'] if c['rejected'] else 'applied'
        action=c['action']['action'] if c['action'] else 'parse-failed'
        timeline.append(f"|{c['request_id']}|{c['actor']}/{c['phase']}|{action}|{status}|{c['delivered_messages']}|{sorted(c['submissions_before'])}→{sorted(c['submissions_after'])}|")
        if c['rejected']:
            following=r['control_sequence'][i+1:]
            nxt=next((v for v in following if v['applied'] and v['actor']==c['actor']),None)
            rejections.append({'stage':s,'trial':t,'request_id':c['request_id'],'actor':c['actor'],'phase':c['phase'],
                               'error':status,'raw_response':c['raw_response'],'next_same_actor_applied':nxt})
            evidence += [f"### 거절 {c['request_id']}: {status}",'','```json',c['raw_response'],'```','']
        if c['applied'] and action=='wait':
            assert len(c['submissions_before'])==1 and c['submissions_before']==c['submissions_after']
            following=r['control_sequence'][i+1:];accept,submit=following
            assert accept['applied']['action']=='send' and submit['applied']['action']=='submit'
            assert accept['submissions_before']==accept['submissions_after']==c['submissions_after']
            peer=r['messages'][-1];assert peer['kind']=='accept' and peer['schedule']==r['submissions']['A']
            assert accept['actor'] in c['submissions_before'] and submit['actor']==c['actor']
            waitchecks.append({'stage':s,'trial':t,'wait':c,'next_accept':accept,'next_submit':submit,'prior_submission_preserved':True})
    timeline.append('')
    for reqmsg,ansmsg,ctype in ({(3,15):[(3,4,'fact'),(5,6,'fact')],(3,16):[(3,4,'summary')],(3,17):[(3,4,'summary')],
                                (4,16):[(3,4,'summary')],(6,15):[(3,4,'summary')]}.get(key,[])):
        q=next(m for m in r['messages'] if m['message']==reqmsg)['questions']
        answers=next(m for m in observed['messages'] if m['message']==ansmsg)['claims']
        qkeys={tuple(x[1:]) for x in q if x[0]==ctype}
        akeys={tuple(c['value'][:-1]) for c in answers if c['type']==ctype}
        assert qkeys==akeys
        followchecks.append({'stage':s,'trial':t,'question_message':reqmsg,'answer_message':ansmsg,'type':ctype,'requested_keys':len(qkeys),'answer_keys_exact_match':True})
    first=r['first_full_candidate'];schedule=','.join(str(first['schedule'][m]) for m in ['M1','M2','M3'])
    firstlabel=f"m{first['message']} {first['sender']} ({schedule}) 20"
    table.append(f"|{s}/{t:02d}|{r['task_messages']}|{r['correct_claims']}/0/0|{firstlabel}|0/0|{r['questions']}|{len(r['wait_events'])}|{len(r['protocol_rejections'])}|{NOTES[key]}|")
    csvrows.append({'stage':s,'trial':t,'source':str(source),'status':r['status'],'score':r['score'],
                    **{k:r[k] for k in totals},'waits':len(r['wait_events']),'rejections':len(r['protocol_rejections']),
                    'first_candidate':firstlabel,'notes':NOTES[key]})

assert controls=={'send':49,'submit':30,'wait':2}
assert len(rejections)==12 and len(waitchecks)==2 and len(candidatechecks)==22 and len(claimchecks)==2163
assert sum(map(len,READ.values()))==23
# Verify exact edits in rejected payloads, independently of the protocol parser.
repairs=[]
for s,t,req,newmsg,substitutions in [(3,16,'request-3',3,{'availability':'available'}),
 (3,17,'request-4',3,{'availability':'available'}),(6,15,'request-4',3,{'availability':'available'}),
 (6,16,'request-5',5,{'askvalid':'aval','askscore':'ascore'}),(6,17,'request-5',5,{'askvalid':'aval','askscore':'ascore'})]:
    r=next(r for r in ROWS if (r['stage'],r['trial'])==(s,t))
    old=next(c for c in r['control_sequence'] if c['request_id']==req)['action']['payload']
    replacement=old
    for a,b in substitutions.items():replacement=replacement.replace(a,b)
    new=next(c for c in r['control_sequence'] if newmsg in c['delivered_messages'])['action']['payload']
    assert replacement==new
    repairs.append({'stage':s,'trial':t,'rejected_request':req,'applied_message':newmsg,'substitutions':substitutions,'only_these_changes':True})
r=next(r for r in ROWS if (r['stage'],r['trial'])==(3,17))
old=next(c for c in r['control_sequence'] if c['request_id']=='request-6')['action']['payload']
new=next(c for c in r['control_sequence'] if 4 in c['delivered_messages'])['action']['payload']
tokens=sorted(set(re.findall(r'te[^\n(]*available(?=\()',old)))
assert re.sub(r'te[^\n(]*available(?=\()','teamavailable',old)==new
repairs.append({'stage':3,'trial':17,'rejected_request':'request-6','applied_message':4,
                'old_tokens':tokens,'old_tokens_codepoints':[[f'U+{ord(ch):04X}' for ch in token] for token in tokens],
                'new_token':'teamavailable','numeric_payload_unchanged':True})
r=next(r for r in ROWS if (r['stage'],r['trial'])==(3,16))
questions=next(m for m in r['messages'] if m['message']==3)['questions']
expectedq={(typ,'A',m['id'],slot) for m in problem['meetings'] for slot in range(12) for typ in ['available','preference']
           if all(problem['people'][p]['availability'][slot] for p in m['attendees'] if problem['people'][p]['owner']=='B')}
assert {tuple(q[1:]) for q in questions}==expectedq and len(expectedq)==54
enumerated=[(sch,independent(problem,sch)) for sch in
            (dict(zip(['M1','M2','M3'],x)) for x in itertools.product(range(12),repeat=3))]
valid=[(s,v) for s,v in enumerated if v['valid']];best=max(v['score'] for s,v in valid)
optimal=[s for s,v in valid if v['score']==best]
assert len(valid)==54 and best==20 and optimal==[{'M1':1,'M2':6,'M3':10}]
unchanged=all(hashes(Path(p))==h for p,h in D['protected_trial_hashes'].items())
code_unchanged=all({str(p.relative_to(BASE/f'stage-{s}')):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==D['evaluator_source_hashes'] for s in range(2,7))
assert unchanged and code_unchanged
dump('verification.json',{'scope':D['scope'],'review_policy_version':D['review_policy_version'],'totals':totals,
 'applied_task_controls':dict(controls),'protocol_rejections':12,'rejections_by_phase':dict(collections.Counter(x['phase'] for x in rejections)),
 'independent_candidate_checks':candidatechecks,'independent_final_checks':finalchecks,'independent_claim_counts':dict(claimtypes),
 'independent_claim_checks_file':'independent-claim-checks.json','question_response_checks':followchecks,
 'stage3_trial16_questions_exactly_B_available_slots':True,'payload_repair_checks':repairs,'wait_followups':waitchecks,
 'independent_enumeration':{'assignments':1728,'valid':54,'optimal_score':20,'optimal_schedules':optimal},
 'original_trial_files_unchanged':unchanged,'execution_source_unchanged':code_unchanged,'all_stage_evaluator_sources_equal':True,'experiment_model_calls':0})
dump('independent-claim-checks.json',claimchecks)
dump('source-reading-log.json',{'method':'automatic all selected trials plus selective direct raw reading; not manual exhaustive review',
     'full_task_payloads_read':23,'task_payloads_total':49,'rejected_full_responses_read':12,'rows':reading})
dump('rejection-followups.json',rejections)
(OUT/'observation-table.md').write_text('\n'.join(table)+'\n')
(OUT/'selected-source-evidence.md').write_text('\n'.join(evidence)+'\n')
(OUT/'control-timeline.md').write_text('\n'.join(timeline)+'\n')
with (OUT/'observation-table.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
print(json.dumps({'trials':15,'totals':totals,'controls':dict(controls),'independent_claims':len(claimchecks),
                  'candidate_checks':len(candidatechecks),'original_unchanged':unchanged,'source_unchanged':code_unchanged},ensure_ascii=False))
