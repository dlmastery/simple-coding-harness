# Bike harness brief

Estimate hourly cnt with calendar inputs, optionally observed weather. This is retrospective, not a day-ahead forecast. Exclude target components casual and registered. Train on 2011, select on 2012-H1, reserve 2012-H2. Use MAE; lower is better. Baseline: training median.

Use the repository-pinned UCI data and attribution. Allow two admitted attempts, including failures; refuse a third. Refuse changed task, metric, or split. Keep candidates, predictions, checks, failures, and measured costs. Default to CPU with sequential commands capped at 60 seconds. The data and evaluator are visible to the host agent. Students type ordinary language; the coding agent supplies code.
