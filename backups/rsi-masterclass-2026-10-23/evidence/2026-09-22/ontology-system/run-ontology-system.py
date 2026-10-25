"""Five command checks and six declared rule fixtures; no fitting operation."""
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path.cwd().resolve()
OUT = REPO.parent / 'rsi-work-2026-09-22-ontology-system'
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
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def command(label, script, arguments, expected):
    argv = [sys.executable, '-B', str(script), *map(str, arguments)]
    start = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=60)
    save(OUT / (label + '-command.txt'), f'Arguments: {argv!r}\nStart: {start}\nEnd: {datetime.now(timezone.utc).isoformat()}\nExit: {result.returncode}\nExpected: {expected}\nWall seconds: {time.perf_counter()-clock}\n\n{result.stdout}{result.stderr}')
    require(result.returncode == expected, f'Unexpected {label} outcome; preserve and inspect')


def main():
    require(not (OUT / 'STARTED.txt').exists(), 'Already started; inspect, do not repeat')
    save(OUT / 'STARTED.txt', datetime.now(timezone.utc).isoformat() + '\n')
    shutil.copyfile(Path(__file__), OUT / Path(__file__).name)
    shutil.copyfile(OLD / '04-04/ORIGINAL.md', OUT / '04-02/LEAKED.md')
    paths = [TOOL, CHECKER, Path(__file__), OLD / '02-04/controller.py',
             REPO / 'rsi/examples/wine-quality/DATA-CARD.md',
             REPO / 'rsi/skills/review-domain/SKILL.md',
             *[p for p in (OLD / '05-01').rglob('*') if p.is_file()],
             *OUT.rglob('*.md')]
    identities = [{'path': str(p), 'sha256': digest(p)} for p in paths]
    table(OUT / 'INPUT-IDENTITIES.csv', identities)
    for filename, label, expected in [('DOMAIN', 'valid', 0), ('UNKNOWN', 'unknown', 1), ('LEAKED', 'leaked', 1), ('OMITTED-DERIVATION', 'omitted', 0)]:
        command('domain-' + label, TOOL, ['audit-domain', '--input', OUT / f'04-02/{filename}.md', '--output', OUT / f'04-02/{label}-CHECK.md'], expected)
    command('historical-predictions', CHECKER, [OLD / '05-01/trial-001', '--report', OUT / '05-01/PREDICTION-CHECK.md'], 0)
    origin = datetime.fromisoformat('2026-09-22T12:00:00+00:00')
    cases = [('forecast-before-origin', '2026-09-22T09:00:00+00:00', 'pass'),
             ('future-observation', '2026-09-23T12:05:00+00:00', 'refuse'),
             ('release-unknown', '', 'refuse')]
    availability = []
    for name, released, expected in cases:
        verdict = 'pass' if released and datetime.fromisoformat(released) <= origin else 'refuse'
        reason = 'known before origin' if verdict == 'pass' else ('release time missing' if not released else 'released after origin')
        availability.append({'fixture': name, 'synthetic': True, 'origin_utc': origin.isoformat(), 'target_utc': '2026-09-23T12:00:00+00:00', 'released_utc': released, 'verdict': verdict, 'expected': expected, 'reason': reason})
        require(verdict == expected, 'Availability fixture failed')
    table(OUT / '04-05/AVAILABILITY.csv', availability)
    leaked_report = (OUT / '04-02/leaked-CHECK.md').read_text(encoding='utf-8')
    require(leaked_report.count('- FAIL:') == 3, 'Unexpected historical leak violations')
    diagnostic = []
    for name, domain_guard, column_guard in [('domain-present', True, False), ('domain-removed', False, False), ('column-guard-remains', False, True)]:
        # This stub never calls a training function. Its additional allowlist is a declared fixture.
        declared_columns = ['total_users']
        if domain_guard and '- FAIL:' in leaked_report:
            verdict, reason, reached = 'refuse', 'domain check: three declared violations', False
        elif column_guard and any(column not in {'hr', 'weekday', 'season'} for column in declared_columns):
            verdict, reason, reached = 'refuse', 'teaching allowlist: total_users is not an allowed column', False
        else:
            verdict, reason, reached = 'stub reached', 'domain guard removed; no remaining guard in this variant', True
        diagnostic.append({'case': name, 'domain_guard': domain_guard, 'teaching_column_guard': column_guard, 'declared_columns': ','.join(declared_columns), 'verdict': verdict, 'reason': reason, 'dry_run_stub_reached': reached, 'fit_calls': 0})
    table(OUT / '05-01/DIAGNOSTIC.csv', diagnostic)
    ledger = rows(OLD / '05-01/trials.csv')
    requests = rows(OLD / '05-01/requests.csv')
    controller = OLD / '02-04/controller.py'
    controller_text = controller.read_text(encoding='utf-8')
    checks = {
        'original identities unchanged': all(digest(Path(r['path'])) == r['sha256'] for r in identities),
        'historical controller hash agrees': digest(controller) in (OLD / '05-01/CONTROLLER-CONTRACT.md').read_text(),
        'historical exactly one successful fit': len(ledger) == 1 and ledger[0]['status'] == 'ok',
        'historical request records check': len(requests) == 1 and requests[0]['attempts_before'] == '0' and requests[0]['attempts_after'] == '1' and requests[0]['exit_status'] == '0' and 'Checked trial-001' in requests[0]['outcome'],
        'controller checks after fitting': controller_text.index('row = lab.experiment') < controller_text.index('check_result.check(workspace / row'),
        'unknown relation refused explicitly': 'Unknown relation: magically improves' in (OUT / '04-02/unknown-CHECK.md').read_text(),
        'omitted fact exposes limited pass': 'PASS:' in (OUT / '04-02/omitted-CHECK.md').read_text(),
        'release cases match': all(r['verdict'] == r['expected'] for r in availability),
        'three diagnostic outcomes': [r['verdict'] for r in diagnostic] == ['refuse', 'stub reached', 'refuse'],
        'zero diagnostic fits': all(r['fit_calls'] == 0 for r in diagnostic),
    }
    table(OUT / 'CHECKS.csv', [{'check': key, 'passed': value} for key, value in checks.items()])
    require(all(checks.values()), 'Audit check failed')
    save(OUT / 'PROGRESS.md', '# Progress\n\nFour domain commands and one historical prediction check have expected exits. Three synthetic availability records and three dry-run diagnostic variants executed. Ten invariants pass. No fits, final evaluation or live child processes. Learner responses remain unattempted.\n')
    print('Five commands, six rule fixtures, ten invariants; zero new fits.')


if __name__ == '__main__':
    main()
