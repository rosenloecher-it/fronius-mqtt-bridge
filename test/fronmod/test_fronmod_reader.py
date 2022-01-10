import unittest
from src.fronmod.fronmod_reader import FronmodReader  # noqa


class TestFronmodReader(unittest.TestCase):

    def test_dummy(self):
        pass

        # reader = FronmodReader('192.168.12.42', 502)
        # try:
        #     reader.open()
        #     #reader.read_float()
        #     reader.read_mppt()
        #     print('succeed')
        # finally:
        #     reader.close()
        #
        # self.assertTrue(True)
