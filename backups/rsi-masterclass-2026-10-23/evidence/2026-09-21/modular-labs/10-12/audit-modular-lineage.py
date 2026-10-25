"""Read retained lineage records; no new model or harness executions."""
import csv
import hashlib
from pathlib import Path
import shutil

repo=Path(__file__).resolve().parents[3]
source=repo/'rsi/evidence/2026-09-20/two-generations'
out=repo.parent/'rsi-work-2026-09-21-modular-labs/10-12'
if out.exists():raise SystemExit('Preserve lineage audit')
out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def table(name,header,data):
    with (out/name).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(header);writer.writerows(data)
copied=set()
def retain(name):
    p=source/name;dest=out/'source-records'/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    if name not in copied:shutil.copyfile(p,dest);copied.add(name)
    if sha(p)!=sha(dest):raise SystemExit('Copy mismatch')
    return sha(p)

for name in ['STATE.csv','LINEAGE.md','PROTOCOL.md','driver.source.py','skills/IMPROVER-v0.md','skills/TASK-initial.md']:retain(name)
edges=[]
for path in ['baseline','recursive']:
    parent_task='skills/TASK-initial.md'
    for generation in [1,2]:
        prefix=f'{path}/generation-{generation}'
        arms_file=prefix+'/ARM-DECISIONS.csv';decision_file=prefix+'/DECISION.csv'
        retain(arms_file);retain(decision_file)
        decision=rows(source/decision_file)[0]
        child=prefix+'/TASK-proposal.md';retain(child)
        for arm in rows(source/arms_file):
            identity=retain(arm['improver'])
            if identity!=arm['improver_sha256']:raise SystemExit('Improver hash mismatch')
            before=prefix+'/'+arm['arm']+'/BEFORE.md';retain(before)
            if identity not in (source/before).read_text():raise SystemExit('Missing before-action identity')
            edges.append([path,generation,'task proposal',parent_task,child,'fixed driver reads recorded schedule',arm['improver'],identity,arm['arm'],arm['promoted'],arm['retained_task'],arm['retained_selection'],arms_file])
        if retain(decision['active_task'])!=decision['active_task_sha256']:raise SystemExit('Retained task hash mismatch')
        if retain(decision['active_improver'])!=decision['active_improver_sha256']:raise SystemExit('Retained improver hash mismatch')
        if path=='recursive':
            proposal=prefix+'/IMPROVER-proposal.md';retain(proposal);retain(prefix+'/CHANGE-PROPOSAL.md')
            edges.append([path,generation,'improver proposal',decision['parent_improver'],proposal,'fixed author-guided driver template',decision['parent_improver'],sha(source/decision['parent_improver']),'outer',decision['improver_promoted'],decision['active_improver'],decision['retained_selection'],decision_file])
        parent_task=decision['active_task']
        if decision['active_improver']!='skills/IMPROVER-v0.md' or decision['improver_promoted']!='False':raise SystemExit('Unexpected promotion; revisit classification')
header=['path','generation','changed_object','parent','proposed_child','producer','improver_version','improver_sha256','arm','promoted','retained_object','retained_selection_mae','decision_record']
table('TYPED-EDGES.csv',header,edges)
keep=[i for i,k in enumerate(header) if k not in ['improver_version','improver_sha256']]
table('WITHOUT-IMPROVER.csv',[header[i] for i in keep],[[row[i] for i in keep] for row in edges])
table('COPIED-SOURCES.csv',['source_relative_path','sha256'],[[p,sha(source/p)] for p in sorted(copied)])
(out/'CHECK.md').write_text(f'# Read-only lineage audit\n\nTyped rows: {len(edges)}\nSource files copied and hash checked: {len(copied)}\nNew model fits: 0\n\nEvery arm row agrees with its retained improver file and before-action trace. Retained task/improver hashes match. Both paths keep IMPROVER-v0 after both generations; neither proposed improver is promoted. The actor supplied the schedule and the driver templates. This audit recomputes identities, not historical model scores or independent-agent behavior.\n',encoding='utf-8',newline='\n')
shutil.copyfile(__file__,out/'audit-modular-lineage.py')
print((out/'CHECK.md').read_text())
