"""Bind a claimed successful report to the exact requested artifact identities."""
import argparse
from pathlib import Path


def fields(path):
    return dict(line[2:].split(': ', 1) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.startswith('- ') and ': ' in line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected', required=True)
    parser.add_argument('--claim', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    expected, claim = fields(args.expected), fields(args.claim)
    required = ['Workspace', 'Candidate', 'Contract SHA256', 'Predictions SHA256']
    missing = [name for name in required if not claim.get(name)]
    errors = [f'Missing required identity: {name}' for name in missing]
    errors += [f'Mismatched identity: {name}' for name in required if claim.get(name) and claim[name] != expected.get(name)]
    if claim.get('Verdict') != 'PASS':
        errors.append('No passing result verdict supplied')
    message = '\n'.join(errors) if errors else 'PASS: claim names the requested workspace, candidate, contract and predictions.'
    Path(args.output).write_text('# Request-specific evidence check\n\n' + message + '\n\nThis binds supplied identities. It does not independently recompute predictions, authenticate the claimant, or authorize a model fit. Pair it with the actual result checker and admission ledger.\n', encoding='utf-8')
    print(message)
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
