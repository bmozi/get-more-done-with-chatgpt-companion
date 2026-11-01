import unittest
from costs import compare


class CostTests(unittest.TestCase):
    def test_zero_visits_retains_fixed_cost(self):
        result = compare(0)
        self.assertEqual((result['plan_A'], result['plan_B'], result['winner']), (20, 0, 'B'))

    def test_opposite_sides_of_the_crossing(self):
        self.assertEqual((compare(3)['plan_A'], compare(3)['plan_B'], compare(3)['winner']), (32, 24, 'B'))
        self.assertEqual((compare(8)['plan_A'], compare(8)['plan_B'], compare(8)['winner']), (52, 64, 'A'))

    def test_tie_does_not_force_a_winner(self):
        result = compare(5)
        self.assertEqual((result['plan_A'], result['plan_B'], result['winner']), (40, 40, None))

    def test_changed_plan_terms(self):
        for visits, expected in [(2, (18,12,'B')), (4,(24,24,None)), (6,(30,36,'A'))]:
            result = compare(visits, fixed_a=12, per_a=3, per_b=6)
            self.assertEqual((result['plan_A'], result['plan_B'], result['winner']), expected)

    def test_invalid_values_are_not_silently_coerced(self):
        for value in [-1, True, 2.5, '5']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare(value)
        with self.assertRaises(ValueError):
            compare(3, per_a=-4)


if __name__ == '__main__':
    unittest.main()
