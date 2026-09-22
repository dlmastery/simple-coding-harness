"""Author-guided, resumable two-generation teaching run; students use prompts."""
import argparse
import csv
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from threadpoolctl import threadpool_limits


SCHEDULE = "Generation 1: propose a tree with calendar fields. Generation 2: keep the retained model family and add observed weather."
STATE_FIELDS = ["path", "generation", "phase", "active_improver", "active_task", "pending_improver"]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def table(path, values, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    temporary.replace(path)


def one_field(text, name):
    found = re.findall(r"^" + re.escape(name) + r": (.+)\.$", text, re.M)
    if len(found) != 1:
        raise ValueError(f"Expected one readable field: {name}")
    return found[0]


def read_improver(path):
    text = path.read_text(encoding="utf-8")
    if text.count(SCHEDULE) != 1:
        raise ValueError("Unsupported proposal schedule")
    partition = one_field(text, "Decision partition")
    margin = float(one_field(text, "Minimum relative gain"))
    if partition not in {"training", "selection"} or margin not in {0.0, 0.15}:
        raise ValueError("Unsupported improver rule")
    return partition, margin


def read_task(path):
    text = path.read_text(encoding="utf-8")
    model, features = one_field(text, "Model family"), one_field(text, "Feature group")
    if model not in {"linear", "tree"} or features not in {"calendar", "all"}:
        raise ValueError("Unsupported task skill")
    return model, features


def task_text(model, features):
    return f"# Task research skill\n\nModel family: {model}.\nFeature group: {features}.\n\nUse the pinned bike task and seed 17. Fit preprocessing and the model on training rows only. Save row-aligned training and selection predictions with nonnegative rental estimates. Report MAE and failures. Do not access final rows for scoring or further selection.\n"


def check_sources(root, repo):
    for row in rows(root / "SOURCE-HASHES.csv"):
        actual = Path(__file__) if row["identity"] == "driver" else repo / row["relative_path"]
        if sha(actual) != row["sha256"]:
            raise ValueError(f"Source identity changed: {row['identity']}")
    if sha(root / "PROTOCOL.md") != (root / "PROTOCOL.sha256").read_text().strip():
        raise ValueError("Protocol changed")


def accepted_identity(root, state):
    generation = int(state["generation"])
    if generation == 0:
        expected = {"active_improver": "skills/IMPROVER-v0.md", "active_task": "skills/TASK-initial.md"}
    else:
        record = rows(root / state["path"] / f"generation-{generation}" / "DECISION.csv")
        if len(record) != 1:
            raise ValueError("Missing accepted decision")
        expected = record[0]
    for field in ["active_improver", "active_task"]:
        if state[field] != expected[field]:
            raise ValueError(f"Active ancestry disagrees with accepted decision: {field}")
        if generation and sha(root / state[field]) != expected[field + "_sha256"]:
            raise ValueError(f"Accepted instruction changed: {field}")
    if not generation:
        for row in rows(root / "INITIAL-SKILLS.csv"):
            if sha(root / row["path"]) != row["sha256"]:
                raise ValueError("Initial instruction changed")
    read_improver(root / state["active_improver"])
    read_task(root / state["active_task"])


def checkpoint(root, state, label):
    current = rows(root / "STATE.csv")
    current = [state if row["path"] == state["path"] else row for row in current]
    table(root / "STATE.csv", current, STATE_FIELDS)
    count = len([r for r in rows(root / "FITS.csv") if r["path"] == state["path"]])
    note = f"# {label}\n\nPath: {state['path']}. Completed generations: {state['generation']}. Phase: {state['phase']}.\n\nActive improver: {state['active_improver']}; SHA-256 {sha(root / state['active_improver'])}.\nActive task skill: {state['active_task']}; SHA-256 {sha(root / state['active_task'])}.\nPending improver: {state['pending_improver'] or 'none'}. A pending proposal is not active.\n\nCharged attempts: {count}. Limits: four for baseline, eight for recursive, two generations each.\n\nLearner predictions, quizzes, and teach-back: unattempted. Same author context.\n"
    write(root / state["path"] / "PROGRESS.md", note)
    write(root / state["path"] / "checkpoints" / f"{state['generation']}-{state['phase']}.md", note)


def initialize(root, repo, protocol):
    root.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(protocol, root / "PROTOCOL.md")
    write(root / "PROTOCOL.sha256", sha(root / "PROTOCOL.md") + "\n")
    sources = [("driver", Path(__file__).resolve()), ("runtime", repo / "rsi/tools/lab.py"),
               ("data", repo / "rsi/examples/bike-demand/source/hour.csv")]
    table(root / "SOURCE-HASHES.csv", [dict(identity=name, relative_path=str(path.relative_to(repo)).replace('\\','/'), sha256=sha(path)) for name,path in sources])
    shutil.copyfile(Path(__file__), root / "driver.source.py")
    shutil.copyfile(repo / "rsi/tools/lab.py", root / "runtime.source.py")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    from importlib.metadata import distributions
    table(root / "ENVIRONMENT.csv", sorted([dict(package=d.metadata['Name'], version=d.version) for d in distributions()], key=lambda r:r['package']))
    write(root / "SOURCE.md", f"# Execution source\n\nRepository commit: {commit}. Python: {sys.version}.\n\nExact source snapshots and hashes are retained. Data stays in its pinned repository source. The constrained interpreter recognizes explicit model, feature, partition, and margin instructions. It is not a general Markdown executor.\n")
    write(root / "skills/IMPROVER-v0.md", f"# Improver v0\n\n{SCHEDULE}\n\nDecision partition: training.\nMinimum relative gain: 0.\n\nFit and check the parent and proposed task skills under equal resources. Promote a child only when its MAE on the named partition is strictly lower and its relative reduction reaches the minimum. Keep the parent on a tie. Preserve failures, rejected skills, hashes, and costs. Stop at the generation limit. The outer evaluator remains fixed.\n")
    write(root / "skills/TASK-initial.md", task_text("linear", "calendar"))
    table(root / "INITIAL-SKILLS.csv", [dict(path=str(path.relative_to(root)).replace('\\','/'), sha256=sha(path)) for path in sorted((root / 'skills').glob('*.md'))])
    states = [dict(path=name, generation=0, phase="ready", active_improver="skills/IMPROVER-v0.md", active_task="skills/TASK-initial.md", pending_improver="") for name in ["baseline", "recursive"]]
    table(root / "STATE.csv", states, STATE_FIELDS)
    for state in states:
        checkpoint(root, state, "Prepared before any fit")
    print("Initialized two paths. No fits. Four baseline and eight recursive attempts maximum.")


def propose(root, state):
    if state["path"] != "recursive" or state["phase"] != "ready" or int(state["generation"]) >= 2:
        raise ValueError("Proposal not allowed in this phase or generation")
    generation = int(state["generation"]) + 1
    parent = root / state["active_improver"]
    before = parent.read_text(encoding="utf-8")
    old, new = (("Decision partition: training.", "Decision partition: selection.") if generation == 1
                else ("Minimum relative gain: 0.", "Minimum relative gain: 0.15."))
    if before.count(old) != 1:
        raise ValueError("The declared revision does not match the active parent")
    candidate = f"recursive/generation-{generation}/IMPROVER-proposal.md"
    revised = re.sub(r"^# [^\n]+", f"# Proposed improver, generation {generation}", before.replace(old,new,1), count=1)
    write(root / candidate, revised)
    read_improver(root / candidate)
    rationale = ("Earlier public runs exposed training-based promotion of an overfit model. Test selection-based promotion without changing proposals or the outer metric."
                 if generation == 1 else "Test whether a 15% margin filters small, noisy gains. It can also reject a useful gain. This margin is predeclared and author-chosen; no noise estimate supports it.")
    write(root / f"recursive/generation-{generation}/CHANGE-PROPOSAL.md", f"# Candidate improver edit\n\n{rationale}\n\nRead parent: {state['active_improver']}; SHA-256 {sha(parent)}.\n\nChange: {old} → {new}\n\nCandidate SHA-256: {sha(root/candidate)}. External rule, task, source, model menu, and four-fit generation allowance remain fixed. Reject the revision when its retained task skill has no strict selection-MAE advantage.\n\nProposal authoring is guided by this recorded schedule, not autonomous invention. The next process must evaluate before promotion.\n")
    state["pending_improver"] = candidate
    state["phase"] = "proposed"
    checkpoint(root,state,"Stopped after proposal; no promotion")
    print(f"Generation {generation} proposed. Active improver unchanged: {state['active_improver']}.")


def fit_worker(root, repo, lab, attempt):
    matching = [r for r in rows(root / "FITS.csv") if r["attempt"] == str(attempt)]
    if len(matching) != 1 or matching[0]["status"] != "running":
        raise ValueError("Fit has no reserved running attempt")
    entry = matching[0]
    folder = root / entry["output"]
    folder.mkdir(parents=True, exist_ok=False)
    model, features = read_task(root / entry["skill"])
    data = lab.read_data("bike")
    masks = lab.partitions(data,"bike")
    names = lab.feature_names("bike",features,data)
    fitted = lab.pipeline("bike",model,names,17)
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        fitted.fit(data.loc[masks['train'],names],data.loc[masks['train'],'cnt'])
        elapsed = time.perf_counter()-started
        measured=[]
        for label,part in [('training','train'),('selection','selection')]:
            values=np.maximum(0,fitted.predict(data.loc[masks[part],names]))
            result=pd.DataFrame(dict(source_row=np.flatnonzero(masks[part]),target=data.loc[masks[part],'cnt'].to_numpy(),prediction=values))
            result.to_csv(folder/f'{label}-predictions.csv',index=False)
            measured.append(dict(partition=label,mae=float(mean_absolute_error(result.target,result.prediction))))
    table(folder/'SCORES.csv',measured)
    table(folder/'COST.csv',[dict(fits=1,fit_seconds=elapsed,inference_cost='unknown')])
    write(folder/'EXECUTION.md', f"# Actual fit\n\nTask skill: {entry['skill']}; SHA-256 {sha(root/entry['skill'])}.\nModel: {model}; features: {features}; seed: 17. Training rows: {int(masks['train'].sum())}; selection rows: {int(masks['selection'].sum())}. No final predictions.\n\nFit seconds: {elapsed:.9f}. Other execution and inference costs are separate.\n")
    print(measured)


def checked_scores(root, lab, folder):
    data=lab.read_data('bike')
    masks=lab.partitions(data,'bike')
    values={}
    for label,part in [('training','train'),('selection','selection')]:
        result=pd.read_csv(folder/f'{label}-predictions.csv')
        if list(result.columns)!=['source_row','target','prediction'] or not np.array_equal(result.source_row,np.flatnonzero(masks[part])):
            raise ValueError('Prediction row identity mismatch')
        if not np.array_equal(result.target,data.loc[masks[part],'cnt']) or not np.isfinite(result.prediction).all():
            raise ValueError('Invalid target or prediction')
        values[label]=float(mean_absolute_error(result.target,result.prediction))
    reported={r['partition']:float(r['mae']) for r in rows(folder/'SCORES.csv')}
    if any(abs(values[k]-reported[k])>1e-9 for k in values):
        raise ValueError('Reported metric differs from predictions')
    write(folder/'CHECK.md','# Executed evidence check\n\nTraining and selection identities and targets match the pinned source. Predictions are finite. MAE recomputes and agrees with the score table. No final predictions were produced.\n')
    return values


def run_fit(root, repo, lab, state, generation, arm, role, skill):
    entries=rows(root/'FITS.csv')
    owned=[r for r in entries if r['path']==state['path']]
    limit=4 if state['path']=='baseline' else 8
    per_generation=2 if state['path']=='baseline' else 4
    if len(owned)>=limit or len([r for r in owned if int(r['generation'])==generation])>=per_generation or len(entries)>=12:
        raise ValueError('Fit budget exhausted before launch')
    if any(r['status']!='success' for r in entries):
        raise ValueError('Unresolved earlier attempt; inspect before continuation')
    attempt=len(entries)+1
    output=f"{state['path']}/generation-{generation}/{arm}/{role}"
    entry=dict(attempt=attempt,path=state['path'],generation=generation,arm=arm,role=role,skill=skill,output=output,status='running',exit_status='',wall_seconds='')
    entries.append(entry)
    table(root/'FITS.csv',entries)
    command=[sys.executable,str(Path(__file__).resolve()),'--repo',str(repo),'--workspace',str(root),'--action','fit','--attempt',str(attempt)]
    start=time.perf_counter()
    try:
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=60)
        code,stdout,stderr=result.returncode,result.stdout,result.stderr
    except subprocess.TimeoutExpired as error:
        code,stdout,stderr=124,str(error.stdout),str(error.stderr)
    elapsed=time.perf_counter()-start
    entry.update(status='success' if code==0 else 'failed',exit_status=code,wall_seconds=elapsed)
    table(root/'FITS.csv',entries)
    write(root/'commands'/f'fit-{attempt:02}.md',f"# Fit {attempt}\n\nArguments: {command!r}\n\nExit: {code}. Wall seconds: {elapsed:.9f}.\n\n```text\n{stdout}\n{stderr}\n```\n")
    if code:
        raise RuntimeError(f'Fit {attempt} failed; evidence and charged attempt preserved')
    return checked_scores(root,lab,root/output)


