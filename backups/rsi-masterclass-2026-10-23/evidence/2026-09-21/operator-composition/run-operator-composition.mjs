// A deterministic, explicitly synthetic author exercise; no model training.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const out=resolve(repo,'../rsi-work-2026-09-21-operator-composition');
if(existsSync(out))throw Error('Preserve the earlier workspace.');
mkdirSync(out);
const save=(p,s)=>{mkdirSync(dirname(resolve(out,p)),{recursive:true});writeFileSync(resolve(out,p),s.trimEnd()+'\n');};
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const copy=s=>structuredClone(s);
const render=s=>Object.entries(s).map(([k,v])=>k+': '+v).join('\n');
copyFileSync(script,resolve(out,'run-operator-composition.mjs'));
copyFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/OPERATOR-COMPOSITION-PROTOCOL.md'),resolve(out,'PROTOCOL.md'));
save('OPERATORS.md','# Synthetic operator contracts\n\n| Operator | Reads | Writes |\n|---|---|---|\n| data | data, task | data.version, data.format |\n| harness | harness, task | harness.version, harness.format |\n| model | data, harness, model | model.version, model.format |\n\nData records task format. Harness supports task format. Model requires a data record and copies current harness format. This is a stub, never training. All evidence also records the current task and complete version vector.');
save('EVALUATOR.md','# Fixed synthetic evaluator\n\n50 points if harness.format equals task.format; 50 if model.format equals task.format. No accuracy interpretation. Operators cannot write this file.');
save('scheduler-q0.md','# Scheduler\n\nOrder: data, model, harness\nBefore model: continue');
const base={'data.version':0,'data.format':0,'harness.version':0,'harness.format':0,'model.version':0,'model.format':0,'task.format':1};
save('INITIAL.md','# Initial synthetic state\n\n'+render(base));
const frozen=Object.fromEntries(['OPERATORS.md','EVALUATOR.md','INITIAL.md','scheduler-q0.md'].map(p=>[p,hash(resolve(out,p))]));
save('FREEZE.md','# Frozen before execution\n\n'+render(frozen)+'\nDriver SHA-256: '+hash(script)+'\nNode: '+process.version+'; '+process.platform+' '+process.arch);
const contracts={data:{read:['data','task'],write:['data.version','data.format']},harness:{read:['harness','task'],write:['harness.version','harness.format']},model:{read:['data','harness','model'],write:['model.version','model.format']}};
let attempts=0,evaluations=0,cases=0;const costs=[],actions=[];
const evidence=s=>Object.fromEntries(Object.entries(s).filter(([k])=>k.endsWith('.version')||k==='task.format'));
const equal=(a,b)=>render(a)===render(b);
function apply(label,op,state,ev,forbidden=false){
 if(++attempts>12)throw Error('Operator attempt limit exhausted');
 const start=performance.now(),folder=label+'/attempt-'+attempts;
 save(folder+'/BEFORE.md','# Before '+op+'\n\nSynthetic state:\n'+render(state)+'\n\nEvidence:\n'+render(ev)+'\n\nContract reads: '+contracts[op].read.join(', ')+'\nAllowed writes: '+contracts[op].write.join(', '));
 let reason=null,next=copy(state),patch={};
 if(!equal(ev,evidence(state)))reason='stale evidence';
 else {
  const read=key=>{if(!contracts[op].read.includes(key.split('.')[0]))throw Error('Undeclared read: '+key);return state[key];};
  patch[op+'.version']=read(op+'.version')+1;
  if(op==='data'||op==='harness')patch[op+'.format']=read('task.format');
  else {if(read('data.version')<1)reason='model needs a data record';patch['model.format']=read('harness.format');}
  if(forbidden)patch['evaluator.score']=999;
  if(Object.keys(patch).some(k=>!contracts[op].write.includes(k)))reason='undeclared write';
 }
 if(!reason)Object.assign(next,patch);
 save(folder+'/AFTER.md','# Operator result\n\n'+(reason?'REJECT: '+reason:'ACCEPT synthetic state update')+'\n\nProposed patch:\n'+render(patch)+'\n\nState after:\n'+render(next));
 const elapsed=(performance.now()-start).toFixed(3);costs.push([label,op,elapsed]);actions.push([label,attempts,op,reason||'accepted']);
 return {state:next,reason};
}
function score(state){if(++evaluations>3)throw Error('Evaluator call limit exhausted');return 50*Number(state['harness.format']===state['task.format'])+50*Number(state['model.format']===state['task.format']);}
function schedule(label,initial,order,policy=null){
 if(++cases>5)throw Error('Schedule-check limit exhausted');
 let state=copy(initial);const pending=[...order],executed=[];
 save(label+'/START.md','# Synthetic schedule input\n\n'+render(initial)+'\n\nProposed order: '+order.join(' → ')+'\nPolicy: '+(policy||'explicit order comparison'));
 while(pending.length){
  let op=pending.shift();
  if(op==='model'&&policy){
   const text=readFileSync(resolve(out,policy),'utf8');
   const rule=/^Before model: (.+)$/m.exec(text)?.[1];
   const compatible=state['harness.format']===state['task.format'];
   save(label+'/POLICY-USE-'+(executed.length+1)+'.md','# Loaded scheduler before model\n\nFile: '+policy+'\nSHA-256: '+hash(resolve(out,policy))+'\nRule: '+rule+'\nCompatible: '+compatible+'\nPending: '+pending.join(', '));
   if(rule==='check interface; move pending harness before model'&&!compatible){
    const at=pending.indexOf('harness');if(at<0)throw Error('No pending harness to repair compatibility');
    pending.splice(at,1);pending.unshift('model');op='harness';
   }
  }
  const result=apply(label,op,state,evidence(state));if(result.reason)throw Error('Allowed schedule rejected');state=result.state;executed.push(op);
 }
 const points=score(state);
 save(label+'/RESULT.md','# Synthetic schedule result\n\nExecuted: '+executed.join(' → ')+'\nSynthetic points: '+points+'\n\n'+render(state));
 return {state,points,executed};
}
const first=schedule('01-harness-before-model',base,['data','harness','model']);
const second=schedule('02-model-before-harness',base,['data','model','harness']);
if(first.points!==100||second.points!==50)throw Error('Order contrast not observed');
cases++;
const staleStart=copy(first.state),oldEvidence=evidence(staleStart);
// A legal repeated harness update changes its version even when its supported format is unchanged.
const changed=apply('03-stale-evidence','harness',staleStart,oldEvidence);
const rejected=apply('03-stale-evidence','model',changed.state,oldEvidence);
if(changed.reason||rejected.reason!=='stale evidence'||!equal(changed.state,rejected.state))throw Error('Stale-evidence check failed');
save('03-stale-evidence/RESULT.md','# Stale evidence\n\nHarness version changed. The model attempt using the old version vector was rejected without mutation.');
cases++;
const unauthorized=apply('04-forbidden-write','data',base,evidence(base),true);
if(unauthorized.reason!=='undeclared write'||!equal(unauthorized.state,base))throw Error('Forbidden-write check failed');
save('04-forbidden-write/RESULT.md','# Forbidden write\n\nData attempted evaluator.score. The whole patch was rejected; state and evaluator were unchanged.');
save('PROPOSAL.md','# One scheduler revision\n\nThe two same-start schedules scored 100 and 50 under the fixed synthetic rule. Model copied an older harness format when scheduled first. Add a pre-model interface check that moves the pending harness operation ahead when needed. Keep Q0, the base order, operator contracts, and evaluator fixed. This conclusion follows from our constructed rule, not real model behavior.');
save('scheduler-q1.md',readFileSync(resolve(out,'scheduler-q0.md'),'utf8').replace('Before model: continue','Before model: check interface; move pending harness before model'));
const policy=readFileSync(resolve(out,'scheduler-q1.md'),'utf8');
const allowed=policy.trim()==='# Scheduler\n\nOrder: data, model, harness\nBefore model: check interface; move pending harness before model';
save('POLICY-GATE.md','# Static policy gate\n\n'+(allowed?'PASS':'REJECT')+'\n\nOne allowed pre-model rule; original order preserved; no evaluator or operator edit. Activation is for the one allocated later demonstration, not proof of a generally better scheduler.');
if(!allowed)throw Error('Policy gate rejected');
const policyHash=hash(resolve(out,'scheduler-q1.md'));
save('POLICY-FREEZE.md','# Before later term\n\nQ1 SHA-256: '+policyHash+'\n\nCarry the released state from check 1. The later constructed task requests format 2, making the inherited format 1 incompatible. This task shift is explicit and author-known.');
const later=copy(first.state);later['task.format']=2;
const order=/^Order: (.+)$/m.exec(policy)[1].split(', ');
const inherited=schedule('05-inherited-scheduler',later,order,'scheduler-q1.md');
if(inherited.points!==100||inherited.executed.join(',')!=='data,harness,model')throw Error('Saved rule did not govern the later term');
for(const [p,h] of Object.entries(frozen))if(hash(resolve(out,p))!==h)throw Error('Frozen artifact changed');
if(hash(resolve(out,'scheduler-q1.md'))!==policyHash)throw Error('Saved scheduler changed');
save('ACTIONS.csv','case,attempt,operator,verdict\n'+actions.map(x=>x.join(',')).join('\n'));
save('COST.csv','case,operator,wall_ms\n'+costs.map(x=>x.join(',')).join('\n'));
save('RESULTS.md','# Observed synthetic mechanisms\n\nFive schedule checks, twelve operator attempts including two rejections, one static scheduler gate, three synthetic evaluator calls. Q1 was loaded and used in the later term; hashes stayed fixed. No model fits. Two schedule orders produced 100 and 50 synthetic points from the same state. The later Q1 case scored 100; Q0 was not rerun on that later task. These constructed scores cannot establish an empirical RSI advantage. Agent inference and complete authoring cost are not measured.');
save('PROGRESS.md','# Author progress\n\nAll allocated simulation actions complete; no allowance remains. Source reading is separate. Learner prediction, teach-back, and quiz untested.');
const files=[];function walk(dir=''){for(const e of readdirSync(resolve(out,dir),{withFileTypes:true})){const p=dir?dir+'/'+e.name:e.name;if(e.isDirectory())walk(p);else files.push(p);}}walk();
save('MANIFEST.csv','file,sha256\n'+files.sort().map(p=>p+','+hash(resolve(out,p))).join('\n'));
console.log('Five schedule checks completed; twelve attempts; zero fits. Workspace: '+out);
