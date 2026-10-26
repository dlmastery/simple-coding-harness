"""Bounded author walkthrough; students invoke Markdown skills, not this driver."""
import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['inner', 'outer', 'roles', 'seal'])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[3]
out = args.output.resolve()
if out == repo or repo in out.parents:
    raise SystemExit('Use a sibling workspace')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, body):
    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.rstrip() + '\n', encoding='utf-8', newline='\n')

def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))

def table(name, columns, values):
    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(columns)
        writer.writerows(values)

def absent(name):
    if (out / name).exists():
        raise SystemExit('Preserve existing phase: ' + name)

def command(label, parts):
    start = time.perf_counter()
    try:
        result = subprocess.run([sys.executable, *map(str, parts)], cwd=repo,
                                capture_output=True, text=True, timeout=60)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, str(error.stdout or ''), '60-second timeout; preserve attempt'
    elapsed = time.perf_counter() - start
    save('commands/' + label + '.md', f'# {label}\n\nExit: {code}\nWall seconds: {elapsed:.9f}\n\nStdout:\n{stdout}\nStderr:\n{stderr or "(empty)"}')
    with (out / 'COMMANDS.csv').open('a', encoding='utf-8', newline='') as stream:
        csv.writer(stream, lineterminator='\n').writerow([label, code, elapsed])
    if code:
        raise SystemExit('Command failed; inspect preserved output: ' + label)

def policy(path):
    fields = dict(line.split(': ', 1) for line in path.read_text().splitlines() if ': ' in line)
    order = fields['Order'].split()
    if len(order) != 4 or set(order) != {'draft', 'refine', 'explore', 'enrich'}:
        raise SystemExit('Invalid policy')
    return order

def propose(operator, parent):
    if operator == 'draft':
        return ('constant', 'calendar')
    if parent is None:
        raise SystemExit('Operator requires a retained parent')
    model, features = parent['model'], parent['features']
    if operator == 'refine': return ('linear', features)
    if operator == 'explore': return ('tree', features)
    if operator == 'enrich': return (model, 'all')
    raise SystemExit('Unknown operator')

def verify_sources():
    for row in rows(out / 'SOURCE-HASHES.csv'):
        if sha(repo / row['path']) != row['sha256']:
            raise SystemExit('Source changed: ' + row['path'])

def search(label, policy_path, allocation):
    verify_sources()
    folder = out / label
    folder.mkdir(parents=True, exist_ok=False)
    frozen = sha(policy_path)
    order = policy(policy_path)
    retained = None
    trace = []
    for index, operator in enumerate(order[:allocation], 1):
        model, features = propose(operator, retained)
        parent = retained['candidate'] if retained else 'root'
        save(f'{label}/before-{index:02d}.md', f'# Before attempt {index}\n\nOperator: {operator}\nParent: {parent}\nModel: {model}\nFeatures: {features}\nRemaining including this attempt: {allocation-index+1}\nPolicy SHA-256: {frozen}\nSelection rule: lower MAE; a tie keeps the earlier candidate.')
        command(label.replace('/', '-') + f'-fit-{index}', [repo / 'rsi/tools/lab.py', 'run', '--task', 'bike', '--workspace', folder / 'experiment', '--model', model, '--features', features, '--seed', '17', '--attempt-limit', str(allocation), '--policy', policy_path, '--hypothesis', f'{operator} applied to {parent}: test {model}/{features} under the fixed operator procedure.'])
        history = rows(folder / 'experiment/trials.csv')
        row = history[-1]
        candidate = folder / 'experiment' / row['candidate']
        command(label.replace('/', '-') + f'-check-{index}', [repo / 'rsi/tools/check_result.py', candidate, '--report', candidate / 'CHECK.md'])
        if row['status'] != 'ok' or len(history) != index or row['policy_sha256'] != frozen or sha(policy_path) != frozen:
            raise SystemExit('Search provenance mismatch')
        keep = retained is None or float(row['score']) < float(retained['score'])
        if keep: retained = row
        trace.append([index, operator, parent, row['candidate'], model, features, row['score'], row['seconds'], 'retained' if keep else 'rejected', retained['candidate'], frozen])
        table(f'{label}/TRACE.csv', ['attempt', 'operator', 'parent', 'candidate', 'model', 'features', 'selection_mae', 'fit_seconds', 'decision', 'retained_after', 'policy_sha256'], trace)
    save(f'{label}/RETAINED.md', f'# Selected recipe\n\nCandidate: {retained["candidate"]}\nModel: {retained["model"]}\nFeatures: {retained["features"]}\nSelection MAE: {retained["score"]}\nPolicy SHA-256: {frozen}\nAll {allocation} attempts count. No final evaluation occurred.')
    return retained

