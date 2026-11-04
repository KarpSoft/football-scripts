import io
import os
import random
import runpy
import unittest
from collections import Counter
from contextlib import redirect_stdout
from unittest.mock import patch

import dynasty_draft_lottery as lottery

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join("dynasty_draft_lottery.py")


def run_with_inputs(func, inputs):
    """Call func() with input() fed from `inputs`, returning (result, stdout)."""
    buf = io.StringIO()
    with patch("builtins.input", side_effect=inputs), redirect_stdout(buf):
        result = func()
    return result, buf.getvalue()


class TestOrderTeams(unittest.TestCase):
    def test_sorts_least_to_greatest(self):
        entries = [("A", 300), ("B", 100), ("C", 200)]
        self.assertEqual(
            lottery.order_teams(entries),
            [("B", 100), ("C", 200), ("A", 300)],
        )

    def test_ties_keep_entry_order(self):
        entries = [("First", 100), ("Second", 100), ("Third", 50)]
        self.assertEqual(
            [n for n, _ in lottery.order_teams(entries)],
            ["Third", "First", "Second"],
        )

    def test_handles_floats(self):
        entries = [("A", 10.5), ("B", 3), ("C", 10.25)]
        self.assertEqual(
            [n for n, _ in lottery.order_teams(entries)],
            ["B", "C", "A"],
        )

    def test_does_not_mutate_input(self):
        entries = [("A", 3), ("B", 1)]
        lottery.order_teams(entries)
        self.assertEqual(entries, [("A", 3), ("B", 1)])


class TestPromptForTeams(unittest.TestCase):
    def test_collects_names_and_points(self):
        inputs = ["Alpha", "100", "Beta", "250.5"]
        result, _ = run_with_inputs(lambda: lottery.prompt_for_teams(2), inputs)
        self.assertEqual(result, [("Alpha", 100.0), ("Beta", 250.5)])

    def test_strips_whitespace_from_name(self):
        result, _ = run_with_inputs(
            lambda: lottery.prompt_for_teams(1), ["  Padded  ", " 5 "]
        )
        self.assertEqual(result, [("Padded", 5.0)])

    def test_reprompts_on_blank_name(self):
        inputs = ["", "   ", "Alpha", "10"]
        with patch("builtins.input", side_effect=inputs) as mock_input, \
                redirect_stdout(io.StringIO()):
            result = lottery.prompt_for_teams(1)
        self.assertEqual(result, [("Alpha", 10.0)])
        blank_prompts = [
            c for c in mock_input.call_args_list if "can't be blank" in c.args[0]
        ]
        self.assertEqual(len(blank_prompts), 2)

    def test_reprompts_on_invalid_points(self):
        inputs = ["Alpha", "abc", "", "12x", "42"]
        result, out = run_with_inputs(lambda: lottery.prompt_for_teams(1), inputs)
        self.assertEqual(result, [("Alpha", 42.0)])
        self.assertEqual(out.count("Please enter a number."), 3)

    def test_asks_for_requested_number_of_teams(self):
        inputs = [x for i in range(8) for x in (f"T{i}", str(i))]
        result, _ = run_with_inputs(lambda: lottery.prompt_for_teams(8), inputs)
        self.assertEqual(len(result), 8)


class TestPrintOddsTable(unittest.TestCase):
    def capture(self, entries, weights):
        buf = io.StringIO()
        with redirect_stdout(buf):
            lottery.print_odds_table(entries, weights)
        return buf.getvalue()

    def test_shows_every_team_and_correct_percentages(self):
        entries = [("Low", 10), ("High", 90)]
        out = self.capture(entries, [75, 25])
        self.assertIn("Low", out)
        self.assertIn("High", out)
        self.assertIn("75.0%", out)
        self.assertIn("25.0%", out)

    def test_default_weights_sum_to_100_percent(self):
        entries = [(f"T{i}", i) for i in range(len(lottery.WEIGHTS))]
        out = self.capture(entries, lottery.WEIGHTS)
        pcts = [
            float(line.split()[-1].rstrip("%"))
            for line in out.splitlines()
            if line.strip().endswith("%")
        ]
        self.assertEqual(len(pcts), len(lottery.WEIGHTS))
        self.assertAlmostEqual(sum(pcts), 100.0, delta=0.5)


