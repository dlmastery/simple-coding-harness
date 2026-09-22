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
related.set('11.05', {path: 'rsi/evidence/2026-09-22/portfolio/README.md', label: 'Evidence-linked portfolio and prepared peer handoff', gap: 'A no-fit assembly audit verifies thirty original identities, one concrete prediction row, matching start bytes and later instruction use. Public portfolio, existing illustration, failure story, separate costs and a one-fit peer guide are complete as author artifacts. Peer reproduction, actual learner answers, feedback and transfer proposal remain explicitly pending; this mapping does not represent a completed peer session.'});
related.set('11.04', {path: 'rsi/evidence/2026-09-22/external-audit/README.md', label: 'Versioned primary-source audit and acceptance-rule arithmetic', gap: 'Date-bounded queries, selected v2 methods/results/limits, pinned repository metadata, a charitable short audit and a discriminating follow-up are retained. One calculator enumerates 441 count pairs with six checks. No source-system execution, raw paper-outcome reanalysis, full implementation audit, complete-paper review, independent peer or learner assessment occurred; HTML and PDF-image access failures remain explicit.'});
related.set('11.03', {path: 'rsi/evidence/2026-09-21/capstone-portability/README.md', label: 'Two-task smoke runs and a declared-capability refusal', gap: 'Bike regression and wine classification execute through one canonical skill and shared host; result checks, both recalls, new-process comparison, four invalid requests and two capability fixtures are retained. This tests existing task adapters, not transfer of the revised improver. Another real agent, native discovery, actual permission removal, cluster cancellation/resume, total inference costs and learner assessment remain untested. Public inspection exposes final-data summaries, not final performance.'});
related.set('11.02', {path: 'rsi/evidence/2026-09-21/capstone-recursion/README.md', label: 'Eight-fit improver comparison with terminal evaluation', gap: 'Two initial fits expose the weak training-ranking rule; two matched three-fit arms execute original and revised Markdown instructions. Candidate-trial inheritance, frozen external acceptance, terminal evaluation, 43 checks and three refusals are retained. No post-acceptance third generation, autonomous proposal, fresh-task effectiveness, complete research cost, independent context, peer or learner assessment occurred.'});
related.set('11.01', {path: 'rsi/evidence/2026-09-21/capstone-harness/README.md', label: 'Generated white-wine regression harness and fresh-environment baseline', gap: 'Two allocated actual fits, independent prediction checks, three invalid requests, seven altered-output checks, and one charged no-training failure stub are retained. Fresh dependencies reproduce prediction bytes. Larger-job plan is generated-only; peer/learner, native-agent, remote-backend, and final-evaluation checks were not performed.'});
related.set('10.01', {path: 'rsi/evidence/2026-09-21/research-reading/README.md', label: 'Versioned framework and three-case evidence classification', gap: 'Selected v2 definitions and historical Weco criteria are mapped separately to actual retry, memory, and inherited-improver records; three artifact identities pass. This is an author audit of scoped demonstrations, not autonomous discovery, full-paper review, general effectiveness, or learner assessment.'});
related.set('10.02', {path: 'rsi/evidence/2026-09-21/research-reading/README.md', label: 'Date-bounded discovery and primary announcement claim trail', gap: 'Six explicit recent-month queries, identity/date checks, methods/results links, and a headline-to-integrity-sample comparison are retained. Original social post, website first date, pinned runnable artifact, complete costs, independent reproduction, and learner assessment remain unverified.'});
related.set('10.37', {path: 'rsi/evidence/2026-09-21/system-comparison/README.md', label: 'Six-system source comparison and checked local claim challenge', gap: 'Mechanism-only and result views retain source versions, boundaries, resources, and reading depth. Four active local identities were checked; both improver proposals remain rejected. No source reproduction, raw paper-log audit, complete cost reconciliation, independent context, or learner assessment occurred.'});
related.set('10.38', {path: 'rsi/evidence/2026-09-21/bottlenecks/README.md', label: 'Five numerical scenarios and a recorded-lineage acceleration audit', gap: 'Calculator inputs, outputs, costlier-verifier extension, separate shrinking-increment arithmetic, copied local lineage/cost rows, and selected source assumptions are retained. No new fits or empirical acceleration follow. Total-resource cost, source-model calibration, and learner assessment remain unestablished; the separate lab-10.37 matrix now has its own evidence mapping.'});
related.set('10.31', {path: 'rsi/evidence/2026-09-21/harness-builder/README.md', label: 'Source-specific map and two matched generated-harness executions', gap: 'The observed parent report failure is repaired by one component edit; child reports both recalls with identical predictions. Historical builder identity is recovered and unchanged; it does not run. The two-brief comparison is an unexecuted proposal. Independent creator/executor contexts, generator superiority, broad transfer, and learner assessment remain untested.'});
related.set('10.30', {path: 'rsi/evidence/2026-09-21/efficient-harnesses/README.md', label: 'Four matched fits with fixed quality and report-cost gates', gap: 'Both task pairs pass fixed floors and have identical predictions; duplicate report calls/bytes fall. The checker-removal fit stub fails, and optional source cost boundaries are audited. One-shot timings, unknown design/inference costs, shared author context, and unattempted learner assessment limit the conclusion; no paper mechanism or recursive compounding was reproduced.'});
related.set('10.29', {path: 'rsi/evidence/2026-09-21/gui-skill/README.md', label: 'Two live browser attempts with saved metrics and screenshots', gap: 'The deliberate first control failed; detail inspection on the unchanged page led to a passing second selection. The visible-trace critique, one-instruction repair, exact checks, and warning-exposure audit are retained. All roles share author context; independent critique, general skill reuse, other browser integrations, and learner assessment remain untested.'});
related.set('10.33', {path: 'rsi/evidence/2026-09-21/scaffolding/README.md', label: 'Four executed agent-operated form attempts', gap: 'Action-hint, richer-observation, changed unassisted, and stale-hint conditions passed exact checks. The stale detour was preplanned; all fixtures were author-known in one context. No weight training, causal scaffold comparison, independent-agent evaluation, or learner assessment occurred.'});
for (const [id,gap] of Object.entries({
  '10.27': 'A real prior failed proposal, immutable-by-procedure trace, persistent notebook versions, and unchanged active skill are retained. Two candidate checks reject the fallback; a separate exposure-only condition reads the notebook without a third task check. Scripted input identities do not establish isolated coding-agent access or general skill-evolution benefit.',
  '10.32': 'Five packets, five actual author answers, exact original-event checks, and an expanded-description operation audit are retained. The faulty summary implies the wrong state. All conditions share a knowledgeable author; provider costs, clean context isolation, broad memory effects, learner assessment, and parameter training are untested.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/memory-interfaces/README.md', label: 'Executed knowledge retention and memory-representation checks', gap});
for (const [id,gap] of Object.entries({
  '10.18': 'A saved hypothesis, two matched fits, prediction checks, hourly errors, and a conditional conclusion are retained. The author had prior development-result exposure; this is not blind hypothesis discovery, causal evidence, or learner assessment.',
  '10.19': 'Two separately implemented subset screens and two matched fuller confirmation/ablation fits executed. The fastest-screen alternative uses measured times without extra fits. No fuller-condition ranking of the unselected idea, protected evaluation, independent-agent screening, or learner assessment is established.',
  '10.20': 'A current-context agent review, frozen two-fit seed follow-up, evidence-linked response, and restatement counterexample are retained. Two seeds do not establish broad robustness; independent peer review, conference acceptance, and learner assessment remain absent.',
  '10.21': 'The two-study lineage records a fixed researcher hash with growing context, actual costs, a measured chart, selected source evaluation audit, and an unexecuted matched researcher comparison. It does not demonstrate a revised improver, researcher-level superiority, or learner understanding.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/scientist-labs/README.md', label: 'Executed scientific workflow and audited result lineage', gap});
for (const [id,gap] of Object.entries({
  '10.16': 'Two separately allocated parent captures, one task-skill edit, two child checks, an unchanged updater, and a byte-identical renamed copy are retained. Constructed ML workflow decisions test a unit repair, not new model performance, independent agents, or learner understanding.',
  '10.17': 'A separately prepared second update trace, one self-directed updater proposal, and two later task-skill arms executed. The revised policy selected a different internal check; both arms faced the same three external cases. A schedule simulation is labelled hypothetical. Shared author context and known fixtures do not establish general autonomous discovery, protected evaluation, statistical benefit, or learner understanding.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/meta-skills/README.md', label: 'Executed fixed task repairs and an inherited updater revision', gap});
for (const [id,gap] of Object.entries({
  '10.13': 'Four regression fits, before-action decisions, retained and rejected recipes, prediction checks, and an unknown-stopping reordered replay executed. The fixed controller and author-exposed data do not establish autonomous discovery, protected evaluation, or learner understanding.',
  '10.14': 'One actor proposal and two frozen three-fit searches executed from empty matched state. An unequal-budget illustration stayed unexecuted. The child improved selection MAE on exposed development data; inference cost, independent tasks, statistical reliability, and learner understanding remain untested.',
  '10.15': 'Two frozen-producer preferences were projected through one shared adapter into target procedures; six behavioral fixtures and one separate overcomplication check executed with zero fits. General researcher-code generation, independent proposer contexts, repeated fresh-task improvement, and ignition are not established.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/aide-labs/README.md', label: 'Executed inner search, matched procedure comparison, and role fixtures', gap});
for (const [id,gap] of Object.entries({
  '10.10': 'Two prerequisite trace captures and two context-only patch checks executed; a two-component alternative remains a labelled proposal. Component and fixed-driver scope is explicit. Constructed records and a stub do not test real language-model compression, independent actors, or learner understanding.',
  '10.11': 'All seven declared fixture executions are retained, including independent-edit passes, combined failures on original/fresh cases, and a malformed-input refusal before the stub. Zero fits. The combination was rejected; broad transfer, real agents, and learner interpretation remain untested.',
  '10.12': 'Selected primary methods and both source figures were inspected. Eight local proposal edges and 28 source files were identity-checked; both improver proposals remain rejected. No new model execution, independent source reproduction, accepted recursive revision in this run, or learner assessment is established.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/modular-labs/README.md', label: 'Executed module checks and source-specific lineage audit', gap});
for (const [id,gap] of Object.entries({
  '10.07': 'Three bike fits and outcome checks, a pre-fit branch decision, a measured tree, and an unexecuted proposal are retained. Recipe ancestry is a classroom simplification; no source-paper workspace inheritance, independent discovery agent, blind task, or learner assessment was tested.',
  '10.08': 'Two primary replays, one unsupported query, and two reduced-coverage replays ran with zero fits. Removing a measured node reversed the ranking. The fixed-order interface omits the paper’s root/leaf batches and objective; no general cost-saving or learner claim follows.',
  '10.09': 'Four fits on new synthetic rows, frozen policies and choices, checked evaluation predictions, costs, and an unexecuted revision proposal are retained. Replay selected the existing baseline, so no accepted policy update was redeployed. Author-known task generation, agent isolation, inference cost, and learner assessment remain limitations.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/dream-labs/README.md', label: 'Executed discovery, replay, and online comparison', gap});
for (const [id,gap] of Object.entries({
  '10.04': 'One outcome check, actor-authored bounded memory, and an inspected historical counterexample are retained; zero fits. The verifier did not approve the lesson. Independent actors and learner interpretation were not tested.',
  '10.05': 'Four fits, pre-fit decisions, frozen choices, prediction checks, and one separate adaptation-copy update executed. Both arms share author context and the same decision rule; equal scores do not isolate a memory effect. Adaptation performance, clean agent contexts, inference costs, and learner understanding remain untested.',
  '10.06': 'Two typed retrieval checks and a conflicting merged copy are retained; zero fits. The new and stale working states are constructed fixtures. General semantic retrieval, autonomous memory formation, and learner interpretation were not tested.'
})) related.set(id, {path: 'rsi/evidence/2026-09-21/memory-labs/README.md', label: 'Executed memory boundaries and retained counterexamples', gap});
related.set('10.03', {
  path: 'rsi/evidence/2026-09-21/exploration/README.md',
  label: 'Executed three-fit exploration and historical duplicate comparison',
  gap: 'Two probes, a pre-fit decision, the third feature probe, and three result checks executed. The duplicate example reuses inspected historical repeats. Author context knew prior results; no task-memory file was loaded, but cold-start exploration, causal attribution, and learner understanding were not tested.'
});
related.set('10.35', {
  path: 'rsi/evidence/2026-09-21/operator-composition/README.md',
  label: 'Executed typed-operator and scheduler simulation',
  gap: 'Five checks, twelve operator attempts, one policy gate, and three synthetic scores executed; a saved rule governed later work. Selected source comparison is read. No actual model training, later-task original/revised comparison, autonomous adaptation, or learner assessment was tested.'
});
related.set('10.34', {
  path: 'rsi/evidence/2026-09-21/model-harness-fit/README.md',
  label: 'Executed interface comparison and source audit',
  gap: 'Four parser subprocesses and unchanged hashes demonstrate format repair only. Selected primary-method reading is recorded; no weight training, source reproduction, native-agent portability, or learner assessment was tested.'
});
related.set('10.36', {
  path: 'rsi/evidence/2026-09-21/checked-reference/README.md',
  label: 'Executed reference gates and candidate fixtures',
  gap: 'Four instrumented traces, one quality gate, and two candidate evaluations executed. Author-known deterministic fixtures, a tiny declarative skill, and trusted instrumentation do not establish independent agent learning, general leakage detection, or learner understanding.'
});
related.set('10.28', {
  path: 'rsi/evidence/2026-09-21/procedure-graph/README.md',
  label: 'Executed procedure-graph fixtures',
  gap: 'One edge edit, two parent/child selection pairs, one frozen distinct fixture, and one semantic check executed in six traversals with zero fits. Author-constructed deterministic cases are not independent LLM adaptation, blinded transfer, or learner assessment.'
});
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
  '03.03': 'The join executed sequentially with declared resource fixtures. The newly explicit wrong-contract case still needs execution evidence; measured parallel resource checks are also absent.',
  '03.06': 'The three views are described, but three separately rendered diagrams were not produced by this run.',
  '04.03': 'The mapped folder contains an invariants note, not six separately retained case inputs and verdicts. The six base cases and two units-extension cases remain to be demonstrated individually.',
  '04.04': 'Original and corrected tables and checks are retained. A separate consistently renamed copy and its third check remain unverified in this mapped folder.',
  '06.06': 'Saved generated packages ran in fresh output state. Independent regeneration from the brief in another agent is untested.',
  '08.02': 'Final lock and row/target recomputation executed. The author had seen the public final result before; this is a replay.',
  '09.05': 'Eight-fit matched comparison executed. Two constructed cases, one shared author context, and unmeasured inference cost limit the result.'
};
for (const [id,gap] of Object.entries(limitations)) related.get(id).gap = gap;
for (const [id,gap] of Object.entries({
  '00.01':'The original retrospective brief and source inspection are supplemented by all eight required rows, field explanations and a separate tomorrow-noon brief. No forecast data or model is invented. Learner interpretation remains unattempted.',
  '00.02':'The actual original data-inspection command, source check, environment report and plot are retained. This pass visually inspects that plot and supplies the disabled-command analysis. Permissions were not actually removed; native other-agent and learner checks remain untested.',
  '00.03':'The original one-fit ledger and commands are linked to three explicit errors and a quiet/busy contrast from saved predictions. Zero new fits. Deliberately selected extreme rows illustrate directions, not typical error rates; learner responses remain unattempted.',
  '00.04':'A generated checker validates the original report and refuses the score-10 copy with nonzero exit. Complete row membership, source targets, candidate records and six-decimal tolerance are checked; prediction bytes stay unchanged. Wrong-partition arithmetic is explained. The evaluator shares author access, and learner assessment remains unattempted.'
})) related.set(id,{path:'rsi/evidence/2026-09-22/start-reconciliation/README.md',label:'Original starting activities plus checked missing steps',gap});
related.set('01.04', {path: 'rsi/evidence/2026-09-22/generated-checker/README.md', label: 'Generated separate checker with actual pass and row-substitution refusal', gap: 'The generated standard-library implementation checks the archived baseline, then refuses one changed source-row ID in exactly two invocations and zero fits. One-cell differences and five source identities are retained; the metric-only limitation is explained. This closes the prior supplied-checker reuse gap. Same author context, trusted references, untested other tampering branches and unattempted learner responses limit the result.'});
related.set('02.05', {path:'rsi/evidence/2026-09-22/interrupted-attempt/README.md',label:'Original orderly resume plus actual stale-worker recovery',gap:'The earlier three-fit sequence retains its first result and budget. A separate admitted no-training fixture leaves a stale worker record; OS absence checks, two pre-fit refusals, manual reconciliation, one real trial-002 fit and nine invariants are retained. Initial launcher-PID and expected-exit errors are preserved, not rerun away. This tests stale-record recovery, not optimizer checkpoint resumption, an independently validated termination driver, a fresh agent or learner assessment.'});
for (const [id,gap] of Object.entries({
  '01.01':'Five actions now have concrete inputs, outputs and completion checks. A real baseline row is traced backward; split-after-fit bias is explained as a hypothetical counterexample. No fit or learner response is attributed to this planning activity.',
  '01.02':'A new one-fit process has a contemporaneous five-action trace, data inspection and prediction check. Full prediction bytes match the prior run; tool/contract changes and runtimes are explicit. A copied missing report is diagnosed without retraining. The environment and author context are reused; learner assessment remains unattempted.',
  '01.03':'A saved skill supplies recipe arguments to the fixed driver in a new one-fit workspace. Its snapshot, instruction record, five-action trace and checked predictions agree. Ambiguous and repaired text variants are retained without extra fits. Autonomous planning, changed-skill effectiveness, fresh contexts and learner understanding are not established.'
})) related.set(id,{path:'rsi/evidence/2026-09-22/fixed-process/README.md',label:'Five-action process and saved-skill executions with concrete extensions',gap});
for (const [id,gap] of Object.entries({
  '02.01':'The original controlled two-fit comparison now has a checked 24-hour slice audit and actual-data figure. Its missing pre-fit diagnosis remains a specific historical gap: a retrospective explanation cannot govern an earlier fit. No new fit or learner answer is attributed to this audit.',
  '02.02':'Three newly allocated fits read and cross-check durable state in separate controller processes. All state versions, retained-best decisions, prediction checks and a fourth-request refusal are preserved. The one-limit extension is a separate zero-fit plan. The fixed author-written controller, prior public exposure and unattempted learner assessment limit the result.',
  '02.03':'Two new fits use saved feedback and decision fields written before execution. Frozen identities, checked predictions, hourly improvements and regressions, and a weak-feedback counterexample are retained. The author knew related outcomes; this is not blind or autonomous diagnosis, causal attribution, independent-agent evidence or learner assessment.',
  '02.04':'Six read-only checks verify the original two fits, duplicate and budget refusals, source hash and pre-fit duplicate guard. The rule explanation is a later reconstruction, not an original LOOP.md. Intentional replication is explained without extra fitting; adversarial isolation and learner assessment remain untested.'
})) related.set(id,{path:'rsi/evidence/2026-09-22/loop-state-feedback/README.md',label:'Pre-action state and feedback runs with historical slice and stop audits',gap});
related.set('02.01',{path:'rsi/evidence/2026-09-22/model-hypothesis/README.md',label:'New pre-fit diagnosis and controlled two-fit comparison',gap:'A separately allocated run saves a hypothesis, alternative and possible failure before two checked fits. Saved fields govern recipes; all 24 hourly comparisons and eight checks are retained. This closes the missing-note evidence gap without rewriting the historical run. Prior outcome exposure, one selection period, same author context and unattempted student assessment remain explicit.'});
related.set('03.06', {
  path: 'rsi/evidence/2026-09-21/three-views/README.md',
  label: 'Rendered views and audit of existing run records',
  gap: 'Three separate diagrams, artifact table, failure audit, and unexecuted plan extension are retained. Recovery chronology is reconstructed from program order and retained outputs; exact event timestamps and a separate recovery journal are absent. Learner interpretation was not tested.'
});
for (const [id,gap] of Object.entries({
  '03.03': 'Four joins now execute, including wrong contract and the late-result simulation within the missing case. Resource inputs are declared fixtures; actual concurrent workers, machine capacity, and learner responses were not tested.',
  '04.03': 'Six base cases and two separate units-extension cases now execute with individual inputs and verdicts. Units checks require a label only. Unknown-relation rejection was source-inspected but not separately executed in this allocation; omitted facts and learner understanding remain untested.',
  '04.04': 'Original, corrected, and consistently renamed tables now execute with failure counts three, zero, and three. Record repair does not validate a real leaked experiment; no learner responses were collected.'
})) related.set(id, {
  path: 'rsi/evidence/2026-09-21/foundation-gaps/README.md',
  label: 'Executed foundation cases and additional changes', gap
});
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
for (const id of ['07.01','07.02','07.03','07.04','07.08','08.03','08.04','08.05','08.06']) related.set(id, {
  path: evidenceRoot+'self-star-and-measurement/README.md',
  label: 'Executed self-* and measurement activities with labelled replays',
  gap: 'The eight-fit comparison, fixed-rule checks, copied inputs, numerical examples, additional proposals, and actual rollback are retained. Cached comparisons are replays; interpreter behavior is not independent LLM behavior. Real learner assessment remains untested.'
});
related.get('07.01').gap = 'Correction and a later fixed-reporter process executed without editing its rule. A fresh coding-agent session, rather than a Python process, was not tested.';
related.get('07.02').gap = 'Two prediction-based checks recompute existing regression/classification evidence and test the overbroad rule. These known cases are replays, not fresh reflection-validation tasks.';
related.get('07.03').gap = 'A separate process reads the retained rule, changes a later cached-candidate decision, and refuses a metric-scope mismatch. The no-memory control is deliberately weak; benefit does not establish LLM learning or unseen generalization.';
related.get('08.05').gap = 'Four new fits use frozen skill hashes and a predeclared wine interface. Prior public wine outcomes were author-known, so the run is a transfer replay, not an uncontaminated transfer test. A new development proposal stays unexecuted.';

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
