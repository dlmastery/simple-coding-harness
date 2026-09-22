Check: nothing outside the workspace changed. run.py takes a manifest of the
workspace's parent directory (every file except the workspace itself, with a
hash) before and after the harness run and passes the file's path in
CAPSTONE_MANIFEST. The check fails on any file added, removed or changed, and
fails when no manifest was given.
