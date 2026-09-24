# Preserve evidence bytes through Git

21 September 2026. The staged publication check exposed automatic line-ending conversion in raw CSV and SVG artifacts. A workspace manifest could match its local files while Git stored different bytes. This invalidated byte-hash claims for the affected published copies even though parsed values stayed the same.

The [before audit](EVIDENCE-BYTES-BEFORE.csv) compared 1,533 indexed evidence files with their raw working-tree bytes and found 217 differences. Every difference was limited to CRLF versus LF. The audit refused to proceed on any other difference. For example, the archived original baseline predictions had local SHA-256 `0004513ae666f36bcf4987e2b36944f1c4a8d79bf949ef09b788d0b95e6af93c`, which the recovery report cited, while the normalized Git blob hashed to `4ecfcc39730ec111eafb65bd293e1a1c81718075a5ff462e50c2b64b90a8232b`.

An initial root-level attribute rule left 12 text files subject to the deeper `rsi/.gitattributes` rule; that unsuccessful intermediate audit is [retained](EVIDENCE-BYTES-INTERMEDIATE.csv). The final [evidence-specific attributes](../../../rsi/evidence/.gitattributes) preserve raw bytes throughout the archive. Generated SVGs retain their renderer-produced path whitespace; this is a scoped artifact-format rule, not a relaxation for course source code.

Restaged evidence from the original local bytes. The [final audit](EVIDENCE-BYTES-AFTER.csv) inspected 1,534 indexed files, including the new attribute file, and found zero raw/index differences. The [audit program](../scripts/audit-evidence-bytes.py) compares actual Git blob identities, not decoded shell text. The staged whitespace check then passed. No model fit, prediction value, scientific result, or original workspace was altered.

This establishes byte agreement for the current archive and index. It does not retroactively change older commits, prove every historical manifest entry complete, or supply missing experiment events. Future archive checks must inspect stored Git bytes as well as local copies.
