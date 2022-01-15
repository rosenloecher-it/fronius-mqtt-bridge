import unittest

from src.runner import Runner


class TestRunner(unittest.TestCase):

    def test_round_floats(self):
        values_in = {
            "f": 1.1234567890123456,
            "i": 9,
            "t": "text",
        }
        values_exp = {
            "f": 1.1234568,
            "i": 9,
            "t": "text",
        }

        values_out = Runner.round_floats(values_in)
        self.assertEqual(values_out, values_exp)
