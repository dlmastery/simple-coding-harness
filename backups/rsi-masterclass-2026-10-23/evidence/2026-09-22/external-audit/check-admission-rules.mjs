// One original arithmetic illustration. No research-system execution or model fit.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(process.argv[2]);
const started=new Date().toISOString(),t=performance.now();
const protocol=resolve(root,'PROTOCOL.md');
const protocolHash=createHash('sha256').update(readFileSync(protocol)).digest('hex');
const z=1.96,threshold=0.85;
function wald(k,n){const p=k/n;return Math.max(0,p-z*Math.sqrt(p*(1-p)/n));}
function wilson(k,n){const p=k/n;return (p+z*z/(2*n)-z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n);}
const rows=[];
for(let first=0;first<=20;first++)for(let second=0;second<=20;second++){
  const a=wald(first,20),b=wald(second,20),c=wilson(first+second,40);
  rows.push({first,second,split_wald_min:Math.min(a,b),pooled_wilson_lower:c,split_accept:a>=threshold&&b>=threshold,pooled_accept:c>=threshold});
}
const disagreements=rows.filter(r=>r.split_accept!==r.pooled_accept);
const put=(name,value)=>{const p=resolve(root,name);if(existsSync(p))throw Error('Refuse overwrite '+p);writeFileSync(p,value);};
const csv=data=>Object.keys(rows[0]).join(',')+'\n'+data.map(r=>Object.values(r).join(',')).join('\n')+'\n';
put('ALL-COUNT-PAIRS.csv',csv(rows));put('RULE-DISAGREEMENTS.csv',csv(disagreements));
const edge=rows.find(r=>r.first===19&&r.second===19);
const zeros=rows.find(r=>r.first===0&&r.second===0),full=rows.find(r=>r.first===20&&r.second===20);
const checks=[['enumeration',rows.length===441],['both reject zero successes',!zeros.split_accept&&!zeros.pooled_accept],
  ['both accept all successes',full.split_accept&&full.pooled_accept],['all-success Wilson closed form',Math.abs(full.pooled_wilson_lower-1/(1+z*z/40))<1e-12],
  ['separate exact-count criterion',rows.every(r=>r.split_accept===(r.first>=19&&r.second>=19))],
  ['pooled exact-count criterion',rows.every(r=>r.pooled_accept===(r.first+r.second>=39))]];
put('CHECKS.csv','check,status\n'+checks.map(([k,v])=>k+','+(v?'PASS':'FAIL')).join('\n')+'\n');
put('RESULT.md',`# One arithmetic check\n\nEnumerated ${rows.length} integer count pairs. Found ${disagreements.length} disagreement: two groups with nineteen successes each. Split Wald minimum: ${edge.split_wald_min}; pooled Wilson lower endpoint: ${edge.pooled_wilson_lower}. The split rule accepts and the pooled rule rejects at 0.85.\n\nThe two rules agree on many outcomes and still differ as functions. This does not contradict a claim that a particular recorded dataset contains no disagreement. The source already identified this case; our calculation verifies arithmetic, not the source's raw experiment or statistical calibration.\n\nZero model fits, zero paper-system runs. Six numerical checks are recorded.\n`);
put('RUN.md',`# Calculator execution\n\nStarted UTC: ${started}\nRuntime: ${process.version}; ${process.platform} ${process.arch}\nCommand: node check-admission-rules.mjs WORKSPACE\nWorkspace: ${root}\nProtocol SHA-256: ${protocolHash}\nElapsed calculator seconds before this log: ${(performance.now()-t)/1000}\n\nNo network or model calls inside this calculator. Source reading, authoring, inference and publication costs are additional and unmeasured.\n`);
console.log(`441 count pairs; ${disagreements.length} disagreement; ${checks.filter(([,v])=>v).length}/6 checks PASS.`);
if(checks.some(([,v])=>!v))process.exitCode=1;
