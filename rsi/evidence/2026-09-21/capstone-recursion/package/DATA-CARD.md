# White-wine benchmark data

[UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine+quality), by P. Cortez, A. Cerdeira, F. Almeida, T. Matos, and J. Reis. Cite *Modeling wine preferences by data mining from physicochemical properties*, Decision Support Systems, 2009. The course records UCI's [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license and retains attribution here.

The original white table was already downloaded with the course on 20 September 2026. This package copies it without changing bytes. SHA-256: `76c3f809815c17c07212622f776311faeb31e87610d52c26d87d6e361b169836`.

One row represents a sample with laboratory measurements and a sensory quality score. The eleven inputs cover acidity, sugar, chlorides, sulfur dioxide, density, pH, sulphates, and alcohol. The benchmark target is the original quality score, not the earlier course threshold.

The agent records row counts, missing values, duplicate input groups, partition sizes, and training-target counts before fitting. Repeated input rows stay together even when their labels differ. Missing or non-finite data is refused instead of silently imputed under a changed contract.

This is not a representative sample of all wines. The released fields omit producer and time identifiers, so a feature-group split cannot rule out every source of dependence. Do not interpret MAE as a causal relationship between a chemical property and preference. No proprietary or personal data is introduced.
