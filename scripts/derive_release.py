"""Analyze the selected 30 original trials and v3.1 reviews, without rerunning models.
Only this analysis directory is written. Run/codec/evaluation modules are not imported.
"""
import base64
import hashlib
import itertools
import json
import math
import statistics
import struct
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

import argparse
import os
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay_review import restrict_io

parser=argparse.ArgumentParser(description='Recompute the frozen 30-trial analysis from a portable release; no models.')
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args=parser.parse_args()
ROOT=args.root.resolve()
HERE=args.output.resolve()
if HERE.exists():
    raise ValueError('Choose a new analysis output directory')
HERE.mkdir(parents=True)
sys.dont_write_bytecode=True
restrict_io([ROOT, Path(__file__).parent], HERE)
PLAN='20260911T092336Z-plan-cfd3ab2b1222'
SELECTED=ROOT/'results/readable'/(PLAN+'-review-v3-1')
collection=json.loads((SELECTED/'collection.json').read_text())

def portable(path):return Path(path).relative_to(ROOT).as_posix()
def link(path):return Path(os.path.relpath(path, HERE)).as_posix()

def read(p):return json.loads(p.read_text())
def save(name,value):(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}
def seal(folder):
    actual=hashes(folder);actual.pop('seal.json')
    assert actual==read(folder/'seal.json')['files'],folder

def stats(values):
    assert all(v is not None for v in values)
    return {'count':len(values),'sum':sum(values),'mean':statistics.mean(values),'median':statistics.median(values),'min':min(values),'max':max(values)} if values else None

def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9),(a,b)

def independent_schedule(problem,s):
    if set(s)!={'M1','M2','M3'}:return {'valid':False,'score':None}
    meetings=problem['meetings']
    possible=all(problem['people'][p]['availability'][s[m['id']]] for m in meetings for p in m['attendees'])
    possible &= all(s[a]<s[b] for a,b in problem['precedence'])
    possible &= all(s[a['id']]!=s[b['id']] or not set(a['attendees'])&set(b['attendees']) for a,b in itertools.combinations(meetings,2))
    raw=sum(problem['people'][p]['preferences'][s[m['id']]] for m in meetings for p in m['attendees'])
    return {'valid':possible,'score':raw if possible else None,'arithmetic_sum':raw}

def cost(usage,pricing,no_cache_discount=False):
    inp,cache,out=(usage[k] for k in ('inputTokens','cachedInputTokens','outputTokens'))
    writes=usage.get('cacheWriteInputTokens',0)
    return ((inp-cache)*pricing['input_per_million']+cache*(pricing['input_per_million'] if no_cache_discount else pricing['cached_input_per_million'])+writes*pricing['input_per_million']*(pricing['cache_write_multiplier']-1)+out*pricing['output_per_million'])/1e6

