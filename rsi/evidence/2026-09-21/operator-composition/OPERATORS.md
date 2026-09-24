# Synthetic operator contracts

| Operator | Reads | Writes |
|---|---|---|
| data | data, task | data.version, data.format |
| harness | harness, task | harness.version, harness.format |
| model | data, harness, model | model.version, model.format |

Data records task format. Harness supports task format. Model requires a data record and copies current harness format. This is a stub, never training. All evidence also records the current task and complete version vector.
