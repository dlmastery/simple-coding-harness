# 10.15 · Calculate RSI-Index

**Purpose:** Understand RSIGym's performance metric.

## RSI-Index Formula

```
RSI-Index = mean( (initial_score - final_score) / (ideal_score - initial_score) )
```

For each benchmark:
- initial_score: Starting performance
- final_score: After RSI system runs
- ideal_score: Best possible performance

RSI-Index measures the fraction of remaining performance gap closed.

## Example

```
Benchmark 1: Initial 50%, Final 75%, Ideal 100%
Gap closed = (75 - 50) / (100 - 50) = 25/50 = 0.5

Benchmark 2: Initial 20%, Final 60%, Ideal 100%
Gap closed = (60 - 20) / (100 - 20) = 40/80 = 0.5

RSI-Index = mean(0.5, 0.5) = 0.5
```

## Your Task

Calculate RSI-Index for a synthetic scenario with 5 benchmarks.

## Quiz

**Q1:** Why use RSI-Index instead of raw scores?

**A1:** RSI-Index normalizes across benchmarks with different difficulty levels. A 10% absolute improvement is more impressive if starting from 90% than from 10%. RSI-Index accounts for this.

## Next

[10.16 · Compare environments](../step_02_environments/README.md)