def compare(root, repo, lab, state):
    generation=int(state['generation'])+1
    if generation>2 or (state['path']=='recursive' and state['phase']!='proposed') or (state['path']=='baseline' and state['phase']!='ready'):
        raise ValueError('Comparison refused: generation limit or missing proposal')
    parent_task=state['active_task']
    model,features=read_task(root/parent_task)
    # The exact supported schedule was read from the active instruction above.
    read_improver(root/state['active_improver'])
    child_task=f"{state['path']}/generation-{generation}/TASK-proposal.md"
    write(root/child_task,task_text('tree' if generation==1 else model,'calendar' if generation==1 else 'all'))
    arms=[('active',state['active_improver'])]
    if state['path']=='recursive':
        arms.append(('proposed',state['pending_improver']))
    outcomes=[]
    for arm,improver in arms:
        partition,margin=read_improver(root/improver)
        before=f"# Inherited instruction before fits\n\nGeneration: {generation}. Arm: {arm}.\nRead improver: {improver}; SHA-256 {sha(root/improver)}.\nRead task parent: {parent_task}; SHA-256 {sha(root/parent_task)}.\nProposed task: {child_task}; SHA-256 {sha(root/child_task)}.\n\nApplied schedule: {SCHEDULE}\nApplied decision: strictly lower {partition} MAE and relative reduction at least {margin}.\n\nThis instruction is read before the two fits, not attached only after a result.\n"
        write(root/state['path']/f'generation-{generation}'/arm/'BEFORE.md',before)
        scores={role:run_fit(root,repo,lab,state,generation,arm,role,skill) for role,skill in [('parent',parent_task),('child',child_task)]}
        parent,child=scores['parent'][partition],scores['child'][partition]
        gain=(parent-child)/parent if parent else 0.0
        promote=child<parent and gain>=margin
        retained=child_task if promote else parent_task
        outcome=dict(arm=arm,improver=improver,improver_sha256=sha(root/improver),partition=partition,minimum_relative_gain=margin,parent_training=scores['parent']['training'],child_training=scores['child']['training'],parent_selection=scores['parent']['selection'],child_selection=scores['child']['selection'],promoted=promote,retained_task=retained,retained_selection=scores['child' if promote else 'parent']['selection'])
        outcomes.append(outcome)
    folder=root/state['path']/f'generation-{generation}'
    table(folder/'ARM-DECISIONS.csv',outcomes)
    if len(arms)==2:
        for role in ['parent','child']:
            for part in ['training','selection']:
                if sha(folder/'active'/role/f'{part}-predictions.csv')!=sha(folder/'proposed'/role/f'{part}-predictions.csv'):
                    raise ValueError('Matched arm predictions differ')
    selected=outcomes[0]
    changed=len(outcomes)==2 and outcomes[1]['retained_selection']<selected['retained_selection']
    if changed:
        selected=outcomes[1]
    decision=dict(generation=generation,parent_improver=state['active_improver'],proposed_improver=state['pending_improver'],active_improver=selected['improver'],active_improver_sha256=sha(root/selected['improver']),parent_task=parent_task,active_task=selected['retained_task'],active_task_sha256=sha(root/selected['retained_task']),selected_arm=selected['arm'],improver_promoted=changed,retained_selection=selected['retained_selection'])
    table(folder/'DECISION.csv',[decision])
    write(folder/'DECISION.md',f"# Retained versions\n\nExternal rule: strictly lower selection MAE of the retained task skill; keep active improver on a tie.\n\nSelected arm: {selected['arm']}. Improver proposal accepted: {changed}. Retained selection MAE: {selected['retained_selection']:.9f}.\n\nActive improver: {selected['improver']}. Active task skill: {selected['retained_task']}.\n\nThis is development selection on a known public task, not independent final evidence.\n")
    state.update(generation=generation,phase='done' if generation==2 else 'ready',active_improver=selected['improver'],active_task=selected['retained_task'],pending_improver='')
    checkpoint(root,state,'Generation evaluated and checkpointed')
    print(decision)