if args.phase == 'inner':
    if out.exists(): raise SystemExit('Preserve existing workspace')
    out.mkdir()
    shutil.copyfile(__file__, out / 'run-aide-labs.py')
    shutil.copyfile(repo / 'how-did-i-generate-it/rsi/validation/AIDE-LABS-PROTOCOL.md', out / 'PROTOCOL.md')
    save('COMMANDS.csv', 'action,exit,wall_seconds')
    paths = ['rsi/tools/lab.py', 'rsi/tools/check_result.py', 'rsi/examples/bike-demand/source/hour.csv', 'how-did-i-generate-it/rsi/scripts/run-aide-labs.py']
    table('SOURCE-HASHES.csv', ['path', 'sha256'], [(p, sha(repo / p)) for p in paths])
    save('ALLOCATION.md', '# Declared before fitting\n\n10.13: four fits. 10.14: three fits per arm, six total. 10.15: zero fits. Total: ten. Data inspection and prediction checks add measured subprocess time. Author and provider costs are unknown. No final evaluation.')
    save('procedures/R0.md', '# Fixed inner researcher R0\n\nOrder: draft refine explore enrich\nParent: retained candidate with lowest selection MAE; tie keeps earlier\nRetention: lower selection MAE; failed attempts remain in budget\nDefault fit allowance: 4\nComparison fit allowance: 3\n\nDraft fits constant/calendar. Refine changes model to linear. Explore changes model to tree. Enrich changes inputs to all permitted calendar and weather fields. Each non-draft operator uses the retained parent. No operator edits this procedure. The controller implements these readable instructions; the fit tool alone does not propose work.')
    command('inspect-bike', [repo / 'rsi/tools/lab.py', 'inspect', '--task', 'bike', '--workspace', out / 'data-inspection'])
    search('10-13', out / 'procedures/R0.md', 4)
    known = {(r['model'], r['features']): r for r in rows(out / '10-13/experiment/trials.csv')}
    retained = None
    replay = []
    for operator in ['draft', 'refine', 'enrich', 'explore']:
        recipe = propose(operator, retained)
        row = known.get(recipe)
        if row is None:
            replay.append([operator, *recipe, 'unknown', 'unobserved recipe; stop'])
            break
        if retained is None or float(row['score']) < float(retained['score']): retained = row
        replay.append([operator, *recipe, row['score'], 'recorded deterministic recipe'])
    table('10-13/REPLAY.csv', ['operator', 'model', 'features', 'selection_mae', 'status'], replay)
    save('10-13/PAUSE.md', '# Read the trace before proposing R1\n\nFour fits used. Replay ran zero fits and cannot answer an unobserved recipe. Write OUTER-PROPOSAL.md and procedures/R1.md before the comparison. The author has prior exposure to bike outcomes; this is development, not a fresh evaluation.')
    print((out / '10-13/TRACE.csv').read_text())
