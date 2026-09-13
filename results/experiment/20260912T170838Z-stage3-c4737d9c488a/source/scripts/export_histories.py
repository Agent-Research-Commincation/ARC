"""Render one sealed run and an explicitly selected review. Never rescore or call models."""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiment.artifacts import file_hashes as hashes, verify_seal, write_json, digest, seal_run


def export(source, output, review=None):
    source,output = Path(source).resolve(),Path(output).resolve()
    if output.exists() or output==source or source in output.parents:
        raise ValueError('Choose a new output folder outside the source run')
    verify_seal(source)
    manifest = json.loads((source/'manifest.json').read_text())
    if manifest['status']=='running': raise ValueError('Wait for run termination')
    before = hashes(source)
    if review:
        review = Path(review).resolve()
        verify_seal(review)
        selected = json.loads((review/'manifest.json').read_text())
        if selected['source_files'] != before:
            raise ValueError('Selected review belongs to different source data')
        code = review/'evaluation-source'
        if not code.is_dir() or hashes(code) != selected.get('evaluation_source_files'):
            raise ValueError('Selected review must archive its exact evaluator sources for a replayable export')
    output.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.history-build-',dir=output.parent))
    try:
        target = staging/'records'
        shutil.copytree(source,target)
        (target/'seal.json').rename(target/'source-seal.json')
        if (target/'report.md').exists():
            (target/'report.md').rename(target/'source-report.md')
            report = (target/'source-report.md').read_text()
            report = report.replace('모델 호출 합계:', '실행기 요청/턴 합계:').replace('모델 요청', '실행기 요청/턴')
            report += '\n실행기 요청/턴은 제공자 내부 호출 수나 HTTP 요청 수가 아닙니다. 사용량 갱신 횟수와도 구분합니다. 수치는 종료 당시 값을 유지하며, 원문은 [source-report.md](source-report.md)에 있습니다.\n'
            (target/'report.md').write_text(report)
        if review:
            # Preserve the exact post-run evaluator, annotations, manifest and seal.
            # source/ remains the code used to execute the experiment.
            shutil.copytree(review, target/'selected-review')
            for trial in sorted(review.glob('trial-*')):
                for name in ('observation.json','observation.md','manual-review.json'):
                    if (trial/name).exists(): shutil.copy2(trial/name,target/trial.name/name)
        lines = ['# 단계별 실험 기록','','방식: '+manifest['stage_name'],'',
                 '[지표 보고서](report.md)','','검수 버전: '+(selected['review_id'] if review else '미선택 — 내용 검수 대기'),'',
                 '사후 평가 정책: '+(selected.get('review_policy_version','이전 정책') if review else '미선택'),'',
                 '`source-report.md`는 종료 당시 보고서 원문이고, `report.md`는 수치를 유지한 채 요청/턴의 단위명을 정리한 표시용 사본입니다. 최신 내용 검수 상태는 아래 관찰표와 선택한 검수 버전을 기준으로 합니다. AI 주석 검수와 사람의 독립 검수는 구별합니다.','',
                 '| 회차 | 상태 | 관찰 | 대화 | Agent 이력 |','|---|---|---|---|---|']
        for i in range(1,manifest['expected_trials']+1):
            name='trial-%02d'%i
            result=target/name/'result.json'
            if not result.exists():
                lines.append('| %d | 미실행 | — | — | — |'%i)
                continue
            row=json.loads(result.read_text())
            lines.append('| %d | %s | [관찰](%s/observation.md) | [대화](%s/transcript.md) | [A](%s/Agent_A.md) · [B](%s/Agent_B.md) |'%(i,row['status'],name,name,name,name))
        if review:
            shutil.copy2(ROOT/'scripts/replay_review.py',target/'replay_review.py')
            lines += ['', '## 선택한 평가 재현', '',
                      '`source/`는 실험 실행 코드, `selected-review/evaluation-source/`는 사후 평가 코드입니다.', '',
                      '`python3 replay_review.py --export . --output <새 출력 폴더>`로 선택한 주석의 판정과 관찰표를 재현합니다. 모델을 호출하지 않습니다. 자연어 의미를 새로 독립 주석하는 작업은 아닙니다.', '',
                      '[평가 버전·주석 정보](selected-review/manifest.json) · [평가 집계](selected-review/summary.json)']
        (target/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        write_json(target/'export.json',{'source':str(source),'source_hashes':before,'review':str(review) if review else None,
            'review_hashes':hashes(review) if review else None,'rescore':False,
            'export_version':2,'selected_review':'selected-review' if review else None})
        for relative,expected in before.items():
            if Path(relative).name in ('events.jsonl','result.json','manifest.json','language.json'):
                if hashes(target).get(relative)!=expected: raise ValueError('Export changed raw content: '+relative)
        if hashes(source)!=before: raise ValueError('Source changed during export')
        seal_run(target)
        target.rename(output)
    finally:
        shutil.rmtree(staging)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--review',type=Path,help='Exact review directory; omit to display pending content review')
    args=parser.parse_args()
    print(export(args.source,args.output,args.review))
