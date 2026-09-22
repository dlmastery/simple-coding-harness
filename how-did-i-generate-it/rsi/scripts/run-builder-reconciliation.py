"""One fresh bike fit; bounded refusals and read-only historical package checks."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / 'rsi-work-2026-09-22-builder-reconciliation'
OLD = REPO / 'rsi/evidence/2026-09-20/clean-journey'
TOOL = REPO / 'rsi/tools/lab.py'
CHECKER = REPO / 'rsi/tools/check_result.py'


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


def command(label, script, args, expected=0):
    argv = [sys.executable, '-B', str(script), *map(str, args)]
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=60)
    save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart: {started}\nEnd: {datetime.now(timezone.utc).isoformat()}\nExit: {result.returncode}\nExpected: {expected}\nWall seconds: {time.perf_counter()-clock}\nOutput:\n{result.stdout}{result.stderr}'.rstrip() + '\n')
    require(result.returncode == expected, f'{label} unexpected exit; preserve and inspect')


def recover(relative, wanted, filename):
    revisions = subprocess.run(['git', 'log', '-n', '60', '--format=%H', '--', relative], capture_output=True, check=True, text=True, timeout=60).stdout.splitlines()
    for revision in revisions:
        blob = subprocess.run(['git', 'show', revision + ':' + relative], capture_output=True, check=True, timeout=60).stdout
        if hashlib.sha256(blob).hexdigest() == wanted:
            path = OUT / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            return {'git_revision': revision, 'git_path': relative, 'sha256': wanted, 'saved_as': filename}
    raise RuntimeError('Historical source not recovered; inspect before fitting: ' + relative)


def identity_text(workspace, candidate):
    return f'- Workspace: {workspace.resolve()}\n- Candidate: {candidate}\n- Contract SHA256: {digest(workspace / "CONTRACT.md")}\n- Predictions SHA256: {digest(workspace / candidate / "predictions.csv")}\n- Verdict: PASS\n'


def main():
    require(not (OUT / 'STARTED.txt').exists(), 'Already started; do not repeat')
    save(OUT / 'STARTED.txt', datetime.now(timezone.utc).isoformat() + '\n')
    shutil.copyfile(Path(__file__), OUT / Path(__file__).name)
    recovered = [recover('rsi/skills/build-ml-harness/SKILL.md', '5a1e076b9c58cfed745ee2e29823eb6a090cfa664d974893188996625506a649', 'historical-source/BUILDER-SKILL.md'),
                 recover('rsi/tools/lab.py', '1febbe8eacac7873d9a09031cc133200e55224e2fea0205c88090eea4bd5b5a0', 'historical-source/lab.py')]
    table(OUT / 'RECOVERED-SOURCES.csv', recovered)
    paths = [TOOL, CHECKER, Path(__file__), REPO / 'rsi/skills/build-ml-harness/SKILL.md', REPO / 'rsi/examples/wine-quality/source/winequality-red.csv']
    for directory in [OLD / '06-01', OLD / '06-02', OLD / '06-05', OUT / 'package']:
        paths += [p for p in directory.rglob('*') if p.is_file()]
    paths += [OLD / 'HARNESS-EXECUTION.md', *[p for p in (OLD / 'harness-commands').glob('*.md')]]
    table(OUT / 'INPUT-IDENTITIES.csv', [{'path': str(p), 'sha256': digest(p)} for p in paths])
    generation = []
    for task, directory, brief in [('bike', '06-02', OLD / '06-01/HARNESS-BRIEF.md'), ('wine', '06-05', OLD / '06-05/HARNESS-BRIEF.md')]:
        package = OLD / directory / 'package'
        provenance = (package / 'PROVENANCE.md').read_text()
        for role, source in [('brief', brief), ('entry', package / 'run.py'), ('builder', OUT / 'historical-source/BUILDER-SKILL.md')]:
            generation.append({'task': task, 'role': role, 'sha256': digest(source), 'matches_record': digest(source) in provenance})
    table(OUT / 'GENERATION-CHECKS.csv', generation)
    require(all(r['matches_record'] for r in generation), 'Generation identity mismatch')
    tree = ast.parse((OUT / 'package/run.py').read_text())
    limits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument' and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == '--limit':
            limits.append({item.arg: ast.literal_eval(item.value) for item in node.keywords if item.arg in ('choices', 'default')})
    require(limits == [{'choices': [2], 'default': 2}], 'Unexpected runtime limit')
    original_readme = (OUT / 'package/README.md').read_text()
    require('two-attempt limit' in original_readme, 'Budget phrase not found')
    save(OUT / 'diagnostic/README.md', original_readme.replace('two-attempt limit', 'ten-attempt limit'))
    shutil.copyfile(OUT / 'package/run.py', OUT / 'diagnostic/run.py')
    save(OUT / 'BUDGET-REVIEW.md', '# Executed document/source comparison\n\nOriginal README: two attempts. Diagnostic README: ten attempts. AST inspection of both byte-identical entry scripts finds choices=[2], default=2 for --limit. The diagnostic description disagrees with implementation. No model fit uses that copy.\n')
    run = OUT / '06-04-run'
    entry = OUT / 'package/run.py'
    common = ['--repo', REPO, '--workspace', run, '--limit', '2', '--hypothesis', 'Exercise the generated bike package under a fresh two-slot refusal contract.']
    command('bike-baseline', entry, ['run', *common, '--model', 'constant', '--features', 'calendar'])
    command('bike-check', CHECKER, [run / 'trial-001', '--report', OUT / 'BASELINE-CHECK.md'])
    command('bike-leakage', entry, ['run', *common, '--model', 'constant', '--features', 'casual'], 1)
    command('bike-budget', entry, ['run', *common, '--model', 'linear', '--features', 'calendar'], 1)
    save(OUT / 'EXPECTED.md', '# Current request\n\n' + identity_text(run, 'trial-001'))
    shutil.copyfile(OUT / 'EXPECTED.md', OUT / 'MATCHING-CLAIM.md')
    save(OUT / 'UNRELATED-CLAIM.md', '# Actual older successful candidate\n\n' + identity_text(OLD / '06-02/run', 'trial-001'))
    shutil.copyfile(OLD / '06-02/run/trial-001/RESULT.md', OUT / 'UNRELATED-RESULT.md')
    expected = (OUT / 'EXPECTED.md').read_text()
    save(OUT / 'MISSING-CANDIDATE.md', expected.replace('- Candidate: trial-001\n', ''))
    for name, claim, code in [('matching', 'MATCHING-CLAIM.md', 0), ('unrelated', 'UNRELATED-CLAIM.md', 2), ('missing', 'MISSING-CANDIDATE.md', 2)]:
        command('binding-' + name, OUT / 'package/check-evidence.py', ['--expected', OUT / 'EXPECTED.md', '--claim', OUT / claim, '--output', OUT / ('BINDING-' + name + '.md')], code)
    wine = OLD / '06-05/run'
    for candidate in ('trial-001', 'trial-002'):
        command('wine-' + candidate, CHECKER, [wine / candidate, '--report', OUT / ('WINE-' + candidate + '-CHECK.md')])
    recalls = []
    for candidate in ('trial-001', 'trial-002'):
        predictions = rows(wine / candidate / 'predictions.csv')
        values = []
        for label in ('0', '1'):
            actual = [r for r in predictions if r['actual'] == label]
            require(actual, 'Empty classification slice')
            recall = sum(r['predicted'] == label for r in actual) / len(actual)
            values.append(recall)
            recalls.append({'candidate': candidate, 'actual_class': label, 'rows': len(actual), 'recall': recall})
        saved = next(r for r in rows(wine / 'trials.csv') if r['candidate'] == candidate)
        require(abs(sum(values)/2-float(saved['score'])) < 1e-12, 'Recall mismatch')
    table(OUT / 'WINE-RECALLS.csv', recalls)
    import pandas as pd
    data = pd.read_csv(REPO / 'rsi/examples/wine-quality/source/winequality-red.csv', sep=';')
    feature_keys = data.drop(columns='quality').astype(str).agg('|'.join, axis=1)
    buckets = feature_keys.map(lambda key: int(hashlib.sha256(('wine-v1|' + key).encode()).hexdigest()[:8], 16) % 100)
    roles = buckets.map(lambda bucket: 'train' if bucket < 60 else ('selection' if bucket < 80 else 'final'))
    groups = pd.DataFrame({'key': feature_keys, 'partition': roles}).groupby('key').partition.nunique()
    save(OUT / 'WINE-GROUPS.md', f'# Feature-only group audit\n\nRows: {len(data)}. Distinct input vectors: {len(groups)}. Extra repeated-input rows: {len(data)-len(groups)}. Groups crossing partitions: {int((groups > 1).sum())}.\n\nThe feature-only wine-v1 hash is recomputed; labels are dropped before grouping. Current prediction checks separately verify exact selection row membership. No final target statistics, final score or fit is produced.\n')
    ledger, requests = rows(run / 'trials.csv'), rows(run / 'requests.csv')
    historical_tool = (OUT / 'historical-source/lab.py').read_text()
    checks = {
        'source inputs unchanged': all(digest(Path(r['path'])) == r['sha256'] for r in rows(OUT / 'INPUT-IDENTITIES.csv')),
        'two slots one successful fit': len(ledger) == 2 and [r['status'] for r in ledger] == ['ok', 'failed'],
        'invalid features fail without predictions': not (run / 'trial-002/predictions.csv').exists(),
        'third request does not spend another slot': len(requests) == 3 and requests[-1]['attempts_before'] == requests[-1]['attempts_after'] == '2',
        'generated entry preserved': digest(entry) == digest(OLD / '06-02/package/run.py'),
        'diagnostic changes docs only': digest(OUT / 'diagnostic/run.py') == digest(entry),
        'builder is not a runtime import': 'build-ml-harness' not in entry.read_text() and 'builder' not in entry.read_text().lower(),
        'historical training mask explicit': 'fitted.fit(data.loc[masks["train"], names], y[masks["train"]])' in historical_tool,
        'wine groups remain together': bool((groups == 1).all()),
        'no final lock': not (run / 'FINAL-LOCK.md').exists(),
    }
    table(OUT / 'CHECKS.csv', [{'check': k, 'passed': v} for k, v in checks.items()])
    require(all(checks.values()), 'Post-run invariant failed')
    save(OUT / 'PROGRESS.md', '# Progress\n\nOne new bike fit, one admitted pre-fit failure, one budget refusal, three evidence-binding cases and two historical wine prediction checks completed. Nine child commands have expected exits; ten invariants and six generation-identity checks pass. No final evaluation or live child process. Do not run another fit. Learner responses remain unattempted.\n')
    print('One fresh fit; nine command checks, six generation identities and ten invariants pass.')


if __name__ == '__main__':
    main()
