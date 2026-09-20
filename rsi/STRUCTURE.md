# Where the course lives

[Course](README.md) · [Start here](START-HERE.md) · [Every lab](COURSE-MAP.md)

The RSI course lives inside `rsi/`. Its intended final organization is already in place: twelve theme directories, with another level of grouping for advanced research. The current course has 101 authored labs. Finishing their illustrations, skills, implementation support, and verification does not require adding more numbered steps. Split or add a lab when a learning need warrants it.

The repository also contains an earlier coding-harness course in its root `step_*` directories and a generative-UI course in `genui/`. Those are separate series. Their step counts do not describe the RSI rebuild.

## The reading path

```text
simple-coding-harness/
├── README.md                         Guide to the separate course series
├── step_*/                           Existing coding-harness course
├── genui/                            Existing generative-UI course
├── rsi/
│   ├── README.md                     RSI walkthrough and learning path
│   ├── START-HERE.md                 First session and agent setup
│   ├── STRUCTURE.md                  This folder map
│   ├── COURSE-MAP.md                 Links to all 101 labs
│   ├── LEARNING-PATH.md              Teaching blocks and checkpoints
│   ├── VISUAL-GUIDE.md               Illustrations linked to their labs
│   ├── GLOSSARY.md                   Terms, examples, and distinctions
│   ├── 00_start_here/                         4 labs
│   ├── 01_process_without_loops/              5 labs
│   ├── 02_loop_engineering/                   6 labs
│   ├── 03_graph_engineering/                  6 labs
│   ├── 04_ontology_engineering/               5 labs
│   ├── 05_system_intelligence/                5 labs
│   ├── 06_meta_harness_engineering/           6 labs
│   ├── 07_understanding_self_star/            8 labs
│   ├── 08_measuring_improvement/              6 labs
│   ├── 09_recursive_self_improvement/         7 labs
│   ├── 10_research_studio/                   38 labs in 13 groups
│   ├── 11_capstones/                         5 labs
│   ├── skills/                       Seven shared agent procedures
│   ├── tools/                        Agent-run implementation
│   ├── adapters/                     Entry paths for coding agents
│   ├── assets/                       Illustrations and technical diagrams
│   ├── examples/                     Pinned teaching data and examples
│   ├── research/                     Source connections
│   ├── compute/                      Laptop-to-cluster extension
│   ├── instructor/                   Teaching and assessment guidance
│   ├── evidence/                     Dated execution records and limits
│   └── maintenance/                  Publication and runtime checks
├── skills/
│   └── build-research-codelabs/       Reusable course-authoring skill
└── how-did-i-generate-it/
    └── rsi/                          Plans, sources, drafts, and provenance
```

Start at the course README and follow its theme links. The [course map](COURSE-MAP.md) gives the complete sequence. Each theme README explains its purpose, prerequisites, and handoff to the next theme.

## Inside one theme

For example, the first process theme uses this layout:

```text
01_process_without_loops/
├── README.md
├── step_01_describe_the_process/
│   ├── README.md
│   └── BRIEF.md
├── step_02_run_the_process/
├── step_03_make_a_skill/
├── step_04_separate_the_check/
└── step_05_reuse_the_skill/
```

Every lab has a README and a readable task brief. The README explains what to do, why it matters, how the mechanism works, and what evidence to inspect. It includes a concrete example, agent prompts, expected outputs, recovery guidance, key takeaways, an explained quiz, and the next lesson. Its illustrations are embedded where they help explain the mechanism.

The brief gives the agent the task and constraints. Shared skills and tools avoid copying the same implementation into every lab. Later labs ask the agent to generate a harness when that construction is the learning objective. Generated learner code, reports, and progress belong in a separate sibling `rsi-work/` workspace; the course source stays readable.

## Inside the research studio

The 38 advanced labs are grouped by the question they investigate:

```text
10_research_studio/
├── README.md
├── 00_reading_frontier_research/
├── 01_memory_and_exploration/             Includes RSIAgent
├── 02_dream_rsi/
├── 03_modular_harness_evolution/          Includes ModularRSI
├── 04_aide2/
├── 05_meta_skill_evolution/
├── 06_scientist_two/
├── 07_sciencebuddy/
├── 08_skills_and_procedures/
├── 09_efficient_harnesses/
├── 10_feedback_and_transfer/
├── 11_composition_and_reference_learning/
└── 12_evidence_and_open_questions/
```

Each group has its own introduction and lab subdirectories. Follow the [research-studio index](10_research_studio/README.md) for the exact order and source connections. A laptop adaptation explains a mechanism; its stated limits distinguish it from reproducing the original paper.

## Why the count can stay the same

The old RSI course had eighteen flat lesson directories. The rebuild has 101 labs nested under twelve themes. This organization has already been published on the [working branch](https://github.com/dlmastery/simple-coding-harness/tree/codex/rsi-masterclass-rebuild/rsi); it has not been merged into `main`.

Recent work completes the content inside that structure. A new illustration, clearer prompt, stronger skill, or corrected implementation does not create another lab automatically. The same lesson count can therefore accompany substantial changes. Completion depends on the quality and evidence for each activity, not the number of folders.

During the rebuild, the [completion ledger](../how-did-i-generate-it/rsi/COURSE-COMPLETION-LEDGER.md) records remaining work. Current priorities are diagrams, READMEs, skills, and implementation support, followed by the full verification pass. An existing directory is not a completion claim.
