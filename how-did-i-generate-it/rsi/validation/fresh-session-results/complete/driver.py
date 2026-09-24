"""One-attempt maintenance driver. Invoke preflight, then attempt, never retry."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
REPO = OUT.parent / 'simple-coding-harness'
PYTHON = REPO / '.venv/Scripts/python.exe'
PACKET = REPO / 'how-did-i-generate-it/rsi/validation/fresh-session-plan/complete'
LOG = OUT / 'commands'
LOG.mkdir(exist_ok=True)

def write(name, value):
    (OUT / name).write_text(value, encoding='utf-8')

def command(name, args):
    folder = LOG / name
    folder.mkdir(exist_ok=False)
    meta = dict(argv=[str(x) for x in args], cwd=str(REPO), timeout_seconds=60,
                started_utc=datetime.now(timezone.utc).isoformat())
    (folder / 'command.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    start = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with (folder / 'stdout.txt').open('wb') as stdout, (folder / 'stderr.txt').open('wb') as stderr:
        child = subprocess.Popen(args, cwd=REPO, stdout=stdout, stderr=stderr, env=env)
        meta['pid'] = child.pid
        try:
            meta['exit_code'] = child.wait(timeout=60)
            meta['timed_out'] = False
        except subprocess.TimeoutExpired:
            child.kill()
            meta['exit_code'] = child.wait()
            meta['timed_out'] = True
    meta['elapsed_seconds'] = time.monotonic() - start
    meta['ended_utc'] = datetime.now(timezone.utc).isoformat()
    (folder / 'exit.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(json.dumps(meta), flush=True)
    return meta['exit_code'] == 0 and not meta['timed_out']

def identities(name):
    paths = [PACKET / x for x in ('HANDOFF.md', 'BASELINE-SKILL.md', 'TASK.md')]
    paths += [REPO / x for x in ('rsi/AGENTS.md', 'rsi/tools/README.md', 'rsi/tools/requirements.txt',
        'rsi/tools/lab.py', 'rsi/tools/check_result.py', 'rsi/examples/bike-demand/DATA-CARD.md',
        'rsi/examples/bike-demand/source/hour.csv', 'rsi/examples/bike-demand/source/bike-sharing.zip')]
    paths += [PYTHON, Path(__file__).resolve()]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    write(name, json.dumps(hashes, indent=2))
    assert hashes[str(PACKET / 'BASELINE-SKILL.md')] == '210bed6c0528855a878771f8c8c9acd635a7af1da38ab6f8d15a9ab1946e1d2b'
    assert hashes[str(REPO / 'rsi/examples/bike-demand/source/hour.csv')] == 'e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f'
    assert hashes[str(REPO / 'rsi/examples/bike-demand/source/bike-sharing.zip')] == 'b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401'

def main():
    assert Path(sys.executable).resolve() == PYTHON.resolve(), sys.executable
    mode = sys.argv[1]
    if mode == 'preflight':
        (OUT / 'PREFLIGHT-STARTED').open('x').close()
        identities('identities-before.json')
        versions = {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
                    'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}
        write('dependencies.json', json.dumps(versions, indent=2, sort_keys=True))
        assert command('01-commit', ['git', 'rev-parse', 'HEAD'])
        commit = (LOG / '01-commit/stdout.txt').read_text().strip()
        assert commit == '0132b2302e3e0212fb233f229322a09e8f2c2a88'
        assert command('02-inspect', [PYTHON, REPO / 'rsi/tools/lab.py', 'inspect', '--task', 'bike', '--workspace', OUT])
        write('PROGRESS.md', '# Progress\n\nPreflight and data inspection completed. No baseline attempt yet. One attempt remains.\n')
    elif mode == 'attempt':
        (OUT / 'BASELINE-ATTEMPT-STARTED').open('x').close()
        ok = command('03-baseline', [PYTHON, REPO / 'rsi/tools/lab.py', 'run', '--task', 'bike',
            '--workspace', OUT, '--model', 'constant', '--features', 'calendar', '--seed', '17',
            '--attempt-limit', '1', '--hypothesis', 'Use the training median as the fixed hourly-rental baseline.',
            '--policy', PACKET / 'BASELINE-SKILL.md'])
        checked = False
        if ok:
            checked = command('04-check', [PYTHON, REPO / 'rsi/tools/check_result.py', OUT / 'trial-001',
                              '--report', OUT / 'trial-001/CHECK.md'])
        identities('identities-after.json')
        write('PROGRESS.md', '# Progress\n\nThe sole baseline attempt has ended. Baseline success: ' + str(ok) +
              '. Course prediction check passed: ' + str(checked) + '. No attempts remain. No final evaluation was run.\n')
        return 0 if ok and checked else 1
    else:
        raise ValueError('Only preflight or attempt is allowed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
