// Deterministic author walkthrough. This instrumented runner is trusted, not a security boundary.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const out=resolve(repo,'../rsi-work-2026-09-21-checked-reference');
if(existsSync(out))throw Error('Preserve the earlier workspace.');
mkdirSync(out);
const save=(p,s)=>{mkdirSync(dirname(resolve(out,p)),{recursive:true});writeFileSync(resolve(out,p),s.trimEnd()+'\n');};
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
copyFileSync(script,resolve(out,'run-checked-reference.mjs'));
copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/CHECKED-REFERENCE-PROTOCOL.md'),resolve(out,'PROTOCOL.md'));
save('CONTRACT.md','# Required report fields\n\n- Target\n- Metric\n- Split');
save('current.md','Target: wine quality\nMetric: balanced accuracy');
save('prior.md','Target: bike count\nMetric: mean absolute error\nSplit: chronological');
save('parent-skill.md','# Report audit\n\nCheck fields: Target, Metric');
save('ORACLES.md','# Fixture expectations\n\ncurrent.md: missing Split.\nprior.md: complete.\n\nThese author-known oracles check field presence, not scientific correctness. The prior control has a predeclared expected outcome; this run does not add a separate parent evaluation on that fixture.');
const frozen=Object.fromEntries(['CONTRACT.md','current.md','prior.md','ORACLES.md','parent-skill.md'].map(p=>[p,hash(resolve(out,p))]));
save('FREEZE.md','# Frozen before actions\n\n'+Object.entries(frozen).map(([p,h])=>p+': '+h).join('\n')+'\nDriver (includes fixed checker): '+hash(script)+'\nNode: '+process.version+'; '+process.platform+' '+process.arch);
const costs=[];let runs=0,validations=0,evaluations=0;
const required=text=>text.split('\n').filter(x=>x.startsWith('- ')).map(x=>x.slice(2));
const fields=text=>new Map(text.trim().split(/\r?\n/).map(x=>{const at=x.indexOf(':');return [x.slice(0,at),x.slice(at+1).trim()];}));
function execute(label,fixture,skill,order=['contract','report'],shortcut=false){
 if(++runs>6)throw Error('Action-run budget exhausted');
 const start=performance.now(),events=[];
 save(label+'/BEFORE.md','# Before execution\n\nFixture: '+fixture+'\nSkill: '+(skill||'answer-only shortcut')+'\nRead order: '+(shortcut?'none':order.join(', '))+'\nCompletion: emit field-presence verdict; no model fits.');
 const record=(op,subject,value)=>events.push([op,subject,value]);
 let verdict;
 if(shortcut){verdict='missing Split';record('emit','verdict',verdict);}
 else {
  let contract,report;
  for(const kind of order){
   const file=kind==='contract'?'CONTRACT.md':fixture;
   const content=readFileSync(resolve(out,file),'utf8');record('read',file,hash(resolve(out,file)));
   if(kind==='contract')contract=required(content);else report=fields(content);
  }
  const instruction=readFileSync(resolve(out,skill),'utf8');record('read',skill,hash(resolve(out,skill)));
  const scope=/^Check fields: (.+)$/m.exec(instruction)?.[1];
  if(!scope)throw Error('Unsupported skill');
  const names=scope==='all required'?contract:scope.split(', '),missing=[];
  for(const name of names){const present=Boolean(report.get(name));record('check',name,present?'present':'absent');if(!present)missing.push(name);}
  verdict=missing.length?'missing '+missing.join(', '):'complete';record('emit','verdict',verdict);
 }
 save(label+'/TRACE.tsv','action\tsubject\tobservation\n'+events.map(x=>x.join('\t')).join('\n'));
 save(label+'/RESULT.md','# Execution output\n\n'+verdict);
 costs.push([label,'action execution',(performance.now()-start).toFixed(3)]);
 return verdict;
}
function validate(label,fixture){
 if(++validations>4)throw Error('Trace-check budget exhausted');
 const start=performance.now(),events=readFileSync(resolve(out,label,'TRACE.tsv'),'utf8').trim().split('\n').slice(1).map(x=>x.split('\t'));
 const problems=[],names=required(readFileSync(resolve(out,'CONTRACT.md'),'utf8')),report=fields(readFileSync(resolve(out,fixture),'utf8'));
 const firstCheck=events.findIndex(x=>x[0]==='check'),emitIndex=events.findIndex(x=>x[0]==='emit');
 for(const file of ['CONTRACT.md',fixture]){
  const at=events.findIndex(x=>x[0]==='read'&&x[1]===file&&x[2]===frozen[file]);
  if(at<0||at>=firstCheck)problems.push('No matching input read before checks: '+file);
 }
 for(const name of names){
  const matches=events.map((e,i)=>({e,i})).filter(({e})=>e[0]==='check'&&e[1]===name);
  if(matches.length!==1||matches[0].i>=emitIndex||matches[0].e[2]!== (report.get(name)?'present':'absent'))problems.push('Missing or invalid field check: '+name);
 }
 if(events.filter(x=>x[0]==='check').length!==names.length)problems.push('Coverage differs from the contract');
 const missing=names.filter(n=>!report.get(n)),expected=missing.length?'missing '+missing.join(', '):'complete';
 if(events.filter(x=>x[0]==='emit').length!==1||events[emitIndex]?.[2]!==expected)problems.push('Final verdict disagrees with input evidence');
 save(label+'/VALIDATION.md','# Trace check\n\n'+(problems.length?'REJECT\n\n'+problems.join('\n'):'ACCEPT: required reads, observations, coverage, and final verdict agree.'));
 costs.push([label,'trace validation',(performance.now()-start).toFixed(3)]);
 return problems.length===0;
}
execute('failed-parent','current.md','parent-skill.md');
if(validate('failed-parent','current.md'))throw Error('Failure fixture unexpectedly accepted');
// The reference is a declared demonstration procedure, not a searched candidate.
save('reference-skill.md','# Report audit\n\nCheck fields: all required');
execute('valid-reference','current.md','reference-skill.md');
if(!validate('valid-reference','current.md'))throw Error('Valid reference rejected');
execute('shortcut','current.md',null,[],true);
if(validate('shortcut','current.md'))throw Error('Shortcut accepted');
execute('alternative','current.md','reference-skill.md',['report','contract']);
if(!validate('alternative','current.md'))throw Error('Valid alternative rejected');
save('DIAGNOSIS.md','# Diagnosis from traces\n\nThe parent read both inputs but checked only Target and Metric and emitted complete. The valid reference checked the remaining required field and emitted missing Split. The shortcut reached that same answer without reads or checks and was rejected. Reversing the two input reads remained valid. The missing check is the actionable defect; the read-order difference is not.');
save('PROPOSAL.md','# One general edit\n\nReplace the limited field list with all required fields from the contract. Keep the runner, checker, contract, and fixture oracles fixed. No field name or answer from the current case is included in the new instruction.');
save('candidate-skill.md','# Report audit\n\nCheck fields: all required');
const qstart=performance.now(),candidate=readFileSync(resolve(out,'candidate-skill.md'),'utf8');
const parent=readFileSync(resolve(out,'parent-skill.md'),'utf8');
const quality=candidate.trim()==='# Report audit\n\nCheck fields: all required'&&candidate.length<=parent.length+40&&!/Split|Target|Metric|missing|complete/.test(candidate);
save('QUALITY.md','# Proposal quality gate\n\n'+(quality?'PASS':'REJECT')+'\n\nOne allowed general operation; no fixture field names or answer literals; growth <= 40 characters. This gate recognizes a tiny declarative language. It is not a general leakage detector.');
costs.push(['candidate','quality gate',(performance.now()-qstart).toFixed(3)]);
if(!quality)throw Error('Candidate rejected before evaluation');
const candidateHash=hash(resolve(out,'candidate-skill.md'));
save('CANDIDATE-FREEZE.md','# Before candidate evaluation\n\nSHA-256: '+candidateHash+'\nQuality gate passed. Two evaluation slots allocated.');
const outcomes=[];
for(const [fixture,expected] of [['current.md','missing Split'],['prior.md','complete']]){
 if(++evaluations>2)throw Error('Evaluation budget exhausted');
 const label='candidate-'+fixture.replace('.md',''),actual=execute(label,fixture,'candidate-skill.md');
 const passed=actual===expected;outcomes.push(passed);
 save(label+'/EVALUATION.md','# Fixture evaluation\n\nExpected: '+expected+'\nObserved: '+actual+'\nVerdict: '+(passed?'PASS':'REJECT'));
}
for(const [p,h] of Object.entries(frozen))if(hash(resolve(out,p))!==h)throw Error('Frozen file changed: '+p);
if(hash(resolve(out,'candidate-skill.md'))!==candidateHash)throw Error('Candidate changed during evaluation');
const keep=outcomes.every(Boolean);
save('PROMOTION.md','# Local decision\n\n'+(keep?'RETAIN':'REJECT')+' candidate.\n\nBoth fixture outcomes match their predeclared oracles. The prior control is complete; no newly measured parent/prior result is claimed. Candidate and input hashes remained fixed. Retention applies only to this constructed exercise, not general agent competence.');
save('COST.csv','case,operation,wall_ms\n'+costs.map(x=>x.join(',')).join('\n'));
save('PROGRESS.md','# Author progress\n\nFour traces generated and checked; one proposal; one quality gate; two candidate fixture executions; zero fits. No execution allowance remains. Predictions, teach-back, and quiz were not tested with a learner. Agent inference cost is unknown. All cases share author context; instrumentation is trusted.');
const files=[];function walk(dir=''){for(const e of readdirSync(resolve(out,dir),{withFileTypes:true})){const p=dir?dir+'/'+e.name:e.name;if(e.isDirectory())walk(p);else files.push(p);}}walk();
save('MANIFEST.csv','file,sha256\n'+files.sort().map(p=>p+','+hash(resolve(out,p))).join('\n'));
if(!keep)throw Error('Candidate failed fixture gate; records preserved');
console.log('Four trace checks, one quality gate, two candidate evaluations completed. Workspace: '+out);
