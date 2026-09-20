# Task research skill: parent

Read the task contract and available inputs. Choose the fixed linear pipeline for this task.

Train only on training rows. Fit scaling there when the pipeline requires it. Save predictions with source row identities, then report the task's declared metric on training and selection rows. Never train on or choose using final rows. Keep all failures and measured fit costs. The protocol fixes the precise model settings.
