// Author walkthrough; students ask their agent to generate their implementation.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const out=resolve(repo,'../rsi-work-2026-09-21-model-harness-fit');
if(existsSync(out))throw Error('Preserve the earlier workspace.');
mkdirSync(out);
const save=(name,s)=>writeFileSync(resolve(out,name),s.trimEnd()+'\n');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
copyFileSync(script,resolve(out,'run-model-harness-fit.mjs'));
copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/MODEL-HARNESS-FIT-PROTOCOL.md'),resolve(out,'PROTOCOL.md'));
save('CONTRACT.md','# Report contract\n\nExactly two nonempty key/value lines, in either order. Required unique keys: Candidate and Status. Candidate: one uppercase letter. Status: checked or unchecked. No extra fields. This is structural validation; truth of the status is outside the parser.');
save('parser.mjs',`import {readFileSync} from 'node:fs';
const lines=readFileSync(process.argv[2],'utf8').trim().split(/\\r?\\n/);
const fields=new Map(),errors=[];
for(const line of lines){
 const match=/^([A-Za-z]+): (.+)$/.exec(line);
 if(!match){errors.push('Malformed line');continue;}
 const [,key,value]=match;
 if(!['Candidate','Status'].includes(key))errors.push('Unexpected field: '+key);
 if(fields.has(key))errors.push('Repeated field: '+key);
 fields.set(key,value);
}
if(lines.length!==2)errors.push('Expected exactly two lines');
if(!/^[A-Z]$/.test(fields.get('Candidate')||''))errors.push('Candidate must be one uppercase letter');
if(!['checked','unchecked'].includes(fields.get('Status')))errors.push('Status must be checked or unchecked');
console.log(errors.length?'REJECT\\n'+errors.join('\\n'):'ACCEPT: structural contract only');
process.exitCode=errors.length?1:0;`);
save('valid.txt','Candidate: A\nStatus: checked');
save('mismatched.txt','Candidate: A\nResult: checked');
save('incompatible.txt','Run: A\nVerdict: checked');
const parserHash=hash(resolve(out,'parser.mjs')),contractHash=hash(resolve(out,'CONTRACT.md'));
save('FREEZE.md','# Before execution\n\nParser SHA-256: '+parserHash+'\nContract SHA-256: '+contractHash+'\nDriver SHA-256: '+hash(script)+'\nNode: '+process.version+'; '+process.platform+' '+process.arch);
let checks=0;const rows=[];
function check(name,expected){
 if(++checks>4)throw Error('Check budget exhausted');
 const start=performance.now();
 const result=spawnSync(process.execPath,[resolve(out,'parser.mjs'),resolve(out,name+'.txt')],{encoding:'utf8',timeout:60000});
 rows.push([name,result.status,(performance.now()-start).toFixed(3)]);
 save(name+'-VERDICT.md','# '+name+'\n\nExit: '+result.status+'\n\n'+result.stdout+'\nStderr: '+(result.stderr||'(empty)'));
 if(result.error||result.status!==expected)throw Error('Unexpected parser result: '+result.error);
}
check('valid',0);check('mismatched',1);
save('CHANGE.md','# Local repair\n\nThe parser rejected Result and found no valid Status. Change only the Result field name to Status; leave Candidate and both values unchanged. Keep the parser fixed.');
save('repaired.txt',readFileSync(resolve(out,'mismatched.txt'),'utf8').replace('Result:','Status:'));
check('repaired',0);check('incompatible',1);
if(hash(resolve(out,'parser.mjs'))!==parserHash||hash(resolve(out,'CONTRACT.md'))!==contractHash)throw Error('Frozen checker changed');
save('COST.csv','check,exit,wall_ms\n'+rows.map(x=>x.join(',')).join('\n'));
save('RESULTS.md','# Observed results\n\nValid accepted; mismatched rejected; one-field repair accepted; incompatible template rejected. Four subprocess checks, zero fits. Parser and contract hashes unchanged. Status truth was never evaluated. Timings include Node subprocess startup. Agent inference cost is unknown.');
save('PROGRESS.md','# Author progress\n\nFour checks complete; zero check allowance remains. Source audit is a separate reading artifact. Learner prediction, teach-back, and quiz untested.');
const files=readdirSync(out).sort();
save('MANIFEST.csv','file,sha256\n'+files.map(p=>p+','+hash(resolve(out,p))).join('\n'));
console.log('Four interface checks completed. Workspace: '+out);
