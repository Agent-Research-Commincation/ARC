"""Read-only identity/seal/coverage checks for this six-stage, thirty-attempt plan."""
from collections import Counter
import hashlib
import json
from pathlib import Path


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())
def digest(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def hashes(folder):
    result={}
    for p in sorted(Path(folder).rglob('*')):
        require(not p.is_symlink(), 'Symlink in saved record: '+str(p))
        if p.is_file(): result[str(p.relative_to(folder))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def sealed(folder):
    folder=Path(folder); actual=hashes(folder); expected=dict(actual)
    require('seal.json' in expected, 'Missing seal: '+str(folder));expected.pop('seal.json')
    require(read(folder/'seal.json')['files']==expected, 'Seal mismatch: '+str(folder))
    return actual


def trial_paths(source, stage, count=30):
    found=list(Path(source).glob('trial-*/result.json'))
    require({p.parent.name for p in found}=={'trial-%02d'%n for n in range(1,count+1)} and len(found)==count,
            'Exact trial 01..%02d coverage required: %s'%(count,source))
    for p in found:
        r=read(p);n=r.get('trial_number')
        require(type(n) is int and p.parent.name=='trial-%02d'%n and r.get('stage')==stage, 'Trial identity mismatch: '+str(p))
        require(r.get('status') in {'success','failed','stopped','cancelled','infrastructure_error','unconfirmed'}, 'Nonterminal trial: '+str(p))
    return sorted(found)


def collection_inputs(path, with_review=False):
    path=Path(path).resolve(); c=read(path);records=c['records']
    require(Counter(r['stage'] for r in records)==Counter(range(1,7)), 'Exactly one record for stages 1..6 required')
    loaded=[];settings=None
    for r in records:
        source=(path.parent/r['source']).resolve();m=read(source/'manifest.json');sh=sealed(source)
        require(m['status'] in {'completed','incomplete','interrupted','cancelled'}, 'Source is not terminated')
        require(m.get('plan_id')==c['plan_id'] and m.get('stage')==r['stage'] and m.get('purpose')=='experiment' and m.get('expected_trials')==30, 'Wrong plan/stage/count')
        require(m.get('comparison_group')==digest(m['comparison_settings']), 'Comparison digest mismatch')
        if settings is None:settings=m['comparison_settings']
        require(settings==m['comparison_settings'], 'Mixed comparison settings')
        item={'collection_base':path.parent,'record':r,'source':source,'manifest':m,'source_hashes':sh,'trials':trial_paths(source,r['stage'])}
        if with_review:
            review=(path.parent/r['review']).resolve();rm=read(review/'manifest.json');rh=sealed(review)
            require(rm['status'] in {'complete','pending'} and not (review/'review-error.json').exists(), 'Review is incomplete')
            require(rm.get('source_files')==sh and rm.get('source_hash')==digest(sh), 'Selected review/source exact hash mismatch')
            require(rm.get('codec_version')==m['comparison_settings']['codec_version'], 'Review codec mismatch')
            require({p.parent.name for p in review.glob('trial-*/observation.json')}=={p.parent.name for p in item['trials']}, 'Review trial coverage mismatch')
            require(hashes(review/'evaluation-source')==rm.get('evaluation_source_files'), 'Selected evaluator files mismatch')
            for trial in item['trials']:
                for name in ['result.json','events.jsonl','language.json']:
                    original=trial.with_name(name);copied=review/trial.parent.name/name
                    require(original.exists()==copied.exists(), 'Review/source file presence mismatch: '+str(copied))
                    if original.exists():require(original.read_bytes()==copied.read_bytes(), 'Review/source bytes mismatch: '+str(copied))
            for trial,sha in rm.get('manual_input_hashes',{}).items():
                require(hashlib.sha256((review/trial/'manual-review.json').read_bytes()).hexdigest()==sha, 'Selected annotation hash mismatch')
            item.update(review=review,review_manifest=rm,review_hashes=rh)
        loaded.append(item)
    return c,loaded


def output_outside_inputs(output, loaded):
    output=Path(output).resolve()
    require(not output.exists(), 'Output already exists')
    for item in loaded:
        roots=[item['source']]
        if 'review' in item: roots.append(item['review'])
        # A readable export is also sealed original evidence for downstream readers.
        if item['record'].get('readable'):
            roots.append(item['collection_base']/item['record']['readable'])
        for root in roots:
            root=Path(root).resolve()
            require(output!=root and root not in output.parents, 'Output would alter saved input: '+str(root))


def unchanged(loaded):
    for item in loaded:
        require(hashes(item['source'])==item['source_hashes'], 'Source changed during read')
        if 'review' in item:require(hashes(item['review'])==item['review_hashes'], 'Selected review changed during read')