summaries=[];trials=[];evidence=[];input_hashes={};settings=[]
for record in collection['records']:
    source=ROOT/record['source'];review=ROOT/record['review'];stage=record['stage']
    seal(source);seal(review);seal(ROOT/record['readable'])
    manifest=read(source/'manifest.json');rm=read(review/'manifest.json')
    assert rm['source_files']==hashes(source)
    assert rm['review_policy_version']=='observation-review-v3.1'
    settings.append(manifest['comparison_settings'])
    problem=manifest['comparison_settings']['problem'];pricing=manifest['comparison_settings']['config']['pricing']
    feasible={slots:independent_schedule(problem,dict(zip(('M1','M2','M3'),slots))) for slots in itertools.product(range(12),repeat=3)}
    feasible={s:q['score'] for s,q in feasible.items() if q['valid']}
    assert len(feasible)==54 and max(feasible.values())==20
    local=[]
    for number in range(1,6):
        folder=source/('trial-%02d'%number)
        r=read(folder/'result.json');obs=read(review/folder.name/'observation.json')
        ev=[json.loads(l) for l in (folder/'events.jsonl').read_text().splitlines()]
        for p in (folder/'result.json',folder/'events.jsonl',review/folder.name/'observation.json',source/'manifest.json',review/'manifest.json'):
            input_hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        packets=[e['params'] for e in ev if e['method']=='experiment/packet'];task=[p for p in packets if p['phase']=='task']
        for p in packets:
            payload=base64.b64decode(p['payload_base64'],validate=True);framed=base64.b64decode(p['packet_base64'],validate=True)
            headerlen=struct.unpack('<I',framed[:4])[0]
            assert len(payload)==p['payload_length'] and headerlen+4==p['header_bytes']
            assert framed[headerlen+4:]==payload
        for key,values in [('payload_bytes',[p['payload_length'] for p in packets]),('envelope_bytes',[p['header_bytes'] for p in packets]),('communication_bytes',[p['payload_length']+p['header_bytes'] for p in packets]),('task_sender_text_bytes',[len(p['sender_source'].encode()) for p in task]),('task_receiver_text_bytes',[len(p['receiver_text'].encode()) for p in task])]:assert r[key]==sum(values)
        rejected=[e for e in ev if e['method']=='experiment/rejected']
        inputs=[e for e in ev if e['method']=='experiment/input']
        responses={e['params']['request_id']:e for e in ev if e['method']=='experiment/response_received'}
        outcomes={e['params']['request_id']:('rejected' if e['method']=='experiment/rejected' else e['params']['action']) for e in ev if e['method'] in ('experiment/rejected','experiment/applied')}
        assert len(inputs)==len(responses)==r['actions']
        assert len(rejected)==r['protocol_errors']
        usage_final={};usage_by_turn={};first_cache={}
        for e in ev:
            if e['method']=='thread/tokenUsage/updated':
                p=e['params'];usage_final[p['threadId']]=p['tokenUsage']['total'];usage_by_turn[p['turnId']]=p['tokenUsage']['total']
                first_cache.setdefault(p['threadId'],p['tokenUsage']['last']['cachedInputTokens'])
        for actor,tid in r['sessions'].items():assert usage_final[tid]==r['usage'][actor]
        keys=['inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens','cacheWriteInputTokens']
        usage={k:sum(r['usage'][a].get(k,0) for a in ('A','B')) for k in keys}
        close(cost(usage,pricing),r['model_cost_estimate_usd'])
        per_request=[];previous={a:{k:0 for k in keys} for a in ('A','B')}
        for e in inputs:
            q=e['params'];response=responses[q['request_id']];total=usage_by_turn[response['params']['turn_id']]
            delta={k:total.get(k,0)-previous[q['actor']].get(k,0) for k in keys};previous[q['actor']]=total
            assert all(v>=0 for v in delta.values())
            per_request.append({'request_id':q['request_id'],'actor':q['actor'],'phase':q['phase'],
                'outcome':outcomes[q['request_id']],'elapsed_input_to_response_seconds':(datetime.fromisoformat(response['recorded_at'])-datetime.fromisoformat(e['recorded_at'])).total_seconds(),
                'model_cost_estimate_usd':cost(delta,pricing),'usage_delta':delta})
        close(sum(x['model_cost_estimate_usd'] for x in per_request),r['model_cost_estimate_usd'])
        own=independent_schedule(problem,r['submissions']['A'])
        assert r['submissions']['A']==r['submissions']['B'] and own['valid']==r['success']
        assert own['score']==r['evaluation']['score']
        assert obs['content_review_status']=='complete' and obs['codec_errors']==0
        claims=[c for m in obs['messages'] for c in m['claims']]
        row={'stage':stage,'trial':number,'status':r['status'],'success':r['success'],'score':own['score'],
            'optimal':r['success'] and own['score']==20,'quality_gap':r['quality_gap'],'first_speaker':r['first_speaker'],
            **{k:r[k] for k in ['elapsed_seconds','actions','protocol_errors','language_setup_seconds','model_cost_estimate_usd','total_cost_estimate_usd','communication_processing_cost_estimate_usd','communication_bytes','payload_bytes','envelope_bytes','protocol_cpu_seconds','task_sender_text_bytes','task_receiver_text_bytes']},
            'model_cost_reweighted_without_cache_discount_usd':cost(usage,pricing,True),
            'input_to_response_seconds':sum(x['elapsed_input_to_response_seconds'] for x in per_request),
            'rejected_request_seconds':sum(x['elapsed_input_to_response_seconds'] for x in per_request if x['outcome']=='rejected'),
            'rejected_request_model_cost_usd':sum(x['model_cost_estimate_usd'] for x in per_request if x['outcome']=='rejected'),
            'usage':usage,'first_calls_with_cache':sum(v>0 for v in first_cache.values()),
            'task_messages':len(task),'setup_messages':len(packets)-len(task),
            'task_payload_sizes':[p['payload_length'] for p in task],
            'explicit_revisions':obs['explicit_revisions'],'claim_occurrences':len(claims),
            'correct_claims':sum(c['correct'] is True for c in claims),'incorrect_claims':sum(c['correct'] is False for c in claims),
            'undetermined_claims':sum(c['correct'] is None for c in claims),'unjudgeable_expressions':obs['unjudgeable_expressions'],
            'content_error_messages':sum(any(c['correct'] is False for c in m['claims']) for m in obs['messages']),
            'unique_claims':obs['unique_claims'],'claim_changes':len(obs['claim_changes']),
            'information_sharing':obs['information_sharing'],
            'explicit_recheck_ids':sum(len(m['references']) for m in obs['messages']),
            'per_request':per_request,'source':portable(folder),'review':portable(review/folder.name),
            'transcript':str(Path(record['readable'])/folder.name/'transcript.md')}
        local.append(row);trials.append(row)
        # Auditable full sent messages and controller events. No hidden reasoning is exported here.
        if (stage,number) in [(1,3),(2,2),(3,4),(4,2),(4,5),(5,4),(6,3),(6,4),(6,5)]:
            eventrows=[{'source_line':lineno,'recorded_at':e['recorded_at'],'method':e['method'],'params':e['params']} for lineno,e in enumerate(ev,1) if e['method'] in ('experiment/packet','experiment/action','experiment/rejected','experiment/applied','experiment/submissions_invalidated')]
            evidence.append({'stage':stage,'trial':number,'source_events':portable(folder/'events.jsonl'),'events':eventrows,
                'messages':obs['messages'],'result':{k:row[k] for k in ('success','score','quality_gap','protocol_errors','elapsed_seconds','rejected_request_seconds','rejected_request_model_cost_usd')},
                'language':read(folder/'language.json') if (folder/'language.json').exists() else None})
    count=sum(t['success'] for t in local)
    metric_keys=['elapsed_seconds','actions','task_messages','setup_messages','communication_bytes','payload_bytes','envelope_bytes','protocol_cpu_seconds','task_sender_text_bytes','task_receiver_text_bytes','model_cost_estimate_usd','language_setup_seconds']
    summary={'stage':stage,'label':record['label'],'slug':record['slug'],'run_id':record['run_id'],
        'source':record['source'],'review':record['review'],'readable':record['readable'],
        'trials':len(local),'success_count':count,'optimal_count':sum(t['optimal'] for t in local),
        'scores_in_trial_order':[t['score'] for t in local],'quality_gap_successes':stats([t['quality_gap'] for t in local if t['success']]),
        'termination_seconds_all':stats([t['elapsed_seconds'] for t in local]),
        'completion_seconds_successes':stats([t['elapsed_seconds'] for t in local if t['success']]),
        'model_cost_per_success_usd':sum(t['model_cost_estimate_usd'] for t in local)/count,
        'model_cost_per_success_without_cache_discount_usd':sum(t['model_cost_reweighted_without_cache_discount_usd'] for t in local)/count,
        'total_cost_per_success_usd':None,'communication_processing_cost_usd':None,
        'usage':{k:stats([t['usage'][k] for t in local]) for k in keys},
        'stats':{k:stats([t[k] for t in local]) for k in metric_keys},
        **{k:sum(t[k] for t in local) for k in ('protocol_errors','first_calls_with_cache','explicit_revisions','claim_occurrences','correct_claims','incorrect_claims','undetermined_claims','unjudgeable_expressions','content_error_messages','explicit_recheck_ids')},
        'content_error_trials':[t['trial'] for t in local if t['incorrect_claims']],
        'summary_sent_trials':[t['trial'] for t in local if any(x['summary_claims'] for x in t['information_sharing'].values())],
        'raw_sent_trials':[t['trial'] for t in local if any(x['unique_own_raw_claims'] for x in t['information_sharing'].values())],
        'first_cache_sessions':sum(t['first_calls_with_cache'] for t in local)}
    summaries.append(summary)
