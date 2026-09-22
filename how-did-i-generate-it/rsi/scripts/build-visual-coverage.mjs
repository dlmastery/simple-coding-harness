// Agent-authored inventory; image presence is not teaching or execution validation.
import {writeFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {themes,lessons} from './lesson-content.mjs';
import {illustrations} from './lesson-illustrations.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const mapped=lessons.filter(l=>illustrations[l.id]);
const rows=[
 '# Individual infographic coverage',
 '',
 'This inventory tracks a generated infographic mapped directly to a lab. Shared theme maps and the precise step schematics are separate. A present image does not establish scientific correctness, rendering quality, execution, or learner understanding.',
 '',
 '**'+mapped.length+' of '+lessons.length+' labs** currently have a mapped generated infographic; **'+(lessons.length-mapped.length)+' remain**. The selected gallery also contains course maps and the compute guide, so its total image count is not a completed-lab count.',
 '',
 'All seven theme-09 RSI labs, all 38 research-studio labs, and all five capstones have mapped images. Continue with the remaining foundation labs. Preserve the two-or-three-attempt generation discipline.',
 '',
 '| Theme | Labs | Mapped lab infographics | Remaining |',
 '|---|---|---|---|'
];
const ordered=Object.entries(themes).sort(([a],[b])=>Number(a)-Number(b));
for(const [id,t] of ordered){
 const all=lessons.filter(l=>l.theme===id),done=all.filter(l=>illustrations[l.id]);
 rows.push('| '+id+' · '+t.title+' | '+all.length+' | '+done.length+' | '+(all.length-done.length)+' |');
}
for(const [id,t] of ordered){
 rows.push('','## '+id+' · '+t.title,'','| Lab | Generated infographic | Precise step schematic |','|---|---|---|');
 for(const l of lessons.filter(item=>item.theme===id)){
  const path=t.directory+'/'+(l.group?l.group+'/':'')+'step_'+l.id.split('.')[1]+'_'+l.slug+'/README.md';
  const image=illustrations[l.id]?.file;
  if(image && !existsSync(resolve(repo,'rsi/assets/illustrations',image))) throw new Error('Missing image '+image);
  const schematic='lab-'+l.id.replace('.','-')+'.png';
  const hasSchematic=existsSync(resolve(repo,'rsi/assets/diagrams',schematic));
  rows.push('| ['+l.id+' · '+l.title+'](../../../rsi/'+path+') | '+(image?'[Selected figure](../../../rsi/assets/illustrations/'+image+')':'Pending')+' | '+(hasSchematic?'[Present](../../../rsi/assets/diagrams/'+schematic+')':'Missing')+' |');
 }
}
rows.push('','Generated from the [lesson index](../scripts/lesson-content.mjs) and [illustration map](../scripts/lesson-illustrations.mjs). Keep exact prompts, all outputs, and the substantive review in the [visual provenance](../visuals/generated/README.md).');
writeFileSync(resolve(repo,'how-did-i-generate-it/rsi/validation/INFOGRAPHIC-COVERAGE.md'),rows.join('\n')+'\n');
console.log('Mapped generated infographics: '+mapped.length+'/'+lessons.length+'; remaining: '+(lessons.length-mapped.length)+'.');
