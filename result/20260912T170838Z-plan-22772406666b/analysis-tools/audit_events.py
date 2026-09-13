"""Read saved usage and exact local packets; no model calls or general codec proof."""
import argparse
import base64
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
from record_checks import read, require, digest, collection_inputs, output_outside_inputs, unchanged


def price(usage, rates):
    if not isinstance(usage,dict):return None
    keys=['inputTokens','cachedInputTokens','outputTokens']
    if not all(k in usage for k in keys):return None
    i,c,o=(usage[k] for k in keys);w=usage.get('cacheWriteInputTokens',0)
    if any(type(x) is not int or x<0 for x in (i,c,o,w)) or c>i or w>i-c:return None
    if any(type(rates.get(k)) not in (int,float) or not math.isfinite(rates[k]) for k in ['input_per_million','cached_input_per_million','output_per_million','cache_write_multiplier']):return None
    return ((i-c)*rates['input_per_million']+c*rates['cached_input_per_million']+w*rates['input_per_million']*(rates['cache_write_multiplier']-1)+o*rates['output_per_million'])/1e6


def complete_cost(usage,rates):
    costs={a:price((usage or {}).get(a),rates) for a in ('A','B')}
    return (sum(costs.values()) if all(v is not None for v in costs.values()) else None),costs


def packet_measurements(packets,language=None):
    body=header=wire=sender=receiver=0;latest=accepted=None;proposer=None;setup=[]
    for p in packets:
        b=base64.b64decode(p['payload_base64'],validate=True);w=base64.b64decode(p['packet_base64'],validate=True)
        require(len(w)>=4,'Truncated packet prefix')
        length=struct.unpack('<I',w[:4])[0]
        require(length+4==p['header_bytes'] and length+4<=len(w),'Actual header prefix mismatch')
        decoded=json.loads(w[4:4+length].decode('utf-8'))
        expected={k:p[k] for k in ['sequence','sender','receiver','stage','phase','payload_length','proposal_revision']}
        require(decoded==expected,'Actual packet header differs from recorded fields')
        require(w[4+length:]==b and len(b)==p['payload_length'],'Actual framed body differs from saved payload')
        body+=len(b);header+=length+4;wire+=len(w)
        if p['phase']=='task':
            require(isinstance(p['sender_source'],str) and isinstance(p['receiver_text'],str),'Missing task text')
            sender+=len(p['sender_source'].encode());receiver+=len(p['receiver_text'].encode())
        elif p['phase']=='language_setup':
            require(p['sender_source'] is None and b.decode('utf-8')==p['receiver_text'],'Setup text was not preserved')
            value=json.loads(b.decode('utf-8'))
            if isinstance(value,list):
                require(all(isinstance(e,dict) and set(e)=={'meaning','symbol'} for e in value),'Invalid dictionary entries')
                latest={e['meaning']:e['symbol'] for e in value};proposer=p['sender']
                require(len(latest)==len(value) and len(set(latest.values()))==len(value),'Repeated dictionary meaning or symbol')
                setup.append({'message':p['sequence'],'kind':'proposal','sender':proposer,'dictionary_hash':digest(latest)})
            else:
                require(isinstance(value,dict) and set(value)=={'accept_dictionary_hash'} and latest is not None,'Ack without dictionary proposal')
                require(p['sender']!=proposer and value['accept_dictionary_hash']==digest(latest),'Dictionary acknowledgement mismatch')
                accepted=dict(latest);setup.append({'message':p['sequence'],'kind':'accept','sender':p['sender'],'dictionary_hash':digest(accepted)})
        else:raise ValueError('Unknown packet phase')
    if language is not None:require(accepted==language,'Final language.json differs from accepted dictionary')
    setup_status=('accepted_and_final_file_matched' if language is not None else ('accepted_packet_without_final_file' if accepted is not None else ('proposal_only' if setup else 'no_setup_packet')))
    return {'body':body,'header':header,'wire':wire,'sender':sender,'receiver':receiver,'language_setup':setup,'language_setup_status':setup_status}


