# What the scheduling results support

The two main lab 07.05 runs finish at ticks 21 and 14. The optional coordination-cost case finishes at tick 23. These results demonstrate a change in work assignment with fixed worker capabilities. They do not estimate a real platform's scheduler overhead.

For lab 07.06, FIFO gives same-type adjacency 0.00, local history 0.80, and randomized history 0.70. The control weakens a tempting story: accurate memory is not the only way to create grouping in this fixture. Even a random preferred type selects matching jobs while they remain available. One seed cannot establish a stable difference between 0.80 and 0.70. A stronger follow-up would declare multiple seeds and another control before running them.

The deadline pair keeps the same jobs, setup cost, and deadlines across policies. Local preference completes the batch at tick 8 versus 12, while maximum lateness increases from 1 to 3. The claimed benefit depends on the objective. “More organized,” “more clustered,” and “better” do not mean the same thing.

The driver checked identity, durations, expected constructed results, and non-overlap in all eight cases. Manual inspection of the local-history event CSV confirmed the A runs, switch cost, and delayed first B jobs. The fixed-assignment result also agrees with the direct workload calculation, 8 + 7 + 6 = 21 and 1 + 1 + 1 = 3.

This is an author walkthrough with deterministic rules and synthetic jobs. It supplies no human learner responses, independent-agent behavior, learned scheduling policy, or evidence of recursive improvement.
