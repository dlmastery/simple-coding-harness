# A recent source for the tabular benchmark repair

Discovery on 22 September used the exact query:
`ML agent tabular benchmark OpenML small regression classification after:2026-08-22 before:2026-09-23`
restricted to arXiv, OpenML and GitHub. Older search results are not treated as
recent releases. OpenML's benchmark-search page returned a tool error.

[Agentic Search Spaces for Tabular Machine Learning](https://arxiv.org/abs/2609.16309)
is a 14 September 2026 preprint by Renat Sergazinov, Artem Chistyakov, Sergey
Pankevich and Artem Babenko, with Yandex/HSE affiliations. Read the method,
results, ablations, limitations and selected evaluation appendices in
[v1](https://arxiv.org/html/2609.16309v1).

Agents generate reusable pipeline modules; conventional optimization searches
their combinations. The authors report modest average gains across 45 datasets,
with a separate TabArena evaluation. Their main protocol uses 100–200 tuning
trials and fifteen evaluation seeds. Equal trial budgets do not imply equal
compute: expanded pipelines can cost more per fit. The source also reports an
end-to-end autoresearch comparison that slightly trails classical HPO.

Our interpretation: changing the buildable search space is relevant to harness
engineering, but this paper alone does not demonstrate recursive improvement
of its module-generating procedure. Its strongest teaching use is a comparison
of search-space design, ordinary optimization and total-cost accounting.

The [official repository](https://github.com/yandex-research/agentic-hpset)
contains implementation and analysis artifacts. Its README says the roughly
7 GB raw dataset collection is available on request, rather than committed.
Repository inspection is not reproduction. No external training or dependency
installation was performed for this source audit.

The earlier six-task experiment stays unchanged. Its rejected spline revision
and noise diagnostic motivate a separate benchmark decision, not a retroactive
claim that this paper's gains occurred locally. Candidate follow-up: documented
small public tabular tasks, diverse pipelines, a strong fixed optimizer control,
and frozen module/updater transfer tests. Dataset identity, licensing, split
and budget checks must precede any new model fit.
