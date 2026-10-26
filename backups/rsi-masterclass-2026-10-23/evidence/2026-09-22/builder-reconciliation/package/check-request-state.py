"""Check current admission state before a supplied success claim can count."""
import argparse
import csv
import hashlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--claim', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with (args.workspace / 'trials.csv').open(encoding='utf-8', newline='') as stream:
        matches = [row for row in csv.DictReader(stream) if row['candidate'] == args.candidate]
    claim = dict(line[2:].split(': ', 1) for line in args.claim.read_text(encoding='utf-8').splitlines() if line.startswith('- ') and ': ' in line)
    if len(matches) != 1:
        errors = ['No unique admitted candidate exists for this request.']
    elif matches[0]['status'] != 'ok':
        errors = [f'Current candidate status is {matches[0]["status"]}; a claimed old success cannot replace it.']
    else:
        expected = {'Workspace': str(args.workspace.resolve()), 'Candidate': args.candidate,
                    'Contract SHA256': hashlib.sha256((args.workspace / 'CONTRACT.md').read_bytes()).hexdigest(),
                    'Predictions SHA256': hashlib.sha256((args.workspace / args.candidate / 'predictions.csv').read_bytes()).hexdigest(), 'Verdict': 'PASS'}
        errors = [f'Missing or mismatched {key}' for key, value in expected.items() if claim.get(key) != value]
    message = '\n'.join(errors) if errors else 'PASS: successful current admission and exact claim identities agree.'
    args.output.write_text('# Current-request state guard\n\n' + message + '\n\nNo training, ledger mutation or metric recomputation. This local check assumes trusted ledger and reference files; it does not authenticate them against a hostile writer.\n', encoding='utf-8')
    print(message)
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
