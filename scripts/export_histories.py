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
    output.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.history-build-',dir=output.parent))
    try:
        target = staging/'records'
        shutil.copytree(source,target)
        (target/'seal.json').rename(target/'source-seal.json')
        if review:
            for trial in sorted(review.glob('trial-*')):
                for name in ('observation.json','observation.md','manual-review.json'):
                    if (trial/name).exists(): shutil.copy2(trial/name,target/trial.name/name)
        lines = ['# 단계별 실험 기록','','방식: '+manifest['stage_name'],'',
                 '[지표 보고서](report.md)','','검수 버전: '+(selected['review_id'] if review else '미선택 — 내용 검수 대기'),'',
                 '| 회차 | 상태 | 관찰 | 대화 | Agent 이력 |','|---|---|---|---|---|']
        for i in range(1,manifest['expected_trials']+1):
            name='trial-%02d'%i
            result=target/name/'result.json'
            if not result.exists():
                lines.append('| %d | 미실행 | — | — | — |'%i)
                continue
            row=json.loads(result.read_text())
            lines.append('| %d | %s | [관찰](%s/observation.md) | [대화](%s/transcript.md) | [A](%s/Agent_A.md) · [B](%s/Agent_B.md) |'%(i,row['status'],name,name,name,name))
        (target/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        write_json(target/'export.json',{'source':str(source),'source_hashes':before,'review':str(review) if review else None,
            'review_hashes':hashes(review) if review else None,'rescore':False})
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