def audit(collection_path, output):
    collection_path=Path(collection_path).resolve();collection_bytes=collection_path.read_bytes()
    c,loaded=collection_inputs(collection_path);output_outside_inputs(output,loaded)
    all_sessions=[];rows=[];files={};last_sum_mismatches=[]
    for item in loaded:
        record=item['record'];source=item['source'];manifest=item['manifest'];rates=manifest['comparison_settings']['config']['pricing']
        for trial in item['trials']:
            result=read(trial);events=[json.loads(l) for l in trial.with_name('events.jsonl').read_text().splitlines()]
            counters=Counter(e['method'] for e in events);tokens={};full_tokens={};sum_last={};first_cache={};session_rows=[]
            for e in events:
                p=e.get('params',{})
                require(e['method']!='model/rerouted', 'Saved model reroute event violates fixed-model condition')
                if e['method'] in ('item/started','item/completed'):
                    require(p.get('item',{}).get('type') not in {'commandExecution','fileChange','mcpToolCall','collabToolCall','webSearch','imageView','dynamicToolCall'}, 'Saved tool event violates isolated-session condition')
                if e['method']=='experiment/session':
                    require(p['model']=='gpt-5.6-luna' and p['reasoningEffort']=='high' and p['instructionSources']==[], 'Unexpected session settings')
                    session_rows.append(p);all_sessions.append(p['thread_id'])
                elif e['method']=='thread/tokenUsage/updated':
                    tid=p['threadId'];u=p['tokenUsage'];tokens[tid]=u['total'];full_tokens[tid]=u
                    first_cache.setdefault(tid,u['total'].get('cachedInputTokens'))
                    sums=sum_last.setdefault(tid,{})
                    for k,v in u.get('last',{}).items():sums[k]=sums.get(k,0)+v
            require(Counter(p['agent'] for p in session_rows)==Counter(result.get('sessions',{}).keys()), 'Session actor coverage mismatch')
            if result.get('operational_status')=='normal':require(set(result['sessions'])=={'A','B'},'Normal trial missing two sessions')
            usage=result.get('usage') or {};partial=result.get('partial_usage') or {}
            for p in session_rows:
                actor=p['agent'];tid=p['thread_id']
                require(result['sessions'][actor]==tid,'Result/session ID mismatch')
                measured=usage.get(actor)
                if measured is not None:
                    require(tid in tokens and measured==tokens[tid], 'Confirmed usage differs from last provider total')
                    if any(sum_last[tid].get(k,0)!=v for k,v in measured.items()):last_sum_mismatches.append({'stage':record['stage'],'trial':result['trial_number'],'actor':actor})
                if partial.get(actor) is not None:require(partial[actor]==full_tokens.get(tid),'Partial usage differs from latest saved provider update')
            packets=[e['params'] for e in events if e['method']=='experiment/packet']
            language=read(trial.with_name('language.json')) if trial.with_name('language.json').exists() else None
            packet=packet_measurements(packets,language)
            require((packet['body'],packet['header'],packet['wire'])==(result['payload_bytes'],result['envelope_bytes'],result['communication_bytes']), 'Communication totals mismatch')
            require(len(packets)==result['message_count'] and counters['experiment/input']==result['actions'] and counters['experiment/rejected']==result['protocol_errors'],'Saved count mismatch')
            for measured,key in [(packet['sender'],'task_sender_text_bytes'),(packet['receiver'],'task_receiver_text_bytes')]:
                if key in result:require(measured==result[key],'Task text total mismatch')
            cost,by_actor=complete_cost(usage,rates)
            recorded=result.get('model_cost_estimate_usd')
            require((cost is None)==(recorded is None),'Complete/unknown model cost scope differs')
            if cost is not None:require(math.isclose(cost,recorded,abs_tol=1e-12,rel_tol=1e-12),'Model cost mismatch')
            known=[v for v in by_actor.values() if v is not None]
            files[str(trial.relative_to(source))+'@'+str(record['stage'])]=hashlib.sha256(trial.read_bytes()).hexdigest()
            rows.append({'stage':record['stage'],'trial':result['trial_number'],'status':result['status'],'operational_status':result.get('operational_status'),'wire_bytes':packet['wire'],'body_bytes':packet['body'],'header_bytes':packet['header'],'packets':len(packets),'task_packets':sum(p['phase']=='task' for p in packets),'language_setup':packet['language_setup'],'language_setup_status':packet['language_setup_status'],'requests':counters['experiment/input'],'usage_updates':counters['thread/tokenUsage/updated'],'sessions':len(session_rows),'first_observed_usage_cached_sessions':sum(bool(v) for v in first_cache.values()),'event_model_cost':cost,'confirmed_cost_by_actor':by_actor,'known_partial_confirmed_cost':sum(known) if known else None,'confirmed_usage_by_actor':usage,'partial_usage_by_actor':partial,'latest_provider_usage_by_session':full_tokens})
    require(len(all_sessions)==len(set(all_sessions)),'Repeated session identifiers')
    unchanged(loaded);require(collection_bytes==collection_path.read_bytes(),'Collection changed during audit')
    report={'verified':True,'plan_id':c['plan_id'],'trials':len(rows),'expected_trials':180,'expected_sessions':360,'unique_sessions':len(all_sessions),'session_count_complete':len(all_sessions)==360,'rows':rows,'result_hashes':files,'last_usage_sum_mismatches':last_sum_mismatches,'model_calls_by_auditor':0,'model_reroute_events':0,'forbidden_tool_item_events':0,'scope':'Saved provider totals, session configuration and actual local packet header/body bytes, including dictionary proposal/ack/final-file binding. Partial usage is preserved and never promoted to a complete two-agent cost. No model calls, natural-language annotation, general codec proof or causal inference. Summed last updates are diagnostic only; provider updates may repeat.'}
    with Path(output).open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','result_hashes')},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection',required=True);p.add_argument('--output',required=True);a=p.parse_args();audit(a.collection,a.output)
