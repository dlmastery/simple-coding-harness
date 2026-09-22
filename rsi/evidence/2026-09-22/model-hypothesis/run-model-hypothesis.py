"""Two declared fits after reading a saved hypothesis. No final evaluation."""
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / 'rsi-work-2026-09-22-model-hypothesis'
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
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def command(label, script, arguments):
    argv = [sys.executable, '-B', str(script), *map(str, arguments)]
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=60)
    except subprocess.TimeoutExpired as error:
        save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart UTC: {started}\nTimed out; inspect processes and ledger before any recovery.\n{error!r}\n')
        raise
    save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart UTC: {started}\nEnd UTC: {datetime.now(timezone.utc).isoformat()}\nExit: {result.returncode}\nWall seconds: {time.perf_counter()-clock}\n\n{result.stdout}{result.stderr}')
    require(result.returncode == 0, f'{label} failed; preserve and inspect')


def main():
    require(not (OUT / 'STARTED.txt').exists(), 'Already started: inspect, do not repeat')
    save(OUT / 'STARTED.txt', datetime.now(timezone.utc).isoformat() + '\n')
    shutil.copyfile(Path(__file__), OUT / Path(__file__).name)
    paths = [OUT / 'HYPOTHESIS.md', OUT / 'BASELINE-HOURLY.csv', TOOL, CHECKER,
             REPO / 'rsi/examples/bike-demand/source/hour.csv',
             REPO / 'rsi/skills/run-ml-experiment/SKILL.md', Path(__file__)]
    identities = [{'path': str(p), 'sha256': digest(p)} for p in paths]
    table(OUT / 'INPUT-IDENTITIES.csv', identities)
    hypothesis = (OUT / 'HYPOTHESIS.md').read_text(encoding='utf-8')
    fields = dict(line[2:].split(': ', 1) for line in hypothesis.splitlines() if line.startswith('- ') and ': ' in line)
    require(fields == {'Task': 'bike', 'Models': 'constant,linear', 'Features': 'calendar', 'Seed': '17', 'Limit': '2'}, 'Unexpected frozen recipe')
    save(OUT / 'ENVIRONMENT.md', '# Actual runtime\n\n' + f'Python: {sys.version}\nPlatform: {platform.platform()}\nExecutable: {sys.executable}\n\n' + '\n'.join(f'{name}: {importlib.metadata.version(name)}' for name in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'matplotlib']) + '\n')
    work = OUT / 'experiment'
    work.mkdir(exist_ok=False)
    for number, model in enumerate(fields['Models'].split(','), 1):
        require(all(digest(Path(r['path'])) == r['sha256'] for r in identities), 'An input changed before fitting')
        save(OUT / f'DECISION-{number}.md', '# Decision read before fit\n\n' + f'UTC: {datetime.now(timezone.utc).isoformat()}\nHypothesis SHA256: {identities[0]["sha256"]}\nRead saved Models item {number}: {model}. Hold calendar inputs, seed 17, bike split and MAE fixed. Shared allocation: two fits.\n\nThe author supplied the hypothesis; the fixed adapter reads its fields.\n')
        command(f'fit-{number}', TOOL, ['run', '--task', fields['Task'], '--workspace', work,
                '--model', model, '--features', fields['Features'], '--seed', fields['Seed'],
                '--attempt-limit', fields['Limit'], '--hypothesis',
                'A fixed median misses hourly structure; test a calendar linear model while holding inputs and evaluation fixed.'])
        command(f'check-{number}', CHECKER, [work / f'trial-{number:03}', '--report', work / f'trial-{number:03}/CHECK.md'])
    command('compare', TOOL, ['compare', '--workspace', work])
    before = rows(work / 'trial-001/error-by-hour.csv')
    after = rows(work / 'trial-002/error-by-hour.csv')
    require(len(before) == len(after) == 24, 'Missing hourly rows')
    changes = []
    for a, b in zip(before, after):
        require(a['hour'] == b['hour'] and a['size'] == b['size'], 'Hourly alignment changed')
        changes.append({'hour': int(a['hour']), 'rows': int(a['size']), 'constant_mae': float(a['mean']),
                        'linear_mae': float(b['mean']), 'delta': float(b['mean']) - float(a['mean'])})
    table(OUT / 'HOURLY-CHANGES.csv', changes)
    ledger = rows(work / 'trials.csv')
    count = sum(r['rows'] for r in changes)
    checks = {
        'two successful fits': len(ledger) == 2 and all(r['status'] == 'ok' for r in ledger),
        'only model family changes': [(r['task'], r['model'], r['features'], r['seed']) for r in ledger] == [('bike', 'constant', 'calendar', '17'), ('bike', 'linear', 'calendar', '17')],
        'constant slices agree with earlier prerequisite': before == rows(OUT / 'BASELINE-HOURLY.csv'),
        'selection rows total 4358': count == 4358,
        'constant weighted slices match score': abs(sum(r['rows']*r['constant_mae'] for r in changes)/count-float(ledger[0]['score'])) < 1e-9,
        'linear weighted slices match score': abs(sum(r['rows']*r['linear_mae'] for r in changes)/count-float(ledger[1]['score'])) < 1e-9,
        'frozen inputs unchanged': all(digest(Path(r['path'])) == r['sha256'] for r in identities),
        'no final lock': not (work / 'FINAL-LOCK.md').exists(),
    }
    table(OUT / 'CHECKS.csv', [{'check': k, 'passed': v} for k, v in checks.items()])
    require(all(checks.values()), 'Post-run invariant failed')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5), layout='constrained')
    ax.plot([r['hour'] for r in changes], [r['constant_mae'] for r in changes], color='#ad6940', marker='o', label='Constant / calendar')
    ax.plot([r['hour'] for r in changes], [r['linear_mae'] for r in changes], color='#007f88', marker='o', label='Linear / calendar')
    ax.set(xlabel='Recorded hour', ylabel='Selection MAE (rentals per hour)', xticks=range(24), title='A calendar model helps overall, but some hours get worse')
    ax.grid(axis='y', alpha=.2)
    ax.legend(frameon=False)
    fig.savefig(OUT / 'hourly-errors.png', dpi=160, facecolor='white')
    plt.close(fig)
    weak = max(changes, key=lambda r: r['linear_mae'])
    worse = [r['hour'] for r in changes if r['delta'] > 0]
    save(OUT / 'RESULT.md', '# Interpret the measured comparison\n\n' + f'Constant selection MAE: {ledger[0]["score"]}. Linear: {ledger[1]["score"]}. Lower is better; both candidates are retained.\n\nThe weakest linear hour is {weak["hour"]}: MAE {weak["linear_mae"]:.9f}, compared with constant {weak["constant_mae"]:.9f}. Regressing hours: {worse}. The weighted hourly errors agree with the full scores. A better overall score does not mean every hour improves.\n\n' + f'Recorded fit intervals total {sum(float(r["seconds"]) for r in ledger):.6f} seconds. Command intervals also include startup, artifact writing and checks; do not confuse them with fit-only cost. Provider inference and author preparation costs are unknown.\n\nThe hypothesis and decisions preceded fitting and remain hash-checked. Prior public results were author-known. This establishes an executed controlled workflow, not blind discovery, causal attribution, protected evaluation, generalization or learner understanding. No final evaluation ran.\n')
    save(OUT / 'PROGRESS.md', '# Progress\n\nTwo of two allocated fits completed; both prediction checks and eight invariants passed. No live child processes, extra fits or final evaluation. Student prediction and quiz remain unattempted.\n')
    print('Two fits, two prediction checks and eight invariants passed; no final evaluation.')


if __name__ == '__main__':
    main()
