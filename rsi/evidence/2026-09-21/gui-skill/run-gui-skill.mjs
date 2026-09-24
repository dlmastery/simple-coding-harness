// Local evidence page and recorder. Browser actions are performed by the coding agent.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [command,destination,arg]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');
const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const absent=p=>{if(existsSync(join(out,p)))throw Error('Preserve existing artifact: '+p);};
const table=(p,rs)=>save(p,rs.map(r=>r.join(',')).join('\n'));
const rows=p=>read(p).trimEnd().split(/\r?\n/).slice(1).map(r=>r.split(','));
const freeze=()=>{for(const [p,h]of rows('FROZEN.csv'))if(sha(join(out,p))!==h)throw Error('Frozen input changed: '+p);};
if(command==='prepare'){
  absent('PROTOCOL.md');mkdirSync(out,{recursive:true});copyFileSync(script,join(out,'run-gui-skill.mjs'));
  for(const [source,target]of [['validation/GUI-SKILL-PROTOCOL.md','PROTOCOL.md'],['research/2026-09-21-GUI-SKILL-AUDIT.md','SOURCE-AUDIT.md']])copyFileSync(join(repo,'how-did-i-generate-it/rsi',source),join(out,target));
  const root='rsi/evidence/2026-09-21/scientist-labs/10-19/';
  const sources=[['screen/forest/RESULT.md','sources/screen-result.md'],['SCREENING-PLAN.md','sources/screening-plan.md'],['confirmation/experiment/trials.csv','sources/full-trials.csv'],['confirmation/experiment/CONTRACT.md','sources/full-contract.md'],['confirmation/experiment/trial-001/CHECK.md','sources/forest-check.md'],['confirmation/experiment/trial-002/CHECK.md','sources/linear-check.md']];
  mkdirSync(join(out,'sources'),{recursive:true});
  for(const [src,dst]of sources)copyFileSync(join(repo,root,src),join(out,dst));
  table('SOURCES.csv',[['repository_path','copy','sha256'],...sources.map(([s,d])=>[root+s,d,sha(join(out,d))])]);
  const screen=Number(read('sources/screen-result.md').match(/Selection MAE: ([\d.]+)/)[1]),full=rows('sources/full-trials.csv');
  table('CANDIDATES.csv',[['candidate','model','mae','scope'],['A','forest',screen,'screen'],['B','forest',full.find(r=>r[0]==='trial-001')[6],'full'],['C','linear',full.find(r=>r[0]==='trial-002')[6],'full']]);
  save('TASK.md','# Selection task\n\nSelect the lowest-MAE valid candidate trained on full 2011 data and evaluated on January–June 2012. Inspect results using the local page. A smaller error from a different evaluation subset is ineligible.');
  save('SKILL-v1.md','# Inspect experiment results\n\n1. Filter the model table to forest.\n2. Select the row with the lowest displayed MAE.\n\nThis deliberately deficient teaching control omits validity inspection. It is not a recommended student procedure.');
  const page=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Experiment review · lab 10.29</title><style>body{font:17px/1.6 system-ui;background:#f6f8fb;color:#172b40;margin:0}main{max-width:940px;margin:40px auto;background:white;padding:38px;border:1px solid #dce4ed;border-radius:16px}h1{font-size:32px;margin:0}small{color:#547085}table{width:100%;border-collapse:collapse;margin:20px 0}th,td{text-align:left;padding:12px;border-bottom:1px solid #dee6ef}button,input{font:inherit;padding:8px 14px;border:1px solid #aac0d5;border-radius:6px}button{background:#edf4fb;cursor:pointer}button:disabled{opacity:.45}#detail{background:#fff8e6;padding:18px;border-left:4px solid #e5b544}#status{font-weight:650}#work[hidden],#detail[hidden]{display:none}</style><main><small>RSI RESEARCH STUDIO · 10.29</small><h1>Inspect before you select</h1><p>Select the lowest-MAE valid candidate trained on full 2011 data and evaluated on January–June 2012. A smaller error from a different evaluation subset is ineligible.</p><p>Saved bike-rental results. Lower MAE is better. This page runs no models.</p><button id="start">Start attempt</button><section id="work" hidden><p><label for="filter">Filter model</label> <input id="filter" placeholder="For example: forest"> <button id="apply">Apply filter</button></p><table><thead><tr><th>Candidate</th><th>Model</th><th>MAE</th><th>Inspect</th><th>Choose</th></tr></thead><tbody id="body"></tbody></table><section id="detail" hidden></section></section><p id="status" role="status">No attempt started.</p></main><script>
const candidates=${JSON.stringify(rows('CANDIDATES.csv').map(([id,model,mae,scope])=>({id,model,mae:Number(mae),scope})))};
let attempt,closed=false;const $=id=>document.getElementById(id);
async function record(action,value='-'){const r=await fetch('/event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({attempt,action,value})});if(!r.ok)throw Error(await r.text());return r.text();}
function render(){const q=$('filter').value.trim().toLowerCase();$('body').replaceChildren();for(const c of candidates.filter(c=>c.model.includes(q))){const tr=document.createElement('tr');for(const text of [c.id,c.model,c.mae.toFixed(6)]){const td=document.createElement('td');td.textContent=text;tr.append(td);}for(const action of ['Details','Select']){const td=document.createElement('td'),button=document.createElement('button');button.textContent=action+' '+c.id;button.disabled=closed;button.onclick=async()=>{await record(action.toLowerCase(),c.id);if(action==='Details'){$('detail').hidden=false;$('detail').textContent=c.id+': '+(c.scope==='screen'?'Ineligible for this task. Training: January–March 2011. Evaluation: January 2012 only (741 rows). This is a valid screening result, but its scope differs from the required full comparison.':'Eligible for this task. Training: full 2011. Evaluation: January–June 2012. Prediction check passed.');}else{closed=true;$('status').textContent='Selection recorded: '+c.id+'. Attempt complete.';$('filter').disabled=true;$('apply').disabled=true;render();}};td.append(button);tr.append(td);}$('body').append(tr);}}
$('start').onclick=async()=>{attempt=Number(await record('begin'));$('start').disabled=true;$('work').hidden=false;$('status').textContent='Attempt '+attempt+' active.';render();};
$('apply').onclick=async()=>{await record('filter',$('filter').value.trim().toLowerCase());$('detail').hidden=true;render();};
</script></html>`;
  save('index.html',page);
  const files=['index.html','CANDIDATES.csv','TASK.md','SKILL-v1.md','PROTOCOL.md','SOURCE-AUDIT.md','run-gui-skill.mjs',...sources.map(s=>s[1])];
  table('FROZEN.csv',[['path','sha256'],...files.map(p=>[p,sha(join(out,p))])]);console.log('Prepared and frozen. No UI attempts yet.');
}else if(command==='serve'){
  freeze();const port=Number(arg||8769);let active=0,closed=true;
  for(let i=1;i<=2;i++)if(existsSync(join(out,'attempt-'+i,'TRACE.csv')))throw Error('Do not restart this server over recorded attempts');
  createServer(async(req,res)=>{try{
    if(req.method==='GET'&&req.url==='/'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(read('index.html'));return;}
    if(req.method!=='POST'||req.url!=='/event'){res.writeHead(404);res.end('Not found');return;}
    const chunks=[];let bytes=0;for await(const b of req){bytes+=b.length;if(bytes>4096)throw Error('Request too large');chunks.push(b);}
    const event=JSON.parse(Buffer.concat(chunks).toString());freeze();
    let response='Recorded';
    if(event.action==='begin'){
      if(!closed||active>=2)throw Error('Two-attempt limit or active attempt');
      if(active===1&&!existsSync(join(out,'SKILL-v2.md')))throw Error('Save the revised skill first');
      active++;closed=false;response=String(active);
      table('attempt-'+active+'/TRACE.csv',[['sequence','time_utc','action','value']]);
      copyFileSync(join(out,'SKILL-v'+active+'.md'),join(out,'attempt-'+active,'SKILL-SNAPSHOT.md'));
    }else{
      if(closed||event.attempt!==active)throw Error('No matching active attempt');
      if(!['filter','details','select'].includes(event.action))throw Error('Unknown action');
      if(typeof event.value!=='string'||/[\r\n,]/.test(event.value))throw Error('Invalid action value');
      if(event.action!=='filter'&&!['A','B','C'].includes(event.value))throw Error('Unknown candidate');
      if(event.action==='select'){closed=true;save('attempt-'+active+'/SELECTION.md','# UI selection\n\nSelected: '+event.value);}
    }
    const p='attempt-'+active+'/TRACE.csv',trace=rows(p);table(p,[['sequence','time_utc','action','value'],...trace,[trace.length+1,new Date().toISOString(),event.action,event.value||'-']]);
    res.end(response);
  }catch(e){res.writeHead(400);res.end(e.message);}}).listen(port,'127.0.0.1',()=>console.log('Evidence page: http://127.0.0.1:'+port+'/'));
}else if(command==='check'){
  freeze();if(!['1','2'].includes(arg))throw Error('Choose attempt 1 or 2');const base='attempt-'+arg;absent(base+'/CHECK.md');
  const selected=read(base+'/SELECTION.md').match(/Selected: ([ABC])/)[1],eligible=rows('CANDIDATES.csv').filter(r=>r[3]==='full').sort((a,b)=>Number(a[2])-Number(b[2])||a[0].localeCompare(b[0]));
  save(base+'/CHECK.md',`# Fixed selected-candidate check\n\nSelected: ${selected}\nExpected: ${eligible[0][0]}\nPass: ${selected===eligible[0][0]}\nRule: minimum MAE among full-scope candidates. The UI selection is read from the server record. No model fit or additional UI attempt occurs.`);console.log(read(base+'/CHECK.md'));
}else if(command==='seal'){
  absent('MANIFEST.csv');freeze();for(const i of [1,2])if(!existsSync(join(out,'attempt-'+i,'CHECK.md')))throw Error('Missing checked attempt');
  const walk=p=>readdirSync(p).sort().flatMap(n=>{const full=join(p,n);return statSync(full).isDirectory()?walk(full):[full];});table('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);console.log('Sealed GUI evidence.');
}else throw Error('Unknown command');