class TestRunLottery(unittest.TestCase):
    TEAMS = ["A", "B", "C", "D", "E", "F", "G", "H"]

    def test_every_team_drafted_exactly_once(self):
        result = lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)
        self.assertEqual(sorted(t for _, t in result), sorted(self.TEAMS))

    def test_pick_numbers_are_sequential(self):
        result = lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)
        self.assertEqual([p for p, _ in result], list(range(1, 9)))

    def test_seeded_run_is_reproducible(self):
        random.seed(123)
        first = lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)
        random.seed(123)
        second = lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)
        self.assertEqual(first, second)

    def test_single_team(self):
        self.assertEqual(lottery.run_lottery(["Solo"], [10]), [(1, "Solo")])

    def test_empty_pool(self):
        self.assertEqual(lottery.run_lottery([], []), [])

    def test_does_not_mutate_inputs(self):
        teams, weights = list(self.TEAMS), list(lottery.WEIGHTS)
        lottery.run_lottery(teams, weights)
        self.assertEqual(teams, self.TEAMS)
        self.assertEqual(weights, lottery.WEIGHTS)

    def test_zero_weight_remainder_raises(self):
        # Documents current behavior: once only zero-weight teams remain,
        # random.choices refuses to draw. The default weights are all positive.
        with self.assertRaises(ValueError):
            lottery.run_lottery(["A", "B"], [1, 0])

    def test_top_pick_frequencies_match_weights(self):
        random.seed(2024)
        trials = 40000
        counts = Counter(
            lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)[0][1]
            for _ in range(trials)
        )
        total = sum(lottery.WEIGHTS)
        for team, w in zip(self.TEAMS, lottery.WEIGHTS):
            expected = w / total
            observed = counts[team] / trials
            self.assertAlmostEqual(observed, expected, delta=0.015, msg=team)

    def test_worst_team_wins_top_pick_more_than_best_team(self):
        random.seed(99)
        counts = Counter(
            lottery.run_lottery(self.TEAMS, lottery.WEIGHTS)[0][1]
            for _ in range(5000)
        )
        self.assertGreater(counts["A"], counts["H"])


class TestWeights(unittest.TestCase):
    def test_weights_descend(self):
        self.assertEqual(lottery.WEIGHTS, sorted(lottery.WEIGHTS, reverse=True))

    def test_num_teams_matches_weights(self):
        self.assertEqual(lottery.NUM_TEAMS, len(lottery.WEIGHTS))


class TestWholeProgram(unittest.TestCase):
    """Runs lottery.py as __main__ with scripted input."""

    # Deliberately entered out of order; points are unique.
    ENTRIES = [
        ("Gamma", 700),
        ("Alpha", 100),
        ("Hotel", 800),
        ("Beta", 200),
        ("Echo", 500),
        ("Delta", 400),
        ("Foxtrot", 600),
        ("Charlie", 300),
    ]

    def run_program(self, entries, seed=1):
        inputs = [x for name, pts in entries for x in (name, str(pts))]
        buf = io.StringIO()
        random.seed(seed)
        with patch("builtins.input", side_effect=inputs), redirect_stdout(buf):
            runpy.run_path(SCRIPT, run_name="__main__")
        return buf.getvalue()

    def parse_odds_rows(self, out):
        """Returns [(team, tickets)] from the odds table, in displayed order."""
        section = out.split("=== LOTTERY ODDS")[1].split("=== DRAWING")[0]
        rows = []
        for line in section.splitlines():
            parts = line.split()
            if parts and parts[0].isdigit():
                rows.append((parts[1], int(parts[3])))
        return rows

    def parse_draft_rows(self, out):
        section = out.split("=== DRAWING FULL DRAFT ORDER ===")[1]
        rows = []
        for line in section.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit():
                rows.append((int(parts[0]), parts[1]))
        return rows

    def test_teams_ranked_by_points_ascending(self):
        out = self.run_program(self.ENTRIES)
        rows = self.parse_odds_rows(out)
        self.assertEqual(
            [t for t, _ in rows],
            ["Alpha", "Beta", "Charlie", "Delta", "Echo", "Foxtrot", "Gamma", "Hotel"],
        )

    def test_fewest_points_gets_most_tickets(self):
        out = self.run_program(self.ENTRIES)
        rows = self.parse_odds_rows(out)
        self.assertEqual([w for _, w in rows], lottery.WEIGHTS)
        self.assertEqual(rows[0], ("Alpha", max(lottery.WEIGHTS)))
        self.assertEqual(rows[-1], ("Hotel", min(lottery.WEIGHTS)))

    def test_draft_order_contains_all_teams_once(self):
        out = self.run_program(self.ENTRIES)
        rows = self.parse_draft_rows(out)
        self.assertEqual([p for p, _ in rows], list(range(1, 9)))
        self.assertEqual(
            sorted(t for _, t in rows), sorted(n for n, _ in self.ENTRIES)
        )

    def test_same_seed_gives_same_output(self):
        self.assertEqual(
            self.run_program(self.ENTRIES, seed=5),
            self.run_program(self.ENTRIES, seed=5),
        )

    def test_recovers_from_bad_input_end_to_end(self):
        inputs = []
        for i, (name, pts) in enumerate(self.ENTRIES):
            if i == 0:
                inputs += ["", name, "oops", str(pts)]  # blank name, bad points
            else:
                inputs += [name, str(pts)]
        buf = io.StringIO()
        random.seed(1)
        with patch("builtins.input", side_effect=inputs), redirect_stdout(buf):
            runpy.run_path(SCRIPT, run_name="__main__")
        rows = self.parse_draft_rows(buf.getvalue())
        self.assertEqual(len(rows), 8)


if __name__ == "__main__":
    unittest.main()