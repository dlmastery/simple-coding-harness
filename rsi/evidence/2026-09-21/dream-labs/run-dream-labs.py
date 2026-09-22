"""Bounded author discovery and replay activities; never a full Dream-RSI implementation."""
import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time

repo=Path(__file__).resolve().parents[3]
out=repo.parent/'rsi-work-2026-09-21-dream-labs'
parser=argparse.ArgumentParser()
parser.add_argument('phase',choices=['baseline','branches','replay','online','worker','archive'])
parser.add_argument('--arm');parser.add_argument('--node')
args=parser.parse_args()

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,body):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(body.rstrip()+'\n',encoding='utf-8',newline='\n')
def absent(name):
    if (out/name).exists():raise SystemExit('Preserve existing phase: '+name)
def read_csv(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def table(name,columns,rows):
    path=out/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(columns);writer.writerows(rows)
def fields(path):return dict(line.split(': ',1) for line in path.read_text().splitlines() if ': ' in line)
def command(label,parts):
    start=time.perf_counter()
    try:
        result=subprocess.run([sys.executable,*map(str,parts)],cwd=repo,capture_output=True,text=True,timeout=60)
        code=result.returncode;stdout=result.stdout;stderr=result.stderr
    except subprocess.TimeoutExpired as exc:
        code=124;stdout=str(exc.stdout or '');stderr='60-second command timeout; preserve started attempt.'
    elapsed=time.perf_counter()-start
    save('commands/'+label+'.md',f'# {label}\n\nExit: {code}\nWall seconds: {elapsed:.9f}\n\nStdout:\n{stdout}\nStderr:\n{stderr or "(empty)"}')
    with (out/'COMMANDS.csv').open('a',encoding='utf-8',newline='') as stream:csv.writer(stream,lineterminator='\n').writerow([label,code,elapsed])
    if code:raise SystemExit('Command failed; preserve attempt: '+label)
def discovery_fit(node,model,index):
    command('discovery-'+node,[repo/'rsi/tools/lab.py','run','--task','bike','--workspace',out/'discovery/experiment','--model',model,'--features','all','--seed','17','--attempt-limit','3','--hypothesis',f'Node {node}: measure {model} with the same permitted inputs.'])
    candidate=out/f'discovery/experiment/trial-{index:03d}'
    command('check-'+node,[repo/'rsi/tools/check_result.py',candidate,'--report',candidate/'CHECK.md'])

if args.phase=='baseline':
    if out.exists():raise SystemExit('Preserve workspace')
    out.mkdir();shutil.copyfile(__file__,out/'run-dream-labs.py')
    shutil.copyfile(repo/'how-did-i-generate-it/rsi/validation/DREAM-LABS-PROTOCOL.md',out/'PROTOCOL.md')
    shutil.copyfile(repo/'how-did-i-generate-it/rsi/scripts/replay-discovery.py',out/'replay-discovery.py')
    save('COMMANDS.csv','action,exit,wall_seconds')
    save('ALLOCATION.md','# Before execution\n\nDiscovery: three fits in one experiment. Replay: zero fits. Online: two fits per policy, four total. Seven fits across these distinct tasks. Preserve failed attempts; no final evaluation on bike. Agent proposal cost is unknown.')
    table('SOURCE-HASHES.csv',['path','sha256'],[(p,sha(repo/p)) for p in ['rsi/tools/lab.py','rsi/tools/check_result.py','rsi/examples/bike-demand/source/hour.csv','how-did-i-generate-it/rsi/scripts/run-dream-labs.py','how-did-i-generate-it/rsi/scripts/replay-discovery.py']])
    table('discovery/PLAN.csv',['node','parent','model','features','status','mae'],[['R','','','','workspace',''],['A','R','constant','all','planned',''],['B','A','linear','all','planned',''],['C','A','tree','all','planned','']])
    discovery_fit('A','constant',1)
    save('discovery/PAUSE.md','# Read baseline before recording branches\n\nA has executed. B and C remain unexecuted. Read its result and write BRANCH-DECISION.md before continuing. The planned model alternatives and prior author exposure are already declared.')
    print((out/'discovery/experiment/trial-001/RESULT.md').read_text())
elif args.phase=='branches':
    absent('discovery/TREE.csv')
    decision=out/'discovery/BRANCH-DECISION.md'
    if not decision.exists():raise SystemExit('Actor branch decision required')
    ledger=read_csv(out/'discovery/experiment/trials.csv')
    if len(ledger)!=1 or ledger[0]['status']!='ok':raise SystemExit('Expected one completed baseline')
    for r in read_csv(out/'SOURCE-HASHES.csv'):
        if sha(repo/r['path'])!=r['sha256']:raise SystemExit('Source changed')
    frozen=sha(decision);save('discovery/DECISION-FREEZE.md','# Before B and C\n\nSHA-256: '+frozen)
    discovery_fit('B','linear',2);discovery_fit('C','tree',3)
    if sha(decision)!=frozen:raise SystemExit('Decision changed')
    ledger=read_csv(out/'discovery/experiment/trials.csv')
    rows=[['R','','workspace','','','','',0]]
    for node,r in zip(['A','B','C'],ledger):
        rows.append([node,'R' if node=='A' else 'A',r['status'],r['model'],r['features'],r['score'],'experiment/'+r['candidate']+'/RESULT.md',r['seconds']])
    rows.append(['D','B','proposed','forest','all','','',0])
    table('discovery/TREE.csv',['node','parent','status','model','features','mae','result','fit_seconds'],rows)
    save('discovery/FREEZE.md','# Frozen discovery history\n\nSHA-256: '+sha(out/'discovery/TREE.csv')+'\nD has no measured outcome. Zero fit seconds for D means no fit occurred, not zero proposal cost. Parent links record conceptual recipe ancestry; no parent workspace was resumed by a separate discovery agent.')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch
    fig,ax=plt.subplots(figsize=(12,6.5));fig.patch.set_facecolor('white');ax.set_axis_off();ax.set_xlim(0,1);ax.set_ylim(0,1)
    positions={'R':(.11,.5),'A':(.34,.5),'B':(.61,.74),'C':(.61,.25),'D':(.87,.74)}
    values={r[0]:r for r in rows}
    for node,parent in [('A','R'),('B','A'),('C','A'),('D','B')]:
        ax.add_patch(FancyArrowPatch(positions[parent],positions[node],arrowstyle='-|>',mutation_scale=16,linewidth=1.8,color='#607584',linestyle='--' if node=='D' else '-',shrinkA=45,shrinkB=47))
    for node,(x,y) in positions.items():
        r=values[node]
        label='R\nInitial workspace\nUnscored' if node=='R' else ('D\nForest proposal\nUNKNOWN; no fit' if node=='D' else f'{node}  {r[3]}/all\nMAE {float(r[5]):.2f}\n{float(r[7]):.3f} fit s')
        ax.text(x,y,label,ha='center',va='center',fontsize=11,color='#143047',bbox=dict(boxstyle='round,pad=.8',facecolor='#f1f7fa' if node!='D' else '#fff8eb',edgecolor='#397291',linestyle='--' if node=='D' else '-'))
    ax.text(.03,.97,'A tree backed by three measured attempts',fontsize=21,color='#143047',weight='bold',va='top')
    ax.text(.03,.89,'Bike demand · selection MAE · smaller is better · seed 17',fontsize=12,color='#4c6575')
    ax.text(.03,.05,'Solid arrows: recorded recipe ancestry. Dashed arrow: an unexecuted idea.\nThis is a classroom record, not the full Dream-RSI transition system.',fontsize=11,color='#4c6575')
    fig.savefig(out/'discovery/tree.png',dpi=180,bbox_inches='tight');fig.savefig(out/'discovery/tree.svg',bbox_inches='tight');plt.close(fig)
    print('Three fits and checks complete; tree frozen. D remains unknown.')
elif args.phase=='replay':
    absent('replay')
    tree=out/'discovery/TREE.csv'
    if sha(tree)!=fields(out/'discovery/FREEZE.md')['SHA-256']:raise SystemExit('Tree changed')
    save('replay/P0.md','# Fixed baseline policy\n\nOrder: A B\nAttempt units: 2\nRetention: lower selection MAE; tie keeps earlier node.\nRecipe choices are fixed; they do not inspect hidden node scores.')
    save('replay/P1.md','# Alternative policy\n\nOrder: A C\nAttempt units: 2\nRetention: lower selection MAE; tie keeps earlier node.\nRecipe choices are fixed; they do not inspect hidden node scores.')
    for policy in ['P0','P1']:
        command('replay-'+policy,[out/'replay-discovery.py','--tree',tree,'--policy',out/f'replay/{policy}.md','--output',out/f'replay/{policy}'])
    results=[(float(fields(out/f'replay/{p}/RESULT.md')['Best MAE']),p) for p in ['P0','P1']]
    winner=min(results)[1]
    save('replay/SELECTED.md',f'# Selection on the original recorded coverage\n\nSelected: {winner}\nRule: lower best visited MAE; ties keep P0.\nTree SHA-256: {sha(tree)}\nNo claim about unseen work. The author can inspect all archived outcomes; the fixed-order policy interface reveals only visited records.')
    save('replay/ABSENT.md','# Unsupported query\n\nOrder: A B E\nAttempt units: 3')
    command('replay-absent',[out/'replay-discovery.py','--tree',tree,'--policy',out/'replay/ABSENT.md','--output',out/'replay/absent'])
    removed=fields(out/f'replay/{winner}.md')['Order'].split()[-1]
    original=read_csv(tree);columns=list(original[0])
    table('replay/REDUCED.csv',columns,[[r[k] for k in columns] for r in original if r['node']!=removed and r['parent']!=removed])
    for policy in ['P0','P1']:
        command('coverage-'+policy,[out/'replay-discovery.py','--tree',out/'replay/REDUCED.csv','--policy',out/f'replay/{policy}.md','--output',out/f'replay/reduced-{policy}'])
    save('replay/COVERAGE.md',f'# Changed support, unchanged world\n\nRemoved node: {removed}\nOriginal selection: {winner}\nBoth fixed policies were replayed on the reduced copy. Unsupported requests return unknown; retained earlier outcomes remain available. Compare RESULT.md in reduced-P0 and reduced-P1. The original tree and selected policy remain unchanged. No new environment evidence was produced.')
    print('Selected '+winner+'; two primary replays, one absent query, two coverage replays; zero fits.')
elif args.phase=='worker':
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    if args.arm not in ['P0','P1'] or args.node not in ['A','B','C']:raise SystemExit('Unknown arm/node')
    folder=f'online/{args.arm}/{args.node}';absent(folder)
    freeze=fields(out/'online/FREEZE.md')
    for name in ['data.csv','P0.md','P1.md']:
        actual=out/'online/data.csv' if name=='data.csv' else out/'replay'/name
        if sha(actual)!=freeze[name]:raise SystemExit('Online input changed')
    order=fields(out/f'replay/{args.arm}.md')['Order'].split()
    completed=[p.name for p in (out/f'online/{args.arm}').glob('*/STARTED.md')] if (out/f'online/{args.arm}').exists() else []
    used=len(completed)
    if used>=2 or order[used]!=args.node:raise SystemExit('Order/budget mismatch')
    save(folder+'/STARTED.md',f'# Before fitting\n\nArm: {args.arm}\nNode: {args.node}\nPreviously attempted: {used}\nAllowance: 2\nPolicy SHA-256: {sha(out/f"replay/{args.arm}.md")}')
    data=pd.read_csv(out/'online/data.csv');columns=[f'x{i}' for i in range(6)]
    train=data[data.role=='train'];selection=data[data.role=='selection']
    model={'A':lambda:DummyRegressor(strategy='median'),'B':lambda:make_pipeline(StandardScaler(),Ridge(alpha=10)),'C':lambda:DecisionTreeRegressor(max_depth=8,min_samples_leaf=15,random_state=17)}[args.node]()
    start=time.perf_counter();model.fit(train[columns],train.target);elapsed=time.perf_counter()-start
    predictions=model.predict(selection[columns]);score=float(np.mean(np.abs(selection.target-predictions)))
    pd.DataFrame({'row_id':selection.row_id,'actual':selection.target,'predicted':predictions}).to_csv(out/folder/'selection.csv',index=False,lineterminator='\n')
    joblib.dump(model,out/folder/'model.joblib');save(folder+'/MODEL.sha256',sha(out/folder/'model.joblib'))
    save(folder+'/RESULT.md',f'# Online selection result\n\nMAE: {score:.12f}\nFit seconds: {elapsed:.9f}\nStatus: ok')
    print(f'{args.arm}/{args.node}: selection MAE {score:.9f}')
elif args.phase=='online':
    absent('online')
    import joblib
    import numpy as np
    import pandas as pd
    import sklearn
    selected=fields(out/'replay/SELECTED.md')['Selected']
    if selected not in ['P0','P1']:raise SystemExit('Missing replay selection')
    rng=np.random.default_rng(61009);x=rng.normal(size=(600,6));target=100+25*x[:,0]-18*x[:,1]+12*x[:,2]+rng.normal(0,3,600)
    data=pd.DataFrame(x,columns=[f'x{i}' for i in range(6)]);data.insert(0,'row_id',range(600));data['target']=target;data['role']=['train']*360+['selection']*120+['evaluation']*120
    save('online/CONTRACT.md','# New numerical task\n\nPredict a constructed continuous response from six normal inputs. Seed 61009; 600 rows split 360/120/120. Metric: MAE, smaller is better. The target formula and evaluation labels are visible to the author. This is new data, not a blind task. Both policies keep two fits and their fixed orders. No clipping rule is needed for this real-valued target; this differs from nonnegative bike counts. No model-weight changes occur in the coding agent.')
    data.to_csv(out/'online/data.csv',index=False,lineterminator='\n')
    frozen={name:sha(out/'online/data.csv' if name=='data.csv' else out/'replay'/name) for name in ['data.csv','P0.md','P1.md','SELECTED.md']}
    frozen['driver']=sha(Path(__file__))
    save('online/FREEZE.md','# Before online fits\n\n'+'\n'.join(k+': '+v for k,v in frozen.items())+f'\nSelected: {selected}\nPython: {sys.version.split()[0]}\nscikit-learn: {sklearn.__version__}')
    for arm in ['P0','P1']:
        for node in fields(out/f'replay/{arm}.md')['Order'].split():command('online-'+arm+'-'+node,[Path(__file__),'worker','--arm',arm,'--node',node])
    choices=[]
    for arm in ['P0','P1']:
        scores=[(float(fields(out/f'online/{arm}/{n}/RESULT.md')['MAE']),i,n) for i,n in enumerate(fields(out/f'replay/{arm}.md')['Order'].split())]
        score,_,node=min(scores);choices.append([arm,node,score])
    table('online/CHOICES.csv',['arm','node','selection_mae'],choices);choice_hash=sha(out/'online/CHOICES.csv')
    save('online/CHOICES-FREEZE.md','# Before evaluation\n\nSHA-256: '+choice_hash+'\nNo further fits or candidate choices permitted.')
    evaluation=data[data.role=='evaluation'];results=[]
    for arm,node,score in choices:
        folder=out/f'online/{arm}/{node}';model_path=folder/'model.joblib'
        if sha(model_path)!=(folder/'MODEL.sha256').read_text().strip():raise SystemExit('Local model changed')
        model=joblib.load(model_path)  # Trusted local output from this invocation only.
        prediction=model.predict(evaluation[[f'x{i}' for i in range(6)]])
        actual=float(np.mean(np.abs(evaluation.target-prediction)))
        report=pd.DataFrame({'row_id':evaluation.row_id,'actual':evaluation.target,'predicted':prediction})
        path=out/f'online/{arm}/evaluation.csv';report.to_csv(path,index=False,lineterminator='\n');reread=pd.read_csv(path)
        if list(reread.row_id)!=list(evaluation.row_id) or not np.allclose(reread.actual,evaluation.target,atol=1e-12,rtol=0) or abs(float(np.mean(np.abs(reread.actual-reread.predicted)))-actual)>1e-9:raise SystemExit('Evaluation mismatch')
        results.append([arm,node,score,actual])
    for name,expected in frozen.items():
        path=Path(__file__) if name=='driver' else (out/'online/data.csv' if name=='data.csv' else out/'replay'/name)
        if sha(path)!=expected:raise SystemExit('Frozen object changed')
    if sha(out/'online/CHOICES.csv')!=choice_hash:raise SystemExit('Choices changed')
    table('online/RESULTS.csv',['arm','node','selection_mae','evaluation_mae'],results)
    save('online/DONE.md','# Four fits complete\n\nPolicies, data, and selections stayed frozen. Evaluation row identities, targets, and scores agree. No evaluation refits. New synthetic data changes the task distribution; this is not a blind transfer benchmark. Write a separate unexecuted next-policy proposal.')
    print((out/'online/RESULTS.csv').read_text())
elif args.phase=='archive':
    if not (out/'online/NEXT-POLICY-PROPOSAL.md').exists():raise SystemExit('Actor proposal missing')
    absent('MANIFEST.csv')
    files=sorted(p for p in out.rglob('*') if p.is_file())
    table('MANIFEST.csv',['file','sha256'],[[p.relative_to(out).as_posix(),sha(p)] for p in files])
    print(f'Manifest retained {len(files)} files; no fits in archive phase.')
