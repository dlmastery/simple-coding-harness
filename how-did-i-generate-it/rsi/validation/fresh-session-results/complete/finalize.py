import csv
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
REPO = OUT.parent / 'simple-coding-harness'
before = json.loads((OUT / 'identities-before.json').read_text())
after = json.loads((OUT / 'identities-after.json').read_text())
assert before == after, 'Pinned identities changed'
rows = list(csv.DictReader((OUT / 'trials.csv').open(newline='')))
assert len(rows) == 1 and rows[0]['status'] == 'ok'
assert rows[0]['model'] == 'constant' and rows[0]['features'] == 'calendar' and rows[0]['seed'] == '17'
assert not (OUT / 'FINAL.md').exists() and not (OUT / 'final-predictions.csv').exists()
sources = [str(Path(p).relative_to(REPO)) for p in before if Path(p).is_relative_to(REPO) and '.venv' not in Path(p).parts]
cmd = ['git', 'diff', '--exit-code', 'HEAD', '--', *sources]
(OUT / 'source-git-command.json').write_text(json.dumps(cmd, indent=2))
with (OUT / 'source-git.stdout.txt').open('wb') as stdout, (OUT / 'source-git.stderr.txt').open('wb') as stderr:
    result = subprocess.run(cmd, cwd=REPO, stdout=stdout, stderr=stderr, timeout=60)
(OUT / 'source-git.exit.txt').write_text(str(result.returncode))
assert result.returncode == 0
deps = json.loads((OUT / 'dependencies.json').read_text())
lines = ['# Exact identities', '', 'Commit: 0132b2302e3e0212fb233f229322a09e8f2c2a88. Named repository pins agree with HEAD; before/after hashes agree.', '',
         'Python: ' + deps['python'], '', 'Executable: ' + deps['executable'], '', '| Path | SHA-256 |', '|---|---|']
lines += [f'| `{p}` | `{h}` |' for p, h in before.items()]
lines += ['', '| Installed distribution | Version |', '|---|---|']
lines += [f'| {p} | {v} |' for p, v in deps['packages'].items()]
(OUT / 'IDENTITIES.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
logs = [json.loads((OUT / 'commands' / name / 'exit.json').read_text()) for name in ('01-commit', '02-inspect', '03-baseline', '04-check')]
assert all(x['exit_code'] == 0 and not x['timed_out'] for x in logs)
report = f'''# Complete handoff maintenance report

The sole baseline attempt succeeded. The course checker passed. Selection MAE: {rows[0]['score']} rentals per hour over 4,358 selection rows. This is a measured baseline result, not evidence of improved agent behavior or autonomous RSI.

Output: `{OUT}`.
Repository: `{REPO}`.
Pinned commit: `0132b2302e3e0212fb233f229322a09e8f2c2a88`.

The candidate is trial-001, constant median baseline, calendar feature group, seed 17. Transformations and estimator were fit on the 8,645 training rows from 2011. Selection is January–June 2012. The one-attempt allocation is frozen in CONTRACT.md. Exactly one fit command and one fit were completed; no retry, comparison command, additional candidate, or final evaluation ran. The 4,376 final-partition rows remain unevaluated; required public-data inspection did reveal their aggregate target summary.

The model subprocess had a real 60-second deadline through Popen.wait(timeout=60), with child.kill() and wait() on expiry. Actual elapsed model-command wall time: {logs[2]['elapsed_seconds']:.6f} seconds. Recorded internal fit time: {rows[0]['seconds']} seconds. No timeout occurred. Agent inference cost was not measured. The course check recomputed MAE from the expected selection row identities and pinned source targets, checking saved targets, ledger and result agreement. It runs within the same local trust boundary.

| Command | Exit | Timed out | Wall seconds |
|---|---:|---|---:|
'''
for name, log in zip(('git HEAD', 'inspect', 'one baseline', 'course checker'), logs):
    report += f"| {name} | {log['exit_code']} | {log['timed_out']} | {log['elapsed_seconds']:.6f} |\n"
report += '''
The repository's .venv Python 3.12.12 was used, with scikit-learn 1.7.2, pandas 2.3.2, NumPy 2.5.3, matplotlib 3.10.6 and pytest 8.4.2. Full installed distribution versions and exact source/data/tool hashes are in IDENTITIES.md and dependencies.json. Packet skill, hourly source and original archive checksums match their documented pins. Before/after source hashes agree, and the path-scoped git check returned 0. No repository file was edited.

Context limitation: a broad filename-discovery command exposed historical evidence paths and candidate/model names. No historical content, score or prediction was read, and no other packet was opened. Its stdout was truncated in the tool response and is not fully archived. Thus this run must not be described as a perfectly isolated packet-only context test. Full context disclosure is in CONTEXT-EXPOSURE.md and exact reads/actions in READS-AND-ACTIONS.md. No expected score was supplied.

All experiment and checker stdout/stderr, process exits, timestamps, argv and driver source are retained. The initial read-only command outputs exist in the tool transcript, with the stated truncation limitation. Learner prediction, quiz responses and teach-back are explicitly skipped in this maintainer run. No learner response was invented. No publication, delegation or third-party contact occurred.

Key evidence paths:
'''
for file in ('PROGRESS.md', 'driver.py', 'READS-AND-ACTIONS.md', 'CONTEXT-EXPOSURE.md', 'IDENTITIES.md', 'DATA-REPORT.md', 'sample.csv', 'data-overview.png', 'CONTRACT.md', 'trials.csv', 'trial-001/PROPOSAL.md', 'trial-001/RESULT.md', 'trial-001/predictions.csv', 'trial-001/CHECK.md', 'commands/03-baseline/exit.json', 'commands/04-check/exit.json', 'output-sha256.json'):
    report += f'\n- `{OUT / file}`'
(OUT / 'FINAL-REPORT.md').write_text(report + '\n', encoding='utf-8')
(OUT / 'PROGRESS.md').write_text(f'# Progress\n\nComplete: exactly one constant/calendar/seed-17 attempt, one-attempt allocation exhausted. Baseline and course checker exit 0. Selection MAE {rows[0]["score"]}. No retry or final evaluation. Before/after identities match; named sources match HEAD.\n\nFinal report: `{OUT / "FINAL-REPORT.md"}`.\n\nContext limitation: historical filenames were exposed during discovery; no historical file contents or scores were opened. See CONTEXT-EXPOSURE.md. Learner responses skipped for maintenance mode.\n', encoding='utf-8')
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name not in ('output-sha256.json', 'finalize.stdout.txt', 'finalize.stderr.txt', 'finalize.exit.txt')}
(OUT / 'output-sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
print('Final report written; one trial, course checker pass, unchanged named source identities.')
