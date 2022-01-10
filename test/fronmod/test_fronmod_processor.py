import unittest

from src.fronmod.fronmod_config import FronmodConfig, FronmodItem
from src.fronmod.fronmod_processor import FronmodProcessor
from src.fronmod.mobu import MobuResult, MobuFlag
from test.fronmod.mock_fronmod_reader import MockFronmodReader


class TestFronmodProcessor(unittest.TestCase):

    def test_convert_scale_factor(self):

        item = MobuResult('test')

        item.value = -2
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(0.01, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(0.01, out)

        item.value = -1
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(0.1, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(0.1, out)

        item.value = 0
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(1, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(1, out)

        item.value = 1
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(10, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(10, out)

        item.value = 2
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(100, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(100, out)

        try:
            item.value = -11
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = 11
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = None
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            FronmodProcessor.convert_scale_factor(None)
            self.assertTrue(False)
        except ValueError:
            pass


class TestFronmodProcessorProcessing(unittest.TestCase):

    def setUp(self):
        self.mock_reader = MockFronmodReader()
        self.processor = FronmodProcessor(self.mock_reader)

    def test_process_inverter_no_sun(self):
        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0,
            19157, 42320, 32704, 0, 32704, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.INV_AC_POWER: 0.0,
            FronmodItem.INV_DC_POWER: 0.0,
            FronmodItem.INV_EFFICIENCY: 0,
            FronmodItem.SELF_CONSUMPTION: None
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.INV_AC_ENERGY_TOT: 7000744.0,
            FronmodItem.INV_STATE_CODE: 3,
            FronmodItem.INV_STATE_TEXT: FronmodConfig.format_inv_fronius_state(3),
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_process_inverter_sun(self):
        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 16280, 20972, 16076, 52429, 16076, 52429, 16071, 44564, 17354, 45875, 17355, 39322, 17355, 58982, 17258,
            13107, 17258, 39322, 17259, 58982, 17293, 0, 16967, 55050, 17293, 58, 16256, 0, 49863, 65454, 19158, 29366,
            32704, 0, 32704, 0, 17310, 22938, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0
        ])

        self.processor.process_inverter_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.INV_AC_POWER: 282.0,
            FronmodItem.INV_DC_POWER: 316.70001220703125,
            FronmodItem.INV_EFFICIENCY: 89.04325517223303,
            # FronmodProcessor.value_met_ac_power is None (set by "meter")
            FronmodItem.SELF_CONSUMPTION: None
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.INV_AC_ENERGY_TOT: 7027035.0,
            FronmodItem.INV_STATE_CODE: 4,
            FronmodItem.INV_STATE_TEXT: FronmodConfig.format_inv_fronius_state(4),
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_process_storage_empty3(self):
        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
            32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({}, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({}, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({
            FronmodItem.BAT_FILL_LEVEL: 3.0,
            FronmodItem.BAT_STATE_CODE: 2,
            FronmodItem.BAT_STATE_TEXT: FronmodConfig.format_bat_state(2),
        }, send_slow)

    def test_process_storage_discharge(self):
        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 2400, 65535, 65535, 3, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
            32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({}, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({}, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({
            FronmodItem.BAT_FILL_LEVEL: 24.0,
            FronmodItem.BAT_STATE_CODE: 3,
            FronmodItem.BAT_STATE_TEXT: FronmodConfig.format_bat_state(3),
        }, send_slow)

    def test_process_storage_holding(self):
        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 2900, 65535, 65535, 6, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
            32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({}, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({}, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({
            FronmodItem.BAT_FILL_LEVEL: 29.0,
            FronmodItem.BAT_STATE_CODE: 6,
            FronmodItem.BAT_STATE_TEXT: FronmodConfig.format_bat_state(6),
        }, send_slow)

    def test_process_mppt(self):
        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 55, 56620,
            31141, 0, 0, 9155, 20421, 32768, 4, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 2, 18320, 366,
            0, 0, 9155, 20421, 32768, 4
        ])

        bat_power_expected = -3.66
        mod_power_expected = 311.41

        self.processor.value_inv_dc_power = (mod_power_expected + bat_power_expected)

        self.processor.process_mppt_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.MPPT_BAT_POWER: -3.66,
            FronmodItem.MPPT_MOD_POWER: 311.41,
            FronmodItem.MPPT_MOD_VOLTAGE: 566.2
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.MPPT_BAT_STATE_CODE: 4,
            FronmodItem.MPPT_BAT_STATE_TEXT: FronmodConfig.format_mptt_state(4),
            FronmodItem.MPPT_MOD_STATE_CODE: 4,
            FronmodItem.MPPT_MOD_STATE_TEXT: FronmodConfig.format_mptt_state(4),
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_process_mppt_ffff_equals_0(self):
        # fronius delivers 0xffff for *MPPT_MOD_STATE_CODE + MPPT_BAT_POWER !!!
        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 0, 350,
            65535, 0, 0, 9161, 6067, 32768, 3, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 0, 260, 0, 0, 0,
            9161, 6067, 32768, 3
        ])

        self.processor.process_mppt_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.MPPT_BAT_POWER: 0.0,
            FronmodItem.MPPT_MOD_POWER: 0.0,
            FronmodItem.MPPT_MOD_VOLTAGE: 3.5,
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.MPPT_BAT_STATE_CODE: 3,
            FronmodItem.MPPT_BAT_STATE_TEXT: FronmodConfig.format_mptt_state(3),
            FronmodItem.MPPT_MOD_STATE_CODE: 3,
            FronmodItem.MPPT_MOD_STATE_TEXT: FronmodConfig.format_mptt_state(3),
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_mppt_storage_ffff_equals_0(self):
        # fronius delivers 0xffff for *MPPT_MOD_STATE_CODE + MPPT_BAT_POWER !!!
        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 0, 350,
            65535, 0, 0, 9161, 6067, 32768, 3, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 0, 260, 0, 0, 0,
            9161, 6067, 32768, 3
        ])

        self.processor.process_mppt_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.MPPT_BAT_POWER: 0.0,
            FronmodItem.MPPT_MOD_POWER: 0.0,
            FronmodItem.MPPT_MOD_VOLTAGE: 3.5,
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.MPPT_BAT_STATE_CODE: 3,
            FronmodItem.MPPT_BAT_STATE_TEXT: FronmodConfig.format_mptt_state(3),
            FronmodItem.MPPT_MOD_STATE_CODE: 3,
            FronmodItem.MPPT_MOD_STATE_TEXT: FronmodConfig.format_mptt_state(3),
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_process_meter(self):
        self.mock_reader.set_mock_read(FronmodConfig.METER_BATCH, [
            16384, 16968, 0, 16528, 62915, 16967, 55050, 16831, 2621, 49802, 40632, 17298, 61932, 17197, 16187, 17236,
            42362, 17172, 54788, 50066, 61932, 49840, 57672, 49929, 53084, 49799, 18350, 15395, 55050, 16122, 57672,
            15918, 5243, 48949, 49807, 19079, 34320, 32704, 0, 32704, 0, 32704, 0, 18772, 13440, 32704, 0, 32704, 0,
            32704
        ])

        self.processor.process_meter_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.MET_AC_POWER: 4.53000020980835,
            FronmodItem.SELF_CONSUMPTION: None,
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.MET_AC_FREQUENCY: 50.0,
            FronmodItem.MET_ENERGY_EXP_TOT: 4440840.0,
            FronmodItem.MET_ENERGY_IMP_TOT: 869192.0,
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_process_self_consumption(self):
        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 16744, 52429, 16539, 34079, 16539, 34079, 16538, 36700, 17355, 52429, 17357, 39322, 17357, 52429, 17258,
            45875, 17261, 26214, 17262, 13107, 17751, 36864, 16967, 62915, 17751, 37126, 49576, 0, 17095, 65293, 19158,
            64272, 32704, 0, 32704, 0, 17759, 57344, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        self.mock_reader.set_mock_read(FronmodConfig.METER_BATCH, [
            3277, 16968, 0, 50336, 573, 17489, 164, 50308, 49889, 50307, 49070, 17571, 49152, 17494, 1720, 17543, 25876,
            17540, 39715, 50059, 12124, 49841, 47186, 49936, 28180, 49716, 20972, 49016, 20972, 16253, 28836, 49021,
            28836, 49021, 28836, 19079, 35284, 32704, 0, 32704, 0, 32704, 0, 18772, 13440, 32704, 0, 32704, 0, 32704
        ])

        self.processor.process_meter_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.INV_AC_POWER: 3449.0,
            FronmodItem.INV_DC_POWER: 3582.0,
            FronmodItem.INV_EFFICIENCY: 96.28699050809604,
            FronmodItem.MET_AC_POWER: -1280.0699462890625,
            FronmodItem.SELF_CONSUMPTION: -2.1689300537109375,
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.INV_AC_ENERGY_TOT: 7044488.0,
            FronmodItem.INV_STATE_CODE: 4,
            FronmodItem.INV_STATE_TEXT: FronmodConfig.format_inv_fronius_state(4),
            FronmodItem.MET_AC_FREQUENCY: 50.0,
            FronmodItem.MET_ENERGY_EXP_TOT: 4441322.0,
            FronmodItem.MET_ENERGY_IMP_TOT: 869192.0,
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)

    def test_error_reset_items(self):
        self.mock_reader.clear_mock_reads()  # has to fail => ValueError by MockReader

        with self.assertRaises(Exception):
            self.processor.set_show_errors(False)
            self.processor.process_meter_model()

        send_quick = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual({
            FronmodItem.MET_AC_POWER: None,
            FronmodItem.SELF_CONSUMPTION: None
        }, send_quick)
        send_medium = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual({
            FronmodItem.MET_ENERGY_EXP_TOT: None,
            FronmodItem.MET_ENERGY_IMP_TOT: None,
            FronmodItem.MET_AC_FREQUENCY: None
        }, send_medium)
        send_slow = self.processor.get_send_data(MobuFlag.Q_SLOW)
        self.assertEqual({}, send_slow)
