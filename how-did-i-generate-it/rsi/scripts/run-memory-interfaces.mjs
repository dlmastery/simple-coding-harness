// Phased author walkthrough; memory answers are supplied by the coding agent.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');
const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent=p=>{if(existsSync(join(out,p)))throw Error('Preserve existing phase: '+p);};
const identity=p=>sha(join(out,p));
const fields=s=>Object.fromEntries(s.split(/\r?\n/).filter(x=>x.includes(': ')).map(x=>{const i=x.indexOf(': ');return[x.slice(0,i),x.slice(i+2)];}));
const table=(p,cols,data)=>save(p,[cols,...data].map(row=>row.map(String).map(v=>/[",\n]/.test(v)?'"'+v.replaceAll('"','""')+'"':v).join(',')).join('\n'));
const conditions=['raw','summary','faulty','raw-expanded','summary-expanded'];
if(phase==='prepare'){
  if(existsSync(out))throw Error('Preserve existing workspace');mkdirSync(out);
  copyFileSync(script,join(out,'run-memory-interfaces.mjs'));
  copyFileSync(join(repo,'how-did-i-generate-it/rsi/validation/MEMORY-INTERFACES-PROTOCOL.md'),join(out,'PROTOCOL.md'));
  const old='rsi/evidence/2026-09-21/meta-skills/10-17';
  const sources=[['v0/TASK-PROPOSAL.md','10-27/raw/FAILED-PROPOSAL.md'],['v0/external-unknown/INPUT.csv','10-27/raw/INPUT.csv'],['v0/external-unknown/RESULT.md','10-27/raw/RESULT.md'],['v0/external-unknown/CONVERSIONS.csv','10-27/raw/CONVERSIONS.csv'],['v1/TASK-PROPOSAL.md','10-27/ACTIVE-SKILL.md']];
  for(const [source,target]of sources){mkdirSync(dirname(join(out,target)),{recursive:true});copyFileSync(join(repo,old,source),join(out,target));}
  table('10-27/SOURCES.csv',['source','copy','sha256'],sources.map(([s,t])=>[old+'/'+s,t,identity(t)]));
  save('10-27/TRACE.md','# Prior observed failure\n\nThe copied proposal chose A when the fixed unknown-unit case required refusal. Inspect raw/RESULT.md, raw/INPUT.csv, and raw/CONVERSIONS.csv. These are actual archived decisions from the meta-skill walkthrough, not invented measurements. Original identities are in SOURCES.csv.');
  save('10-27/NOTEBOOK.md','# Retained knowledge\n\nThe prior unknown-unit identity fallback selected a candidate from uninterpretable duration metadata. Source: raw/RESULT.md and raw/CONVERSIONS.csv. Scope: the constructed ticks case, not every possible unit convention. Preserve an explicit conversion contract or refuse this comparison. This note is knowledge for the improver, not an automatically promoted task instruction.');
  save('10-27/BOUNDARY.md','# Information roles\n\nThe improver may read trace, notebook, active skill, and proposal. Each scripted task check reads only its supplied proposed skill snapshot and case. The author has access to every artifact and prior knowledge; these role instructions do not isolate the coding agent. Instrumented read logs describe the scripted path, not every possible filesystem access.');
  const locked=['10-27/TRACE.md','10-27/ACTIVE-SKILL.md',...sources.filter(([,t])=>t.includes('/raw/')).map(([,t])=>t)];
  table('10-27/FROZEN.csv',['path','sha256'],locked.map(p=>[p,identity(p)]));
}else if(phase==='wiki'){
  absent('10-27/CHECKS.csv');if(!existsSync(join(out,'10-27/PROPOSAL-NOTE.md')))throw Error('Actor proposal note required');
  const skill='10-27/PROPOSED-SKILL.md', configuration=fields(read(skill));
  const checks=[];
  for(const [name,values,expected]of [['seconds',[['A',.8,'second'],['B',1,'second']],'A'],['unknown',[['A',.001,'tick'],['B',1,'second']],'refused']]){
    const base='10-27/check-'+name;
    table(base+'/INPUT.csv',['candidate','duration','unit'],values);
    // Read the case back from its file, keeping actual reads inspectable.
    const input=read(base+'/INPUT.csv').trim().split('\n').slice(1).map(x=>x.split(','));
    table(base+'/READS.csv',['role','path','sha256'],[['scripted actor',skill,identity(skill)],['scripted actor',base+'/INPUT.csv',identity(base+'/INPUT.csv')]]);
    let refused=false;const candidates=[];
    for(const [candidate,duration,unit]of input){const factor=configuration['Seconds per '+unit];if(factor===undefined&&configuration['Unknown units']==='refuse'){refused=true;break;}candidates.push([candidate,Number(duration)*Number(factor??1)]);}
    candidates.sort((x,y)=>x[1]-y[1]||x[0].localeCompare(y[0]));
    const actual=refused?'refused':candidates[0][0],pass=actual===expected;
    save(base+'/RESULT.md',`# Executed fixture\n\nActual: ${actual}\nExpected: ${expected}\nPass: ${pass}\nBoth candidate MAEs are equal by fixture design. No model fit occurs.`);
    checks.push([name,actual,expected,pass]);
  }
  table('10-27/CHECKS.csv',['case','actual','expected','pass'],checks);
  const pass=checks.every(x=>x[3]);
  save('10-27/DECISION.md',`# Gate result\n\nDecision: ${pass?'candidate eligible':'reject proposed skill; keep active skill'}\nRule: both fixture checks must pass.\nActive SHA-256: ${identity('10-27/ACTIVE-SKILL.md')}\nThe proposal is retained separately; it has not replaced ACTIVE-SKILL.md.`);
  console.log(read('10-27/CHECKS.csv'));
}else if(phase==='expose'){
  absent('10-27/exposure/READS.csv');
  const reads=[];let packet='# Separate exposure condition\n\n';
  for(const p of ['10-27/ACTIVE-SKILL.md','10-27/NOTEBOOK.md']){const content=read(p);reads.push(['scripted actor',p,identity(p),content.length]);packet+='## Read '+p+'\n\n'+content+'\n';}
  table('10-27/exposure/READS.csv',['role','path','sha256','characters'],reads);save('10-27/exposure/PACKET.md',packet);
  save('10-27/exposure/RESULT.md','# Changed information interface\n\nThe scripted actor actually read the active skill and the updated notebook. No task answer or third fixture was run. This demonstrates an expanded packet, not a measured performance benefit or isolated coding-agent context.');
}else if(phase==='memory-prepare'){
  absent('10-32');
  const events=[7,-2,4,-3,5,-1,2,-4];
  table('10-32/ORIGINAL-EVENTS.csv',['event','delta'],events.map((v,i)=>[i+1,v]));
  const checkpoint=events.slice(0,4).reduce((s,v)=>s+v,0),faulty=events.slice(0,3).reduce((s,v)=>s+v,0);
  const expansion=' The crate labels are printed on plain cardboard. The shelf description records packaging color and storage location. These descriptive words do not change inventory.';
  const render=(start,long)=>events.slice(start).map((v,i)=>`Event ${start+i+1}: ${v>0?'add':'remove'} ${Math.abs(v)} crates.${long?expansion.repeat(3):''}`).join('\n');
  for(const condition of conditions){const summary=!condition.startsWith('raw'),long=condition.endsWith('expanded');const state=condition==='faulty'?faulty:checkpoint;const content='# Recover the final inventory\n\nReturn Answer: N and a short calculation, at most 60 words. Use only this supplied representation for the answer.\n\n'+(summary?`Checkpoint after event 4: ${state} crates.\nThe earlier events are replaced by this summary.\n`:'Start with zero crates.\n')+render(summary?4:0,long);save('10-32/'+condition+'/PACKET.md',content);}
  table('10-32/PACKET-FREEZE.csv',['condition','sha256','characters','whitespace_words'],conditions.map(c=>{const s=read('10-32/'+c+'/PACKET.md');return[c,identity('10-32/'+c+'/PACKET.md'),s.length,s.trim().split(/\s+/).length];}));
  save('10-32/CHECKPOINT.md',`# Summary boundary\n\nCheckpoint: after event 4\nCorrect state: ${checkpoint}\nFaulty state: ${faulty}\nFault: omit the fourth removal when preparing the summary.\nThe exact final answer is not placed in an actor packet. The shared author designed these cases and can read all files; there is no technical secrecy.`);
}else if(phase==='memory-check'){
  absent('10-32/RESULTS.csv');
  const events=read('10-32/ORIGINAL-EVENTS.csv').trim().split('\n').slice(1).map(x=>Number(x.split(',')[1]));
  const expected=events.reduce((s,v)=>s+v,0);const results=[];
  for(const c of conditions){const answer=read('10-32/'+c+'/ANSWER.md');const words=answer.trim().split(/\s+/).length;if(words>60)throw Error('Answer budget exceeded');const actual=Number(fields(answer).Answer);if(!Number.isFinite(actual))throw Error('Missing answer');const pass=actual===expected;save('10-32/'+c+'/CHECK.md',`# Exact event check\n\nActor answer: ${actual}\nOriginal-event result: ${expected}\nPass: ${pass}\nAnswer words: ${words}\nGround truth is calculated from ORIGINAL-EVENTS.csv, not the supplied summary.`);results.push([c,actual,expected,pass,words,identity('10-32/'+c+'/PACKET.md'),identity('10-32/'+c+'/ANSWER.md')]);}
  table('10-32/RESULTS.csv',['condition','answer','expected','pass','answer_words','packet_sha256','answer_sha256'],results);console.log(read('10-32/RESULTS.csv'));
}else if(phase==='seal'){
  absent('MANIFEST.csv');
  for(const line of read('10-27/FROZEN.csv').trim().split('\n').slice(1)){const [p,h]=line.split(',');if(identity(p)!==h)throw Error('Frozen artifact changed: '+p);}
  for(const line of read('10-32/PACKET-FREEZE.csv').trim().split('\n').slice(1)){const [c,h]=line.split(',');if(identity('10-32/'+c+'/PACKET.md')!==h)throw Error('Packet changed');}
  save('COST.md','# Counted actions\n\nWiki task checks: 2\nSeparate notebook exposure reads: 1 condition with 2 files\nMemory actor answers and exact checks: 5\nModel fits and weight updates: 0\n\nPacket lengths are characters and whitespace words, not model tokens. Agent/provider costs and independent per-condition inference latency are unavailable. No efficiency superiority follows from these lengths alone.');
  for(const lab of ['10-27','10-32'])save(lab+'/LAB-NOTE.md','# Author walkthrough\n\nLearner prediction, teach-back, and quiz: not attempted. The same author sees all conditions. Read the interface report for actual scripted reads, source exposure, and remaining limits.');
  save('PROGRESS.md','# Declared activities complete\n\nTwo wiki checks, one exposure-only condition, and five memory answers/checks completed. No live process or remaining attempts. No model fits occurred. Preserve failures and all earlier versions before publication.');
  const collect=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?collect(join(dir,e.name)):[join(dir,e.name)]);
  table('MANIFEST.csv',['path','bytes','sha256'],collect(out).sort().map(p=>[relative(out,p).split(sep).join('/'),statSync(p).size,sha(p)]));
}else throw Error('Unknown phase');
console.log('Completed '+phase);
