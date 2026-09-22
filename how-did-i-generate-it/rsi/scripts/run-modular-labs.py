"""Deterministic interface fixtures with explicit budgets and no ML dependencies."""
import argparse
import csv
import hashlib
import importlib.util
from pathlib import Path
import shutil
import time

repo=Path(__file__).resolve().parents[3]
out=repo.parent/'rsi-work-2026-09-21-modular-labs'
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','patch','integration','archive']);args=parser.parse_args()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,body):
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body.rstrip()+'\n',encoding='utf-8',newline='\n')
def table(name,columns,rows):
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(columns);writer.writerows(rows)
def absent(name):
    if (out/name).exists():raise SystemExit('Preserve existing phase: '+name)
def fields(path):return dict(line.split(': ',1) for line in path.read_text().splitlines() if ': ' in line)
def load(path):
    spec=importlib.util.spec_from_file_location('fixture_'+sha(path),path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def identities(root):return {p.name:sha(p) for p in sorted(root.glob('*.py'))}
def record(case,label,version,expected,seconds=None):
    folder=out/label
    if folder.exists():raise SystemExit('Attempt already reserved: '+label)
    folder.mkdir(parents=True)
    before=identities(version);start=time.perf_counter()
    save(label+'/BEFORE.md','# Before fixture\n\nVersion: '+str(version.relative_to(out))+'\nExpected verdict: '+expected+'\nActual model fits allowed: 0')
    table(label+'/COMPONENTS.csv',['component','sha256'],before.items())
    trace=[['loop','enter'],['tool','read constructed fixture; no model execution']]
    supplied=dict(case);observed=load(version/'observation.py').observe(supplied)
    save(label+'/OBSERVATION.md','# Before context\n\n'+'\n'.join(k+': '+str(v) for k,v in observed.items()))
    trace.append(['observation','candidate='+str(observed.get('candidate','MISSING'))])
    context=load(version/'context.py').prepare(observed)
    save(label+'/CONTEXT.md','# After context\n\n'+'\n'.join(k+': '+str(v) for k,v in context.items()))
    trace.append(['context','candidate='+str(context.get('candidate','MISSING'))+'; fields='+','.join(sorted(context))])
    stub=0;value='';reason='';verdict='accepted'
    try:
        value=load(version/'completion.py').check(context)
        trace.append(['completion','accepted']);stub=load(version/'tool.py').fit_stub();trace.append(['fit_stub','reached; no model fitted'])
    except ValueError as exc:
        verdict='refused';reason=str(exc);trace.append(['completion','refused: '+reason])
    elapsed=time.perf_counter()-start
    if identities(version)!=before:raise SystemExit('Component changed during fixture')
    expected_ok=verdict==expected and (seconds is None or verdict!='accepted' or abs(float(value)-seconds)<1e-12) and (stub==0 if verdict=='refused' else stub==1)
    table(label+'/TRACE.csv',['component','event'],trace)
    save(label+'/RESULT.md',f'# Fixture result\n\nHarness verdict: {verdict}\nReason: {reason or "none"}\nSeconds: {value}\nFit stub calls: {stub}\nActual fits: 0\nExpectation matched: {expected_ok}\nWall seconds: {elapsed:.9f}\n\nA matched expected refusal is evidence of a detected fault, not a passing combined harness.')
    with (out/'EXECUTIONS.csv').open('a',encoding='utf-8',newline='') as stream:csv.writer(stream,lineterminator='\n').writerow([label,verdict,expected,expected_ok,stub,0,elapsed])
    if not expected_ok:raise SystemExit('Unexpected fixture outcome; preserve and stop: '+label)

BASE={
 'loop.py':'# The fixture driver invokes observation, context, completion, then the stub.\nORDER = ("observation", "context", "completion", "fit_stub")\n',
 'tool.py':'def fit_stub():\n    """Report a reached boundary; never train a model."""\n    return 1\n',
 'observation.py':'def observe(record):\n    return dict(record)\n',
 'context.py':'def prepare(record):\n    result = dict(record)\n    if len(result.get("details", "")) > 40:\n        result = {k: v for k, v in result.items() if k not in ("details", "candidate")}\n    return result\n',
 'completion.py':'def check(record):\n    if not record.get("candidate"):\n        raise ValueError("missing candidate identity")\n    if "duration_seconds" in record:\n        return float(record["duration_seconds"])\n    unit = record.get("duration_unit")\n    if unit not in ("seconds", "minutes"):\n        raise ValueError("missing or unsupported duration_unit")\n    return float(record["duration_value"]) * (60 if unit == "minutes" else 1)\n'
}
SHORT={'candidate':'trial-001','duration_value':'2','duration_unit':'seconds','details':'Short observation.'}
LONG={**SHORT,'details':'A long constructed diagnostic observation. '*5}

if args.phase=='prepare':
    if out.exists():raise SystemExit('Preserve workspace')
    out.mkdir();shutil.copyfile(__file__,out/'run-modular-labs.py');shutil.copyfile(repo/'how-did-i-generate-it/rsi/validation/MODULAR-LABS-PROTOCOL.md',out/'PROTOCOL.md')
    save('EXECUTIONS.csv','case,harness_verdict,expected,expectation_matched,stub_calls,actual_fits,wall_seconds')
    save('10-10/CONTRACT.md','# Local context boundary\n\nEvery observation must retain candidate identity through compression. Duration fields must remain interpretable. Two supplied traces are generated first, then two patch checks. Zero model fits. The details strings and two-second values are constructed fixture inputs, not measured model runtimes.')
    for name,code in BASE.items():save('10-10/H0/'+name,code)
    for name,case in [('short',SHORT),('long',LONG)]:save('10-10/fixtures/'+name+'.md','# Constructed input\n\n'+'\n'.join(k+': '+v for k,v in case.items()))
    record(SHORT,'10-10/before-short',out/'10-10/H0','accepted',2)
    record(LONG,'10-10/before-long',out/'10-10/H0','refused')
    save('10-10/PAUSE.md','# Actor checkpoint\n\nRead both traces and context records. Write DIAGNOSIS.md and context-patch.py. Only the context component may change. Two patch checks remain; no model fits.')
    print('Prerequisite traces captured: short accepted, long refused. Pause for diagnosis and context-only patch.')
elif args.phase=='patch':
    absent('10-10/H1')
    if not (out/'10-10/DIAGNOSIS.md').exists() or not (out/'10-10/context-patch.py').exists():raise SystemExit('Actor diagnosis and patch required')
    before=identities(out/'10-10/H0');shutil.copytree(out/'10-10/H0',out/'10-10/H1',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(out/'10-10/context-patch.py',out/'10-10/H1/context.py')
    after=identities(out/'10-10/H1');changed=[name for name in before if before[name]!=after[name]]
    table('10-10/DIFF.csv',['component','parent_sha256','child_sha256','changed'],[[name,before[name],after[name],before[name]!=after[name]] for name in before])
    if changed!=['context.py']:raise SystemExit('Patch exceeds context scope')
    record(LONG,'10-10/after-long',out/'10-10/H1','accepted',2)
    record(SHORT,'10-10/after-short',out/'10-10/H1','accepted',2)
    save('10-10/DONE.md','# Local repair\n\nOnly context.py changed. Both patched cases retained candidate identity and two seconds. The original long case was refused. No broader transfer, independent agent, or learner claim follows.')
    print('Two patch checks passed; only context.py changed; zero fits.')
elif args.phase=='integration':
    absent('10-11')
    if not (out/'10-10/DONE.md').exists():raise SystemExit('Complete local repair first')
    base={**BASE,'context.py':'def prepare(record):\n    return {k: v for k, v in record.items() if k != "details"}\n'}
    compact='def prepare(record):\n    result = {k: v for k, v in record.items() if k != "details"}\n    unit = result.get("duration_unit")\n    if unit in ("seconds", "minutes"):\n        result["duration_seconds"] = float(result.pop("duration_value")) * (60 if unit == "minutes" else 1)\n        result.pop("duration_unit")\n    return result\n'
    strict='def check(record):\n    if not record.get("candidate"):\n        raise ValueError("missing candidate identity")\n    if "duration_unit" not in record:\n        raise ValueError("required duration_unit absent at completion interface")\n    unit = record["duration_unit"]\n    if unit not in ("seconds", "minutes"):\n        raise ValueError("unsupported duration_unit")\n    return float(record["duration_value"]) * (60 if unit == "minutes" else 1)\n'
    for version in ['base','A','B','AB']:
        components={**base}
        if version in ['A','AB']:components['context.py']=compact
        if version in ['B','AB']:components['completion.py']=strict
        for name,code in components.items():save('10-11/versions/'+version+'/'+name,code)
    fixtures={'original':SHORT,'fresh':{'candidate':'trial-009','duration_value':'0.5','duration_unit':'minutes','details':'New candidate and duration representation.'},'malformed':{'duration_value':'2','duration_unit':'seconds','details':'Candidate identity deliberately omitted.'}}
    for name,case in fixtures.items():save('10-11/fixtures/'+name+'.md','# Predeclared input\n\n'+'\n'.join(k+': '+v for k,v in case.items()))
    save('10-11/INTERFACES.md','# Before execution\n\n| Version | Context produces | Completion consumes |\n|---|---|---|\n| Base | candidate, duration_value, duration_unit | candidate and either explicit units/value or duration_seconds |\n| A | candidate, duration_seconds | same as base |\n| B | same as base | candidate, duration_value, required duration_unit |\n| A+B | same as A | same as B |\n\nA removes the unit field that B requires. Both may pass alone while the combination refuses. Original: 2 seconds. Fresh: 0.5 minutes, equivalent to 30 seconds. Malformed: candidate missing. All fixtures were authored before this comparison and visible to the author; fresh is not blinded. The fit stub is reachable only after completion validates the interface. These are illustrative components, not the source paper implementation.')
    schedule=[('original',v,'refused' if v=='AB' else 'accepted',2) for v in ['base','A','B','AB']]+[('fresh','base','accepted',30),('fresh','AB','refused',None),('malformed','AB','refused',None)]
    table('10-11/PLAN.csv',['case','version','expected','expected_seconds'],schedule)
    frozen={p.relative_to(out).as_posix():sha(p) for p in sorted((out/'10-11').rglob('*')) if p.is_file()}
    table('10-11/FREEZE.csv',['file','sha256'],frozen.items())
    for i,(name,version,expected,seconds) in enumerate(schedule,1):record(fixtures[name],f'10-11/check-{i:02d}-{name}-{version}',out/'10-11/versions'/version,expected,seconds)
    for name,digest in frozen.items():
        if sha(out/name)!=digest:raise SystemExit('Declared fixture/version changed')
    save('10-11/DONE.md','# Combination rejected\n\nSeven executions completed, zero model fits. Base, A, and B accepted the original fixture. A+B refused both original and fresh fixtures due to the removed duration_unit field. The malformed case refused missing candidate identity before the fit stub. Base remained active; no repair or extra test occurred. Expected refusals establish detection of the conflict, not a successful integration.')
    print('Seven integration fixtures completed; combined version rejected; zero fits.')
elif args.phase=='archive':
    if not (out/'10-12/CLAIM-AUDIT.md').exists():raise SystemExit('Lineage audit required')
    absent('MANIFEST.csv')
    files=sorted(p for p in out.rglob('*') if p.is_file())
    table('MANIFEST.csv',['file','sha256'],[(p.relative_to(out).as_posix(),sha(p)) for p in files])
    print(f'Manifest: {len(files)} retained files; includes generated bytecode as execution artifacts.')
