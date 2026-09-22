"""Continue only the unexecuted substitution guards after the recorded field error."""
import importlib.util
from pathlib import Path
import shutil

source = Path('how-did-i-generate-it/rsi/scripts/run-graph-reconciliation.py').resolve()
spec = importlib.util.spec_from_file_location('original_graph_driver', source)
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
OUT = original.OUT
require, save, digest, rows, table = original.require, original.save, original.digest, original.rows, original.table
require((OUT / 'STARTED.txt').exists(), 'No started run to continue')
require(not (OUT / 'CONTINUATION-STARTED.txt').exists(), 'Continuation already attempted; inspect')
require(not (OUT / 'dependency-original-command.txt').exists(), 'Guard already executed')
require(not (OUT / 'dependency-altered-command.txt').exists(), 'Guard already executed')
require('KeyError' in (OUT / 'EXECUTION-FAILURE.txt').read_text(), 'Preserve the original failure first')
commands = list(OUT.glob('*-command.txt'))
require(len(commands) == 13, 'Unexpected earlier command count')
for command in commands:
    text = command.read_text(encoding='utf-8')
    fields = dict(line.split(': ', 1) for line in text.splitlines() if ': ' in line and line.split(': ', 1)[0] in ('Exit', 'Expected'))
    require(fields.get('Exit') == fields.get('Expected'), 'Earlier command did not match its expectation')
identities = rows(OUT / 'INPUT-IDENTITIES.csv')
require(all(digest(Path(r['path'])) == r['sha256'] for r in identities), 'An original input changed')
save(OUT / 'CONTINUATION-STARTED.txt', original.datetime.now(original.timezone.utc).isoformat() + '\n')
shutil.copyfile(Path(__file__), OUT / Path(__file__).name)
folder = OUT / '03-05'
predictions = folder / 'diagnostic/trial-001/predictions.csv'
ledger = folder / 'diagnostic/trials.csv'
before_ledger = digest(ledger)
data = rows(predictions)
require(list(data[0]) == ['source_row', 'actual', 'predicted', 'hour'], 'Unexpected prediction schema')
before = data[0]['predicted']
data[0]['predicted'] = str(float(before) + 1)
table(folder / 'altered-predictions.csv', data)
save(folder / 'SUBSTITUTION.md', f'# Deliberate teaching copy\n\nOnly the first parsed predicted value changes: {before} → {data[0]["predicted"]}. Original predictions and targets stay unchanged. CSV serialization may also differ; the guard binds exact bytes, not semantic equivalence. No new model fit.\n')
original.command('dependency-original', source, ['guard', 'original'])
original.command('dependency-altered', source, ['guard', 'altered'], 2)
descendants = {'split'}
while True:
    expanded = descendants | {b for a, b in original.EDGES if a in descendants}
    if expanded == descendants:
        break
    descendants = expanded
save(folder / 'INVALIDATION.md', '# Changed split: plan only\n\nAffected actions: ' + ', '.join(sorted(descendants)) + '. Predictions, metric checks and reports become stale for the changed split. Frame and inspection may be reused only if their own inputs remain unchanged. Old artifacts keep their original meaning. No descendant executes here.\n')
effective = rows(OUT / '03-04/effective/TRACE.csv')
ineffective = rows(OUT / '03-04/ineffective/TRACE.csv')
source_ledger = original.REPO / 'rsi/evidence/2026-09-22/fixed-process/01-02/trials.csv'
checks = {
    'source inputs unchanged': all(digest(Path(r['path'])) == r['sha256'] for r in identities),
    'copied prediction unchanged': digest(predictions) == (folder / 'predictions.sha256').read_text().strip(),
    'copied one-fit ledger unchanged': digest(ledger) == before_ledger == digest(source_ledger) and len(rows(ledger)) == 1,
    'exactly one parsed prediction cell changed': len(rows(predictions)) == len(data) and sum(a[k] != b[k] for a, b in zip(rows(predictions), data) for k in a) == 1,
    'effective repairs use one slot': [r['repairs_used'] for r in effective] == ['0', '1'] and effective[-1]['valid'] == 'True',
    'ineffective repairs use two slots': [r['repairs_used'] for r in ineffective] == ['0', '1', '2'] and ineffective[-1]['valid'] == 'False',
    'validator stays unchanged': all(r['validator_source_sha256'] == digest(source) for r in effective + ineffective),
    'split descendants complete': descendants == {'split', 'fit', 'check', 'report'},
    'unknown path remains absent': not (OUT / '03-02/absent.csv').exists(),
}
table(OUT / 'CHECKS.csv', [{'check': k, 'passed': v} for k, v in checks.items()])
require(all(checks.values()), 'Post-run invariant failed')
save(OUT / 'PROGRESS.md', '# Progress\n\nFifteen child commands completed with expected exits across original and continuation. The original parent failed after command 13 on the wrong prediction field name; retained code and failure are not a clean-pass claim. Continuation ran only the remaining two guards. Nine invariants pass. Zero new fits, three repairs across two fixtures. No live child process or final evaluation. Learner responses unattempted.\n')
print('Continuation completed two guards only; 15 total child commands and 9 invariants, zero new fits.')
