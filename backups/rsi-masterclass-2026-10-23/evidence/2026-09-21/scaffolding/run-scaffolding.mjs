// Agent-operated form environment. This driver checks actions; it does not choose them.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url), repo=resolve(dirname(script),'../../..');
const [command,destination,condition,field,value]=process.argv.slice(2);
if(!destination)throw Error('Supply a sibling workspace');
const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use a sibling workspace');
const names=['action','observation','fresh','stale'];
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent=p=>{if(existsSync(join(out,p)))throw Error('Preserve existing artifact: '+p);};
const table=(p,rows)=>save(p,rows.map(r=>r.join(',')).join('\n'));
const rows=p=>read(p).trimEnd().split('\n').slice(1).map(r=>r.split(','));
if(command==='prepare'){
  absent('PROTOCOL.md');mkdirSync(out,{recursive:true});
  copyFileSync(script,join(out,'run-scaffolding.mjs'));
  copyFileSync(join(repo,'how-did-i-generate-it/rsi/validation/SCAFFOLDING-PROTOCOL.md'),join(out,'PROTOCOL.md'));
  copyFileSync(join(repo,'how-did-i-generate-it/rsi/research/2026-09-21-SCAFFOLDING-AUDIT.md'),join(out,'SOURCE-AUDIT.md'));
  for(const name of names){
    const required=name==='fresh'?['wine','stratified','macro_f1']:['bike','chronological','MAE'];
    const missing={action:1,observation:1,fresh:0,stale:2}[name];
    const fixture=['Dataset','Split','Metric'].map((f,i)=>[f,required[i],i===missing?'':required[i]]);
    table(name+'/ORIGINAL.csv',[['field','required','initial'],...fixture]);
    table(name+'/STATE.csv',[['field','value'],...fixture.map(r=>[r[0],r[2]])]);
    const help={action:'Action hint: Inspect Split next.',observation:'Observation: The Split field is empty.',fresh:'No added hint or enriched observation.',stale:'Action hint: Inspect Split next.\n\nObservation: The Metric field is empty. The action hint may be outdated.'}[name];
    save(name+'/PACKET.md',`# ${name} condition\n\nComplete the experiment form. Required values: ${fixture.map(r=>r[0]+' = '+r[1]).join('; ')}.\n\n${help}\n\nInspect fields by name. Repair one field. Then submit one final check. At most three inspections, one repair, one check. The packet states task requirements; current field values come from inspection.`);
    table(name+'/TRACE.csv',[['sequence','time_utc','command','field','value','output']]);
  }
  const files=['run-scaffolding.mjs','PROTOCOL.md','SOURCE-AUDIT.md',...names.flatMap(n=>[n+'/ORIGINAL.csv',n+'/PACKET.md'])];
  table('FROZEN.csv',[['path','sha256'],...files.map(p=>[p,sha(join(out,p))])]);
  console.log('Four fixtures frozen. No task actions executed.');
}else if(command==='seal'){
  absent('MANIFEST.csv');
  for(const n of names)if(!existsSync(join(out,n,'CHECK.md')))throw Error('Missing check: '+n);
  const results=names.map(n=>{const trace=rows(n+'/TRACE.csv');return[n,trace.filter(r=>r[2]==='inspect').length,trace.filter(r=>r[2]==='repair').length,read(n+'/CHECK.md').includes('Pass: true')];});
  table('RESULTS.csv',[['condition','inspections','repairs','pass'],...results]);
  const walk=p=>readdirSync(p).sort().flatMap(n=>{const full=join(p,n);return statSync(full).isDirectory()?walk(full):[full];});
  table('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
  console.log(read('RESULTS.csv'));
}else{
  if(!names.includes(condition)||!['inspect','repair','check'].includes(command))throw Error('Invalid command or condition');
  absent(condition+'/CHECK.md');
  for(const [p,hash]of rows('FROZEN.csv'))if(sha(join(out,p))!==hash)throw Error('Frozen file changed: '+p);
  const trace=rows(condition+'/TRACE.csv'),state=rows(condition+'/STATE.csv'),original=rows(condition+'/ORIGINAL.csv');
  const target=state.find(r=>r[0]===field);let output;
  if(command==='inspect'){
    if(!target||trace.filter(r=>r[2]==='inspect').length>=3)throw Error('Invalid inspection or exhausted budget');
    output=target[1]||'<empty>';
  }else if(command==='repair'){
    if(!target||value===undefined||/[\r\n,]/.test(value)||trace.some(r=>r[2]==='repair'))throw Error('Invalid repair or exhausted budget');
    if(!trace.some(r=>r[2]==='inspect'&&r[3]===field))throw Error('Inspect the field before repair');
    target[1]=value;table(condition+'/STATE.csv',[['field','value'],...state]);output='saved';
  }else{
    const correct=state.every(([f,v])=>v===original.find(r=>r[0]===f)[1]);
    const preserved=original.filter(r=>r[2]!=='').every(r=>state.find(s=>s[0]===r[0])[1]===r[2]);
    const pass=correct&&preserved&&trace.filter(r=>r[2]==='repair').length===1;
    output=pass?'PASS':'FAIL';
    save(condition+'/CHECK.md',`# Exact form check\n\nPass: ${pass}\nAll required values present: ${correct}\nInitially correct fields preserved: ${preserved}\nOne repair: ${trace.filter(r=>r[2]==='repair').length===1}\nNo further attempt allowed.`);
  }
  table(condition+'/TRACE.csv',[['sequence','time_utc','command','field','value','output'],...trace,[trace.length+1,new Date().toISOString(),command,field||'-',value||'-',output]]);
  console.log(`${condition} ${command} ${field||''}: ${output}`);
}
