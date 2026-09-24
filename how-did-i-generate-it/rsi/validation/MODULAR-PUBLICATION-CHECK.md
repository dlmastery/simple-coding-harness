# Preserve the refused-run reports

The first staged whitespace check found four original RESULT.md files with a trailing space after an empty Seconds field. All four are refused runs. They have no accepted duration value.

Do not edit those reports after execution: their original bytes are in the manifest. The archive now contains a narrowly scoped .gitattributes exception for those four files. This publication metadata is outside the experiment manifest. The inherited no-conversion rule still applies. No experiment was repeated and no outcome was changed to resolve this publication check.

The staged-byte audit and course link check run after this correction. Their results are recorded in the checkpoint log.

Final checks: 1,883 indexed evidence files matched their raw workspace bytes. The course check covered 101 lessons and 4,509 local links with zero publication problems. The corrected staged whitespace check passed.
