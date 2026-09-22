"""Replay boundary tests on explicitly constructed fixtures, not ML evidence."""
import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools/discovery.py"
spec = importlib.util.spec_from_file_location("rsi_discovery", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Observation, World, replay = module.Observation, module.World, module.replay


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.world = World((Observation("a", "root", "ok", .7, 2),
                            Observation("b", "root", "ok", .5, 3),
                            Observation("a1", "a", "ok", .3, 4),
                            Observation("b1", "b", "failed", None, 5)))

    def test_unseen_scores_are_not_policy_observations(self):
        seen = []
        def policy(view):
            seen.append(tuple(item.node for item in view.observations))
            return "root"
        result = replay(self.world, policy, 2)
        self.assertEqual(seen, [(), ("a",)])
        self.assertEqual([item.node for item in result.observations], ["a", "b"])
        self.assertEqual(result.best_loss, .5)

    def test_branch_continuations_follow_recorded_ancestry(self):
        choices = iter(("root", "a", "a1"))
        result = replay(self.world, lambda _: next(choices), 3)
        self.assertEqual(result.decisions, (("root", "a"), ("a", "a1"), ("a1", "UNKNOWN")))
        self.assertEqual(result.unknown_requests, 1)
        self.assertEqual(result.represented_seconds, 6)

    def test_unobserved_or_nonleaf_parent_refused(self):
        with self.assertRaises(ValueError):
            replay(self.world, lambda _: "b", 1)
        choices = iter(("root", "a", "a"))
        with self.assertRaises(ValueError):
            replay(self.world, lambda _: next(choices), 3)

    def test_failure_cost_is_charged_without_a_score(self):
        choices = iter(("root", "root", "b"))
        result = replay(self.world, lambda _: next(choices), 3)
        self.assertEqual(result.best_loss, .5)
        self.assertEqual(result.represented_seconds, 10)
        self.assertEqual(result.observations[-1].status, "failed")

    def test_stop_does_not_reveal_future(self):
        result = replay(self.world, lambda _: None, 8)
        self.assertEqual(result.terminal, "policy_stop")
        self.assertIsNone(result.best_loss)
        self.assertEqual(result.represented_seconds, 0)

    def test_invalid_world_refused(self):
        for records in ((Observation("x", "missing", "ok", 1, 1),),
                        (Observation("x", "root", "failed", 1, 1),),
                        (Observation("x", "root", "ok", float("nan"), 1),),
                        self.world.observations + (Observation("a2", "a", "ok", .1, 1),)):
            with self.assertRaises(ValueError):
                World(records)


if __name__ == "__main__":
    unittest.main()
