// Author review of saved evidence. No model fits or agent sessions are launched.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve, dirname, relative} from 'node:path';
import {fileURLToPath} from 'node:url';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const dest = resolve(repo, 'how-did-i-generate-it/rsi/validation/saved-reuse-review');
mkdirSync(dest, {recursive:true});
const root = 'rsi/evidence/2026-09-20/clean-journey';
const recovered = 'rsi/evidence/2026-09-22/builder-reconciliation/historical-source/BUILDER-SKILL.md';
const sources = new Map();
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
function bytes(path) {
  const value = readFileSync(resolve(repo,path));
  sources.set(path, hash(value));
  return value;
}
const read = path => bytes(path).toString('utf8');
const link = path => relative(dest,resolve(repo,path)).replaceAll('\\','/');
const out = (name,value) => writeFileSync(resolve(dest,name),value);
const checks = [];
function check(name,pass) { checks.push([name, pass ? 'PASS' : 'FAIL']); }
const builder = read(recovered);
const builderHash = sources.get(recovered);
for (const [task,lab,brief,features,metric,refusal] of [
  ['bike','06-02','06-01','calendar','MAE','12-bike-recreated-wrong-task.md'],
  ['wine','06-05','06-05','all','balanced accuracy','14-wine-recreated-wrong-task.md']
]) {
  const pack = `${root}/${lab}/package`;
  const old = `${root}/${lab}/run`;
  const again = `${root}/06-06/${task}`;
  const predictions = 'trial-001/predictions.csv';
  const oldHash = hash(bytes(`${old}/${predictions}`));
  const newHash = hash(bytes(`${again}/${predictions}`));
  check(`${task}: complete prediction bytes equal`,oldHash===newHash);
  check(`${task}: complete frozen contracts equal`,bytes(`${old}/CONTRACT.md`).equals(bytes(`${again}/CONTRACT.md`)));
  const provenance = read(`${pack}/PROVENANCE.md`);
  check(`${task}: saved entry matches generation record`,provenance.includes(hash(bytes(`${pack}/run.py`))));
  check(`${task}: recovered builder matches generation record`,provenance.includes(builderHash));
  check(`${task}: brief matches generation record`,provenance.includes(hash(bytes(`${root}/${brief}/HARNESS-BRIEF.md`))));
  const rows = read(`${again}/trials.csv`).trim().split(/\r?\n/);
  check(`${task}: one successful admitted fit retained`,rows.length===2 && rows[1].startsWith(`trial-001,ok,${task},constant,${features},17,`));
  const wrongTask = read(`${root}/harness-commands/${refusal}`);
  check(`${task}: historical wrong-task command refused`,wrongTask.includes('Exit: 2; expected 2;') && wrongTask.includes('invalid choice:'));
  const result = read(`${again}/trial-001/RESULT.md`);
  check(`${task}: recreated result records expected metric and runtime`,result.toLowerCase().includes(metric.toLowerCase()) && result.includes('Python 3.12.12;'));
  out(`HANDOFF-${task.toUpperCase()}.md`, `# Saved ${task} package handoff\n\nPrepared on 22 September from retained records. This document was not an input to the 20 September run. It improves retrieval without backdating preparation.\n\nRead the [brief](${link(`${root}/${brief}/HARNESS-BRIEF.md`)}), [generated package](${link(`${pack}/README.md`)}), [entry](${link(`${pack}/run.py`)}), [workflow](${link(`${pack}/WORKFLOW.md`)}), [acceptance rules](${link(`${pack}/ACCEPTANCE.md`)}) and [recovery guide](${link(`${pack}/RECOVERY.md`)}). The [generation record](${link(`${pack}/PROVENANCE.md`)}) binds this entry and brief to the [exact recovered builder](${link(recovered)}), SHA-256 ${builderHash}. The builder does not run when the saved package runs.\n\nThe entry imports the shared course tools and needs the pinned data. The [frozen contract](${link(`${again}/CONTRACT.md`)}) names the data and tool hashes, target, split and metric. Recover matching source from the recorded Git revision before claiming an exact historical replay. See the [source recovery record](${link('rsi/evidence/2026-09-22/builder-reconciliation/RECOVERED-SOURCES.csv')}). A current tool revision creates a separately labelled comparison. Do not silently substitute it.\n\nThe agent prepares Python 3.12.12 and the [declared requirements](${link(`${pack}/requirements.txt`)}), then checks the [resolved package record](${link(`${root}/package-versions.csv`)}). This historical run used Windows AMD64. The saved output states actual library versions; installing just the four top-level requirements does not pin every transitive dependency.\n\nFor a future lesson run, create a new sibling output folder and record its absolute path. Ask the agent to execute one constant/${features} baseline, seed 17, then submit the other task name to this fixed-task package. The lesson permits one fit and one wrong-task refusal per package; its generated two-attempt ceiling is not permission to use a second fit. Preserve errors and stop. Do not invoke final evaluation. The agent supplies command syntax and a 60-second command timeout.\n\nCheck actual predictions and metric with the package's acceptance procedure, then compare versions, complete prediction bytes, contract and refusal with the [earlier run](${link(old)}) and [saved recreation](${link(again)}). Do not supply an earlier score as a target to manufacture. The [historical refusal](${link(`${root}/harness-commands/${refusal}`)}) exits before the controller records a request; therefore it lives in the command log, not requests.csv.\n\nNo new fit, fresh environment or fresh agent was launched by this review.\n`);
}
read(`${root}/package-versions.csv`);
const skillPath = `${root}/01-03/BASELINE-SKILL.md`;
const handoff = read(`${root}/01-05/HANDOFF.md`);
check('01.05: handoff names exact retained skill',handoff.includes(hash(bytes(skillPath))));
check('01.05: prediction bytes match retained recipe run',bytes(`${root}/01-03/trial-001/predictions.csv`).equals(bytes(`${root}/01-05/trial-001/predictions.csv`)));
check('01.05: original handoff declares shared context',handoff.includes('same agent context'));
const missingTask = handoff.replace(' and ../01-03/TASK.md','');
out('HANDOFF-WITHOUT-TASK.md', missingTask);
read(`${root}/01-03/TASK.md`);
out('MISSING-TASK-REVIEW.md', `# A missing task file is a dependency finding\n\nThe [diagnostic handoff](HANDOFF-WITHOUT-TASK.md) removes the explicit task reference from a copy of the [original](${link(`${root}/01-05/HANDOFF.md`)}). The original remains unchanged. The retained [skill](${link(skillPath)}) itself still says to read TASK.md. A reader should flag that missing dependency and retrieve the exact task before fitting.\n\nThe skill supplies constant/calendar, seed 17 and one fit. It does not fully specify the prediction unit, target, metric, chronological boundaries or whether observed weather is valid at deployment. Those choices live in the [saved task](${link(`${root}/01-03/TASK.md`)}). Finding its indirect reference is useful; guessing those choices or copying a remembered score is not.\n\nThis is an author review with the original task available, not evidence that another agent discovered the omission. The historical one-fit reuse ran in the same author context. The lesson permits that labelled demonstration while leaving genuine fresh-session reuse unverified. No extra fit or learner response occurred.\n`);
out('BUILDER-PROPOSAL-V2.md',builder + '\n\n## Proposal revision v2 — unexecuted lesson variant\n\nBefore proposing a model change, name one observed error slice, one possible cause, one controlled intervention and one result that would count against that explanation. Keep the task, metric, split and allocated budget fixed. If the evidence does not support a specific cause, state the uncertainty rather than adding an unsupported causal claim.\n');
out('BUILDER-COMPARISON.md', `# A proposed builder change still needs a test\n\n[Proposal revision v2](BUILDER-PROPOSAL-V2.md) preserves the recovered builder and adds one instruction about evidence-based proposals. It is a saved text variant, not an installed skill or an accepted improvement. No harness was generated or run from it.\n\nBefore testing, freeze new regression and classification briefs, shared data and environment, identical generation and fit budgets, and a separate acceptance rubric. Give both builder versions the same inputs in recorded agent contexts. Evaluate the harnesses they produce for scientific contract compliance, refusal behavior, runnable outputs, predictive quality and total measured cost. Keep failures. Separate the cost of generating a harness from its fit cost. Do not choose tasks after seeing which builder wins.\n\nA clearer rationale alone does not establish better harnesses. Better selection scores alone do not excuse leakage or broken refusals. The current two saved-package reruns test repeatable execution; they do not execute this comparison. No additional budget is consumed here.\n`);
out('CHECKS.csv','check,status\n'+checks.map(row=>row.join(',')).join('\n')+'\n');
out('SOURCE-IDENTITIES.csv','path,sha256\n'+[...sources].map(row=>row.join(',')).join('\n')+'\n');
out('README.md', `# Repeat the saved procedure, then state what repeated\n\nThis 22 September author review connects labs 01.05 and 06.06 to their existing executions. It adds no fits, no fresh agent and no new generated harness. The source records stay unchanged.\n\nThe two [historical package executions](${link(`${root}/HARNESS-EXECUTION.md`)}) each ran one baseline into a new output folder and rejected the wrong task with exit 2. This review compares their complete prediction bytes and contracts to the earlier runs, checks generation identities, and confirms their one-row successful fit ledgers. See [actual checks](CHECKS.csv) and [source hashes](SOURCE-IDENTITIES.csv). These are file and record checks, not reruns of the commands.\n\n| Package | Recorded recipe | Repeated result | Handoff prepared in this review |\n|---|---|---|---|\n| Bike | constant/calendar, seed 17 | MAE 159.947912; identical prediction bytes | [Bike handoff](HANDOFF-BIKE.md) |\n| Wine | constant/all, seed 17 | Balanced accuracy 0.5; identical prediction bytes | [Wine handoff](HANDOFF-WINE.md) |\n\nThe original package folders contain task, workflow, acceptance, recovery and generation records, but no separate task-specific HANDOFF.md was retained before those executions. The two new handoffs consolidate those dependencies now. They must not be described as inputs used by the older run. Resolved dependencies and shared repository imports remain necessary; the package is not standalone.\n\nFor 01.05, the original handoff names the exact saved skill, and the later predictions equal the earlier recipe's bytes. Its own text declares the same author context. The [missing-task copy and analysis](MISSING-TASK-REVIEW.md) demonstrate the dependency question without claiming a new session forgot information.\n\nThe 06.06 extension now has a real [builder text variant](BUILDER-PROPOSAL-V2.md) and a [prespecified comparison design](BUILDER-COMPARISON.md). It remains unexecuted, as this extension asks students to change instructions and state the needed comparison. Repeating saved execution, generating new code and comparing builder versions are three separate experiments.\n\nThe existing repeat-saved-harnesses-v1 and fresh-session-handoff-v2 figures were inspected at full size and retained unchanged. Their captions distinguish saved execution, shared dependencies and actual context boundaries. This is a local visual check, not a new published-page inspection. Learner predictions, quizzes and teach-back remain unattempted.\n`);
out('README.md',readFileSync(resolve(dest,'README.md'),'utf8')+'\nThe [first-pass audit failure and repair](AUDIT-REPAIR.md) are retained separately. A case-sensitive metric-label search failed before correction; no historical evidence was changed.\n');
if(checks.some(([,status])=>status!=='PASS')) throw new Error('Saved reuse review failed; inspect CHECKS.csv');
console.log(`${checks.length} checks pass; ${sources.size} source identities retained; zero fits.`);
