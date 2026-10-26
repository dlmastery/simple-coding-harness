// Five synthetic timing scenarios plus read-only arithmetic on existing lineage.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination]=process.argv.slice(2);if(!destination)throw Error('Supply sibling workspace');const out=resolve(destination);if(out===repo||out.startsWith(repo+sep))throw Error('Use sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const read=p=>readFileSync(join(out,p),'utf8');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const table=(p,rs)=>save(p,rs.map(r=>r.join(',')).join('\n'));
const rows=p=>{const lines=read(p).trim().split(/\r?\n/),head=lines.shift().split(',');return lines.map(s=>Object.fromEntries(s.split(',').map((v,i)=>[head[i],v])));};
const walk=p=>readdirSync(p).sort().flatMap(n=>{const f=join(p,n);return statSync(f).isDirectory()?walk(f):[f];});
if(phase==='run'){
  if(existsSync(join(out,'PROTOCOL.md')))throw Error('Preserve prior execution');mkdirSync(out,{recursive:true});
  const sourceRoot='rsi/evidence/2026-09-20/two-generations/';
  const sources=[['how-did-i-generate-it/rsi/validation/BOTTLENECKS-PROTOCOL.md','PROTOCOL.md'],['how-did-i-generate-it/rsi/research/2026-09-21-BOTTLENECKS-AUDIT.md','SOURCE-AUDIT.md'],...[['LINEAGE.md','LINEAGE.md'],['COSTS.csv','COSTS.csv'],['RESULTS.csv','RESULTS.csv'],['STATE.csv','STATE.csv']].map(([s,d])=>[sourceRoot+s,'local/'+d])];
  for(const [s,d]of sources){mkdirSync(dirname(join(out,d)),{recursive:true});copyFileSync(join(repo,s),join(out,d));}copyFileSync(script,join(out,'run-bottlenecks.mjs'));
  table('SOURCES.csv',[['repository_path','copy','sha256'],...sources.map(([s,d])=>[s,d,sha(join(out,d))])]);
  const scenarios=[['baseline',1,0,9,0],['faster_proposals',.5,0,9,0],['faster_evaluation',1,0,4.5,0],['checking_overhead',.5,0,9,1],['costlier_verifier',.5,0,12,0]];
  table('SCENARIOS.csv',[['scenario','proposal_minutes','execution_minutes','evaluation_minutes','extra_check_minutes'],...scenarios]);
  table('FROZEN.csv',[['path','sha256'],...['PROTOCOL.md','SOURCE-AUDIT.md','SCENARIOS.csv','run-bottlenecks.mjs',...sources.filter(x=>x[1].startsWith('local/')).map(x=>x[1])].map(p=>[p,sha(join(out,p))])]);
  const evaluated=rows('SCENARIOS.csv').map(r=>{const t=['proposal_minutes','execution_minutes','evaluation_minutes','extra_check_minutes'].reduce((s,k)=>s+Number(r[k]),0);return[r.scenario,t,100*(10-t)/10,10/t];});
  table('TIMING-RESULTS.csv',[['scenario','total_minutes','time_reduction_percent','throughput_multiplier_vs_baseline'],...evaluated]);
  const expected=[10,9.5,5.5,10.5,12.5];if(!evaluated.every((r,i)=>r[1]===expected[i]))throw Error('Incorrect timing arithmetic');
  let cumulative=0;table('SYNTHETIC-GAINS.csv',[['round','increment_units','cumulative_units'],...[4,2,1].map((v,i)=>[i+1,v,cumulative+=v])]);
  const metrics=rows('local/RESULTS.csv'),costs=rows('local/COSTS.csv'),actual=[];
  for(const path of ['baseline','recursive']){
    const active=metrics.filter(r=>r.path===path&&r.arm==='active').sort((a,b)=>Number(a.generation)-Number(b.generation));const start=Number(active[0].parent_selection);let prior=start,cumulativeSeconds=0;
    for(const r of active){const relevant=costs.filter(c=>c.path===path&&c.generation===r.generation),seconds=relevant.reduce((s,c)=>s+Number(c.wall_seconds),0),retained=Number(r.retained_selection),gain=prior-retained;cumulativeSeconds+=seconds;actual.push([path,r.generation,retained,gain,start-retained,seconds,cumulativeSeconds,gain/seconds,(start-retained)/cumulativeSeconds,'unknown',r.improver_sha256]);prior=retained;}
  }
  table('LOCAL-RATES.csv',[['path','generation','retained_MAE','incremental_MAE_reduction','cumulative_MAE_reduction','fit_process_wall_seconds','cumulative_fit_process_wall_seconds','increment_per_fit_process_second','cumulative_gain_per_fit_process_second','total_research_cost','active_improver_sha256'],...actual]);
  const identities=new Set(actual.map(r=>r.at(-1)));if(identities.size!==1)throw Error('Expected unchanged active improver; inspect source');
  save('ARITHMETIC-CHECK.md',`# Arithmetic check\n\nFive totals match 10, 9.5, 5.5, 10.5, 12.5 minutes. Cumulative synthetic gain is ${cumulative} with shrinking increments 4, 2, 1.\n\nThe baseline proposal stage is one of ten minutes. Removing it entirely leaves nine minutes: maximum total-time reduction 10 percent under these serial assumptions. This bound is not a sixth scenario.\n\nLocal rates are recomputed from copied result and cost rows. All four active entries name the same improver hash. No new fit or source-paper simulation ran.`);
  console.log(read('TIMING-RESULTS.csv'));console.log(read('LOCAL-RATES.csv'));
}else if(phase==='seal'){
  if(existsSync(join(out,'MANIFEST.csv')))throw Error('Already sealed');table('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
}else throw Error('Unknown phase');
