"""A declared-capability fixture, not a probe or change to actual permissions."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
text=a.profile.read_text(encoding='utf-8')
allowed='Command execution: available' in text and 'File access: available' in text
message=('PASS: declared file and command capabilities allow the planned smoke procedure.' if allowed else
         'REFUSED: declared command execution is unavailable. New fits, command-based checks and runtime recovery cannot be completed. Reading supplied artifacts remains possible. No training subprocess was called.')
with a.output.open('x',encoding='utf-8') as stream:stream.write('# Capability fixture result\n\n'+message+'\n\nThis local fixture does not disable actual host permissions or test another agent.\n')
print(message)
raise SystemExit(0 if allowed else 2)
