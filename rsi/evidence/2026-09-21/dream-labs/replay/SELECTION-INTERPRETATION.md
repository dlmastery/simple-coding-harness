# Replay retained the baseline

P0 visits the median baseline and linear recipe: best MAE 99.175923787. P1 visits the median baseline and tree recipe: best MAE 115.284257283. The replay selection therefore retains P0, which was already the declared baseline. No revised policy was promoted.

Continue the declared online comparison of the two frozen policies. P0 is both the retained baseline and replay winner; P1 is its rejected challenger. Do not relabel the policies after seeing this result or claim a newly improved policy. The online comparison can test the ordering of these two fixed recipe strategies on the declared synthetic task. It cannot demonstrate an accepted policy update returning online.

In the reduced coverage copy, B is absent. P0 now retains A at MAE 159.947911886 while P1 can still reach C at 115.284257283. The apparent ranking reverses because the record's support changed, not because a new model was trained.
