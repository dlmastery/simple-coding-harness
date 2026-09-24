# Source manifest

The user supplied `rsiresearch.mhtml` from Downloads. It was decoded locally into HTML and then extracted into text. The archived public derivative is a redacted text file, not the browser capture. It contains unverified source claims, not current course instructions.

| Artifact | SHA-256 | Storage |
|---|---|---|
| Original `rsiresearch.mhtml` | `CCD0681B8925FC9F006994AC520307AEBF426C3626006E21BD7E3BA21CD37064` | Local original |
| Decoded HTML | `8B80605FD2789656E5CA7D20C83ABAB0E6A6A4C4E8605E64AC9C9AE217A1BDEF` | Local intermediate |
| Extracted unredacted text | `E12B48AB614390E8BCC62C874E1D969873A1961148A296E55FF8FEE0DFB23ED5` | Local intermediate |
| [Redacted text](rsiresearch-redacted.txt) | `FFC9C2E54319CDFBD339981CC5801F79A324DF245F616C679AC1CE1A281F001E` | Checked into this directory |

The [redaction script](../scripts/redact-transcript.ps1) removes forwarded-message sender names and timestamps, email addresses, and video share tokens. It adds a warning that the source is unverified. Technical content is retained for audit. The published file uses UTF-8 without a byte-order mark, LF line endings, and one final newline. The local attributes file preserves that format through Git checkout.

An intermediate redacted copy had mixed line endings and an extra blank line at the end. Its hash was `901CC12230528264D216F24A20F246D1BBE84FBA4749F321581F653738754C0E`. It was normalized before the first source-artifact commit. The canonical file above retains the same text content.

The original MHTML extraction was performed before the provenance directory existed. Its intermediate hashes are retained, but the exact extraction command was not saved as a script. This is a recorded provenance gap. The redaction step is reproducible from the hashed extracted text.

Do not publish the raw browser files merely to fill the gap. Use the redacted source and primary research to check claims. The [correction ledger](../research/CLAIM-CORRECTIONS.md) records findings so far.
