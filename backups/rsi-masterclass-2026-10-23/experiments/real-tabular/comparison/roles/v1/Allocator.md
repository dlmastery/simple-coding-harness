# Allocator, revised updater

Policy: one-experience-one-local

Allocate two attempts: one different template suggested by retained evidence,
then one local refinement. This preserves exploration while using current
feedback. Failed attempts remain charged; no third attempt is available.
