import random
import unittest
from engine import Game


class SimulationTests(unittest.TestCase):
    def test_many_complete_games(self):
        for size in (2, 3, 10, 40):
            for seed in range(250):
                game = Game(list(range(size)), random.Random(seed))
                while len(game.alive) > 1:
                    before = set(game.alive)
                    lines = game.step()
                    self.assertTrue(lines)
                    removed = before - set(game.alive)
                    self.assertEqual({event['eliminated'] for event in game.events}, removed)
                    for event in game.events:
                        self.assertIn(event['text'], lines)
                        if event['kind'] == 'battle':
                            self.assertIn(event['winner'], before)
                            self.assertNotEqual(event['winner'], event['eliminated'])
                        else:
                            self.assertIsNone(event['winner'])
                    self.assertLess(len(game.alive), len(before))
                    self.assertLessEqual(set(game.alive), before)
                    self.assertEqual(len(game.deaths), len(set(game.deaths)))
                self.assertEqual(len(game.deaths), size - 1)
                self.assertEqual(sum(game.kills.values()) + len(game.unexpected), size - 1)
                self.assertEqual(set(game.deaths) | set(game.alive), set(range(size)))
                self.assertEqual(game.awards()['First death'], game.deaths[:1])
                self.assertEqual(game.awards()['Runner-up'], game.deaths[-1:])
                self.assertLessEqual(set(game.unexpected), set(game.deaths))
                self.assertEqual(game.step(), [])

    def test_invalid_rosters(self):
        for players in ([], [1], [1, 1], list(range(41))):
            with self.assertRaises(ValueError):
                Game(players)

    def test_awards_require_finish(self):
        with self.assertRaises(ValueError):
            Game([1, 2]).awards()


if __name__ == '__main__':
    unittest.main()
