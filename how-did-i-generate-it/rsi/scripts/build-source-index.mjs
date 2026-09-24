// Publish a browsable index of course instructions, not execution outputs.
import {writeFileSync} from 'node:fs';
import {resolve, dirname, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons, themes} from './lesson-content.mjs';
import {foundation} from './lessons-foundation.mjs';
import {structure} from './lessons-structure.mjs';
import {systems} from './lessons-systems.mjs';
import {improvement} from './lessons-improvement.mjs';
import {research} from './lessons-research.mjs';
import {science} from './lessons-science.mjs';
import {frontier} from './lessons-frontier.mjs';
import {capstones} from './lessons-capstone.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const rsi=resolve(repo,'rsi');
const sourceRoot='how-did-i-generate-it/rsi/scripts/';
const link=path=>relative(rsi,resolve(repo,path)).split(sep).join('/');
const sourceById=new Map();
for (const [file,items] of [
  ['lessons-foundation.mjs',foundation], ['lessons-structure.mjs',structure],
  ['lessons-systems.mjs',systems], ['lessons-improvement.mjs',improvement],
  ['lessons-research.mjs',research], ['lessons-science.mjs',science],
  ['lessons-frontier.mjs',frontier], ['lessons-capstone.mjs',capstones]
]) {
  for (const item of items) {
    if(sourceById.has(item.id)) throw new Error('Duplicate authored lab '+item.id);
    sourceById.set(item.id,file);
  }
}
if(sourceById.size!==lessons.length) throw new Error('Authoring source count differs from lab count');

const body=[
  '# Source instructions for every codelab',
  '[Course](README.md) · [Course map](COURSE-MAP.md) · [Folder map](STRUCTURE.md)',
  'This index links the instructions that define all '+lessons.length+' codelabs: their purpose, procedure, constraints, and authoring source. These are course materials, not generated learner inputs, experiment outputs, or execution records.',
  'The per-lab intent file is named **BRIEF.md**. The detailed procedure is in the lab **README.md**, including its run prompts and checks. There is currently no separate INTENT.md or dedicated SKILL.md in each lab folder. Eight shared skills provide the common agent procedures; the tutor reads the selected lab and its brief.',
  'The current course is on the default branch, [main](https://github.com/dlmastery/simple-coding-harness/tree/main/rsi). The [previous eighteen-step course](../backups/rsi-before-masterclass-2026-09-24/README.md) is preserved separately.',
  '## Whole-course intent and skills',
  '| Source | What it defines |\n|---|---|',
  '| [Requirements and restart notes](../how-did-i-generate-it/rsi/RSI-STEERING-AND-RESTART.md) | The complete user requirements, accepted changes, and current priority |',
  '| [Masterclass plan](../how-did-i-generate-it/rsi/RSI-MASTERCLASS-PLAN.md) | Learning progression, research treatment, architecture, and acceptance criteria |',
  '| [Reusable course-building skill](../skills/build-research-codelabs/SKILL.md) | How to build a course for RSI or another complex topic |',
  '| [Course agent entry point](AGENTS.md) | How an agent enters this course and finds its teaching procedure |',
  '| [RSI tutor](skills/rsi-tutor/SKILL.md) | How to teach and execute one lab, with learner checkpoints |',
  '| [Run an ML experiment](skills/run-ml-experiment/SKILL.md) | How to run one declared ML hypothesis |',
  '| [Review domain meaning](skills/review-domain/SKILL.md) | How to check data, metrics, splits, and evidence meanings |',
  '| [Run a discovery cycle](skills/run-discovery-cycle/SKILL.md) | How to build real discovery trees, revise a policy through replay and deploy it later |',
  '| [Improve a research skill](skills/improve-research-skill/SKILL.md) | How to propose and compare a procedural change |',
  '| [Build an ML harness](skills/build-ml-harness/SKILL.md) | How to generate a harness from a readable brief |',
  '| [Audit an RSI claim](skills/audit-rsi-claim/SKILL.md) | How to match a claim to its evidence |',
  '| [Scale an experiment](skills/scale-experiment/SKILL.md) | How to preserve the experiment contract on larger compute |',
  '## Per-lab source instructions',
  'Open a lesson for the complete procedure, or its brief for the compact intent and constraints. The authoring module is the maintained source used to publish those Markdown files. Students read the Markdown and speak to the agent; they do not edit the publisher code.'
];
for (const [key,theme] of Object.entries(themes).sort(([a],[b])=>Number(a)-Number(b))) {
  const selected=lessons.filter(l=>l.theme===key);
  body.push('### '+key+' · '+theme.title+' — '+selected.length+' labs');
  const rows=['| Lab | Purpose and procedure | Intent brief | Authoring module |','|---|---|---|---|'];
  for (const lab of selected) {
    const folder=theme.directory+'/'+(lab.group ? lab.group+'/' : '')+'step_'+lab.id.split('.')[1]+'_'+lab.slug;
    const source=sourceById.get(lab.id);
    if(!source) throw new Error('Missing authoring source for '+lab.id);
    rows.push('| '+lab.id+' | ['+lab.title+']('+folder+'/README.md) | [BRIEF.md]('+folder+'/BRIEF.md) | [Source]('+link(sourceRoot+source)+') |');
  }
  body.push(rows.join('\n'));
}
body.push(
  '## Supporting authoring sources',
  'The [lesson index](../how-did-i-generate-it/rsi/scripts/lesson-content.mjs) assembles the themed modules. [Teaching guidance](../how-did-i-generate-it/rsi/scripts/lesson-guidance.mjs) supplies worked examples, output explanations, recovery, and quiz hints. [Research-group introductions](../how-did-i-generate-it/rsi/scripts/research-groups.mjs) supply the advanced group walkthroughs.',
  '[Technical diagram source](../how-did-i-generate-it/rsi/scripts/lesson-diagrams.mjs), [selected illustration captions](../how-did-i-generate-it/rsi/scripts/lesson-illustrations.mjs), and [image prompts and revisions](../how-did-i-generate-it/rsi/visuals/generated/README.md) preserve the visual authoring work.',
  'The [lesson publisher](../how-did-i-generate-it/rsi/scripts/build-lessons.mjs) rebuilds the readable course and invokes [this index publisher](../how-did-i-generate-it/rsi/scripts/build-source-index.mjs). A source file establishes authored instructions; it does not establish successful execution.'
);
const markdown=body.join('\n\n').replaceAll('|\n\n|','|\n|');
writeFileSync(resolve(rsi,'SOURCE-ARTIFACTS.md'),markdown+'\n');
console.log('Published source links for '+lessons.length+' labs and eight shared course skills.');
