"""Agent-operated, bounded tabular self-play lesson. No network or model service."""
import argparse
import csv
import hashlib
import random
import sys
import time
from collections import Counter
from pathlib import Path

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7),
         (2, 5, 8), (0, 4, 8), (2, 4, 6))
EMPTY = "........."


def outcome(board):
    """Return X/O for a winner, draw for a full board, or None."""
    for a, b, c in LINES:
        if board[a] != "." and board[a] == board[b] == board[c]:
            return board[a]
    return "draw" if "." not in board else None


def legal_actions(board):
    return [] if outcome(board) else [i for i, mark in enumerate(board) if mark == "."]


def move(board, player, action):
    expected = "X" if board.count("X") == board.count("O") else "O"
    if player not in ("X", "O") or player != expected or action not in legal_actions(board):
        raise ValueError("Illegal move, wrong turn, or finished game")
    return board[:action] + player + board[action + 1:]


def choose(table, board, player, rng, epsilon=0):
    actions = legal_actions(board)
    if not actions:
        raise ValueError("No legal action in a finished game")
    if epsilon and rng.random() < epsilon:
        return rng.choice(actions)
    values = [table.get((board, player, action), 0.0) for action in actions]
    best = max(values)
    return rng.choice([a for a, v in zip(actions, values) if v == best])


def update(table, history, winner, alpha=0.2):
    """Return the full update trace; each player receives its own terminal return."""
    rows = []
    for board, player, action in history:
        target = 0 if winner == "draw" else (1 if winner == player else -1)
        key = (board, player, action)
        before = table.get(key, 0.0)
        after = before + alpha * (target - before)
        table[key] = after
        rows.append((board, player, action, target, before, after))
    return rows


def train(games=3000, seed=17):
    table, episodes, updates = {}, [], []
    rng = random.Random(seed)
    for game in range(games):
        board, player, history = EMPTY, "X", []
        while outcome(board) is None:
            action = choose(table, board, player, rng, epsilon=0.2)
            history.append((board, player, action))
            board = move(board, player, action)
            player = "O" if player == "X" else "X"
        winner = outcome(board)
        for ply, row in enumerate(update(table, history, winner), 1):
            updates.append((game, ply, *row))
        episodes.append((game, winner, len(history), board))
    return table, episodes, updates


def evaluate(table, games=500):
    """Read the policy without inserting table entries or applying updates."""
    episodes, moves = [], []
    for game in range(games):
        agent = "X" if game % 2 == 0 else "O"
        agent_rng, opponent_rng = random.Random(43 + game), random.Random(29 + game)
        board, player, ply = EMPTY, "X", 0
        while outcome(board) is None:
            action = (choose(table, board, player, agent_rng) if player == agent
                      else opponent_rng.choice(legal_actions(board)))
            after = move(board, player, action)
            ply += 1
            moves.append((game, agent, ply, board, player, action, after))
            board = after
            player = "O" if player == "X" else "X"
        winner = outcome(board)
        result = "draw" if winner == "draw" else ("win" if winner == agent else "loss")
        episodes.append((game, agent, winner, result, ply, board))
    return episodes, moves


def table_bytes(table):
    rows = ["board,player,action,value\n"]
    rows.extend(f"{board},{player},{action},{value!r}\n"
                for (board, player, action), value in sorted(table.items()))
    return "".join(rows).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def run(output):
    # A nonempty path is never reused: a failed or completed experiment is evidence.
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be new or empty; preserve the existing experiment")
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    source_hash = digest(Path(__file__).read_bytes())
    initial = table_bytes({})
    (output / "initial-policy.csv").write_bytes(initial)
    (output / "RUN-CONTRACT.md").write_text(
        "# Fixed self-play run\n\n"
        "Tic-tac-toe; X starts. Shared board/player/action values begin at zero.\n"
        "3,000 training games; seed 17; epsilon 0.2; learning rate 0.2.\n"
        "Terminal returns: win +1, draw 0, loss -1, from each mover's perspective.\n"
        "Update after each game. No temporal-difference bootstrap.\n"
        "500 evaluation games per policy; alternate policy seat X/O.\n"
        "Opponent seed 29 + game; policy tie seed 43 + game.\n"
        "Frozen greedy evaluation; no updates, exploration, or later tuning.\n"
        "Zero entries are implicit when absent from the policy CSV.\n"
        f"Source SHA-256: {source_hash}\nPython: {sys.version.split()[0]}\n",
        encoding="utf-8")
    table, episodes, updates = train()
    frozen = table_bytes(table)
    (output / "trained-policy.csv").write_bytes(frozen)
    (output / "FROZEN-POLICY.sha256").write_text(digest(frozen) + "\n", encoding="utf-8")
    write_csv(output / "training-games.csv", ("game", "winner", "plies", "final_board"), episodes)
    write_csv(output / "training-updates.csv",
              ("game", "ply", "board", "player", "action", "return", "before", "after"), updates)
    counts = []
    hash_rows = []
    for label, policy in (("untrained", {}), ("trained", table)):
        before = digest(table_bytes(policy))
        results, moves = evaluate(policy)
        after = digest(table_bytes(policy))
        if before != after:
            raise RuntimeError("Evaluation changed the policy")
        hash_rows.append((label, before, after, before == after))
        write_csv(output / f"{label}-evaluation-games.csv",
                  ("game", "agent_mark", "winner", "result", "plies", "final_board"), results)
        write_csv(output / f"{label}-evaluation-moves.csv",
                  ("game", "agent_mark", "ply", "board", "player", "action", "after"), moves)
        for seat in ("X", "O", "all"):
            totals = Counter(row[3] for row in results if seat == "all" or row[1] == seat)
            counts.append((label, seat, totals["win"], totals["draw"], totals["loss"]))
    write_csv(output / "evaluation-counts.csv", ("policy", "seat", "wins", "draws", "losses"), counts)
    write_csv(output / "evaluation-policy-hashes.csv", ("policy", "before", "after", "unchanged"), hash_rows)
    write_csv(output / "cost.csv", ("quantity", "value"), (
        ("training_games", 3000), ("evaluation_games", 1000),
        ("training_moves_and_updates", len(updates)), ("stored_state_action_values", len(table)),
        ("nonzero_values", sum(v != 0 for v in table.values())),
        ("runtime_seconds", time.perf_counter() - start), ("authoring_inference_cost", "unknown")))
    print("policy,seat,wins,draws,losses")
    for row in counts:
        print(",".join(map(str, row)))
    print(f"Retained {len(updates)} updates; frozen evaluation hashes agree.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve())
