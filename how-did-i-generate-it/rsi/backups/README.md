# Original course backup

The original RSI course is preserved at commit [`eed9cbbdf19c665ae54646253f303be85030798c`](https://github.com/dlmastery/simple-coding-harness/tree/eed9cbbdf19c665ae54646253f303be85030798c/rsi), before this masterclass rewrite. That Git snapshot already existed when the rewrite began. These explicit backup files were extracted from it on 20 September 2026 after the user asked for an easy-to-find backup. They are not reconstructed from the rewritten course.

- [Original README, unchanged text](before-rebuild-eed9cbb/README.original.txt).
- [Complete original tracked RSI directory, ZIP](before-rebuild-eed9cbb/rsi-original.zip).
- [Original README in its working GitHub context](https://github.com/dlmastery/simple-coding-harness/blob/eed9cbbdf19c665ae54646253f303be85030798c/rsi/README.md).
- [Current course](../../../rsi/README.md).

The separate text copy preserves the exact original Markdown bytes. Its `.txt` extension identifies an archival source, outside the active course's navigation checks; its relative links still assume the original directory. Git attributes prevent line-ending conversion of this copy. Use the historical GitHub page for browsing, or ask the coding agent to extract the ZIP into a separate directory. The archive contains `original-rsi/rsi/README.md` with its original filename and preserves the original file layout. It does not contain untracked local files or external dependencies.

## Verification

| Artifact | Identity |
|---|---|
| Source commit | `eed9cbbdf19c665ae54646253f303be85030798c` |
| Original README Git blob | `57a4ea315be4ada9193df0d8f575a913c76d5441` |
| README SHA-256 | `99033ee483924a29137c955d02cf64105489c321fda459657279b3e03256d6bd` |
| ZIP SHA-256 | `54b2b9d754301bbe96881676d64126c9b6181c241b59ead3e2b9947e192e57fb` |
| ZIP size | 1,075,588 bytes |
| ZIP entries, including directories | 718 |

The extracted Markdown matched the original Git blob using `git hash-object --no-filters`. The README inside the ZIP has the same SHA-256 as the separate copy. The archive was made directly with `git archive`, not assembled from the modified working tree. Preserve these files when revising the course again.