assert all(s==settings[0] for s in settings)
assert sum(s['success_count'] for s in summaries)==29 and sum(s['optimal_count'] for s in summaries)==28
assert sum(s['stats']['actions']['sum'] for s in summaries)==225
assert sum(s['stats']['task_messages']['sum']+s['stats']['setup_messages']['sum'] for s in summaries)==128
assert sum(s['incorrect_claims'] for s in summaries)==47 and sum(s['undetermined_claims'] for s in summaries)==8
result={'generated_at':datetime.now(timezone.utc).isoformat(),'plan_id':PLAN,'review_policy_version':'observation-review-v3.1',
    'selected_collection':portable(SELECTED/'collection.json'),'settings':settings[0],
    'analysis_scope':'Existing run observations; no new model execution or causal isolation.',
    'request_count_scope':'actions counts runner turns, not provider calls or HTTP requests.',
    'total_cost_status':'Unmeasured; model-only API-equivalent estimates are partial costs.',
    'token_scope':'Input includes cache; reasoning is included in output. Token counts are accumulated over all requests.',
    'request_elapsed_scope':'Runner input record to response_received; includes service/inference wait, not isolated communication processing.',
    'cache_reweighting_scope':'Same observed tokens at a different arithmetic weight, not a prediction of uncached execution.',
    'stages':summaries,'source_files':input_hashes}
