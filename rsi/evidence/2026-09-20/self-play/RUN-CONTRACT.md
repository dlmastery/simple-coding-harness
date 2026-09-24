# Fixed self-play run

Tic-tac-toe; X starts. Shared board/player/action values begin at zero.
3,000 training games; seed 17; epsilon 0.2; learning rate 0.2.
Terminal returns: win +1, draw 0, loss -1, from each mover's perspective.
Update after each game. No temporal-difference bootstrap.
500 evaluation games per policy; alternate policy seat X/O.
Opponent seed 29 + game; policy tie seed 43 + game.
Frozen greedy evaluation; no updates, exploration, or later tuning.
Zero entries are implicit when absent from the policy CSV.
Source SHA-256: b7bb9480e72ff901ea1b3c9a961fa257e70fc7f93d8ac902ade62c1b28d7c62f
Python: 3.12.12
