"""Independent enumeration and descriptive process summaries of selected completed records."""
import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import statistics
import math
import hashlib
from record_checks import collection_inputs, output_outside_inputs, unchanged, require, digest


def read(p): return json.loads(p.read_text())
def dist(xs):
    ys=[x for x in xs if type(x) in (int,float) and math.isfinite(x)]
    return {'n':len(ys),'expected_count':len(xs),'missing_count':len(xs)-len(ys),'mean':statistics.mean(ys) if ys else None,'median':statistics.median(ys) if ys else None,'min':min(ys) if ys else None,'max':max(ys) if ys else None}

def enumerate_schedules(p):
    meetings=p['meetings'];ids=[m['id'] for m in meetings]; valid={}
    for choices in itertools.product(range(len(p['slots'])),repeat=len(ids)):
        schedule=dict(zip(ids,choices))
        if any(schedule[a]>=schedule[b] for a,b in p['precedence']):continue
        attendance=[(person,schedule[m['id']]) for m in meetings for person in m['attendees']]
        if len(attendance)!=len(set(attendance)):continue
        if any(not p['people'][who]['availability'][slot] for who,slot in attendance):continue
        valid[choices]=sum(p['people'][who]['preferences'][slot] for who,slot in attendance)
    return ids,valid

def analyze(collection, aggregate, output):
    collection=Path(collection).resolve();base=collection.parent;collection_bytes=collection.read_bytes()
    c,loaded=collection_inputs(collection,with_review=True);output_outside_inputs(output,loaded)
    aggregate=Path(aggregate).resolve();aggregate_path=aggregate/'trial_rows.json';aggregate_bytes=aggregate_path.read_bytes()
    integrity_path=aggregate/'integrity.json';integrity_bytes=integrity_path.read_bytes();integrity=read(integrity_path)
    require(integrity.get('valid') is True and integrity.get('collection_sha256')==hashlib.sha256(collection_bytes).hexdigest(), 'Aggregate is not verified for the selected exact collection')
    require(integrity.get('plan_id')==c['plan_id'], 'Aggregate plan differs')
    require(Counter(r['stage'] for r in integrity['records'])==Counter(range(1,7)), 'Aggregate stage coverage differs')
    checks={r['stage']:r for r in integrity['records']}
    for item in loaded:
        check=checks[item['record']['stage']]
        require(Path(check['source']).resolve()==item['source'] and Path(check['review']).resolve()==item['review'], 'Aggregate selected different source/review')
        require(check['source_files_digest']==digest(item['source_hashes']) and check['review_files_digest']==digest(item['review_hashes']), 'Aggregate selected-review exact hash differs')
    table=read(aggregate_path);require(table['plan_id']==c['plan_id'], 'Trial table plan differs')
    rows=table['rows'];keys=[(r['stage'],r['trial']) for r in rows]
    require(Counter(keys)==Counter((s,n) for s in range(1,7) for n in range(1,31)), 'Trial table must cover each of 6 x 30 slots exactly once')
    indexed=dict(zip(keys,rows))
    stages=[];evidence=[];all_seen=0;first_problem=None
    for item in loaded:
        record=item['record'];source=item['source'];review=item['review'];m=item['manifest'];p=m['comparison_settings']['problem']
        ids,valid=enumerate_schedules(p);best=max(valid.values());best_schedules=[dict(zip(ids,s)) for s,v in valid.items() if v==best]
        if first_problem is None:first_problem={'valid_schedules':len(valid),'optimal_preference_sum':best,'optimal_schedules':best_schedules}
        assert first_problem=={'valid_schedules':len(valid),'optimal_preference_sum':best,'optimal_schedules':best_schedules}
        counters=Counter();trial_indices={};subset=[];errors=[];undetermined=[];first_candidate_transitions=Counter()
        for f in item['trials']:
            result=read(f);o=read(review/f.parent.name/'observation.json');n=result['trial_number'];row=indexed[record['stage'],n];subset.append(row);all_seen+=1
            for field in ['success','status','first_speaker','elapsed_seconds','model_cost_estimate_usd']:
                require(row.get(field)==result.get(field), 'Aggregate/result field mismatch: '+field)
            require(row.get('content_review_status')==o['content_review_status'], 'Aggregate/review status differs')
            submissions=result.get('submissions',{});both=set(submissions)=={'A','B'};same=both and submissions['A']==submissions['B']
            key=tuple(submissions['A'][i] for i in ids) if same else None
            if result['status'] in ('success','failed','stopped'):
                require(result['success']==bool(same and key in valid), 'Confirmed task outcome differs from submissions')
            else:
                require(result.get('success') is not True, 'Operational interruption cannot invent task success')
            if result.get('optimal_score') is not None:require(result['optimal_score']==best,'Recorded optimum differs')
            if result.get('evaluation') is not None:
                assert result['evaluation']['valid']==(key in valid)
                assert result['evaluation']['score']==valid.get(key)
            def mark(label,condition):
                if condition:counters[label]+=1;trial_indices.setdefault(label,[]).append(n)
            complete=o['content_review_status']=='complete'
            mark('delivered_content_review_complete',complete)
            mark('with_confirmed_content_error',complete and o['incorrect_claims']>0)
            mark('with_undetermined_claim',complete and o['undetermined_claims']>0)
            mark('with_outside_schema_or_ambiguous_expression',complete and o['unjudgeable_expressions']>0)
            mark('with_protocol_rejection',result['protocol_errors']>0)
            mark('with_explicit_revision',o.get('explicit_revisions') is not None and o['explicit_revisions']>0)
            mark('with_changed_proposal',complete and o['changed_proposal_messages']>0)
            mark('with_explicit_accept_message',complete and o['accept_messages']>0)
            mark('with_request_or_question',complete and any('request' in r['kinds'] or r['questions'] or r['requests'] for r in o['messages']))
            mark('both_agents_shared_all_own_raw_items',complete and all(s['all_72_own_raw_claims_stated'] is True for s in o['information_sharing'].values()))
            mark('both_agents_shared_some_team_summary',complete and all((s['summary_claims'] or 0)>0 for s in o['information_sharing'].values()))
            mark('no_delivered_task_message',o['task_messages']==0)
            for message in o['messages']:
                for claim in message['claims']:
                    item={'stage':record['stage'],'trial':n,'message':message['message'],'sender':message['sender'],'claim':claim}
                    if claim['correct'] is False:errors.append(item)
                    elif claim['correct'] is None:undetermined.append(item)
            fc=row['first_candidate']
            expected_first=next((x for x in o['messages'] if set(x.get('schedule') or {})==set(ids)),None) if complete else None
            require((fc is None)==(expected_first is None),'Aggregate/review first candidate presence differs')
            if fc is not None:
                for field in ['message','sender','kinds','schedule']:require(fc[field]==expected_first[field], 'Aggregate/review first candidate differs: '+field)
                schedule=fc['schedule'];bounded=all(type(v) is int and 0<=v<len(p['slots']) for v in schedule.values())
                candidate_key=tuple(schedule[i] for i in ids);candidate_valid=bounded and candidate_key in valid
                require(fc['quality']['valid']==candidate_valid and fc['quality']['score']==(valid[candidate_key] if candidate_valid else None), 'First candidate quality differs from independent enumeration')
            initial=('unreviewed' if not complete and o['task_messages'] else 'no_task_message') if not complete else ('missing' if fc is None else ('invalid' if not fc['quality']['valid'] else ('optimal' if fc['quality']['score']==best else 'valid_suboptimal')))
            final='optimal' if result['success'] and valid[key]==best else ('valid_suboptimal' if result['success'] else result['status'])
            first_candidate_transitions[initial+' -> '+final]+=1
            evidence.append({'stage':record['stage'],'trial':n,'first':initial,'final':final,'first_candidate':fc,'submissions':submissions,'explicit_revisions':o['explicit_revisions'],'changed_proposal_messages':o['changed_proposal_messages'],'explicit_accept_messages':o['accept_messages'],'task_kinds':[x['kinds'] for x in o['messages']],'content_review_status':o['content_review_status'],'reviewed_messages':o['reviewed_messages'],'task_messages':o['task_messages'],'protocol_errors':result.get('protocol_error_counts'),'claim_changes':o['claim_changes']})
        by_speaker={who:{'trials':sum(r['first_speaker']==who for r in subset),'model_cost':dist([r['model_cost_estimate_usd'] for r in subset if r['first_speaker']==who]),'elapsed_seconds':dist([r['elapsed_seconds'] for r in subset if r['first_speaker']==who]),'successes':sum(r['success'] is True for r in subset if r['first_speaker']==who)} for who in ('A','B')}
        stages.append({'stage':record['stage'],'n':len(subset),'content_review_counts':dict(Counter(r['content_review_status'] for r in subset)),'counts':dict(counters),'trial_indices':trial_indices,'candidate_transitions':dict(first_candidate_transitions),'by_first_speaker':by_speaker,'all_elapsed_seconds':dist([r['elapsed_seconds'] for r in subset]),'success_elapsed_seconds':dist([r['elapsed_seconds'] for r in subset if r['success']]),'errors':errors,'undetermined':undetermined})
    unchanged(loaded)
    require(collection.read_bytes()==collection_bytes and aggregate_path.read_bytes()==aggregate_bytes and integrity_path.read_bytes()==integrity_bytes, 'Selected inputs changed during analysis')
    out={'plan_id':c['plan_id'],'trials_checked':all_seen,'expected_trials':180,'selected_review_hash_binding_verified':True,'independent_outcome_check_passed':True,'problem':first_problem,'stages':stages,'trial_processes':evidence,'limits':['Same fixed problem repeated; not causal factor isolation.','Full-trial content counts require complete reviews. Errors/undetermined lists preserve claims in reviewed messages even within a pending trial; each trial records its review coverage. Omitted and ambiguous claims are not false.','First candidate is the first complete schedule in the selected message annotations, not necessarily an explicit proposal.','Question and accept markers vary in expressiveness; counts do not prove verification or understanding.','An error-free supported-claim count does not exclude outside-schema, ambiguous, or undetermined expressions.']}
    with Path(output).open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'trials_checked':all_seen,'problem':first_problem},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--collection',required=True);ap.add_argument('--aggregate',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();analyze(a.collection,a.aggregate,a.output)
