// Check selected illustrations in actual published Markdown, not just the asset inventory.
import {readFileSync, existsSync, writeFileSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {themes, lessons} from './lesson-content.mjs';
import {illustrations} from './lesson-illustrations.mjs';
import {researchGroups} from './research-groups.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const records=[];
function check(page, figure, kind, id) {
  const path=resolve(repo,page), text=readFileSync(path,'utf8');
  const images=[...text.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)].map(m=>m[1]);
  const matches=images.filter(p=>p.endsWith('/'+figure));
  const passed=matches.length>0 && matches.every(p=>existsSync(resolve(dirname(path),p)));
  records.push({kind,id,page,figure,passed});
}
for(const l of lessons) {
  const page='rsi/'+themes[l.theme].directory+'/'+(l.group?l.group+'/':'')+'step_'+l.id.split('.')[1]+'_'+l.slug+'/README.md';
  check(page,illustrations[l.id].file,'individual',l.id);
  check(page,'lab-'+l.id.replace('.','-')+'.png','step-schematic',l.id);
  check('rsi/VISUAL-GUIDE.md',illustrations[l.id].file,'gallery',l.id);
}
for(const [id,t] of Object.entries(themes)) check('rsi/'+t.directory+'/README.md','course-mindmap-v2.png','theme-map',id);
for(const [id,g] of Object.entries(researchGroups)) check('rsi/10_research_studio/'+id+'/README.md',illustrations[g.figure].file,'research-group',id);
for(const figure of ['main-overview-v2.png','course-mindmap-v2.png','research-studio-map-v3.png','capstone-map-v3.png']) check('rsi/README.md',figure,'entry-page','RSI');
check('README.md','course-mindmap-v2.png','entry-page','repository');
check('rsi/10_research_studio/README.md','research-studio-map-v3.png','expanded-map','studio');
check('rsi/11_capstones/README.md','capstone-map-v3.png','expanded-map','capstones');
const dest=resolve(repo,'how-did-i-generate-it/rsi/validation/ILLUSTRATION-PLACEMENT-2026-09-22.csv');
writeFileSync(dest,'kind,id,page,figure,passed\n'+records.map(r=>Object.values(r).join(',')).join('\n')+'\n');
const failures=records.filter(r=>!r.passed);
console.log(`${records.length} illustration placement checks; ${failures.length} failures`);
for(const failure of failures) console.log(failure);
process.exitCode=failures.length?1:0;
