"""Read-only index/artifact/source validation of all 150 structured trial audits."""
import collections
import csv
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
HOME_AUDITS=OUT.parent
PLAN='20260912T170838Z-plan-22772406666b'
BASE=Path('/Users/hyohyeon/Desktop/agent-research-commincation/.worktree')/PLAN
EXPECTED={(s,t) for s in range(2,7) for t in range(1,31)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(folder):return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
indices=sorted(HOME_AUDITS.glob('structured-audit-*/audit-index.json'))
rows=[];batches=[];seen=collections.Counter();final_seen=collections.Counter();issues=[];changed=[];policies=set();groups=set();code_snapshots=[]
for index in indices:
    folder=index.parent;d=json.loads(index.read_text());assert d['plan_id']==PLAN
    policies.add(d['review_policy_version']);code_snapshots.append(d['evaluator_source_hashes'])
    artifacts={name:folder/name for name in ['verification.json','process-audit.md','observation-table.md','selected-source-evidence.md','source-reading-log.json']}
    for name,path in artifacts.items():
        if not path.exists():issues.append({'batch':folder.name,'missing':name})
    ver=json.loads(artifacts['verification.json'].read_text())
    final_key=next(k for k in ['independent_final_checks','final_checks'] if k in ver)
    final_checks=ver[final_key]
    byfinal={(f['stage'],f['trial']):f for f in final_checks}
    for f in final_checks:final_seen[f['stage'],f['trial']]+=1
    assert set(byfinal)=={(r['stage'],r['trial']) for r in d['rows']}
    for r in d['rows']:
        key=r['stage'],r['trial'];seen[key]+=1;groups.add(r['comparison_group'])
        src=Path(r['source']);output=Path(r['output'])
        assert src.is_relative_to(BASE/f'stage-{r["stage"]}') and src.name==f'trial-{r["trial"]:02d}'
        original=json.loads((src/'result.json').read_text());obs=json.loads((output/'observation.json').read_text())
        assert original['stage']==r['stage'] and original['trial_number']==r['trial'] and original.get('finished_at')
        assert (original['status'],original['evaluation']['score'],original['quality_gap'])==(r['status'],r['score'],r['quality_gap'])
        for k in ['task_messages','correct_claims','incorrect_claims','undetermined_claims','codec_errors']:assert obs[k]==r[k]
        f=byfinal[key];iv=f.get('independent',f)
        assert (iv['valid'],iv['score'])==(original['evaluation']['valid'],original['evaluation']['score'])
        assert f['schedule']==original['submissions']['A']
        event_count=sum(e['method']=='experiment/packet' and e['params']['phase']=='task' for e in map(json.loads,(src/'events.jsonl').read_text().splitlines()))
        assert event_count==obs['task_messages']
        expected_hashes=d['protected_trial_hashes'][str(src)];actual_hashes=hashes(src)
        if expected_hashes!=actual_hashes:changed.append({'stage':r['stage'],'trial':r['trial'],'source':str(src),'changed_files':[n for n in sorted(set(expected_hashes)|set(actual_hashes)) if expected_hashes.get(n)!=actual_hashes.get(n)]})
        rows.append({'stage':r['stage'],'trial':r['trial'],'batch':folder.name,'source':str(src),'observation':str(output/'observation.json'),'verification':str(artifacts['verification.json']),'status':r['status'],'score':r['score'],'task_messages':r['task_messages'],'original_source_matches_audit_hash':expected_hashes==actual_hashes})
    batches.append({'batch':folder.name,'trials':len(d['rows']),'trial_numbers':sorted({r['trial'] for r in d['rows']}),'stages':sorted({r['stage'] for r in d['rows']}),'index_sha256':sha(index),'verification_sha256':sha(artifacts['verification.json']),'final_checks':len(final_checks),'reading_scope_log':str(artifacts['source-reading-log.json'])})
missing=sorted(EXPECTED-set(seen));unexpected=sorted(set(seen)-EXPECTED);duplicates=[{'stage':s,'trial':t,'count':n} for (s,t),n in sorted(seen.items()) if n!=1]
assert len(indices)==13 and len(rows)==150 and not missing and not unexpected and not duplicates
assert set(final_seen)==EXPECTED and all(n==1 for n in final_seen.values())
assert policies=={'observation-review-v3.1'} and len(groups)==1 and all(c==code_snapshots[0] for c in code_snapshots)
current_code_equal=all({str(p.relative_to(BASE/f'stage-{s}')):sha(p) for p in sorted((BASE/f'stage-{s}'/'experiment').glob('*.py'))}==code_snapshots[0] for s in range(2,7))
assert current_code_equal and not issues and not changed
result={'plan_id':PLAN,'scope':'audit coverage of stages2..6, trials1..30; no additional experiment execution or re-scoring','audit_batches':13,'expected':150,'row_count':len(rows),'unique_trials':len(seen),'per_stage_counts':dict(collections.Counter(r['stage'] for r in rows)),'missing_trials':missing,'duplicate_trials':duplicates,'unexpected_trials':unexpected,'independent_final_checks':len(final_seen),'source_folders_unique':len({r['source'] for r in rows}),'all_observation_counts_match_indices':True,'all_audit_status_scores_match_original_results':True,'all_independent_final_checks_match_original_results':True,'all_task_packet_counts_match_observations':True,'all_150_original_trial_files_match_their_audit_hashes':not changed,'current_execution_sources_match_all_batch_snapshots':current_code_equal,'review_policy_versions':sorted(policies),'comparison_groups':sorted(groups),'missing_artifacts':issues,'source_changes':changed,'secondary_pattern_trial07_excluded_from_duplicate_count':True,'manual_exhaustive_review_claimed':False,'reading_scope':'each batch combines automatic all-fields checks with explicitly logged selected raw reads; see the per-batch source-reading-log.json','model_calls_added':0,'batches':batches}
(OUT/'coverage-150.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (OUT/'coverage-150.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['stage'],r['trial'])))
md=['# 구조화150개 회차 감사 coverage','','**2~6단계 × 1~30회차 =150개를 정확히 한 번씩 포함한다. 누락0·중복0·범위 밖0이다.** 단계별30개이며13개 감사 묶음에 저장돼 있다.','', '|감사 묶음|회차|대상 단계|건수|','|---|---|---|---:|']
for b in batches:md.append(f"|{b['batch']}|{min(b['trial_numbers']):02d}~{max(b['trial_numbers']):02d}|2~6|{b['trials']}|")
md+=['','150개 모두 임시 observation.json, 감사 지표·원문 읽기 범위, 독립 최종 산술 검산 기록이 있다. 임시 관찰값과 감사 인덱스, 원본 result의 상태·점수·quality gap, 원본 task packet 수를 대조했다. 독립 최종 검산도150개를 정확히 한 번씩 포함하며 원본 판정과 일치한다.','', '모든 묶음은 같은 `observation-review-v3.1`과 같은 comparison group이다. 150개 원본 회차 파일은 각각 감사 당시 해시와 현재 해시가 같고, 현재 단계별 실행 소스도13개 묶음의 저장 해시와 같다. 중앙 복사본을 별도 회차로 세지 않았으며, 27~28 감사에 포함된 3/07의 추가 값 비교도 중복 감사 회차로 세지 않았다.','', '**이것은 자동 전체 대조와 선별 원문 독해의 coverage다. 모든 메시지의 완전 수동 전수검수라는 뜻은 아니다.** 직접 읽은 메시지 범위는 각 묶음의 source-reading-log.json에 있다. 기존150개를 다시 모델 실행하거나 새로운 평가기로 재채점하지 않았다.','', '[150행 원본·산출물 대응표](coverage-150.csv) · [검사 결과와 묶음별 해시](coverage-150.json).']
(OUT/'coverage-150.md').write_text('\n'.join(md)+'\n')
print(json.dumps({k:result[k] for k in ['audit_batches','expected','unique_trials','per_stage_counts','missing_trials','duplicate_trials','independent_final_checks','all_150_original_trial_files_match_their_audit_hashes','current_execution_sources_match_all_batch_snapshots']},ensure_ascii=False))
