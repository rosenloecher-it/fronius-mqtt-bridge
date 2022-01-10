import copy
import datetime
from typing import Optional


class EflowAggregate:

    def __init__(self, item_name: str):
        self.item_name = item_name
        self.value_agg = 0

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.item_name, self.value_agg)


class EflowChannel:
    MIN_NULL = 1e-9

    def __init__(self, source_name: str, agg_plus: Optional[EflowAggregate], agg_minus: Optional[EflowAggregate]):
        self.source_name = source_name
        self.last_time = None
        self.last_value = None

        self.plus: EflowAggregate = agg_plus
        self.minus: EflowAggregate = agg_minus

    def __repr__(self) -> str:
        return '{}({},+{},-{})'.format(self.__class__.__name__, self.source_name, self.plus, self.minus)

    def get_current_time(self):
        # overwrite and mock time calculation
        return datetime.datetime.now()

    def push_value(self, value_curr):
        curr_time = self.get_current_time()
        if self.last_time is not None and self.last_value is not None:
            self.calc(curr_time, value_curr)

        self.last_time = curr_time
        self.last_value = value_curr

    def _add_value(self, value_agg):
        if value_agg > 0:
            if self.plus:
                self.plus.value_agg += value_agg
        else:
            if self.minus:
                self.minus.value_agg += value_agg

    def calc(self, curr_time, curr_value):
        last_bias = self.get_bias(self.last_value)
        curr_bias = self.get_bias(curr_value)
        elapsed_time = (curr_time - self.last_time).total_seconds()
        factor_full = elapsed_time / 60.0 / 60.0

        if factor_full > 0:
            if last_bias + curr_bias == 0 and last_bias != curr_bias:
                factor_last = factor_full * self.get_normed_intercept(self.last_value, curr_value)
                factor_curr = factor_full - factor_last

                agg_last = self.last_value * factor_last / 2.0
                agg_curr = curr_value * factor_curr / 2.0

                self._add_value(agg_last)
                self._add_value(agg_curr)
            else:
                value_agg = (self.last_value + curr_value) / 2 * factor_full
                self._add_value(value_agg)

    def get_aggregates_and_reset(self):
        aggregates = []

        def add_aggregate(agg: EflowAggregate):
            if agg:
                aggregates.append(copy.deepcopy(agg))
                agg.value_agg = 0

        add_aggregate(self.plus)
        add_aggregate(self.minus)

        return aggregates

    @classmethod
    def get_bias(cls, value):
        if abs(value) < cls.MIN_NULL:
            return 0
        if value >= 0:
            return 1
        return -1

    @staticmethod
    def get_normed_intercept(last_value, curr_value):
        abs_last_value = abs(last_value)
        if abs_last_value == 0:
            return 0  # condition: bias != ... !
        else:
            intercept = 1.0 / (1 + abs(curr_value) / abs_last_value)
        return intercept
