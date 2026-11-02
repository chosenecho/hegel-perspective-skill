"""Offline package/evidence checks; not proof of philosophical or behavioral quality.
Python 3.10+, standard library only. See recorded independent tests for semantics.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import unquote
import corpus
ROOT = Path(__file__).resolve().parents[1]

def within(relative):
    p = (ROOT / relative).resolve()
    if not p.is_relative_to(ROOT.resolve()):
        raise ValueError(f'path leaves skill: {relative}')
    return p

def inspect(skill_path, structure_only=False):
    results = []
    def check(name, ok, detail):
        results.append(dict(check=name, status='PASS' if ok else 'FAIL', detail=detail))
    text = skill_path.read_text(encoding='utf-8-sig')
    fm = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    head = fm[1] if fm else ''
    check('frontmatter', bool(fm and re.search(r'^name: hegel-perspective\s*$',head,re.M) and re.search(r'^description:\s*\S',head,re.M)), 'Basic required fields; official skill-creator validation is separate.')
    models = list(re.finditer(r'^### 模型(\d+)：([^\n]+)\n(.*?)(?=^### |^## |\Z)',text,re.M|re.S))
    check('seven_models',[int(m[1]) for m in models] == list(range(1,8)),[m[1] for m in models])
    bad = [m[1] for m in models if any(s not in m[3] for s in ['**一句话**','**证据**','**应用**','**局限**'])]
    check('model_sections',not bad,{'missing':bad})
    section = text.split('## 决策启发式',1)[-1].split('## 表达DNA',1)[0]
    numbers = [int(x) for x in re.findall(r'^(\d+)\. \*\*',section,re.M)]
    check('ten_heuristics',numbers == list(range(1,11)),numbers)
    sm = within('references/source-map.md').read_text(encoding='utf-8')
    defined = set(re.findall(r'\*\*((?:H|D)\d{2})\*\*',sm))
    used = set(re.findall(r'\b(?:H|D)\d{2}\b',text))
    check('source_ids',not (used-defined),{'undefined':sorted(used-defined)})
    broken=[]
    docs=[skill_path]+list((ROOT/'references').glob('*.md'))+list((ROOT/'references/research').glob('*.md'))+list((ROOT/'references/validation').glob('*.md'))
    for file in docs:
        for raw in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',file.read_text(encoding='utf-8-sig')):
            target=raw.strip().strip('<>').split('#',1)[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target): continue
            p=(file.parent/unquote(target)).resolve()
            if not p.is_relative_to(ROOT.resolve()) or not p.exists(): broken.append({'file':file.relative_to(ROOT).as_posix(),'target':target})
    check('self_contained_links',not broken,{'documents':len(docs),'broken':broken})
    ledger=json.loads(within('references/evidence-ledger.json').read_text(encoding='utf-8'))
    rows=corpus.read_manifest(); by_id={r['id']:r for r in rows}
    check('manifest_unique_ids',len(by_id)==len(rows),{'resources':len(rows),'unique_ids':len(by_id)})
    errors=[]; ids=set(); supports={i:set() for i in range(1,8)}
    for r in ledger['records']:
        ident=r['id']
        if ident in ids: errors.append(f'duplicate evidence id {ident}')
        ids.add(ident); w=by_id.get(r['source_id'])
        if not w or w.get('text_path')!=r['path']: errors.append(f'{ident}: mismatched witness')
        if r.get('effective_grade') not in {'A','B','C','D'}: errors.append(f'{ident}: invalid grade')
        if not r.get('locator') or not r.get('claim'): errors.append(f'{ident}: missing locator/claim')
        witness_path=within(r['path'])
        if not structure_only:
            body=corpus.normalize(witness_path.read_text(encoding='utf-8'))
            if corpus.normalize(r['needle']) not in body: errors.append(f'{ident}: fingerprint absent')
        for model in r.get('models',[]):
            if model not in supports: errors.append(f'{ident}: unknown model')
            elif r['effective_grade'] in {'A','B','C'}: supports[model].add(r['work_key'])
    check('evidence_metadata' if structure_only else 'evidence_fingerprints',not errors,{'entries':len(ids),'errors':errors,'fingerprints_checked':0 if structure_only else len(ids),'scope':'Metadata only; source text was not read.' if structure_only else 'Textual presence only, not semantic proof.'})
    check('cross_work_support',all(len(x)>=2 for x in supports.values()),{str(k):sorted(v) for k,v in supports.items()})
    primary=sum(r['effective_grade'] in {'A','B','C'} for r in ledger['records'])
    check('curated_primary_evidence',primary>len(ids)/2,{'primary_entries':primary,'curated_entries':len(ids),'scope':'Curated ledger only; NOT whole archive or independent-source ratio.'})
    if structure_only:
        results.append({'check':'main_archive_integrity','status':'SKIP','detail':'Source distribution intentionally excludes third-party original archives.'})
    else:
        archive=corpus.audit(rows)
        check('main_archive_integrity',archive['status']=='PASS',archive)
    aux=[]; checked=0
    for name in ['letters-agent','critics-agent']:
        data=json.loads(within(f'references/sources/{name}/source-index.json').read_text(encoding='utf-8-sig'))
        if structure_only:
            continue
        records=data if isinstance(data,list) else data.get('records',[])
        for row in records:
            artifacts=list(row.get('artifacts',[]))
            if name == 'letters-agent':
                for key, sha in [('file','sha256'),('text_file','text_sha256')]:
                    if row.get(key):
                        artifacts.append({'path':f'references/sources/{name}/'+row[key],'sha256':row.get(sha)})
            for artifact in artifacts:
                rel=artifact.get('path','')
                if rel.startswith('hegel-perspective/'):rel=rel[len('hegel-perspective/'):]
                f=within(rel); expected=artifact.get('sha256');checked+=1
                if not f.is_file() or (expected and hashlib.sha256(f.read_bytes()).hexdigest()!=expected): aux.append({'index':name,'path':rel})
        if name == 'letters-agent' and isinstance(data,dict):
            for artifact in data.get('local_support_artifacts',[]):
                rel=f'references/sources/{name}/'+artifact['file']; f=within(rel); checked+=1
                if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=artifact['sha256']:
                    aux.append({'index':name,'path':rel})
    if structure_only:
        results.append({'check':'auxiliary_archive_integrity','status':'SKIP','detail':'Source indexes are present; their archived payloads are not audited in this mode.'})
    else:
        check('auxiliary_archive_integrity',not aux,{'artifacts_checked':checked,'errors':aux})
    check('behavioral_artifacts',all(within('references/validation/'+p).is_file() for p in ['forward-test-responses.md','routing-test-responses.md']),'Existence only; read research/07-validation.md for assessment.')
    return {'status':'PASS' if all(r['status'] in {'PASS','SKIP'} for r in results) else 'FAIL','mode':'structure-only' if structure_only else 'full-archive','scope':'Package structure only; original archive hashes and textual fingerprints were not verified.' if structure_only else 'Package and source integrity, not philosophical correctness or independent behavioral validation.','checks':results}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('skill',nargs='?',type=Path,default=ROOT/'SKILL.md')
    ap.add_argument('--structure-only',action='store_true',help='validate the distributable package without reading excluded third-party archives')
    args=ap.parse_args()
    try:result=inspect(args.skill.resolve(),args.structure_only)
    except (OSError,ValueError,KeyError,TypeError) as exc: result={'status':'FAIL','error':str(exc)}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
