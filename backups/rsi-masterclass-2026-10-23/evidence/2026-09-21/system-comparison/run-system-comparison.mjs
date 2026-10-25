// Archive an authored source audit and check existing lineage; no new fits.
import {readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname,join,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const script=fileURLToPath(import.meta.url),repo=resolve(dirname(script),'../../..');
const [phase,destination]=process.argv.slice(2);
if(!destination)throw Error('Supply a sibling workspace');
const out=resolve(destination);
if(out===repo||out.startsWith(repo+sep))throw Error('Use a sibling workspace');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const save=(p,s)=>{mkdirSync(dirname(join(out,p)),{recursive:true});writeFileSync(join(out,p),s.trimEnd()+'\n');};
const csv=(p,rows)=>save(p,rows.map(r=>r.join(',')).join('\n'));
const parse=p=>{const lines=readFileSync(join(out,p),'utf8').trim().split(/\r?\n/),header=lines.shift().split(',');return lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));};
const walk=p=>readdirSync(p).sort().flatMap(n=>{const f=join(p,n);return statSync(f).isDirectory()?walk(f):[f];});
if(phase==='run'){
  if(existsSync(out))throw Error('Preserve existing workspace');
  mkdirSync(out,{recursive:true});
  const sources=[['how-did-i-generate-it/rsi/validation/SYSTEM-COMPARISON-PROTOCOL.md','PROTOCOL.md'],...['SYSTEM-COMPARISON.md','RESULTS-AND-BOUNDARIES.md','CLAIM-CHALLENGE.md','READING-LEDGER.md'].map(n=>['how-did-i-generate-it/rsi/research/system-comparison/'+n,n]),...['LINEAGE.md','STATE.csv','RESULTS.csv','COSTS.csv'].map(n=>['rsi/evidence/2026-09-20/two-generations/'+n,'local/'+n])];
  for(const [s,d]of sources){
    mkdirSync(dirname(join(out,d)),{recursive:true});
    if(s.includes('/research/system-comparison/')){
      save(d,readFileSync(join(repo,s),'utf8').replaceAll('../../../../rsi/evidence/2026-09-20/two-generations/','local/').replaceAll('../../../../rsi/evidence/2026-09-21/system-comparison/',''));
    }else copyFileSync(join(repo,s),join(out,d));
  }
  copyFileSync(script,join(out,'run-system-comparison.mjs'));
  csv('SOURCES.csv',[['repository_path','copy','source_sha256','copy_sha256'],...sources.map(([s,d])=>[s,d,sha(join(repo,s)),sha(join(out,d))])]);
  const rows=parse('local/RESULTS.csv'),active=rows.filter(r=>r.arm==='active'),proposals=rows.filter(r=>r.arm!=='active');
  if(active.length!==4||new Set(active.map(r=>r.improver_sha256)).size!==1)throw Error('Active identities differ from the authored interpretation');
  save('LOCAL-CHECK.md',`# Checked the recorded active identities\n\nRead four active result rows: two paths, two generations. All name SHA-256 ${active[0].improver_sha256}. Read ${proposals.length} comparison rows; the copied lineage explains the rejected decisions. This check verifies identities, not semantic correctness of a paper or an independent rerun.\n\nNo new fits. Existing costs remain separate from this source-audit work.`);
  save('LAB-NOTE.md','# Author observation\n\nThe same RSI label covers different mutable objects. The local task result improved while its active improver stayed fixed. The mechanism-only view avoids a false ranking; the results view restores the scope of each claim.\n\nLearner prediction, teach-back, quiz, and transfer response: unattempted. Author context knew prior results. Source reproduction and total author/inference cost: unknown or unperformed, not zero.');
  console.log(`Checked ${active.length} active identities; ${sources.length} source files copied; zero fits.`);
}else if(phase==='seal'){
  if(existsSync(join(out,'MANIFEST.csv')))throw Error('Already sealed');
  csv('MANIFEST.csv',[['path','sha256'],...walk(out).map(p=>[relative(out,p).split(sep).join('/'),sha(p)])]);
}else throw Error('Use run or seal');
