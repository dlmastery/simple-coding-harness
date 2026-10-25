# Failed first execution

Source revision: 06a7d2231f8d1e2e12fefbbda1151155a61781b9.
Command: .venv/Scripts/python.exe how-did-i-generate-it/rsi/scripts/run-self-star-and-measurement.py --repo . --workspace ../rsi-work/self-star-and-measurement-2026-09-20
Exit: 1. Observed shell wall time: 1.9929722 seconds.

The fixed-reporter subprocess returned exit 0. The parent then raised AssertionError at the exact regression-target comparison in driver line 130. No new fits ran. This failure note was written after inspecting the terminal result; the original driver did not catch this assertion to write its own failure file.

Retain the exact driver.source.py, protocol, partial outputs, and inputs. See the separate precision audit. Do not resume this directory or overwrite its files.
