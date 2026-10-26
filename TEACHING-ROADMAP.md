# Teaching Roadmap

Session plans, readiness checks, and capstone milestones for instructors.

---

## Course Formats

### Quick Start Workshop (5 hours)

**Audience**: Beginners who want a fast introduction  
**Prerequisites**: Basic ML concepts (tables, training, evaluation)  
**Goal**: Understand dependable ML loops and see one RSI mechanism

**Session 1 (2 hours)**: Themes 00-01
- Lab 00.01: Meet the prediction task
- Lab 00.02: Prepare workspace
- Lab 00.03: Run one baseline
- Lab 00.04: Check evidence
- Lab 01.01: Write the process

**Session 2 (1.5 hours)**: Theme 02
- Lab 02.01: Why repeat
- Lab 02.02: Bounded state
- Lab 02.03: Use feedback
- Lab 02.04: Stop the loop

**Session 3 (1.5 hours)**: October 2026 demo + capstone
- Run Budget RSI demo (30 min)
- Capstone 11.01: Build a harness from brief (1 hour)

**Checkpoint**: Students can explain one prediction, its evidence, and a bounded loop.

---

### Standard Course (30 hours)

**Audience**: Students who want full foundations  
**Prerequisites**: Basic ML concepts  
**Goal**: Complete RSI understanding with October 2026 research

**Week 1 (8 hours)**: Themes 00-02
- Day 1: Theme 00 (2 hours)
- Day 2: Theme 01 (2 hours)
- Day 3: Theme 02 first half (2 hours)
- Day 4: Theme 02 second half (2 hours)

**Week 2 (8 hours)**: Themes 03-05
- Day 1: Theme 03 (2 hours)
- Day 2: Theme 04 (2 hours)
- Day 3: Theme 05 first half (2 hours)
- Day 4: Theme 05 second half (2 hours)

**Week 3 (8 hours)**: Themes 06-08
- Day 1: Theme 06 (2 hours)
- Day 2: Theme 07 (2 hours)
- Day 3: Theme 08 (2 hours)
- Day 4: Quiz and review (2 hours)

**Week 4 (6 hours)**: Themes 09-10
- Day 1: Theme 09 (2 hours)
- Day 2: October 2026 reading (1 hour)
- Day 2: Budget RSI labs (1 hour)
- Day 3: SO-RSI labs (1 hour)
- Day 3: Capstone selection (1 hour)

**Checkpoint**: Students complete Themes 00-09 and two October 2026 groups.

---

### Full Masterclass (60 hours)

**Audience**: Researchers who want deep RSI understanding  
**Prerequisites**: Basic ML concepts  
**Goal**: Complete mastery with all October 2026 papers and capstones

**Weeks 1-4**: Same as standard course (30 hours)

**Week 5 (8 hours)**: Complete October 2026 research studio
- Day 1: Groups 00-01 (2 hours)
- Day 2: Groups 02-03 (2 hours)
- Day 3: Groups 04-05 (2 hours)
- Day 4: Paper deep-dives (2 hours)

**Week 6 (8 hours)**: Capstones
- Day 1: Capstone 11.01 (2 hours)
- Day 2: Capstone 11.02 (2 hours)
- Day 3: Capstone 11.03 (2 hours)
- Day 4: Capstone 11.04 (2 hours)

**Week 7 (8 hours)**: Advanced topics
- Day 1: Paper deep-dives (2 hours)
- Day 2: Mechanism analysis (2 hours)
- Day 3: Peer review (2 hours)
- Day 4: Teaching back (2 hours)

**Week 8 (6 hours)**: Final projects
- Day 1: Project work (2 hours)
- Day 2: Project work (2 hours)
- Day 3: Presentations (2 hours)

**Checkpoint**: Students complete all themes, all October 2026 groups, and all capstones.

---

## Readiness Checks

### Before Theme 00
- [ ] Understand what "prediction" means in ML
- [ ] Know what "training" and "evaluation" are
- [ ] Have access to a coding agent with file/command access
- [ ] Have Python 3.8+ installed

### Before Theme 03
- [ ] Can explain one prediction with its evidence
- [ ] Have run a repeatable process
- [ ] Can distinguish a claim from evidence

### Before Theme 06
- [ ] Can trace a failure through a loop
- [ ] Can explain why a graph branch fires
- [ ] Have written an ontology rule

### Before Theme 09
- [ ] Can identify which component contributed to a result
- [ ] Have generated a working harness
- [ ] Can distinguish the self-* mechanisms

### Before Theme 10
- [ ] Can explain what "recursive self-improvement" requires
- [ ] Have run a fair comparison with ablation
- [ ] Can state a claim with its limits

### Before Capstones
- [ ] Have completed Themes 00-09
- [ ] Have run at least one October 2026 demo
- [ ] Can audit a paper's claims

