// Agent-authored publisher for the guided course map.
import {writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {themes,lessons} from './lesson-content.mjs';
import {researchGroups} from './research-groups.mjs';
import {themeCheckpoints,themeBlocks} from './course-orientation.mjs';
import {renderIllustration} from './lesson-illustrations.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const lessonFolder=l=>themes[l.theme].directory+'/'+(l.group ? l.group+'/' : '')+'step_'+l.id.split('.')[1]+'_'+l.slug;
const minutes=l=>{
  const values=(l.time||'20–35').match(/\d+/g)?.map(Number);
  if(values?.length!==2) throw new Error('Unclear duration for '+l.id);
  return values;
};
const duration=items=>items.reduce((sum,l)=>{const n=minutes(l);return [sum[0]+n[0],sum[1]+n[1]];},[0,0]);
const hours=items=>{const n=duration(items);return (n[0]/60).toFixed(1)+'–'+(n[1]/60).toFixed(1)+' hours';};
const table=items=>[
  '| Lab | Codelab | Why it matters and what you will make |',
  '|---|---|---|',
  ...items.map(l=>'| '+l.id+' | ['+l.title+']('+lessonFolder(l)+'/README.md) | '+l.why+' '+l.build+' |')
].join('\n');
const ordered=Object.entries(themes).sort(([a],[b])=>Number(a)-Number(b));
const body=[
  '# Your route through the RSI masterclass',
  '[Course](README.md) · [Start here](START-HERE.md) · [Intent, skills, and authoring sources](SOURCE-ARTIFACTS.md)',
  'Start with one bike-demand prediction. Make its evidence trustworthy. Then add a reason for another experiment, rules for choosing the next action, and a way to preserve useful work. Only after those ideas are clear do you change the research procedure—and then the procedure that improves it.',
  'This guide explains the full '+lessons.length+'-lab route. It is also a place to return when a new term obscures the purpose of the next step. The numbered themes give reading order; the mindmap shows how the ideas belong together. Your position in the course is not a claim that earlier experiments succeeded.',
  '<a id="whole-course-mindmap"></a>\n\n## The whole course',
  renderIllustration('course-map',p=>p),
  'The destination is the research studio and the capstones. The earlier themes give you the vocabulary, tools, and judgment to inspect those systems instead of treating their names or headline scores as explanations.',
  '## Objectives',
  'By the end, you should be able to:\n\n- Build and inspect a complete small ML experiment, from the question and data to a checked result.\n- Design bounded loops, dependency graphs, domain rules, and reliable recovery.\n- Use skills to have a coding agent generate and operate a research harness.\n- Distinguish self-* mechanisms, harness generation, and recursive improvement.\n- Test whether a changed research procedure helps under a fair comparison.\n- Read current research, explain its mechanism, and state what a laptop adaptation preserves.\n- Build, transfer, audit, and teach a bounded project with an honest conclusion.',
  '## Prerequisites and time',
  'You need basic ML familiarity: tables, features and targets, training versus evaluation, and prediction error. No RSI, agent-harness, cluster, or infrastructure background is assumed. Students give natural-language instructions; the agent writes code and configuration. Use a coding agent with file and command access, a laptop for CPU experiments, and internet access for setup and research reading. Hosted-agent charges are separate.',
  'The current per-lab author estimates sum to **'+hours(lessons)+'** of reading and guided discussion. They are planning estimates, not measured learner durations. Allow additional time for setup, debugging, deeper paper reading, independent capstone work, and optional larger jobs.',
  '| Part | Scope | Current author estimate |\n|---|---|---|\n| Foundations through RSI | Themes 00–09, 58 labs | '+hours(lessons.filter(l=>Number(l.theme)<10))+' |\n| Research studio | Theme 10, 38 labs | '+hours(lessons.filter(l=>l.theme==='10'))+' |\n| Capstones | Theme 11, 5 labs | '+hours(lessons.filter(l=>l.theme==='11'))+' |',
  'Each lab includes an explained quiz and a next step. Attempt the quiz and explain one new case before continuing. A short workshop may stop after theme 02; that route teaches dependable ML loops and does not reach the full RSI outcome.',
  '## Find your theme',
  '| Theme | New capability | Labs |\n|---|---|---|\n'+ordered.map(([key,t])=>'| ['+key+' · '+t.title+'](#theme-'+key+') | '+themeBlocks[key]+' | '+lessons.filter(l=>l.theme===key).length+' |').join('\n')
];
for(let i=0;i<ordered.length;i++){
  const [key,t]=ordered[i];
  const items=lessons.filter(l=>l.theme===key);
  const previous=ordered[i-1], next=ordered[i+1];
  body.push('<a id="theme-'+key+'"></a>\n\n## '+key+' · '+t.title);
  body.push('**Your place:** '+themeBlocks[key]+'. '+items.length+' labs; '+hours(items)+' of planned reading and discussion. [Open the theme]('+t.directory+'/README.md).');
  body.push(t.intro+'\n\n'+t.bridge);
  if(key==='10' || key==='11') body.push(renderIllustration(key==='10' ? 'research-map' : 'capstone-map',p=>p));
  if(key==='10'){
    body.push('Work through the groups below in order. Each gives a source mechanism a concrete classroom question. Preserve the differences between live execution, replay, simulation, numerical illustration, and a paper-result audit.');
    for(const [group,g] of Object.entries(researchGroups)){
      const selected=items.filter(l=>l.group===group);
      body.push('### '+g.title+'\n\n'+g.question+' '+g.intro+' [Group introduction]('+t.directory+'/'+group+'/README.md).');
      body.push(table(selected));
    }
  }else{
    body.push(table(items));
  }
  body.push('**Ready to continue when:** '+themeCheckpoints[key]);
  body.push(t.exit);
  if(key==='11') body.push('The [example portfolio](PORTFOLIO.md) connects actual author evidence. Its peer reproduction is prepared and explicitly pending.');
  const navigation=[];
  if(previous) navigation.push('[Previous theme: '+previous[0]+'](#theme-'+previous[0]+')');
  if(next) navigation.push('[Next theme: '+next[0]+'](#theme-'+next[0]+')');
  navigation.push('[Whole-course mindmap](#whole-course-mindmap)');
  body.push(navigation.join(' · '));
}
body.push('## Find the instructions behind a lab','The [source-artifact index](SOURCE-ARTIFACTS.md) links every lab README, intent brief, authoring module, and shared skill. Use it to inspect how the course is authored. Follow the [learning path](LEARNING-PATH.md) for conceptual checkpoints, the [teaching roadmap](TEACHING-ROADMAP.md) for session plans and capstone milestones, and the [glossary](GLOSSARY.md) for definitions and examples. Written coverage and completed execution are tracked separately in the [completion ledger](../how-did-i-generate-it/rsi/COURSE-COMPLETION-LEDGER.md).');
writeFileSync(resolve(repo,'rsi/COURSE-MAP.md'),body.join('\n\n')+'\n');
console.log('Published the guided '+lessons.length+'-lab course map with twelve readiness checkpoints.');