def audit(root):
    states=rows(root/'STATE.csv')
    if any(int(s['generation'])!=2 or s['phase']!='done' for s in states):
        raise ValueError('Both two-generation paths must finish before this audit')
    for state in states:
        accepted_identity(root,state)
    fits=rows(root/'FITS.csv')
    if len(fits)!=12 or any(row['status']!='success' for row in fits):
        raise ValueError('Expected twelve retained successful attempts under the fixed protocol')
    baseline=[rows(root/'baseline'/f'generation-{g}'/'ARM-DECISIONS.csv')[0] for g in [1,2]]
    if baseline[0]['improver_sha256']!=baseline[1]['improver_sha256']:
        raise ValueError('Fixed improver changed')
    accepted=rows(root/'recursive/generation-1/DECISION.csv')[0]
    inherited=rows(root/'recursive/generation-2/ARM-DECISIONS.csv')[0]
    if inherited['improver_sha256']!=accepted['active_improver_sha256']:
        raise ValueError('Second generation did not inherit the accepted improver')
    results=[]
    for state in states:
        for g in [1,2]:
            for row in rows(root/state['path']/f'generation-{g}'/'ARM-DECISIONS.csv'):
                results.append(dict(path=state['path'],generation=g,**row))
    table(root/'RESULTS.csv',results)
    bad=dict(states[1],active_improver='skills/IMPROVER-v0.md')
    # If v0 happened to remain active, use the archived pending candidate instead.
    if bad['active_improver']==states[1]['active_improver']:
        bad['active_improver']='recursive/generation-2/IMPROVER-proposal.md'
    table(root/'diagnostics/invalid-active-state.csv',[bad],STATE_FIELDS)
    try:
        accepted_identity(root,bad)
    except ValueError as error:
        write(root/'diagnostics/ACTIVE-POINTER-REFUSAL.md',f'# Executed diagnostic refusal\n\n{error}\n\nOnly the diagnostic state was altered; real STATE.csv is unchanged. No fit ran.\n')
    else:
        raise ValueError('Invalid active pointer was not refused')
    # The baseline extra asks for a rejected-child replay; label a verdict mutation
    # when both actual edits were accepted instead of inventing a real rejection.
    rejected=next((row for row in baseline if row['promoted']=='False'),None)
    g=baseline.index(rejected)+1 if rejected else 2
    actual=baseline[g-1]
    actual_decision=rows(root/'baseline'/f'generation-{g}'/'DECISION.csv')[0]
    proposed=f'baseline/generation-{g}/TASK-proposal.md'
    fixture=dict(generation=g,verdict='reject',expected_active=actual_decision['parent_task'],invalid_active=proposed,origin='actual rejected child' if rejected else 'labelled mutation of an accepted verdict')
    table(root/'diagnostics/rejected-child-replay.csv',[fixture])
    if fixture['invalid_active']==fixture['expected_active']:
        raise ValueError('The ancestry diagnostic is not a distinct child')
    write(root/'diagnostics/REJECTED-CHILD-REPLAY.md',f"# Labelled ancestry replay\n\nOrigin: {fixture['origin']}. A rejection must retain {fixture['expected_active']}. Activating {fixture['invalid_active']} contradicts that verdict. The mismatch was checked. Real promotion records and state are unchanged. No fit ran.\n")
    costs=[dict(path=r['path'],generation=r['generation'],attempt=r['attempt'],**rows(root/r['output']/'COST.csv')[0],wall_seconds=r['wall_seconds']) for r in fits]
    table(root/'COSTS.csv',costs)
    write(root/'AUDIT.md',f"# Executed two-generation audit\n\nTwelve fits: four baseline and eight recursive. Both paths stop after generation 2. Baseline improver hashes match across rounds. Recursive generation 2 reads the accepted generation-1 improver hash. Matched arms produce identical prediction bytes before their different internal decisions. Saved scores recompute from row-aligned source targets.\n\nFit seconds: {sum(float(r['fit_seconds']) for r in costs):.9f}. Child-process wall seconds: {sum(float(r['wall_seconds']) for r in costs):.9f}. Fit time is inside wall time; do not add them. Authoring and inference costs are unknown.\n\nInvalid active ancestry and a rejected-child replay were checked without altering real state. No final predictions, independent contexts, learner responses, or acceleration claim. The source-guided proposals and unchanged outer controller limit the recursive claim.\n")
    print('Audited twelve fits, two lineages, inherited instructions, and two diagnostic checks.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--protocol',type=Path)
    parser.add_argument('--action',choices=['init','propose','compare','fit','audit','status'],required=True)
    parser.add_argument('--path',choices=['baseline','recursive'])
    parser.add_argument('--attempt',type=int)
    args=parser.parse_args()
    repo,root=args.repo.resolve(),args.workspace.resolve()
    spec=importlib.util.spec_from_file_location('generation_lab',repo/'rsi/tools/lab.py')
    lab=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    if args.action=='init':
        if args.protocol is None:
            parser.error('Initialization needs the predeclared protocol')
        initialize(root,repo,args.protocol.resolve())
        return
    check_sources(root,repo)
    if args.action=='fit':
        fit_worker(root,repo,lab,args.attempt)
        return
    with lab.workspace_lock(root):
        states=rows(root/'STATE.csv')
        for state in states:
            accepted_identity(root,state)
        if args.action=='audit':
            audit(root)
        elif args.action=='status':
            print(states)
        else:
            if args.path is None:
                parser.error('Name a path for this action')
            state=next(s for s in states if s['path']==args.path)
            if args.action=='propose':
                propose(root,state)
            else:
                compare(root,repo,lab,state)


if __name__=='__main__':
    main()
