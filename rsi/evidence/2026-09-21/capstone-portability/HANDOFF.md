# Read or repeat the portability checks

Read PROTOCOL.md, DECISION.md and PORTABILITY.md before the results. OUTCOMES.csv and each task's RESULT.md describe different metrics. Do not compare their numeric values directly. The original source files and copied skills are recorded by SOURCES.csv; AUDIT-CHECKS.csv verifies them after the runs. The source/ descriptions retain dataset attribution.

The generated author driver has prepare, execute and seal phases. It invokes the repository's unchanged lab.py and check_result.py through project Python. The flat sources/ copies are provenance snapshots, not a standalone relocated package: lab.py expects the original repository layout. Students use the canonical tutor and run-ml-experiment skills, with a separately declared sibling workspace and one fit per task. No native skill installation was tested.

The extra preflight commands ran preflight.py twice, each with --profile naming HOST-AVAILABLE.md or HOST-NO-COMMANDS.md and --output naming its corresponding CHECK.md. Expected exits were zero and two. Their outputs and measured wall intervals are in commands/capability-*.md. The no-fit audit ran audit.py with --repo pointing to the source checkout and --root pointing to this workspace; AUDIT-OUTPUT.txt retains exit zero and its output. The exact scripts are preserved.

The capability fixture checks a readable declaration. It does not probe real host permissions or submit jobs. A commandless agent could still explain existing artifacts if it has file access; it could not perform the measured fits, command-based checks or runtime recovery without another authorized execution path.

Data inspection uses all public rows, including final-partition target summaries. No final model score was produced. Treat this as a transparent teaching smoke test, not protected evaluation.

Publication may add link bridges for relative links inside byte-identical skill snapshots. Such guides do not modify the skill bytes that ran. The manifest covers original files only; archive README and explicit publication supplements are identified separately.
