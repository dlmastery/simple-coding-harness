"""Bounded graph fixtures and copied-report recovery: no training operation."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / 'rsi-work-2026-09-22-graph-reconciliation'
NODES = ['frame', 'inspect', 'split', 'fit', 'check', 'report']
EDGES = list(zip(NODES, NODES[1:]))


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def table(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def event(action, detail):
    path = OUT / 'EVENTS.csv'
    with path.open('a', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        if stream.tell() == 0:
            writer.writerow(['utc', 'action', 'detail'])
        writer.writerow([datetime.now(timezone.utc).isoformat(), action, detail])


def command(label, script, args, expected=0):
    argv = [sys.executable, '-B', str(script), *map(str, args)]
    started = datetime.now(timezone.utc).isoformat()
    event('command start', label)
    clock = time.perf_counter()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=60)
    except subprocess.TimeoutExpired as error:
        save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart: {started}\nTimeout: {error!r}\nInspect before recovery.\n')
        raise
    save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart: {started}\nEnd: {datetime.now(timezone.utc).isoformat()}\nExit: {result.returncode}\nExpected: {expected}\nWall seconds: {time.perf_counter()-clock}\n\n{result.stdout}{result.stderr}')
    event('command end', f'{label}: exit {result.returncode}')
    require(result.returncode == expected, f'{label}: unexpected exit; inspect before continuing')


def order_case(name):
    order = NODES if name == 'normal' else (['frame', 'inspect', 'split', 'check', 'fit', 'report'] if name == 'check-first' else ['frame', 'split', 'inspect', 'fit', 'check', 'report'])
    edges = [edge for edge in EDGES if name != 'edge-removed' or edge != ('inspect', 'split')]
    positions = {node: index for index, node in enumerate(order)}
    violated = [f'{a} -> {b}' for a, b in edges if positions[a] >= positions[b]]
    save(OUT / '03-01' / (name + '.md'), '# Ordering verdict\n\n' + f'Order: {" → ".join(order)}\n\nEdges: {edges!r}\n\nViolations: {violated!r}\n\n' + ('PASS for the supplied graph.\n' if not violated else 'REFUSED: predecessor occurs after its dependent action.\n'))
    print('PASS' if not violated else 'REFUSED: ' + ', '.join(violated))
    return 2 if violated else 0


def route_case(name):
    folder = OUT / '03-02'
    path = folder / ('absent.csv' if name in ('unknown', 'unsafe-unknown') else name + '.csv')
    state = 'unknown' if not path.exists() else ('valid' if 'cnt' in rows(path)[0] else 'invalid')
    accepted = state == 'valid' or (state == 'unknown' and name == 'unsafe-unknown')
    action = 'ready for modeling; no fit executed' if accepted else ('repair missing target' if state == 'invalid' else 'stop and obtain evidence')
    save(folder / (name + '-verdict.md'), f'# Routing verdict\n\nInput: {path.name}\nState: {state}\nPolicy: {"UNSAFE unknown means pass" if name == "unsafe-unknown" else "unknown means stop"}\nAction: {action}\nFit calls: 0\n')
    print(f'{state}: {action}')
    return 0 if accepted else 2


def validate_report(text):
    # The same function is used for every repair and recheck.
    return 'Candidate: trial-001' in text.splitlines()


def repair_case(name):
    folder = OUT / '03-04' / name
    report = '# Selection report\n\nMetric: MAE\n'
    used = 0
    history = []
    validator_hash = digest(Path(__file__))
    while True:
        save(folder / f'REPORT-{used}.md', report)
        valid = validate_report(report)
        history.append({'repairs_used': used, 'valid': valid, 'report_sha256': digest(folder / f'REPORT-{used}.md'), 'validator_source_sha256': validator_hash})
        table(folder / 'TRACE.csv', history)
        event('report check', f'{name}: repairs={used}, valid={valid}')
        if valid or used == 2:
            save(folder / 'STOP.md', '# Terminal state\n\n' + f'{"Valid report" if valid else "Repair budget exhausted"}. Repairs used: {used}; remaining: {2-used}.\n')
            print(f'{name}: valid={valid}, repairs={used}')
            return 0 if valid else 2
        used += 1
        save(folder / f'RESERVED-{used}.md', f'# Reserve before edit\n\nRepairs used: {used}\nRemaining: {2-used}\nFeedback: required Candidate: trial-001 line is missing.\nValidator source SHA256: {validator_hash}\n')
        event('repair reserved', f'{name}: slot {used} of 2')
        report += ('\nCandidate: trial-001\n' if name == 'effective' else f'\nTitle revision {used}; candidate ID still absent.\n')


def report_case(mode):
    folder = OUT / '03-05'
    if mode == 'fail':
        raise OSError('Declared teaching failure: report renderer unavailable')
    predictions = folder / 'diagnostic/trial-001/predictions.csv'
    identity = digest(predictions)
    score = float(rows(folder / 'diagnostic/trials.csv')[0]['score'])
    save(folder / 'RECOVERED-REPORT.md', f'# Recovered report\n\nSelection MAE: {score:.12f}\nPredictions SHA256: {identity}\nRead the separate RECOVERY-CHECK.md verdict before accepting this report.\nNo model fit requested.\n')
    print('Report rebuilt from saved checked artifacts.')
    return 0


def guard_case(name):
    folder = OUT / '03-05'
    path = folder / ('altered-predictions.csv' if name == 'altered' else 'diagnostic/trial-001/predictions.csv')
    expected = (folder / 'predictions.sha256').read_text().strip()
    accepted = digest(path) == expected
    save(folder / (name + '-dependency.md'), f'# Prediction dependency\n\nExpected SHA256: {expected}\nObserved SHA256: {digest(path)}\nVerdict: {"PASS" if accepted else "REFUSED: stale report for substituted prediction bytes"}\n')
    print('PASS' if accepted else 'REFUSED: changed prediction dependency')
    return 0 if accepted else 2


def main():
    require(not (OUT / 'STARTED.txt').exists(), 'Already started; do not repeat')
    save(OUT / 'STARTED.txt', datetime.now(timezone.utc).isoformat() + '\n')
    shutil.copyfile(Path(__file__), OUT / Path(__file__).name)
    old = REPO / 'rsi/evidence/2026-09-20/clean-journey'
    baseline = REPO / 'rsi/evidence/2026-09-22/fixed-process/01-02'
    source_paths = [old / '03-01/workflow.mmd', old / '03-01/workflow.png', old / '03-02/valid.csv', old / '03-02/missing-target.csv', REPO / 'rsi/tools/check_result.py', Path(__file__)]
    source_paths += [p for p in baseline.rglob('*') if p.is_file()]
    identities = [{'path': str(p), 'sha256': digest(p)} for p in source_paths]
    table(OUT / 'INPUT-IDENTITIES.csv', identities)
    for name in ('03-01', '03-02', '03-04', '03-05'):
        (OUT / name).mkdir(exist_ok=False)
    for filename in ('workflow.mmd', 'workflow.png'):
        shutil.copyfile(old / '03-01' / filename, OUT / '03-01' / filename)
    for name, expected in [('normal', 0), ('check-first', 2), ('split-first', 2), ('edge-removed', 0)]:
        command('order-' + name, Path(__file__), ['order', name], expected)
    for filename in ('valid.csv', 'missing-target.csv'):
        shutil.copyfile(old / '03-02' / filename, OUT / '03-02' / filename)
    for name, expected in [('valid', 0), ('missing-target', 2), ('unknown', 2), ('unsafe-unknown', 0)]:
        command('route-' + name, Path(__file__), ['route', name], expected)
    for name, expected in [('effective', 0), ('ineffective', 2)]:
        command('repair-' + name, Path(__file__), ['repair', name], expected)
    recovery = OUT / '03-05'
    shutil.copytree(baseline, recovery / 'diagnostic')
    predictions = recovery / 'diagnostic/trial-001/predictions.csv'
    ledger = recovery / 'diagnostic/trials.csv'
    before_predictions, before_ledger = digest(predictions), digest(ledger)
    save(recovery / 'predictions.sha256', before_predictions + '\n')
    command('report-failure', Path(__file__), ['report', 'fail'], 1)
    command('recovery-check', REPO / 'rsi/tools/check_result.py', [recovery / 'diagnostic/trial-001', '--report', recovery / 'RECOVERY-CHECK.md'])
    command('report-recovery', Path(__file__), ['report', 'recover'])
    altered = rows(predictions)
    old_value = altered[0]['prediction']
    altered[0]['prediction'] = str(float(old_value) + 1)
    table(recovery / 'altered-predictions.csv', altered)
    save(recovery / 'SUBSTITUTION.md', f'# Deliberate teaching copy\n\nOnly the first parsed prediction value changes: {old_value} → {altered[0]["prediction"]}. Originals stay unchanged. CSV serialization can also differ; the guard binds exact bytes, not semantic equivalence. No changed model fit is implied.\n')
    command('dependency-original', Path(__file__), ['guard', 'original'])
    command('dependency-altered', Path(__file__), ['guard', 'altered'], 2)
    descendants = {'split'}
    while True:
        expanded = descendants | {b for a, b in EDGES if a in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    save(recovery / 'INVALIDATION.md', '# Changed split: plan only\n\nAffected actions: ' + ', '.join(sorted(descendants)) + '. Predictions, metric checks and reports become stale for the changed split. Frame and inspection may be reused only if their own inputs remain unchanged. Old artifacts keep their original meaning. No descendant executes here.\n')
    effective = rows(OUT / '03-04/effective/TRACE.csv')
    ineffective = rows(OUT / '03-04/ineffective/TRACE.csv')
    checks = {
        'source inputs unchanged': all(digest(Path(r['path'])) == r['sha256'] for r in identities),
        'copied prediction unchanged': digest(predictions) == before_predictions,
        'copied one-fit ledger unchanged': digest(ledger) == before_ledger and len(rows(ledger)) == 1,
        'exactly one parsed prediction cell changed': sum(a[k] != b[k] for a, b in zip(rows(predictions), altered) for k in a) == 1,
        'effective repairs use one slot': [r['repairs_used'] for r in effective] == ['0', '1'] and effective[-1]['valid'] == 'True',
        'ineffective repairs use two slots': [r['repairs_used'] for r in ineffective] == ['0', '1', '2'] and ineffective[-1]['valid'] == 'False',
        'validator stays unchanged': all(r['validator_source_sha256'] == digest(Path(__file__)) for r in effective + ineffective),
        'split descendants complete': descendants == {'split', 'fit', 'check', 'report'},
        'unknown path remains absent': not (OUT / '03-02/absent.csv').exists(),
    }
    table(OUT / 'CHECKS.csv', [{'check': k, 'passed': v} for k, v in checks.items()])
    require(all(checks.values()), 'Post-run invariant failed')
    save(OUT / 'PROGRESS.md', '# Progress\n\nFifteen child commands completed with expected exits. Nine invariants pass. Zero new fits; copied baseline is not a new fit. Three repair slots used across two fixtures. No final evaluation or live child process. Learner responses unattempted.\n')
    print('15 commands, 9 invariants, 3 report repairs, zero new fits.')


if __name__ == '__main__':
    handlers = {'order': order_case, 'route': route_case, 'repair': repair_case, 'report': report_case, 'guard': guard_case}
    if len(sys.argv) > 1:
        raise SystemExit(handlers[sys.argv[1]](sys.argv[2]))
    main()
