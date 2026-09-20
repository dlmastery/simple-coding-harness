"""Check game validity, learning targets, and the frozen evaluation boundary."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("self_play", Path(__file__).resolve().parents[1] / "tools/self_play.py")
play = importlib.util.module_from_spec(spec)
spec.loader.exec_module(play)


def test_game_ends_and_rejects_illegal_actions():
    board = play.EMPTY
    for player, action in (("X", 0), ("O", 3), ("X", 1), ("O", 4), ("X", 2)):
        board = play.move(board, player, action)
    assert play.outcome(board) == "X"
    assert play.legal_actions(board) == []
    with pytest.raises(ValueError):
        play.move(board, "O", 8)
    with pytest.raises(ValueError):
        play.move(play.EMPTY, "O", 0)
    with pytest.raises(ValueError):
        play.move("X........", "O", 0)
    assert play.outcome("XOXXOOOXX") == "draw"
    assert play.outcome("X.O.O.OXX") == "O"


def test_rewards_follow_each_movers_perspective():
    history = [(play.EMPTY, "X", 0), ("X........", "O", 1)]
    table = {}
    play.update(table, history, "X")
    assert table[history[0]] == pytest.approx(0.2)
    assert table[history[1]] == pytest.approx(-0.2)
    play.update(table, history, "draw")
    assert table[history[0]] == pytest.approx(0.16)
    assert table[history[1]] == pytest.approx(-0.16)


def test_learning_is_repeatable_and_evaluation_cannot_update_it():
    table, games, updates = play.train(games=30)
    assert (table, games, updates) == play.train(games=30)
    assert any(v != 0 for v in table.values())
    before = play.table_bytes(table)
    results, moves = play.evaluate(table, games=20)
    assert before == play.table_bytes(table)
    assert len(results) == 20
    assert sum(r[1] == "X" for r in results) == 10
    for _, _, _, board, player, action, after in moves:
        assert play.move(board, player, action) == after
    empty = {}
    play.evaluate(empty, games=10)
    assert empty == {}


def test_existing_evidence_is_not_overwritten(tmp_path):
    record = tmp_path / "prior.txt"
    record.write_text("retain this", encoding="utf-8")
    with pytest.raises(ValueError, match="preserve"):
        play.run(tmp_path)
    assert record.read_text(encoding="utf-8") == "retain this"
