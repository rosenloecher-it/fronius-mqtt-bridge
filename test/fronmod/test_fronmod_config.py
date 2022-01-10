import unittest

from src.fronmod.fronmod_config import FronmodItem, FronmodConfig, FronmodDelivery


class TestFronmodItem(unittest.TestCase):

    def test_get_items(self):
        items = FronmodItem.get_items()

        self.assertTrue(bool(items))

        items_set = set(items)

        self.assertEqual(len(items), len(items_set))  # no doubles

    def test_get_item_keys(self):
        items = FronmodConfig.get_item_keys(FronmodDelivery.QUICK)
        self.assertTrue(bool(items))

        items = FronmodConfig.get_item_keys(FronmodDelivery.MEDIUM)
        self.assertTrue(bool(items))

        items = FronmodConfig.get_item_keys(FronmodDelivery.SLOW)
        self.assertTrue(bool(items))