save('comparison.json',result);save('trials.json',trials);save('case-evidence.json',evidence)

# Human-readable numeric tables generated from the same unrounded aggregate.
def table(headers,rows):return ['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows]
def lab(s):return '[%d %s](%s/README.md)'%(s['stage'],s['label'],link(ROOT/s['readable']))
lines=['# 여섯 방식 비교표 · 사후 검수 v3.1','','같은 문제·Luna high·방식별5회·병렬 jobs=6. 아래는 기존30회 원본의 관측값이며 실험을 재실행하지 않았다.','',
    '[종합 인사이트](../../../docs/experiment-insights-v3-1.md) · [계산 원자료](comparison.json) · [30회별 계산](trials.json) · [재현 코드](derive.py)','',
    '## 성공·품질과 비용','','성공은 동일한 유효 일정의 공동 제출이다. 최적 점수20 도달은 별도다. 성공당 모델 비용은 실패·사전 합의·거절된 요청까지 포함한5회 전체 모델 비용 ÷ 성공 수다.','']
lines+=table(['방식','성공 / 5','최적 / 5','회차별 점수','성공한 회차 평균 최적 차이','모델 비용 합계 USD','성공당 모델 비용 USD','성공당 총비용'],[
    [lab(s),s['success_count'],s['optimal_count'],', '.join('무효' if x is None else str(x) for x in s['scores_in_trial_order']),f"{s['quality_gap_successes']['mean']:.2f}",f"{s['stats']['model_cost_estimate_usd']['sum']:.6f}",f"{s['model_cost_per_success_usd']:.6f}",'미측정'] for s in summaries])
lines+=['','단가는 실행 manifest에 고정된 입력 $0.20·캐시 입력 $0.02·출력 $1.20/백만 토큰을 재사용했다. 현재 가격을 새로 조회한 결과나 실제 구독 청구액이 아니다. 통신 처리 금액과 성공당 총비용은 모든 방식에서 미측정이다.','',
    '## 시간 분포','','회차 시간은 초기화부터 결과 기록까지의 원래 측정 경계다. 요청 전체1137.20초에는 worktree 준비·조정기 대기·취합도 포함되며 아래 회차 시간의 합과 다르다.','']
lines+=table(['방식','전체5회 평균 초','전체5회 중앙값 초','범위 초','성공 회차 평균 초','실행기 요청/턴 수','형식·행동 거절'],[
    [lab(s),f"{s['termination_seconds_all']['mean']:.2f}",f"{s['termination_seconds_all']['median']:.2f}",f"{s['termination_seconds_all']['min']:.2f}–{s['termination_seconds_all']['max']:.2f}",f"{s['completion_seconds_successes']['mean']:.2f}",s['stats']['actions']['sum'],s['protocol_errors']] for s in summaries])
lines+=['','3단계의 빠른 실패83.07초가 전체 평균을 낮춘다. 실패를 성공 완료 시간으로 읽지 않도록 두 평균을 분리했다. 실행기 요청/턴 수는 제공자 내부 호출이나 HTTP 요청 수가 아니다. 사용량 갱신 이벤트와도 구분한다.','',
    '## 통신량과 로컬 처리','','바이트는 실험 채널의 실제 본문과 헤더다. 모델 API·TLS/IP 전체 트래픽이나 로그 base64 크기는 포함하지 않는다. CPU는 전송·복원·프레이밍과 기록된 실패 변환의 처리 합계이며 모델의 문제 풀이·메시지 생성 시간과 다르다.','']
lines+=table(['방식','작업 메시지 합계','합의 메시지 합계','본문 평균 B/회','헤더 평균 B/회','채널 합계 평균 B/회','수신 텍스트 평균 B/회','통신 CPU 평균 ms/회'],[
    [lab(s),s['stats']['task_messages']['sum'],s['stats']['setup_messages']['sum'],f"{s['stats']['payload_bytes']['mean']:.1f}",f"{s['stats']['envelope_bytes']['mean']:.1f}",f"{s['stats']['communication_bytes']['mean']:.1f}",f"{s['stats']['task_receiver_text_bytes']['mean']:.1f}",f"{s['stats']['protocol_cpu_seconds']['mean']*1000:.3f}"] for s in summaries])
lines+=['','6단계 채널 합계には 합의 메시지가 포함되며, 수신 텍스트 열은 모든 방식에서 작업 메시지만이다. 합의·반복 대화의 모델 사용량은 다음 표의 전체 토큰에 포함된다.'.replace('には','에는'),'',
    '## 모델 토큰과 캐시 민감도','','아래 토큰은 A·B 전체 요청 누적 사용량의 회차 평균이다. 입력에는 캐시 입력이 이미 포함되며 reasoning은 출력에 포함된다.','']
lines+=table(['방식','입력 평균','캐시 입력 평균','출력 평균','입력 중 캐시 비중','관측 성공당 모델 비용 USD','캐시 할인 없는 가상 재가중 USD/성공'],[
    [lab(s),f"{s['usage']['inputTokens']['mean']:.1f}",f"{s['usage']['cachedInputTokens']['mean']:.1f}",f"{s['usage']['outputTokens']['mean']:.1f}",f"{100*s['usage']['cachedInputTokens']['sum']/s['usage']['inputTokens']['sum']:.1f}%",f"{s['model_cost_per_success_usd']:.6f}",f"{s['model_cost_per_success_without_cache_discount_usd']:.6f}"] for s in summaries])
lines+=['','가상 재가중은 동일 토큰의 캐시 할인만 제거한 산술 민감도다. 실제 캐시를 끄고 실행한 결과나 그때의 시간·성공률 예측이 아니다. 첫 호출부터 캐시가 기록된 세션은20/60개다. 새 대화 세션이 서버 캐시와 공유 부하까지 격리했다는 뜻은 아니다.','',
    '## 내용 검수와 실제 행동','','자연어는 원문에 근거한AI 전수 주석과 별도AI 재검수, 구조화 표현은 고정 의미의 자동 평가다. 사람의 독립 검수는 대기다. 자연어 추가 자유 표현·반복·슬롯별 전개 때문에 총분모와 오류 개수를 그대로 정확도 순위로 사용하지 않는다.','']
lines+=table(['방식','명시 주장','맞음','틀림','규약 보류','모호한 표현','내용 오류 회차','명시적 revise'],[
    [lab(s),s['claim_occurrences'],s['correct_claims'],s['incorrect_claims'],s['undetermined_claims'],s['unjudgeable_expressions'],', '.join(map(str,s['content_error_trials'])) or '없음',s['explicit_revisions']] for s in summaries])
lines+=['','코덱 보존 오류는30회 모두0건이다. 3단계 실패 회차에는 전달된 명시 주장 오류가0건이지만 최종 일정이 무효였다. 제안 배치는 검증할 후보이며, 그 자체로 유효성·최적성 주장을 추가하지 않는 검수 규칙에 따른다.','',
    '## 30회 개별 결과','','아래5회 모두를 각 방식의 집계에 포함했다. 느린 회차나 실패를 삭제하지 않았다.','']
lines+=table(['단계','회차','결과','점수','시간 초','모델 비용 USD','실행기 턴','거절','채널 B','내용 오류'],[
    [t['stage'],f"[{t['trial']}]({link(ROOT/t['transcript'])})",t['status'],t['score'] if t['score'] is not None else '무효',f"{t['elapsed_seconds']:.2f}",f"{t['model_cost_estimate_usd']:.6f}",t['actions'],t['protocol_errors'],t['communication_bytes'],t['incorrect_claims']] for t in trials])
(HERE/'comparison.md').write_text('\n'.join(lines).replace('../../../docs/experiment-insights-v3-1.md',link(ROOT/'docs/experiment-insights-v3-1.md')).replace('(derive.py)', '('+link(ROOT/'scripts/derive_release.py')+')')+'\n')
print('Verified and aggregated 30 trials, 225 requests, 128 packets.')
for s in summaries:
 print(s['stage'],'model/success',round(s['model_cost_per_success_usd'],8),'time mean/median',round(s['termination_seconds_all']['mean'],2),round(s['termination_seconds_all']['median'],2),'CPU ms',round(s['stats']['protocol_cpu_seconds']['mean']*1000,3),'usage', {k:round(v['mean'],1) for k,v in s['usage'].items()})
for t in trials:
 if t['stage']==6 and t['trial']==4:print('S6T4', {k:t[k] for k in ['rejected_request_seconds','rejected_request_model_cost_usd','input_to_response_seconds','model_cost_estimate_usd']})
