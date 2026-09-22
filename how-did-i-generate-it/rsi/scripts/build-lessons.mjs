// Agent-authored publishing tool. Lesson prose lives in the adjacent modules.
// Students never run or edit this file.
import {mkdirSync, writeFileSync, existsSync} from 'node:fs';
import {resolve, dirname, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {themes, lessons} from './lesson-content.mjs';
import {renderDiagram, diagrams} from './lesson-diagrams.mjs';
import {examples} from './lesson-examples.mjs';
import {guidance} from './lesson-guidance.mjs';
import {researchGroups} from './research-groups.mjs';
import {renderIllustration} from './lesson-illustrations.mjs';
import {themeCheckpoints, themeBlocks} from './course-orientation.mjs';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const rsi = resolve(repo, 'rsi');
const save = (path, body) => {mkdirSync(dirname(path), {recursive:true}); writeFileSync(path, body.trim().replace(/\n{3,}/g,'\n\n')+'\n');};
const link = (from, to) => relative(from, to).split(sep).join('/');
const lessonPath = l => resolve(rsi, themes[l.theme].directory, l.group || '', `step_${l.id.split('.')[1]}_${l.slug}`);
// These are natural-language prompts, not executable snippets. Keep whole words
// and paragraph breaks while making the copyable blocks readable in narrow panes.
const wrapPrompt = text => text.split('\n').map(line => {
  const lines = [''];
  for (const word of line.split(/\s+/).filter(Boolean)) {
    const last = lines.length - 1;
    if (lines[last] && lines[last].length + word.length + 1 > 44) lines.push(word);
    else lines[last] += (lines[last] ? ' ' : '') + word;
  }
  return lines.join('\n');
}).join('\n');

for (let index=0; index<lessons.length; index++) {
  const l=lessons[index], folder=lessonPath(l), theme=themes[l.theme];
  const support=guidance[l.id];
  const workedExample=support?.example || examples[l.id];
  const outputs=support ? `### Open these outputs\n\nThe agent keeps these in your lab workspace or records the original experiment path when reusing evidence.\n\n| Output | What to inspect |\n|---|---|\n${support.outputs.map(([name,meaning])=>`| ${name} | ${meaning} |`).join('\n')}` : '';
  const prev=lessons[index-1], next=lessons[index+1];
  const to=p=>link(folder,resolve(rsi,p));
  const figurePath=`assets/diagrams/lab-${l.id.replace('.','-')}.png`;
  const schematic=existsSync(resolve(rsi,figurePath))
    ? `![${diagrams[l.id].caption}](${to(figurePath)})\n\n*Read the diagram:* ${diagrams[l.id].caption}`
    : renderDiagram(l.id);
  const illustration=renderIllustration(l.id,to);
  const mechanism=illustration
    ? `${illustration}\n\n<details>\n<summary>See the step diagram</summary>\n\n${schematic}\n\n</details>`
    : schematic;
  const nav=`[Course](${to('README.md')}) · [Theme](${to(theme.directory+'/README.md')})`;
  const themeLabs=lessons.filter(item=>item.theme===l.theme);
  const location=`**You are here:** Theme ${l.theme}, ${themeBlocks[l.theme]} → lab ${themeLabs.findIndex(item=>item.id===l.id)+1} of ${themeLabs.length}. [Find this theme in the course map](${to('COURSE-MAP.md')}#theme-${l.theme}) · [Whole-course mindmap](${to('COURSE-MAP.md')}#whole-course-mindmap).`;
  const previous=prev ? `[${prev.id}: ${prev.title}](${link(folder,lessonPath(prev))}/README.md)` : `[Start here](${to('START-HERE.md')})`;
  const after=next ? `[${next.id}: ${next.title}](${link(folder,lessonPath(next))}/README.md)` : `[Teaching portfolio](${to('instructor/README.md')})`;
  const steps=l.steps.map((s,i)=>`### ${i+1}. ${s[0]}\n\n${s[1]}\n\n\`\`\`text\n${wrapPrompt(s[2])}\n\`\`\`\n\n**Observe:** ${s[3]}`).join('\n\n');
  const quiz=l.quiz.map((q,i)=>`${i+1}. ${q[0]}`).join('\n');
  const answers=l.quiz.map((q,i)=>`${i+1}. ${q[1]}`).join('\n\n');
  const source=l.source ? `\n## Research connection\n\n${l.source}\n\n${l.adaptation || 'This is a classroom mechanism exercise. Its task, models, and budget differ from the original study. Your measured result belongs to this exercise; it does not reproduce the paper’s headline result.'}\n` : '';
  save(resolve(folder,'README.md'), `# ${l.id} · ${l.title}

${nav}

${location}

## What you will build

${l.build}

## Why this matters

${l.why}

## Before you start

Complete ${previous}. You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](${to('skills/rsi-tutor/SKILL.md')}) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/${l.id.replace('.','-')}</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](${to('tools/README.md')}) before execution. You do not write code or configuration.${l.workspaceNote ? `\n\n${l.workspaceNote}` : ''}

**Starting state:** ${l.start}

**Budget:** ${l.budget || 'At most four small CPU fits, sequentially; no GPU. Apply a 60-second timeout to each command. Stop after the stated comparison.'} Plan about ${l.time || '20–35'} minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

${l.how}

${workedExample ? `**A concrete example.** ${workedExample}\n` : ''}

${mechanism}

${l.figure || ''}

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

\`\`\`text
${wrapPrompt(`Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab ${l.id}, ${l.title}, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.`)}
\`\`\`

**Make a prediction:** ${l.predict}

${steps}

## Check your result

${l.check}

${outputs}

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

${l.change}

## If something goes wrong

${support?.recovery || l.recovery || 'If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.'}

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](${to('tools/README.md')}) for interrupted tool runs.

## Key takeaways

${l.takeaways.map(t=>'- '+t).join('\n')}
${source}
## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

${quiz}

<details>
<summary>Hint</summary>

${support?.hint || l.hint || 'Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.'}

</details>

<details>
<summary>Explained answers</summary>

${answers}

</details>

## What's next

${l.next} Continue to ${after}.
`);
  save(resolve(folder,'BRIEF.md'), `# Lab ${l.id} brief\n\n${l.build}\n\nStarting state: ${l.start}\n\nPrediction to ask: ${l.predict}\n\nExecution limit: ${l.budget || 'Four sequential CPU fits at most, with a 60-second command timeout.'}\n\nFollow the README steps. Keep source data and the supplied evaluation contract unchanged. Use the canonical course skills. Generate any required code yourself. Save observations, failures, and the learner’s progress in the separate workspace. Do not invent student answers, measurements, or protected evaluator access.\n\nAcceptance: ${l.check}`);
}

for (const [key,t] of Object.entries(themes)) {
  const selected=lessons.filter(l=>l.theme===key);
  if (!selected.length) continue;
  const folder=resolve(rsi,t.directory);
  const themeFigure=renderIllustration(`theme-${key}`,p=>link(folder,resolve(rsi,p)));
  const wholeMap=renderIllustration('course-map',p=>link(folder,resolve(rsi,p)));
  const orientation=`**You are here:** Theme ${key} of 00–11 · ${themeBlocks[key]} · ${selected.length} labs. [Your place in the guided map](../COURSE-MAP.md#theme-${key}).`;
  const mapDisclosure=`<details>\n<summary>Find theme ${key} in the whole-course mindmap</summary>\n\n${wholeMap}\n\n</details>`;
  const contents=key==='10'
    ? `The 38 studio labs form 13 connected groups. Follow them in this order; each group explains its starting evidence and what you will carry forward.\n\n| Group | Question | Labs |\n|---|---|---|\n${Object.entries(researchGroups).map(([group,g])=>{const items=selected.filter(l=>l.group===group);return `| [${g.title}](${group}/README.md) | ${g.question} | ${items[0].id}–${items.at(-1).id} |`;}).join('\n')}\n\nThe [complete course map](../COURSE-MAP.md) also lists every individual lab.`
    : `| Lab | What you will build |\n|---|---|\n${selected.map(l=>`| [${l.id} · ${l.title}](${link(folder,lessonPath(l))}/README.md) | ${l.build} |`).join('\n')}`;
  save(resolve(folder,'README.md'), `# ${t.title}

[Course](../README.md)

${orientation}

${t.intro}

${t.bridge}

${themeFigure || wholeMap}

${themeFigure ? mapDisclosure : ''}

${contents}

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

**Ready to continue when:** ${themeCheckpoints[key]}

${t.exit}`);
}

for (const group of [...new Set(lessons.filter(l=>l.group).map(l=>l.group))]) {
  const selected=lessons.filter(l=>l.group===group);
  const folder=resolve(rsi,themes['10'].directory,group);
  const g=researchGroups[group];
  if(!g) throw new Error(`Missing research-group introduction: ${group}`);
  const groupFigure=g.figure ? renderIllustration(g.figure,p=>link(folder,resolve(rsi,p))) : '';
  const opening=[g.intro,groupFigure,g.reading].filter(Boolean).join('\n\n');
  save(resolve(folder,'README.md'), `# ${g.title}\n\n[Research studio](../README.md) · [Course](../../README.md)\n\n**You are here:** Theme 10 → research group ${group.slice(0,2)} of 00–12 → labs ${selected[0].id}–${selected.at(-1).id}. [Studio overview and mindmap](../README.md) · [Whole-course map](../../COURSE-MAP.md#theme-10).\n\n${opening}\n\n**Start with:** ${g.entry}\n\n${selected.map(l=>`- [${l.id} · ${l.title}](${link(folder,lessonPath(l))}/README.md): ${l.build}`).join('\n')}\n\n**Carry forward:** ${g.exit}\n\nRead the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.\n`);
}

await import('./build-course-map.mjs');
console.log(`Published ${lessons.length} lessons in ${Object.keys(themes).length} theme definitions.`);
await import('./build-source-index.mjs');
