// Maintenance inventory, not a student command or an automatic completion test.
import {existsSync, writeFileSync} from 'node:fs';
import {resolve, dirname, relative, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {lessons, themes} from './lesson-content.mjs';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const destination = resolve(repo, 'how-did-i-generate-it/rsi/validation');
const evidenceRoot = 'rsi/evidence/2026-09-20/';
const link = p => relative(destination, resolve(repo, p)).split(sep).join('/');
const related = new Map();
const cleanIds = [
  '00.01','00.02','00.03','00.04',
  '01.01','01.02','01.03','01.04','01.05',
  '02.01','02.02','02.03','02.04','02.05',
  '03.01','03.02','03.03','03.04','03.05','03.06',
  '04.01','04.02','04.03','04.04','04.05','05.01',
  '06.01','06.02','06.03','06.04','06.05','06.06','08.02','09.05'
];
for (const id of cleanIds) related.set(id, {
  path: evidenceRoot + 'clean-journey/' + id.replace('.', '-') + '/',
  label: 'Selected author execution',
  gap: 'Reconcile each action and the additional change below with its files. A directory or progress note alone does not close the lab.'
});
const limitations = {
  '01.04': 'Reuses the supplied checker; independent checker generation is untested. Reconcile the additional change separately.',
  '01.05': 'Same author context; the requested fresh-agent handoff is untested. A new process is not a new coding-agent context.',
  '02.05': 'A clean stop between commands was resumed. Forced process interruption and stale-lock recovery were not exercised.',
  '03.03': 'The join executed sequentially with declared resource fixtures; measured parallel resource checks are absent.',
  '03.06': 'The three views are described, but three separately rendered diagrams were not produced by this run.',
  '06.06': 'Saved generated packages ran in fresh output state. Independent regeneration from the brief in another agent is untested.',
  '08.02': 'Final lock and row/target recomputation executed. The author had seen the public final result before; this is a replay.',
  '09.05': 'Eight-fit matched comparison executed. Two constructed cases, one shared author context, and unmeasured inference cost limit the result.'
};
for (const [id,gap] of Object.entries(limitations)) related.get(id).gap = gap;
for (const id of ['09.01','09.03','09.04','09.07']) related.set(id, {
  path: evidenceRoot+'clean-journey/09-05/README.md',
  label: 'Related comparison evidence',
  gap: 'The matched run illustrates this mechanism. The complete lab actions and additional change have not been individually closed.'
});
for (const id of ['07.05','07.06']) related.set(id, {
  path: evidenceRoot+'organization-and-emergence/README.md',
  label: 'Executed synthetic cases',
  gap: 'Eight cases include overhead, random-history, and urgent-job contrasts. Map the listed outputs to each action; no real agent workers or learner responses were tested.'
});
related.set('07.07', {
  path: evidenceRoot+'self-play/README.md',
  label: 'Executed policy learning',
  gap: 'Training, frozen evaluation, and parameter traces are retained. The proposed stronger-opponent comparison is a planning exercise; it has not run.'
});
related.set('09.02', {
  path: evidenceRoot+'two-generations/README.md',
  label: 'Two executed fixed-improver generations',
  gap: 'Four fits, the same improver hash, one rejected task child, one accepted child, and a rejected-child replay are retained. Learner interpretation remains untested.'
});
related.set('09.06', {
  path: evidenceRoot+'two-generations/README.md',
  label: 'Two executed improver-comparison generations',
  gap: 'Eight fits, proposal/resume checkpoints, ancestry checks, and third-generation refusal executed. Both improver proposals were rejected: this run does not prove an accepted revised improver governs the next generation. The protocol and state predate the run; the consolidated lineage was derived afterward.'
});
for (const id of ['10.22','10.23','10.24','10.25','10.26']) related.set(id, {
  path: evidenceRoot+'sciencebuddy-laptop/README.md',
  label: 'Executed local ScienceBuddy teaching activities',
  gap: 'Report checks, toy numerical updates, synthetic pair transitions, source arithmetic, and additional reading/planning notes are retained. The reporter is deterministic and author-written; no independent agent behavior, real LLM training, paper reproduction, or learner assessment is established.'
});
for (const id of ['02.06','05.02','05.03','05.05','08.01']) related.set(id, {
  path: evidenceRoot+'loops-and-systems/README.md',
  label: 'Executed loop, routing, context, ablation, and repetition activities',
  gap: 'Declared fits and fixtures, source identities, additional analysis, and measured outputs are retained. The fixed router and guards are agent-written code in one author context; no real learner assessment or independent language-model behavior is established.'
});
related.get('02.06').gap = 'Four matched-budget fits and a pre-fit adaptive choice executed. The unequal-budget extension was explained but its additional fits were not run. Baseline outcomes were author-known; inference cost is unmeasured.';
related.get('08.01').gap = 'Six fits across all three prespecified seed pairs, checked predictions, actual-data plot, and post-hoc best-seed contrast are retained. Three seeds share one split; dataset uncertainty and learner interpretation remain untested.';
related.set('05.04', {
  path: evidenceRoot+'live-coordinator/README.md',
  label: 'Executed live state control and process resumption',
  gap: 'One new fit, a later check process, three handoff fixtures, and post-completion refusal executed. The earlier retrospective trace and its separate fit remain preserved. Forced interruption during fitting, independent reviewers, and learner interpretation were not tested.'
});

for (const [id,r] of related) {
  if (!lessons.some(l=>l.id===id) || !existsSync(resolve(repo,r.path))) throw new Error('Invalid evidence mapping: '+id);
}

let body = `# Required activity coverage\n\nThis inventory separates authored instructions from execution evidence. It covers all ${lessons.length} lab READMEs at the current source revision. The [editorial inventory](README-GUIDANCE-COVERAGE.md) answers a different question.\n\n${related.size} labs have mapped related author-execution evidence; ${lessons.length-related.size} do not yet have a lab-specific execution mapping here. **These are mapping counts, not completed-lab counts.** Unmapped means unverified in this inventory, not proof that a mechanism has never run. Component tests, primary-source reading, and a progress-file assertion do not automatically satisfy a lesson activity.\n\nEach entry retains the required steps, the additional change, the closest known execution record, and a closure gap. To close an activity, name its actual input, command or action, output, check, and budget in the execution record. Preserve failed attempts. Source-review activities need the specific inspected primary sections and a completed claim audit; an abstract link alone is insufficient.\n\nAll learner predictions, quizzes, and teach-back remain unattempted by a real student unless later evidence explicitly says otherwise. Other native-agent contexts and optional GPU/cluster backends remain separate checks. No lab is declared fully validated by this generated inventory.\n\nThe selected journey's [scope and omissions](CLEAN-JOURNEY-RESULTS.md) govern its evidence. Later runs must use new, declared experiments; never reopen a final-locked workspace to fill a coverage gap.\n`;
for (const [key,t] of Object.entries(themes).sort(([a],[b])=>Number(a)-Number(b))) {
  body += `\n## ${key} · ${t.title}\n`;
  for (const l of lessons.filter(l=>l.theme===key)) {
    const path = `rsi/${t.directory}/${l.group ? l.group+'/' : ''}step_${l.id.split('.')[1]}_${l.slug}/README.md`;
    const r = related.get(l.id);
    body += `\n### [${l.id} · ${l.title}](${link(path)})\n\n`;
    body += l.steps.map((s,i)=>`${i+1}. **${s[0]}.** ${s[1]}`).join('\n')+'\n';
    body += `\n**Additional change:** ${l.change}\n\n`;
    body += r
      ? `**Evidence:** [${r.label}](${link(r.path)}).\n\n**Closure gap:** ${r.gap}\n`
      : '**Evidence:** No lab-specific execution mapping yet.\n\n**Closure gap:** Execute or locate and inspect the named activities, preserve their artifacts, and assess the additional change. Do not infer completion from the authored example.\n';
    body += `\n**Acceptance to verify:** ${l.check}\n`;
  }
}
writeFileSync(resolve(destination,'REQUIRED-ACTIVITY-COVERAGE.md'),body);
console.log(`Inventoried ${lessons.length} labs; ${related.size} related evidence mappings; no automatic completion claims.`);
