// Two declared checker runs. No training and no solver imports.
import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const repo = process.cwd();
const workspace = resolve(repo, '../rsi-work-2026-09-22-generated-checker');
const python = resolve(repo, '.venv/Scripts/python.exe');
const records = [];
for (const [label,file,expected] of [
  ['valid','reference/predictions.csv',0],
  ['substituted','altered-predictions.csv',2],
]) {
  const args = [resolve(workspace,'checker.py'),'--reference',resolve(workspace,'reference'),
    '--predictions',resolve(workspace,file),'--source',resolve(repo,'rsi/examples/bike-demand/source/hour.csv')];
  const start = performance.now();
  const result = spawnSync(python,args,{encoding:'utf8',timeout:60000});
  const seconds = (performance.now()-start)/1000;
  writeFileSync(resolve(workspace,`${label}-output.txt`),result.stdout + result.stderr +
    `\nExit: ${result.status}\nSignal: ${result.signal}\nError: ${result.error?.message || 'none'}\nSeconds: ${seconds}\n`);
  records.push(`## ${label}\n\nExecutable: ${python}\n\nArguments, one per line:\n\n${args.map(x=>`    ${x}`).join('\n')}\n\nExit ${result.status}; expected ${expected}; elapsed ${seconds} seconds.\n`);
  writeFileSync(resolve(workspace,'COMMANDS.md'),'# Declared checker invocations\n\n'+records.join('\n'));
  if (result.status !== expected || result.error) throw new Error(`${label}: unexpected execution outcome; do not retry silently`);
}
console.log('Two checker invocations complete; expected pass and refusal.');
