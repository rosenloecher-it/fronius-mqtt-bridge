import logging

from src.fronmod.eflow import EflowChannel, EflowAggregate
from src.fronmod.fronmod_config import FronmodConfig, FronmodItem
from src.fronmod.fronmod_exception import FronmodException
from src.fronmod.mobu import MobuFlag, MobuResult, MobuBatch


_logger = logging.getLogger(__name__)


class FronmodProcessor:

    def __init__(self, reader):
        self._reader = reader

        self._send_quick = {}  # 10s
        self._send_medium = {}  # 60s
        self._send_slow = {}  # 300s

        self.eflow_inv_dc = EflowChannel(FronmodItem.INV_DC_POWER,
                                         EflowAggregate(FronmodItem.EFLOW_INV_DC_OUT),
                                         EflowAggregate(FronmodItem.EFLOW_INV_DC_IN))
        self.eflow_inv_ac = EflowChannel(FronmodItem.INV_AC_POWER,
                                         EflowAggregate(FronmodItem.EFLOW_INV_AC_OUT),
                                         EflowAggregate(FronmodItem.EFLOW_INV_AC_IN))
        self.eflow_bat = EflowChannel(FronmodItem.MPPT_BAT_POWER,
                                      EflowAggregate(FronmodItem.EFLOW_BAT_OUT),
                                      EflowAggregate(FronmodItem.EFLOW_BAT_IN))
        self.eflow_mod = EflowChannel(FronmodItem.MPPT_MOD_POWER,
                                      EflowAggregate(FronmodItem.EFLOW_MOD_OUT),
                                      None)

        self.value_inv_ac_power = None
        self.value_inv_dc_power = None
        self.value_met_ac_power = None

        self._show_errors = True

    def set_show_errors(self, show_errors):
        self._show_errors = show_errors

    def open(self):
        if not self._reader.is_open():
            self._reader.open()

    def close(self):
        if self._reader:
            _logger.debug("closing")
            self._reader.close()
            self._reader = None

    def _get_queue_dict(self, flags):
        if flags is None:
            return

        queue_dict = None
        if flags & MobuFlag.Q_QUICK:
            queue_dict = self._send_quick
        elif flags & MobuFlag.Q_MEDIUM:
            queue_dict = self._send_medium
        elif flags & MobuFlag.Q_SLOW:
            queue_dict = self._send_slow

        return queue_dict

    def _process_model(self, read_conf: MobuBatch):
        try:
            results = self._reader.read(read_conf)
        except Exception:
            if self._show_errors:
                _logger.error('read_model failed (%s)!', read_conf)
            raise

        for key, result in results.items():
            self._queue_send(result)

        return results  # used for loading and analysing real values from test context

    def reset_items(self, read_conf: MobuBatch):
        for item in read_conf.items:
            if not item.flags & MobuFlag.Q_ALL:
                continue
            result = MobuResult(item.name)
            result.item = item
            result.ready = True
            self._queue_send(result)

    def process_inverter_model(self):
        batch = FronmodConfig.INVERTER_BATCH
        try:
            results = self._process_model(batch)

            self._process_text_conversion(results, FronmodItem.INV_STATE_CODE, FronmodItem.INV_STATE_TEXT,
                                          FronmodConfig.format_inv_sun_spec_state)

            self._push_eflow(results, self.eflow_inv_dc)
            self._push_eflow(results, self.eflow_inv_ac)

            self.value_inv_ac_power = self.get_value(results, FronmodItem.INV_AC_POWER)
            self.value_inv_dc_power = self.get_value(results, FronmodItem.INV_DC_POWER)

            self._process_self_consumption(results)
            self._process_inv_efficiency(results)

            return results
        except Exception:
            self.reset_items(batch)
            raise

    def process_storage_model(self):
        batch = FronmodConfig.STORAGE_BATCH
        try:
            results = self._process_model(batch)

            self._process_modbus_scale(results, FronmodItem.RAW_BAT_FILL_LEVEL, FronmodItem.RAW_BAT_FILL_LEVEL_SF,
                                       FronmodItem.BAT_FILL_LEVEL)

            self._process_text_conversion(results, FronmodItem.BAT_STATE_CODE, FronmodItem.BAT_STATE_TEXT, FronmodConfig.format_bat_state)

            return results
        except Exception:
            self.reset_items(batch)
            raise

    def process_mppt_model(self):
        batch = FronmodConfig.MPPT_BATCH
        try:
            results = self._process_model(batch)

            self._process_modbus_scale(results, FronmodItem.RAW_MPPT_MOD_VOLTAGE, FronmodItem.RAW_MPPT_VOLTAGE_SF,
                                       FronmodItem.MPPT_MOD_VOLTAGE)

            self._process_modbus_scale(results, FronmodItem.RAW_MPPT_MOD_POWER, FronmodItem.RAW_MPPT_POWER_SF,
                                       FronmodItem.MPPT_MOD_POWER)
            self._log_mobu_registers_when_value_larger_than(results, FronmodItem.MPPT_MOD_POWER, 5500)

            self._process_modbus_scale(results, FronmodItem.RAW_MPPT_BAT_POWER, FronmodItem.RAW_MPPT_POWER_SF,
                                       FronmodItem.RAW2_MPPT_BAT_POWER)

            self._process_text_conversion(results, FronmodItem.MPPT_BAT_STATE_CODE, FronmodItem.MPPT_BAT_STATE_TEXT,
                                          FronmodConfig.format_mptt_state)
            self._process_text_conversion(results, FronmodItem.MPPT_MOD_STATE_CODE, FronmodItem.MPPT_MOD_STATE_TEXT,
                                          FronmodConfig.format_mptt_state)

            self._process_bat_power_sign(results)  # RAW2_MPPT_BAT_POWER => MPPT_BAT_POWER
            self._log_mobu_registers_when_value_larger_than(results, FronmodItem.MPPT_BAT_POWER, 3300)

            self._push_eflow(results, self.eflow_bat)
            self._push_eflow(results, self.eflow_mod)

            return results
        except Exception:
            self.reset_items(batch)
            raise

    def process_meter_model(self):
        batch = FronmodConfig.METER_BATCH
        try:
            results = self._process_model(FronmodConfig.METER_BATCH)

            self.value_met_ac_power = self.get_value(results, FronmodItem.MET_AC_POWER)
            self._process_self_consumption(results)

            return results
        except Exception:
            self.reset_items(batch)
            raise

    def _process_modbus_scale(self, results: dict, value_name: str, scale_name: str, target_name: str):

        try:
            value_temp = results[value_name]
            scale_temp = results[scale_name]
            value_target = self.scale_item(value_temp, scale_temp)
        except (FronmodException, TypeError, ValueError) as ex:
            if self._show_errors:
                _logger.error('process_modbus_scale failed (%s + %s => %s)!', value_name, scale_name, target_name)
                _logger.exception(ex)
            value_target = None

        target_result = results[target_name]
        target_result.value = value_target
        target_result.ready = True
        self._queue_send(target_result)

    def _process_text_conversion(self, results: dict, source_name: str, target_name: str, convertion_func):
        target_result = results[target_name]

        source_mobu = results[source_name]
        if source_mobu:
            target_result.value = convertion_func(source_mobu.value)

        target_result.ready = True
        self._queue_send(target_result)

    def _process_self_consumption(self, results):
        target_result = results[FronmodItem.SELF_CONSUMPTION]
        if self.value_inv_ac_power is not None and self.value_met_ac_power is not None:
            target_result.value = -0.001 * (self.value_inv_ac_power + self.value_met_ac_power)
        target_result.ready = True
        self._queue_send(target_result)

    def _process_bat_power_sign(self, results: dict):
        value_target = None
        try:
            raw_bat_power = results.get(FronmodItem.RAW2_MPPT_BAT_POWER)

            if raw_bat_power and raw_bat_power.ready:
                mod_power = results.get(FronmodItem.MPPT_MOD_POWER)
                if mod_power and mod_power.ready:
                    charge_factor = 0
                    if self.value_inv_dc_power is not None:
                        power_abs_1 = abs(0.0 + self.value_inv_dc_power - mod_power.value + raw_bat_power.value)
                        power_abs_2 = abs(0.0 + self.value_inv_dc_power - mod_power.value - raw_bat_power.value)
                        if power_abs_1 < power_abs_2:
                            charge_factor = -1.0
                        else:
                            charge_factor = 1.0

                    value_target = raw_bat_power.value * charge_factor

        except (TypeError, ValueError) as ex:
            if self._show_errors:
                _logger.error('process_bat_power_sign failed!')
                _logger.exception(ex)
            value_target = None

        target_result = results[FronmodItem.MPPT_BAT_POWER]
        target_result.value = value_target
        target_result.ready = True
        self._queue_send(target_result)

    def _process_inv_efficiency(self, results: dict):
        value_target = None
        try:
            if self.value_inv_ac_power is not None and self.value_inv_dc_power is not None:
                if self.value_inv_dc_power == 0:
                    value_target = 0
                else:
                    value_target = 100.0 * self.value_inv_ac_power / self.value_inv_dc_power

        except (TypeError, ValueError) as ex:
            if self._show_errors:
                _logger.error('process_inv_efficiency failed!')
                _logger.exception(ex)
            value_target = None

        target_result = results[FronmodItem.INV_EFFICIENCY]
        target_result.value = value_target
        target_result.ready = True
        self._queue_send(target_result)

    @classmethod
    def _push_eflow(cls, results, eflow):
        result = results[eflow.source_name]
        if not result.ready:
            raise FronmodException('can only push ready values!')
        eflow.push_value(result.value)

    def get_send_data(self, flags):
        export_data = {}
        queue_dict = self._get_queue_dict(flags)
        if queue_dict:
            for key, value in queue_dict.items():
                # send_data_list.append(send_data)
                export_data[key] = value
            queue_dict.clear()

        if flags & MobuFlag.Q_MEDIUM:
            eflow_list = [self.eflow_inv_dc, self.eflow_inv_ac, self.eflow_bat, self.eflow_mod]
            for eflow in eflow_list:
                agg_list = eflow.get_aggregates_and_reset()
                for agg in agg_list:
                    if agg.value_agg != 0:
                        # channel = Channel.create(ChannelType.ITEM, agg.item_name)
                        # send_data = OhSendData(self.SENDFLAGS, channel, agg.value_agg)
                        # send_data_list.append(send_data)
                        export_data[agg.item_name] = agg.value_agg

        return export_data

    def _queue_send(self, result: MobuResult):
        if not result or not result.ready:
            return

        queue_dict = self._get_queue_dict(result.item.flags)
        if queue_dict is not None:
            # channel = Channel.create(ChannelType.ITEM, result.name)
            # send_data = OhSendData(self.SENDFLAGS, channel, result.value)
            queue_dict[result.name] = result.value

    @classmethod
    def scale_item(cls, value_item: MobuResult, scale_item: MobuResult):
        if value_item is None or value_item.value is None:
            raise ValueError()

        scale = cls.convert_scale_factor(scale_item)
        value = value_item.value * scale
        return value

    @classmethod
    def convert_scale_factor(cls, data_in):
        if isinstance(data_in, MobuResult):
            sunssf = data_in.value
        else:
            sunssf = data_in

        if sunssf is None:
            raise ValueError()
        sunssf = round(sunssf)
        if sunssf > 10 or sunssf < -10:
            raise ValueError()

        scale_factor = pow(10, sunssf)
        return scale_factor

    @classmethod
    def get_value(cls, results, value_name, default_value=None):
        result = results[value_name]
        if not result.ready:
            raise FronmodException('can only deliver ready values!')
        if result.value is not None:
            return result.value
        return default_value

    def _log_mobu_registers_when_value_larger_than(self, results, item_name, limit):
        if limit is None or self._reader is None:
            return
        result = results.get(item_name)
        if result is None or result.value is None:
            return

        if result.value >= limit:
            self._reader.log_last_registers()
