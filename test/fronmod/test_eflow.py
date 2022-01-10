import datetime
import math
import unittest

from src.fronmod.eflow import EflowChannel, EflowAggregate


class MockEflowChannel(EflowChannel):

    def __init__(self, source_name, agg_plus, agg_minus):
        super().__init__(source_name, agg_plus, agg_minus)
        self.mock_time = None

    def get_current_time(self):
        return self.mock_time


class TestEflow(unittest.TestCase):

    def test_get_normed_intercept(self):
        intercept = EflowChannel.get_normed_intercept(-1, 1)
        self.assertEqual(0.5, intercept)

        intercept = EflowChannel.get_normed_intercept(1, -1)
        self.assertEqual(0.5, intercept)

        intercept = EflowChannel.get_normed_intercept(1, -3)
        self.assertEqual(0.25, intercept)

        intercept = EflowChannel.get_normed_intercept(3, -1)
        self.assertEqual(0.75, intercept)

        intercept = EflowChannel.get_normed_intercept(1000, 0)
        self.assertEqual(1, intercept)

        intercept = EflowChannel.get_normed_intercept(0, 1000)
        self.assertEqual(0, intercept)

    def test_complete(self):
        item = 'item'
        plus = 'plus'
        minus = 'minus'

        eflow = MockEflowChannel(item, EflowAggregate(plus), EflowAggregate(minus))
        print(eflow)

        current_time = datetime.datetime(2019, 9, 9, 0, 0, 0)
        eflow.mock_time = current_time

        self.assertEqual(None, eflow.last_time)
        self.assertEqual(None, eflow.last_value)

        last_value = 1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # no time change
        eflow.push_value(last_value)
        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # next step + 1 hour

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        eflow.push_value(last_value)
        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)
        self.assertEqual(1, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-0.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-1.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=0.5)
        eflow.mock_time = current_time

        last_value = -1
        eflow.push_value(last_value)

        self.assertEqual(current_time, eflow.last_time)
        self.assertEqual(last_value, eflow.last_value)

        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-1.75, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 0
        eflow.push_value(last_value)
        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 0
        eflow.push_value(last_value)
        self.assertEqual(1.25, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        # next step

        current_time += datetime.timedelta(hours=1)
        eflow.mock_time = current_time

        last_value = 1
        eflow.push_value(last_value)
        self.assertEqual(1.75, eflow.plus.value_agg)
        self.assertEqual(-2.25, eflow.minus.value_agg)

        print(eflow)

        # finish

        aggs = eflow.get_aggregates_and_reset()
        self.assertEqual(2, len(aggs))

        hit = 0
        for agg in aggs:
            if agg.item_name == plus and agg.value_agg == 1.75:
                hit += 1
            if agg.item_name == minus and agg.value_agg == -2.25:
                hit += 1
        self.assertEqual(2, hit)

        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

    def check_test_realistic_times(self, value):
        item = 'item'
        plus = 'plus'
        minus = 'minus'

        eflow = MockEflowChannel(item, EflowAggregate(plus), EflowAggregate(minus))

        eflow.mock_time = datetime.datetime.now()

        eflow.push_value(value)

        self.assertEqual(eflow.mock_time, eflow.last_time)
        self.assertEqual(value, eflow.last_value)
        self.assertEqual(0, eflow.plus.value_agg)
        self.assertEqual(0, eflow.minus.value_agg)

        # print(eflow)

        offset_seconds = 10
        for i in range(0, 6):
            eflow.mock_time = eflow.mock_time + datetime.timedelta(seconds=offset_seconds)
            eflow.push_value(value)
            # print(eflow)

        if value > 0:
            self.assertEqual(0, eflow.minus.value_agg)
            self.assertTrue(math.isclose(value / 60.0, eflow.plus.value_agg, rel_tol=1e-6))
        else:
            self.assertEqual(0, eflow.plus.value_agg)
            self.assertTrue(math.isclose(value / 60.0, eflow.minus.value_agg, rel_tol=1e-6))

    def test_realistic_times(self):

        self.check_test_realistic_times(-800)
        self.check_test_realistic_times(800)

    def test_realistic_numbers(self):

        item = 'item'
        plus = 'plus'
        minus = 'minus'

        eflow = MockEflowChannel(item, EflowAggregate(plus), EflowAggregate(minus))

        eflow.mock_time = datetime.datetime.now()

        # 1039.4 | 1039.4 => 2.887222222222222
        # 1039.4 | 0 => 1.443611111111111

        value1 = 1039.4
        eflow.push_value(value1)
        # print(eflow)

        offset_seconds = 10
        eflow.mock_time = eflow.mock_time + datetime.timedelta(seconds=offset_seconds)

        value2 = -40.94
        eflow.push_value(value2)
        # print(eflow)

        self.assertTrue(math.isclose(1.3889047789481912, eflow.plus.value_agg, rel_tol=1e-6))
        self.assertTrue(math.isclose(-0.002154778948191209, eflow.minus.value_agg, rel_tol=1e-6))
