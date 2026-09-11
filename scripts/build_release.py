"""Build a shareable, versioned evidence bundle from the selected 30 trials.

Original runs, reviews, readable exports, analyses and worktrees are never edited.
The ZIP and its SHA-256 sidecar can be shared without Git or Codex credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.export_histories import export
from scripts.replay_review import hashes, inside, read_json, verify_seal

PLAN = '20260911T092336Z-plan-cfd3ab2b1222'
BATCH = PLAN + '-review-v3-1'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def reader_text(text):
    return text.replace('모델 요청', '실행기 요청/턴').replace('모델 호출 합계:', '실행기 요청/턴 합계:')


def portable_markdown(source, target, bundle):
    """Rewrite navigation in new presentation copies, never archived originals."""
    text = reader_text(source.read_text())
    def replace(match):
        label, raw = match.group(1), match.group(2)
        path_part, sep, anchor = unquote(raw).partition('#')
        if not path_part or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', path_part):
            return match.group(0)
        original = (source.parent/path_part).resolve()
        if not inside(original, ROOT):
            raise ValueError('Reader link outside project: ' + raw)
        relative = original.relative_to(ROOT)
        if relative.parts[0] in ('config', 'experiment'):
            destination = bundle/'execution-source'/relative
        elif relative.parts[0] == 'releases':
            destination = bundle/'README.md'
        elif relative.as_posix() == 'docs/candidate-score-review-v3-1.md':
            destination = bundle/'docs/metrics.md'
        else:
            destination = bundle/relative
        link = Path(os.path.relpath(destination, target.parent)).as_posix()
        return '[' + label + '](' + link + (sep+anchor if sep else '') + ')'
    text = re.sub(r'\[([^\]\n]*)\]\(([^)\n]+)\)', replace, text)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def language_notes(bundle, records):
    record = next(r for r in records if r['stage'] == 1)
    run = bundle/record['source']
    problem = read_json(run/'manifest.json')['comparison_settings']['problem']
    examples = []
    for number, sequence in ((1, 1), (4, 2)):
        events = [json.loads(line) for line in (run/f'trial-{number:02d}/events.jsonl').read_text().splitlines()]
        packet = next(e['params'] for e in events if e['method']=='experiment/packet' and e['params']['sequence']==sequence)
        for meeting, listed in (('M1', [1,3,4,7,9,11]), ('M2', [1,2,3,4,6,7,9,11])):
            people = next(m['attendees'] for m in problem['meetings'] if m['id']==meeting)
            own = [p for p in people if problem['people'][p]['owner']=='A']
            possible = [s for s in range(12) if all(problem['people'][p]['availability'][s] for p in own)]
            missing = sorted(set(possible)-set(listed))
            if missing != [8]:
                raise ValueError('Identified language sensitivity case changed')
            examples.append({'trial':number, 'message':sequence, 'meeting':meeting,
                             'listed_slots':listed, 'omitted_available_slots':missing,
                             'global_blockers_at_slot_8':[p for p in people if not problem['people'][p]['availability'][8]],
                             'source_text':packet['receiver_text'],
                             'transcript':record['slug']+f'/trial-{number:02d}/transcript.md'})
    folder = bundle/'results/readable'/BATCH
    write(folder/'language-sensitivity.json', {
        'selected_policy':'observation-review-v3.1', 'selected_explicit_errors':6,
        'identified_list_omissions':4, 'unjudgeable_expressions':1,
        'errors_if_only_these_four_lists_are_treated_as_exhaustive':10,
        'scope':'Four previously identified omissions only, not a full re-annotation or an alternative accuracy rate.',
        'original_labels_changed':False, 'final_success_and_optimal_counts_changed':False, 'examples':examples})
    lines = ['# 자연어의 명시 오류·누락·모호함', '',
             '현재 기준의 명시 오류는 6건이다. 별도로 가능한 시간 목록에서 슬롯 8이 빠진 항목 4개와 모호한 표현 1개가 있다. 누락을 자동으로 오류로 합산하지 않는다.', '',
             '아래 네 목록만 전체 목록 주장으로 해석하면 오류가 10건이 되는 대안이 있다. 전체 자연어를 다시 주석한 결과나 새로운 정확도 비율은 아니다. 해당 슬롯은 B1의 제약으로 전체 일정에 사용할 수 없어 최종 성공·최적 수는 변하지 않는다.', '',
             '| 회차 | 메시지 | 회의 | 빠진 가능 슬롯 | 원문 |', '|---|---|---|---|---|']
    for row in examples:
        lines.append('| %d | %d | %s | 8 | [대화](%s) |' % (row['trial'],row['message'],row['meeting'],row['transcript']))
    lines += ['', '[상세 근거](language-sensitivity.json) · [평가 범위](../../../docs/metrics.md)', '',
              '새 실험에서는 목록의 의미와 불가능 후보 점수 기준을 결과 확인 전에 고정한다. 기존 판정 재현과 독립적인 의미 주석은 별개다.']
    (folder/'language-sensitivity.md').write_text('\n'.join(lines)+'\n')


def build(output, release_id):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Release output already exists; choose a new path')
    selected_dir = ROOT/'results/readable'/BATCH
    collection = read_json(selected_dir/'collection.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.release-build-', dir=output.parent))
    try:
        records = []
        originals = {}
        for record in collection['records']:
            source, review = Path(record['source']).resolve(), Path(record['review']).resolve()
            if not inside(source, ROOT) or not inside(review, ROOT):
                raise ValueError('Expected project-local original inputs')
            verify_seal(source)
            verify_seal(review)
            originals[str(source)] = hashes(source)
            originals[str(review)] = hashes(review)
            original_worktree = Path(record['original_worktree'])
            if hashes(original_worktree) != originals[str(source)]:
                raise ValueError('Central run and original worktree differ')
            source_relative = Path('results/experiment')/record['run_id']
            review_relative = Path('results/reviews')/record['run_id']/review.name
            readable_relative = Path('results/readable')/BATCH/record['slug']
            shutil.copytree(source, staging/source_relative)
            shutil.copytree(review, staging/review_relative)
            export(source, staging/readable_relative, review)
            records.append({key:record[key] for key in ('stage','label','slug','run_id')})
            records[-1].update(source=source_relative.as_posix(), review=review_relative.as_posix(), readable=readable_relative.as_posix())
        portable_collection = {'plan_id':PLAN, 'review_policy_version':collection['review_policy_version'],
                              'path_base':'release root', 'records':records}
        write(staging/'results/readable'/BATCH/'collection.json', portable_collection)
        reference = staging/'reference'
        reference.mkdir()
        shutil.copy2(selected_dir/'collection.json', reference/'collection.json')
        shutil.copytree(ROOT/'results/analysis'/BATCH, reference/'analysis')
        shutil.copytree(ROOT/'results/plans'/PLAN, staging/'results/plans'/PLAN)
        shutil.copytree(Path(collection['records'][0]['source'])/'source', staging/'execution-source')
        # Keep annotation inputs, quoted messages and historical policy decisions.
        input_relative = Path('results/review-inputs')/(PLAN+'-v3-1')
        shutil.copytree(ROOT/input_relative, staging/input_relative)
        shutil.copy2(selected_dir/'review-delta.json', staging/'results/readable'/BATCH/'review-delta.json')
        for name in ('replay_review.py','derive_release.py','verify_release.py'):
            target = staging/'scripts'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/'scripts'/name, target)
        for path in (ROOT/'docs').glob('*.md'):
            portable_markdown(path, staging/'docs'/path.name, staging)
        portable_markdown(selected_dir/'natural-language-review.md', staging/'results/readable'/BATCH/'natural-language-review.md', staging)
        analysis_relative = Path('results/analysis')/BATCH
        # A portable derivative of the original analysis writes NEW output only.
        result = subprocess.run([sys.executable, '-I', '-B', str(staging/'scripts/derive_release.py'),
                                 '--root', str(staging), '--output', str(staging/analysis_relative)],
                                cwd=staging, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
        portable_markdown(ROOT/analysis_relative/'cases.md', staging/analysis_relative/'cases.md', staging)
        # The generated table links to its reproducible command.
        table = staging/analysis_relative/'comparison.md'
        table.write_text(table.read_text().replace('(derive.py)', '(../../../scripts/derive_release.py)'))
        language_notes(staging, records)
        nav = ['# 방식별·회차별 대화', '',
               '[전체 비교표](../../analysis/'+BATCH+'/comparison.md) · [자연어 전체 기록](natural-language-review.md) · [누락·해석 민감도](language-sensitivity.md)', '',
               '| 방식 | 실제 대화와 평가 |', '|---|---|']
        nav += ['| %d · %s | [5회 기록](%s/README.md) |' % (r['stage'],r['label'],r['slug']) for r in records]
        (staging/'results/readable'/BATCH/'README.md').write_text('\n'.join(nav)+'\n')
        readme = ['# 여섯 Agent 소통 방식 · 공유용 결과 묶음', '',
                  '같은 일정 문제에서 여섯 방식을 5회씩 실행한 기존 30회의 결과다. 유효 합의 29회·최적 28회다. 모델을 다시 호출하지 않고 원대화·선택한 평가·수치 분석을 확인할 수 있다.', '',
                  '## 읽기', '',
                  '- [결과와 인사이트](docs/experiment-insights-v3-1.md)',
                  '- [실험 소개](docs/phase-1-experiment.md) · [지표 읽는 법](docs/metrics.md)',
                  '- [전체 비교표](results/analysis/'+BATCH+'/comparison.md)',
                  '- [대화 사례 분석](results/analysis/'+BATCH+'/cases.md)',
                  '- [방식별·회차별 대화](results/readable/'+BATCH+'/README.md)',
                  '- [자연어 누락·해석 민감도](results/readable/'+BATCH+'/language-sensitivity.md)', '',
                  '## 평가와 분석 재현', '',
                  'Python 3.9 이상만 필요하다. ZIP을 원하는 위치에 풀고 이 README가 있는 폴더에서 실행한다. Codex 로그인·네트워크·모델 호출은 필요하지 않다.', '',
                  '```sh', 'python3 scripts/verify_release.py --bundle . --output ../new-replay', '```', '',
                  '출력은 아직 없는 새 폴더를 지정한다. 체크섬과 원본 봉인을 확인하고, 저장된 사후 평가 코드로 30회 관찰표를 재생한 뒤 비교표·요청별 비용·사례 근거를 다시 계산한다. 기존 수치와 판정이 다르면 실패한다. 결과는 출력 폴더의 `verification.json`과 `analysis/`에서 확인한다.', '',
                  '자연어 주석은 기존 AI 주석을 사용한다. 같은 판정의 재현은 사람의 독립 해석 검증과 다르다. 명시 오류 6건, 확인된 누락 4개, 모호한 표현 1개를 구분하며, 네 목록을 전체 목록으로 읽는 대안의 10건을 정답으로 확정하지 않는다.', '',
                  '## 자료의 구분', '',
                  '| 위치 | 내용 |', '|---|---|',
                  '| `results/experiment/` | 봉인된 실행 원본과 당시 코드 |',
                  '| `results/reviews/` | 선택한 사후 평가 코드·manifest·주석·판정과 봉인 |',
                  '| `results/readable/` | 새 읽기용 사본. 각 방식의 `selected-review/`에도 실제 평가를 포함 |',
                  '| `results/analysis/` | 상대 경로를 사용한 비교표·사례·파생 데이터 |',
                  '| `execution-source/` | 공통 실행 소스 사본. 기존 실험실 운영 문서는 이 소스를 설명 |',
                  '| `reference/` | 변경하지 않은 이전 분석·경로 메타데이터. 실행 경로로 사용하지 않음 |',
                  '| `scripts/` | 이 배포 묶음의 오프라인 재현 도구 |', '',
                  '봉인된 기록에 들어 있는 과거 절대 경로는 출처 정보로 보존했다. 재현 명령은 상대 경로의 collection을 사용하며 원래 컴퓨터의 파일을 읽지 않는다. 평가·분석 프로세스의 Python 감사 훅은 묶음·출력·표준 라이브러리 밖의 파일 읽기와 네트워크·프로세스 실행을 차단한다. 운영체제 격리를 의미하지는 않는다.', '',
                  '실행기 요청/턴은 225회, 사용량 갱신은 229개다. 실제 HTTP 요청 수나 제공자 내부 호출 수는 측정하지 않았다. 비용에는 모든 누적 토큰을 포함했으며 API 단가 추정 합계는 $0.36349092다. 총비용은 미측정이다.', '',
                  '단일 문제·방식별 5회에 대한 관찰이다. 일반적인 방식 우열이나 실무 도입 효과까지 확정하지 않는다.']
        (staging/'README.md').write_text('\n'.join(readme)+'\n')
        write(staging/'release.json', {'release_id':release_id, 'plan_id':PLAN,
              'collection':str(Path('results/readable')/BATCH/'collection.json'), 'analysis':analysis_relative.as_posix(),
              'originals_preserved':True, 'original_worktree_copies_matched':True,
              'expected_results':{'trials':30,'successes':29,'optimal':28,'runner_turns':225,
                                  'model_cost_estimate_usd':0.36349092,'incorrect_claims':47,'undetermined_claims':8},
              'evaluation_scope':'Selected post-run v3.1 policy and archived AI annotations; no new model calls.',
              'historical_metadata':'Absolute locations in sealed originals/reference are provenance only; portable collection supplies operational paths.'})
        for path, before in originals.items():
            if hashes(Path(path)) != before:
                raise ValueError('Build modified original input')
        write(staging/'checksums.json', {'algorithm':'sha256','files':hashes(staging)})
        staging.rename(output)
        return output
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def archive(folder, target):
    folder, target = Path(folder), Path(target)
    if target.exists() or target.with_suffix(target.suffix+'.sha256').exists():
        raise ValueError('Archive already exists')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(folder.name+'/'+path.relative_to(folder).as_posix(), (2026,9,12,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix+'.sha256').write_text(digest+'  '+target.name+'\n')
    return digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--release-id', required=True)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    folder = build(args.output, args.release_id)
    print('Built release:', folder)
    from scripts.verify_release import verify
    with tempfile.TemporaryDirectory(prefix='release-verification-') as temporary:
        verified = verify(folder, Path(temporary)/'replay')
    if args.archive:
        print('Archive SHA-256:', archive(folder, args.archive))
        write(args.archive.with_suffix('.verification.json'), verified)
