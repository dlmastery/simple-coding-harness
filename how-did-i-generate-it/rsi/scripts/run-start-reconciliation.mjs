import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const repo=process.cwd();
const work=resolve(repo,'../rsi-work-2026-09-22-start-reconciliation');
const python=resolve(repo,'.venv/Scripts/python.exe');
const commands=[];
for (const [label,report,expected] of [['valid','reference/RESULT.md',0],['altered','ALTERED-REPORT.md',2]]) {
  const args=[resolve(work,'check-report.py'),'--reference',resolve(work,'reference'),
    '--source',resolve(repo,'rsi/examples/bike-demand/source/hour.csv'),'--report',resolve(work,report)];
  const started=performance.now();
  const result=spawnSync(python,args,{encoding:'utf8',timeout:60000});
  const seconds=(performance.now()-started)/1000;
  writeFileSync(resolve(work,`${label}-output.txt`),result.stdout+result.stderr+
    `\nExit: ${result.status}\nExpected: ${expected}\nSeconds: ${seconds}\nError: ${result.error?.message || 'none'}\n`);
  commands.push(`## ${label}\n\nExecutable: ${python}\n\nArguments:\n\n${args.map(x=>'    '+x).join('\n')}\n\nExit ${result.status}; expected ${expected}; ${seconds} process wall seconds.\n`);
  writeFileSync(resolve(work,'COMMANDS.md'),'# Actual report checks\n\n'+commands.join('\n'));
  if(result.error || result.status!==expected) throw new Error('Unexpected result; preserve and inspect, do not silently retry');
}
// These known numeric-only prediction fields contain no quoted commas.
const lines=readFileSync(resolve(work,'reference/predictions.csv'),'utf8').trim().split(/\r?\n/);
if(lines[0]!=='source_row,actual,predicted,hour') throw new Error('Unexpected CSV schema');
const rows=lines.slice(1).map(line=>{
  const values=line.split(',').map(Number);
  if(values.length!==4 || values.some(x=>!Number.isFinite(x))) throw new Error('Unexpected numeric CSV row');
  const [id,actual,predicted,hour]=values;
  return {id,actual,predicted,hour};
});
const quiet=rows.reduce((a,b)=>b.actual<a.actual?b:a);
const busy=rows.reduce((a,b)=>b.actual>a.actual?b:a);
const selected=[...rows.slice(0,3).map((r,i)=>['first-'+(i+1),r]),['quiet',quiet],['busy',busy]];
writeFileSync(resolve(work,'ERROR-EXAMPLES.csv'),'example,source_row,hour,actual,predicted,signed_prediction_minus_actual,absolute_error\n'+selected.map(([label,r])=>[label,r.id,r.hour,r.actual,r.predicted,r.predicted-r.actual,Math.abs(r.predicted-r.actual)].join(',')).join('\n')+'\n');
console.log('Two report checks completed with expected exits; five error examples saved. No fits.');
