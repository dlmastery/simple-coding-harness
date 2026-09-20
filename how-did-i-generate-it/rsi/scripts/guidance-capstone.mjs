export const capstoneGuidance = {
  '11.01': {
    example:'You change from describing recorded hourly demand to predicting tomorrow’s demand. That is a new scientific question even on the same public dataset. Tomorrow’s observed weather is no longer an available input. The new brief must resolve input availability and evaluation time before the builder chooses a model.',
    outputs:[['Task brief and data card','Define the new question, permissions, source identity, prediction unit, inputs, split, and objective.'],['Generated harness and real baseline','Retain its dependencies, entry point, predictions, checks, and known costs.'],['Intended refusal and handoff','Demonstrate one meaningful invalid request and supply a clean-start route for a peer.']],
    recovery:'If the new task requires data that the dataset does not provide, narrow the question or identify the missing source before fitting. If generation produces instructions without an executable entry, finish the implementation and retain any failed attempt. A cluster plan remains generated-only until its actual backend checks run.',
    hint:'Before asking whether the model is good, ask whether each input could exist when the prediction is needed and whether the evaluation answers the new question.'
  },
  '11.02': {
    example:'The child improver adds a contrasting-case check to its internal selection rule. A later round uses that rule and rejects a harmful skill edit. The external task metric and budget remain unchanged. This can demonstrate inheritance; whether the changed improver is better still depends on its matched outcomes and added cost.',
    outputs:[['Bounded recursive protocol','Freezes external comparison, allowed inner edits, two generations, eight-fit total, and stop/rollback rules.'],['Lineage and matched outcomes','Connect active versions to later decisions and preserve all rejected proposals.'],['Final claim audit','Separates structure, benefit, efficiency, context limits, and unknown resources.']],
    recovery:'If the newest proposal is automatically active, reconcile it with the last acceptance decision before resuming. If the child receives more attempts, report the resource mismatch. If a final result changes the next proposal, those cases are now development information; do not continue calling them untouched final evidence.',
    hint:'Show the revised improver governing a later improvement action, then compare the consequences. A changed file and a good task score alone leave that chain incomplete.'
  },
  '11.03': {
    example:'The same skill works on bike and wine in one coding agent. That is evidence about task transfer under that host. It does not test another agent’s skill loader or a cluster scheduler. A compatibility matrix keeps those unexecuted combinations visible instead of assigning one global “portable” label.',
    outputs:[['PORTABILITY.md','Separates task, host, version, backend, required capabilities, and actual status.'],['Two small smoke-run records','Retain setup, commands, outputs, refusal/recovery behavior, and observed limits.'],['Optional backend evidence','If executed, records job identity, cancellation, checkpoint resume, and cost; otherwise remains planned or generated.']],
    recovery:'If a target host lacks command execution, identify which course outcomes it cannot produce. If no second agent or backend is available, choose the available meaningful tests and leave other cells unexecuted. Do not invent cluster behavior from a launch file or call a new folder a new agent environment.',
    hint:'Change one portability dimension at a time where possible. A failure is easier to interpret when task, agent, and backend do not all change together.'
  },
  '11.04': {
    example:'A new source reports a better retained agent after several harness edits. You can accept that reported result while asking whether the edit-generating procedure itself changed. The follow-up should inspect or test that missing link, rather than dismissing the result because it does not establish every stronger RSI claim.',
    outputs:[['Dated primary-source trail','Records query, original date, version, exact reading depth, and access gaps.'],['Short audit','States strongest supported claim, evidence, limitation, and alternative explanation fairly.'],['Discriminating follow-up','Names the smallest test that could change the assessment and labels any toy check.']],
    recovery:'If the chosen source is only a social announcement, keep its identity and date but leave unavailable methods unresolved. If a toy counterexample differs from the source’s assumptions, state that difference rather than presenting it as a refutation. Cite primary evidence for both the positive finding and its limitation.',
    hint:'State the strongest reasonable interpretation first. Then identify precisely which additional observation would support or weaken a stronger claim.'
  },
  '11.05': {
    example:'A peer follows one row of data into a prediction, one failed check into a task-skill revision, and one improver revision into a later decision. At each transition they can open the supporting artifact. If they can also explain a case where the revision fails, the portfolio teaches a mechanism rather than only displaying a success.',
    outputs:[['PORTFOLIO.md','Links the scientific brief, agent entry, one valid run, one failure, lineage, costs, and claim limits.'],['Mechanism illustration','Accurately identifies changed objects and feedback paths without inventing measurements.'],['Peer reproduction and teach-back record','Contains actual feedback and unanswered questions, or an explicit pending status.']],
    recovery:'If a peer cannot start without the old chat, add the missing setup or decision to the handoff. If no peer is available, retain the prepared exercise and mark the session pending. Do not fabricate responses, rerun search for a prettier score, or replace the failure that reveals the method’s limit.',
    hint:'Tell the story through one concrete evidence chain, then transfer it to a new prediction question. Vocabulary alone cannot complete that explanation.'
  },
};