---

## Capstone Milestones

### Capstone 11.01: Build a Harness
**Milestone 1 (Day 1)**: Write the brief
- Define task, data, metrics, partitions
- Specify refusal cases

**Milestone 2 (Day 2)**: Generate and test
- Run meta-harness generation
- Test on a simple example
- Verify refusal of invalid requests

**Deliverable**: Generated harness package with test results

---

### Capstone 11.02: Recursive Comparison
**Milestone 1 (Day 1)**: Define two improvers
- I0: Fixed baseline
- I1: Revised version

**Milestone 2 (Day 2)**: Run comparison
- Match search budgets
- Match evaluation protocol
- Measure final scores

**Deliverable**: Comparison report with variance and cost

---

### Capstone 11.03: Portability
**Milestone 1 (Day 1)**: Prepare for port
- Document dependencies
- Package artifacts

**Milestone 2 (Day 2)**: Test in new environment
- Run on different machine
- Run with different agent
- Verify results

**Deliverable**: Portability test report

---

### Capstone 11.04: External Audit
**Milestone 1 (Day 1)**: Prepare evidence
- Compile all artifacts
- Write claim statement

**Milestone 2 (Day 2)**: Conduct audit
- Peer reviewer checks evidence
- Reviewer questions claims
- Address concerns

**Deliverable**: Audit report with reviewer signature

---

### Capstone 11.05: Teach Back
**Milestone 1 (Day 1)**: Prepare teaching
- Choose one concept
- Create explanation plan

**Milestone 2 (Day 2)**: Teach and receive feedback
- 15-minute teaching session
- Peer feedback
- Self-reflection

**Deliverable**: Teaching recording and reflection

---

## Assessment Criteria

### Lab Completion
- [ ] Ran the lab with agent
- [ ] Saved artifacts (predictions, traces, reports)
- [ ] Answered quiz before reading answer
- [ ] Can explain the key concept

### Theme Completion
- [ ] Completed all labs in theme
- [ ] Passed readiness check for next theme
- [ ] Can explain theme's purpose

### October 2026 Group Completion
- [ ] Read paper summary
- [ ] Ran demo (if available)
- [ ] Completed exercises
- [ ] Can explain mechanism

### Capstone Completion
- [ ] Evidence is complete and reproducible
- [ ] Claim is honest about limits
- [ ] External audit passed
- [ ] Teaching explanation is clear

---

## Instructor Resources

### Session Templates
Each session should include:
- 10 min: Review previous session
- 5 min: Introduce today's theme
- 40 min: Guided lab work
- 5 min: Quiz and next steps

### Common Issues
- **Student gets stuck**: Use the "give me a hint" prompt
- **Demo fails**: Check Python version and NumPy installation
- **Agent goes too fast**: Remind agent to wait at checkpoints
- **Confusion about recursion**: Review Theme 07 self-* distinction

### Extension Activities
For students who finish early:
- Read additional October 2026 paper summaries
- Implement partial demos for papers 3-9
- Explore original course evidence in backup
- Teach a concept to a peer

---

## Time Allocation by Theme

| Theme | Labs | Quick Start | Standard | Full |
|-------|------|------------|----------|------|
| 00 | 4 | 1.5h | 2h | 2h |
| 01 | 5 | 0.5h | 2h | 2h |
| 02 | 6 | 1.5h | 2h | 2h |
| 03 | 6 | - | 2h | 2h |
| 04 | 5 | - | 2h | 2h |
| 05 | 5 | - | 2h | 2h |
| 06 | 6 | - | 2h | 2h |
| 07 | 8 | - | 2h | 2h |
| 08 | 6 | - | 2h | 2h |
| 09 | 7 | - | 2h | 2h |
| 10 | 17 | 1.5h | 3h | 8h |
| 11 | 5 | 1.5h | 3h | 8h |
| **Total** | **75** | **6.5h** | **27h** | **38h** |

Note: Times are for guided discussion only. Add time for independent work, debugging, and project work.

---

## FAQ

**Q: Can I skip Theme 00 if I already know ML?**  
A: Theme 00 establishes the evidence standard used throughout the course. Even experienced ML practitioners should complete it to understand the course's approach to evidence.

**Q: Do I need to run all October 2026 demos?**  
A: At minimum, run Budget RSI and SO-RSI (the two full laptop demos). Other groups can be done as mechanism analysis without implementation.

**Q: Can I do capstones out of order?**  
A: Capstone 11.01 can be done anytime after Theme 06. Capstones 11.02-11.05 should be done in order as they build on each other.

**Q: What if a student fails a readiness check?**  
A: Review the relevant labs, focus on the weak area, and reattempt the check. Do not proceed until the check passes.