elif args.phase == 'outer':
    absent('10-14')
    for name in ['OUTER-PROPOSAL.md', 'procedures/R1.md']:
        if not (out / name).exists(): raise SystemExit('Actor proposal required: ' + name)
    names = ['procedures/R0.md', 'procedures/R1.md', 'OUTER-PROPOSAL.md']
    frozen = [(name, sha(out / name)) for name in names]
    table('COMPARISON-FREEZE.csv', ['path', 'sha256'], frozen)
    save('ROLE-ADAPTER.md', '# Shared mechanical role adapter\n\nFrozen before the comparison. Copy T0 = draft refine explore. Replace only its third operator with the frozen proposer third operator. One projection per proposer. This fixed adapter exposes operator preference; it is not autonomous researcher code generation.\nFixture A: linear/calendar retained, tree/calendar already visited, one slot remains.\nFixture B: linear/calendar retained, linear/all already visited, one slot remains.\nFixture C: linear/calendar retained, no slot remains.\nCheck: unseen valid proposal when a slot remains; otherwise stop. A duplicate is a refusal, not a successful new proposal. No model score is available.')
    save('ROLE-ADAPTER-SHA256.md', '# Frozen adapter\n\nSHA-256: ' + sha(out / 'ROLE-ADAPTER.md'))
    result = []
    for researcher in ['R0', 'R1']:
        retained = search('10-14/' + researcher, out / f'procedures/{researcher}.md', 3)
        ledger = rows(out / f'10-14/{researcher}/experiment/trials.csv')
        result.append([researcher, retained['candidate'], retained['score'], len(ledger), sum(float(r['seconds']) for r in ledger)])
    for name, digest in frozen:
        if sha(out / name) != digest: raise SystemExit('Frozen proposal changed')
    table('10-14/COMPARISON.csv', ['researcher', 'retained', 'selection_mae', 'fits', 'all_fit_seconds'], result)
    save('10-14/UNEQUAL-BUDGET.md', '# Unexecuted budget illustration\n\nParent allowance: 3 fits. Child allowance: 6 fits. Child outcome: unknown. Additional fits executed: 0.\n\nEven a better child score in this separate design could reflect more attempts. The actual comparison used 3 each. There is no fabricated score for the six-fit child.')
    print((out / '10-14/COMPARISON.csv').read_text())
elif args.phase == 'roles':
    absent('10-15')
    verify_sources()
    for row in rows(out / 'COMPARISON-FREEZE.csv'):
        if sha(out / row['path']) != row['sha256']: raise SystemExit('Frozen producer changed')
    expected = (out / 'ROLE-ADAPTER-SHA256.md').read_text().split('SHA-256: ')[1].strip()
    if sha(out / 'ROLE-ADAPTER.md') != expected: raise SystemExit('Adapter changed')
    save('10-15/IGNITION-PLAN.md', (out / 'ROLE-ADAPTER.md').read_text() + '\n\nEach producer is frozen from the matched search. Its third preference is projected into T0 under the same adapter. Two proposal calls; three fixtures each. Zero fits. Producer instructions and adapter were author-designed. This cannot establish a general capability to improve researchers.')
    save('10-15/T0.md', '# Identical target for both producers\n\nOrder: draft refine explore\nOnly the third slot may change; evaluation, parent selection, and budget remain fixed.')
    proposals, checks = [], []
    parent = {'model': 'linear', 'features': 'calendar'}
    for researcher in ['R0', 'R1']:
        start = time.perf_counter()
        producer = out / f'procedures/{researcher}.md'
        operation = policy(producer)[2]
        body = '# Projected target proposal\n\nOrder: draft refine ' + operation + '\nProducer: ' + researcher + '\nProducer SHA-256: ' + sha(producer) + '\nTarget SHA-256: ' + sha(out / '10-15/T0.md') + '\nAdapter SHA-256: ' + expected
        save(f'10-15/{researcher}/PROPOSAL.md', body)
        proposals.append([researcher, operation, time.perf_counter() - start, sha(out / f'10-15/{researcher}/PROPOSAL.md')])
        # Read the proposed artifact, rather than substituting an earlier task score.
        fields = dict(line.split(': ', 1) for line in (out / f'10-15/{researcher}/PROPOSAL.md').read_text().splitlines() if ': ' in line)
        proposed_operator = fields['Order'].split()[2]
        for case, visited, remaining in [('A', {('linear', 'calendar'), ('tree', 'calendar')}, 1), ('B', {('linear', 'calendar'), ('linear', 'all')}, 1), ('C', {('linear', 'calendar')}, 0)]:
            start = time.perf_counter()
            recipe = propose(proposed_operator, parent) if remaining else None
            outcome = 'correct stop' if not remaining else ('duplicate refused' if recipe in visited else 'valid unseen proposal')
            passed = outcome != 'duplicate refused'
            checks.append([researcher, case, remaining, proposed_operator, '/'.join(recipe) if recipe else 'none', outcome, int(passed), time.perf_counter() - start])
    table('10-15/PROPOSALS.csv', ['producer', 'third_operator', 'projection_seconds', 'proposal_sha256'], proposals)
    table('10-15/FIXTURES.csv', ['producer', 'case', 'remaining', 'operator', 'recipe', 'outcome', 'expected_behavior_pass', 'decision_seconds'], checks)
    start = time.perf_counter()
    requested_children, slots = 5, 1
    refused = requested_children > slots
    table('10-15/OVERCOMPLICATION.csv', ['requested_children', 'remaining_slots', 'outcome', 'check_seconds', 'model_fits'], [[requested_children, slots, 'refused' if refused else 'accepted', time.perf_counter() - start, 0]])
    save('10-15/OVERCOMPLICATION.md', '# Separate constructed counterexample\n\nSuppose an optimizer has an excellent earlier task score but always proposes five simultaneous child branches. With one remaining slot, this proposal fails the fixed budget rule. The check executed only the comparison 5 > 1; no agent learned this behavior and no children were fitted. Task skill alone cannot certify a feasible improver.')
    print((out / '10-15/FIXTURES.csv').read_text())
