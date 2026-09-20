// Studio support: concrete classroom examples, not substitutes for source methods.
export const researchGuidance = {
  '10.01': {
    example:'Your fixed search loop tries a tree after a linear model. Your memory experiment saves a rule for later tasks. Your inheritance experiment changes the rule that generates future skill edits. These are three different artifacts and feedback paths. Apply a source’s criteria to each; do not infer that similarly numbered levels in two publications mean the same thing.',
    outputs:[['FRAMEWORK.md','Paraphrases criteria with section references and required observations.'],['Three-case evidence map','Connects fixed retries, memory, and inherited improver changes to actual local artifacts.'],['Separate terminology columns','Preserve each source’s definitions instead of merging its level numbers.']],
    recovery:'If a classification depends on a word in the title, find the operational definition in the text. If the necessary inheritance or comparison artifact is missing, leave that criterion unsupported. If the paper has changed versions, record which version supplied the definition before comparing it with earlier notes.',
    hint:'Translate each category into a question that an artifact can answer. A taxonomy helps organize evidence; it cannot create missing evidence.'
  },
  '10.02': {
    example:'An author reposts a July report in September. The post is recent, but the experiment is still July work unless a substantive new result is linked. Conversely, a September methods revision may matter even when the title stays the same. Your claim card records both events and identifies what actually changed.',
    outputs:[['Dated search record','Retains exact queries, source identity, access failures, and the preceding-month window.'],['CLAIM-CARD.md','Links the original announcement, methods, evaluation, available code, and unresolved claims.'],['Headline-to-evidence comparison','Names a condition or limitation omitted by the short announcement.']],
    recovery:'If an X thread is blocked, record its canonical URL and access failure; inspect linked primary materials separately. Do not attribute a repost’s wording to the original author without checking. If search results show only a crawl date, read the paper’s submission history or the original post date before admitting it as new work.',
    hint:'Trace who said it, when it was first said, what changed, and what evidence is available. Those are four separate fields.'
  },
  '10.03': {
    example:'The constant baseline asks how far a model can get without input variation. The calendar model asks whether hour and date structure explain useful variation. The third recipe should address a remaining uncertainty exposed by their errors. Repeating the same deterministic calendar fit does not answer a new feature question, though a separately declared repeat can check reproducibility.',
    outputs:[['Three-attempt exploration plan','States the different uncertainty addressed by each initial probe.'],['Probe traces and final proposal','Record the third hypothesis before its fit and link it to observed selection errors.'],['Exploration report','Retains failures, known cost, and the information gained within the three-fit ceiling.']],
    recovery:'If the third choice was justified only after its score appeared, preserve that ordering and label the explanation as retrospective. If a duplicate recipe is refused, retain the refusal; do not vary an irrelevant label to evade duplicate detection. Use existing repeats or reasoning for the counterexample, without adding a fourth fit.',
    hint:'Complete “this result would distinguish ___ from ___” before running an exploratory action. More scores do not automatically mean more information.'
  },
  '10.04': {
    example:'The checker confirms that the calendar model’s MAE matches its saved predictions. The actor then writes “calendar fields always beat weather.” The verified number does not support that broad lesson: the compared models and conditions matter. The result can be valid while its inferred memory is wrong.',
    outputs:[['Outcome verdict','Checks one actual result without authoring its lesson.'],['Actor-owned MEMORY.md','Names the author, scope, supporting trace, and retained statement.'],['Counterexample inspection','Tests the memory wording separately from the original metric check.']],
    recovery:'If the note says verifier-approved memory, inspect what the verifier actually checked and correct the attribution. A role name in one chat does not create independent authority. If the counterexample requires an unbudgeted fit, use an existing case or leave the additional experiment proposed; this activity has no fit allowance.',
    hint:'Ask whether the evidence validates a measurement or a general rule. A correct measurement can support several competing explanations.'
  },
  '10.05': {
    example:'A frozen memory says to check prediction-time availability before choosing features. One arm may read it and one may not. Both get the same task and two fits. If the supposed no-memory arm already saw the note in the same context, unchanged file hashes cannot make that a clean information comparison.',
    outputs:[['Memory hash and comparison plan','Freeze content, cases, budgets, and permitted exposure before evaluation.'],['Two arm records','Retain decisions, outcomes, costs, and actual context boundaries.'],['Freeze and claim check','Confirms file stability while stating whether the no-memory boundary was real.']],
    recovery:'If the memory file changes during evaluation, preserve the run and reclassify it as adaptation rather than frozen-memory testing. Do not rerun until a separate protocol is declared. If a fresh context is unavailable, execute a labelled shared-context demonstration and restrict the conclusion instead of pretending the agent forgot the note.',
    hint:'A checksum checks file identity. It does not check what the model already knows from the conversation.'
  },
  '10.06': {
    example:'“Candidate trial-003 awaits verification” belongs to one run. “Join predictions to targets by row identity” can be a reusable rule when supported by evidence. The next run can inherit the second statement, but its candidate ID and remaining attempts must come from its own ledger.',
    outputs:[['WORKING.md','Contains current run identity, active candidate, pending action, and budget.'],['EXPERIENCE.md','Contains a reusable lesson with scope and evidence links.'],['Two retrieval checks','Show useful transfer and rejection of a stale run-specific identity.']],
    recovery:'If a retrieved summary changes the current budget, compare its source-run ID with the active contract. Do not edit the ledger to fit old prose. If a general lesson contains an absolute path into an old workspace, separate the principle from the historical example and keep the original evidence link.',
    hint:'Ask whether a statement should still be true after the run ID changes. Its lifetime helps determine where it belongs.'
  },
  '10.07': {
    example:'Node A is a measured baseline. B adds calendar structure after inspecting A. C tests a different permitted recipe, also motivated by A. An imagined child D has no execution report. The discovery tree may include D as a proposal, but its score must remain unknown.',
    outputs:[['Discovery table and rendered tree','Identify nodes, parent links, recipes, execution status, and result paths.'],['Three actual trial records','Supply measured outcomes and costs for the visited nodes.'],['Coverage statement','Separates proposed branches, failed attempts, and successfully measured outcomes.']],
    recovery:'If a node has a score but no matching predictions or report, classify it as unsupported until its source is found. If a failed fit is silently absent, restore the attempted node and its cost. Do not copy a nearby node’s score into an unvisited branch merely because its recipe looks similar.',
    hint:'For each plotted number, follow its link back to one executed trial. An attractive tree is still only a drawing without those links.'
  },
  '10.08': {
    example:'A history contains measured nodes A, B, and C. Policy 1 spends its replay budget on A then B; policy 2 reaches C. Their ranking depends on these recorded outcomes and costs. A request for an unseen forest branch returns unknown. Assigning it C’s score would turn replay into invented evidence.',
    outputs:[['Frozen history and replay tool','Permit only recorded nodes, edges, outcomes, and declared cost accounting.'],['Two replay traces','Show each policy’s visited sequence and retained known result.'],['Unsupported-query record','Returns unknown for the missing branch without invoking a fit.']],
    recovery:'If replay unexpectedly launches training, stop and inspect the execution boundary. If a policy selects an absent edge, keep the unsupported result instead of filling it with a prediction. If it examines all outcomes before choosing, disclose that information access; the replay should match the claimed policy’s observation rules.',
    hint:'Replay can change how known work is selected. It cannot reveal what an unexecuted experiment would have measured.'
  },
  '10.09': {
    example:'A policy selected from a history dominated by calendar models may prioritize them on new work. A newly declared regression condition can reward different structure. The online run tests those actual choices. If the policy loses, the earlier replay result can remain correct within its recorded coverage.',
    outputs:[['Frozen policy versions and new-work plan','Explain what is new relative to the replay history.'],['Four fit records','Give each policy the same two-fit allowance and preserve retained outcomes.'],['Two-phase cost and result report','Separates replay preparation from online execution without omitting either.']],
    recovery:'If the “fresh” task was used to choose the replay winner, treat it as development evidence. If the new condition changes the scientific target, write a new task contract before executing. If online feedback inspires an edit, save it as a new proposed policy; do not insert it into this frozen comparison.',
    hint:'Identify the first result that required a new environment execution. That is where replay ends and online evidence begins.'
  },
  '10.10': {
    example:'A tool correctly reports seconds, but the summary interprets the value as minutes. Changing the estimator will not repair that interface error. Restrict the candidate edit to the observation-to-report step, then test the original unit mismatch and a case whose units were already handled correctly.',
    outputs:[['Failure localization','Compares a successful and failed trace and identifies the earliest relevant divergence.'],['One component patch','Preserves the parent and unchanged neighboring components.'],['Target and regression outcomes','Show whether the patch repairs the fault without breaking the contrast.']],
    recovery:'If the patch changes several components, split the proposed changes or record that attribution is no longer local. If the chosen component is named without trace evidence, revisit the diagnosis. A successful original case is a regression check, not proof that the patch generalizes to all tasks.',
    hint:'Find the first place where a correct upstream fact becomes an incorrect downstream action. Start the repair hypothesis at that boundary.'
  },
  '10.11': {
    example:'Edit A shortens a context record by removing a units field. Edit B adds a completion check that requires units. Each can pass under its own prior fixtures, yet their combination fails. A shared interface table reveals the conflict before a model fit is needed.',
    outputs:[['Four version identities and interface table','Define baseline, A, B, and A+B, including field meanings.'],['Six original/transfer fixture outcomes','Compare all four on the original case and baseline versus A+B on the fresh case.'],['Seventh missing-field refusal','Confirms a precise failure before the fit stub; no training occurs.']],
    recovery:'If the generated harness starts real training, stop and repair the declared fit stub before continuing. If a fresh fixture was chosen after observing combined failure, label it as diagnostic rather than predeclared transfer. Keep both independently checked edits available when their combination is rejected.',
    hint:'A component’s local assumptions become another component’s inputs. Check their meanings and availability, not just matching field names.'
  },
  '10.12': {
    example:'A lineage shows task-agent code v0, v1, and v2, all generated by the same fixed edit-and-test operator. The agent changed repeatedly; the operator did not. A second lineage may instead show a revised operator governing later edits. Annotating the edges distinguishes the mechanisms even if both final agents score well.',
    outputs:[['Two primary-source mechanism maps','Cite changed surfaces, parent selection, evaluation, and inheritance for each historical work.'],['Typed local lineage','Names both the changed object and the procedure used on each edge.'],['Claim comparison','Separates ancestry, operator inheritance, and measured effectiveness.']],
    recovery:'If the source is inaccessible, leave its specific mechanism unresolved instead of substituting a third-party label. These named historical foundations are dated exceptions to the recent discovery window. If the local operator version is missing, the family tree cannot establish that the operator evolved.',
    hint:'Read an edge as “procedure P produced child C from parent B.” Then ask whether P itself changes and is used later.'
  },
  '10.13': {
    example:'An inner researcher can spend four attempts on one model family or reserve attempts for a different permitted family. Even with identical fitting tools, those operator choices can expose different candidates before the budget ends. The researcher’s procedure is therefore an object that an outer process can inspect and revise.',
    outputs:[['INNER-RESEARCHER.md','Defines proposal operators, parent selection, retention, and the four-fit limit.'],['Complete inner-search trace','Records each operator, candidate, predecessor, outcome, and cost.'],['Retained recipe','Identifies the actual selected solution rather than only the best-looking intermediate number.']],
    recovery:'If the agent supplies only four scores, recover the operator and decision trace before claiming a researcher comparison. If replaying a new order requires an unobserved branch, return unknown for that branch. Reordering known results cannot fabricate candidates that the original search never executed.',
    hint:'Separate the model recipe from the rule that decides which recipe to try next. The outer process acts on the second object.'
  },
  '10.14': {
    example:'The parent spends all three comparison fits refining its first promising family. The proposed child reserves its last fit for a contrasting family. Freeze both procedures, then run each with three attempts from the same start. The child’s outcome includes the cost of any discarded exploration, not just its retained model.',
    outputs:[['Outer change proposal','Targets operator choice or allocation and preserves both inner-researcher versions.'],['Two three-fit searches','Start from matched artifacts and retain every nested attempt.'],['Nested cost and outcome report','Includes outer proposals, checks, losing searches, and unknown provider charges.']],
    recovery:'If the parent’s old four-fit result is compared with the child’s new three-fit result, the budgets are mismatched. Use the declared matched comparison or state the limitation. If an outer edit changes the metric, restore the fixed external objective before interpreting it as a procedure improvement.',
    hint:'Draw a box around each inner search, then count the cost of all boxes tried by the outer process. The winning box was not free to discover.'
  },
  '10.15': {
    example:'A researcher becomes good at finding strong ML candidates but proposes brittle changes when asked to improve another researcher. Its earlier task-search win remains real. The new role-transfer test can still fail because producing good solutions and producing better solution-finding procedures are different capabilities.',
    outputs:[['IGNITION-PLAN.md','Defines the new outer-improvement role, starting procedure, allowed changes, and matched fixtures.'],['Two outer proposals and fixture outcomes','Preserve both frozen proposers, context limits, costs, and all failures.'],['Ignition claim audit','Does not recycle inner-search scores as evidence about outer improvement ability.']],
    recovery:'If the fixtures merely score writing quality, redesign them to execute a decision affected by the proposed researcher change. Keep that limited procedural result separate from task-performance evidence. No extra model fits are authorized by this lab’s default budget; declare an extension before adding them.',
    hint:'Complete “better at what?” twice: once for the earlier researcher win and once for this outer-improvement test.'
  },
  '10.16': {
    example:'META-SKILL-v0 asks for one failure diagnosis, one task-skill edit, and a target/regression check. It produces TASK-SKILL-v1 but stays byte-identical itself. The word meta names what it operates on; it does not show that its own improvement method changed.',
    outputs:[['META-SKILL-v0.md','Freezes the diagnosis, proposal, check, and retention procedure.'],['Task-skill parent and child','Expose the allowed edit and motivating evidence.'],['Two executed checks and decision','Connect the fixed updater to actual changed task behavior.']],
    recovery:'If the updater rewrites itself while creating the child, preserve the diff and separate that new experiment from this fixed baseline. If the child is accepted because its prose sounds better, run the declared behavioral checks before retaining it. Renaming a file does not substitute for a procedural change.',
    hint:'Name both the operator and its operand. In this lab the operand changes while the operator stays fixed.'
  },
  '10.17': {
    example:'Several task-level outcomes expose a repeated omission: the updater tests only favorable cases. A slower meta-skill revision adds a contrasting check. Freeze that revised updater during the next task-skill round, then compare the decisions it produces with v0. Changing both layers after each result would obscure which change mattered.',
    outputs:[['Accumulated trace review','Uses existing update traces with their actual updater identities and outcomes.'],['Unchanged v0, candidate v1, and proposal trace','Show the original pipeline acting on its own instructions, the proposed edit, overhead, and limit.'],['Later matched improvement record and retention decision','Uses the same starting task skill, at most two fits per arm, frozen updater identities, and separate structure/benefit conclusions. Separate folders do not erase shared agent context.']],
    recovery:'If only one prior update trace exists, locate a suitable earlier trace or explicitly prepare the missing starting state before freezing this protocol. Do not invent a second run. If the active updater changes during its evaluation, preserve the event and narrow attribution. A version hash alone cannot prove its changed instruction governed the later action.',
    hint:'Place task-skill updates and meta-skill updates on separate timelines. Mark when each candidate is frozen and when its later behavior is measured.'
  },
};
