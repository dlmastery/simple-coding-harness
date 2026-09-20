// Agent-authored publishing tool. Lesson prose lives in the adjacent modules.
// Students never run or edit this file.
import {mkdirSync, writeFileSync, existsSync} from 'node:fs';
import {resolve, dirname, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {themes, lessons} from './lesson-content.mjs';
import {renderDiagram, diagrams} from './lesson-diagrams.mjs';
import {examples} from './lesson-examples.mjs';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const rsi = resolve(repo, 'rsi');
const save = (path, body) => {mkdirSync(dirname(path), {recursive:true}); writeFileSync(path, body.trim()+'\n');};
const link = (from, to) => relative(from, to).split(sep).join('/');
const lessonPath = l => resolve(rsi, themes[l.theme].directory, l.group || '', `step_${l.id.split('.')[1]}_${l.slug}`);

for (let index=0; index<lessons.length; index++) {
  const l=lessons[index], folder=lessonPath(l), theme=themes[l.theme];
  const prev=lessons[index-1], next=lessons[index+1];
  const to=p=>link(folder,resolve(rsi,p));
  const figurePath=`assets/diagrams/lab-${l.id.replace('.','-')}.png`;
  const schematic=existsSync(resolve(rsi,figurePath))
    ? `![${diagrams[l.id].caption}](${to(figurePath)})\n\n*Read the diagram:* ${diagrams[l.id].caption}`
    : renderDiagram(l.id);
  const nav=`[Course](${to('README.md')}) · [Theme](${to(theme.directory+'/README.md')})`;
  const previous=prev ? `[${prev.id}: ${prev.title}](${link(folder,lessonPath(prev))}/README.md)` : `[Start here](${to('START-HERE.md')})`;
  const after=next ? `[${next.id}: ${next.title}](${link(folder,lessonPath(next))}/README.md)` : `[Teaching portfolio](${to('instructor/README.md')})`;
  const steps=l.steps.map((s,i)=>`### ${i+1}. ${s[0]}\n\n${s[1]}\n\n\`\`\`text\n${s[2]}\n\`\`\`\n\n**Observe:** ${s[3]}`).join('\n\n');
  const quiz=l.quiz.map((q,i)=>`${i+1}. ${q[0]}`).join('\n');
  const answers=l.quiz.map((q,i)=>`${i+1}. ${q[1]}`).join('\n\n');
  const source=l.source ? `\n## Research connection\n\n${l.source}\n\n${l.adaptation || 'This is a classroom mechanism exercise. Its task, models, and budget differ from the original study. Your measured result belongs to this exercise; it does not reproduce the paper’s headline result.'}\n` : '';
  save(resolve(folder,'README.md'), `# ${l.id} · ${l.title}

${nav}

## What you will build

${l.build}

## Why this matters

${l.why}

## Before you start

Complete ${previous}. You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](${to('skills/rsi-tutor/SKILL.md')}) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/${l.id.replace('.','-')}</code> and reports its absolute path. It checks local Python and the [tool requirements](${to('tools/README.md')}) before execution. You do not write code or configuration.${l.workspaceNote ? `\n\n${l.workspaceNote}` : ''}

**Starting state:** ${l.start}

**Budget:** ${l.budget || 'At most four small CPU fits, sequentially; no GPU. Apply a 60-second timeout to each command. Stop after the stated comparison.'} Plan about ${l.time || '20–35'} minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

${l.how}

${examples[l.id] ? `**A concrete example.** ${examples[l.id]}\n` : ''}

${schematic}

${l.figure || ''}

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

\`\`\`text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab ${l.id}, ${l.title}, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
\`\`\`

**Make a prediction:** ${l.predict}

${steps}

## Check your result

${l.check}

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

${l.change}

## If something goes wrong

${l.recovery || 'If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.'}

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](${to('tools/README.md')}) for interrupted tool runs.

## Key takeaways

${l.takeaways.map(t=>'- '+t).join('\n')}
${source}
## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

${quiz}

<details>
<summary>Hint</summary>

${l.hint || 'Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.'}

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
  save(resolve(folder,'README.md'), `# ${t.title}\n\n[Course](../README.md)\n\n${t.intro}\n\n${t.bridge}\n\n| Lab | What changes |\n|---|---|\n${selected.map(l=>`| [${l.id} · ${l.title}](${link(folder,lessonPath(l))}/README.md) | ${l.build} |`).join('\n')}\n\nStart with the first lab and follow its next link. Each lab uses a separate workspace and keeps its evidence. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).\n\n${t.exit}`);
}

for (const group of [...new Set(lessons.filter(l=>l.group).map(l=>l.group))]) {
  const selected=lessons.filter(l=>l.group===group);
  const folder=resolve(rsi,themes['10'].directory,group);
  const title=group.slice(3).replaceAll('_',' ');
  save(resolve(folder,'README.md'), `# ${title.charAt(0).toUpperCase()+title.slice(1)}\n\n[Research studio](../README.md) · [Course](../../README.md)\n\n${selected[0].why} These labs build the mechanism in small steps and state the limits of the classroom adaptation. Complete the foundation themes before beginning.\n\n${selected.map(l=>`- [${l.id} · ${l.title}](${link(folder,lessonPath(l))}/README.md): ${l.build}`).join('\n')}\n\nRead the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.\n`);
}

save(resolve(rsi,'COURSE-MAP.md'), `# Course map\n\n[Course](README.md)\n\nThis is the current authored sequence. The [validation record](evidence/2026-09-20/README.md) states which runs have actually been checked. A written lesson is not automatically a validated lesson.\n\n| Lab | Theme | Lesson |\n|---|---|---|\n${lessons.map(l=>`| ${l.id} | ${themes[l.theme].title} | [${l.title}](${link(rsi,lessonPath(l))}/README.md) |`).join('\n')}\n`);
console.log(`Published ${lessons.length} lessons in ${Object.keys(themes).length} theme definitions.`);