elif args.phase == 'seal':
    absent('MANIFEST.csv')
    verify_sources()
    ledgers = [out / '10-13/experiment/trials.csv', out / '10-14/R0/experiment/trials.csv', out / '10-14/R1/experiment/trials.csv']
    counts = [len(rows(p)) for p in ledgers]
    if counts != [4, 3, 3]: raise SystemExit('Unexpected fit allocations')
    all_fits = [r for p in ledgers for r in rows(p)]
    if any(r['status'] != 'ok' for r in all_fits): raise SystemExit('Inspect unsuccessful fit')
    commands = rows(out / 'COMMANDS.csv')
    save('COST.md', f'# Measured and missing costs\n\nModel fits: {sum(counts)}\nRecorded fit seconds across all candidates: {sum(float(r["seconds"]) for r in all_fits):.9f}\nSubprocess commands: {len(commands)}\nSubprocess wall seconds: {sum(float(r["wall_seconds"]) for r in commands):.9f}\n\nFit time is included in subprocess wall time; do not add them. Proposal projections and fixture-decision times are recorded separately. Python startup, data inspection, and prediction checks are included in subprocess time. Author reasoning, provider inference, and total elapsed development time are unknown. Zero extra fits for replay, role fixtures, or unequal-budget illustration.')
    for name in ['10-13', '10-14', '10-15']:
        save(name + '/LAB-NOTE.md', '# Author walkthrough\n\nLearner prediction: not attempted. Teach-back: not attempted. Quiz: not attempted. Read the trace and claim audit for measured observations. This verifies local mechanisms, not teaching effectiveness or independent-agent behavior.')
    save('PROGRESS.md', '# Stopped at the declared budget\n\nAll phases completed. Ten fits used; zero remaining. No final evaluation. The role test used two projections, six decision fixtures, and one separate overcomplication check. No live subprocess remains. Retain rejected task recipes and duplicate proposals. Next: inspect the archive and publish without changing raw bytes.')
    table('MANIFEST.csv', ['path', 'bytes', 'sha256'], [(p.relative_to(out).as_posix(), p.stat().st_size, sha(p)) for p in sorted(out.rglob('*')) if p.is_file()])
    print((out / 'COST.md').read_text())
