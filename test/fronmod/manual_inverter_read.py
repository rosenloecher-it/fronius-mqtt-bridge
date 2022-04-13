import unittest


# manual read inverter data
from src.fronmod.fronmod_config import FronmodConfKey
from src.fronmod.fronmod_processor import FronmodProcessor
from src.fronmod.fronmod_reader import FronmodReader


class TestFronmodProcessorReadReal(unittest.TestCase):

    CONFIG = {
        FronmodConfKey.HOST: '192.168.12.42',
        FronmodConfKey.PORT: 502,
    }

    @classmethod
    def print_read_result(cls, desc, results):
        print(desc)
        if results is None:
            print('    None')
        else:
            for key, val in results.items():
                print('    {} = {}'.format(key, val))

    # def test_print_read_result(self):
    #     self.print_read_result('test', None)

    @classmethod
    def print_cached_values(cls, processor):
        print('cached: value_inv_ac_power = ', processor.value_inv_ac_power)
        print('cached: value_inv_dc_power = ', processor.value_inv_dc_power)
        print('cached: value_met_ac_power = ', processor.value_met_ac_power)

    def test_process_all(self):
        reader = FronmodReader(self.CONFIG, print_registers=True)
        processor = FronmodProcessor(reader)

        try:
            processor.open()
            results = processor.process_inverter_model()
            self.print_read_result('process_inverter_model', results)

            self.print_cached_values(processor)

            results = processor.process_storage_model()
            self.print_read_result('process_storage_model', results)

            self.print_cached_values(processor)

            results = processor.process_meter_model()
            self.print_read_result('process_meter_model', results)

            self.print_cached_values(processor)

            results = processor.process_mppt_model()
            self.print_read_result('process_mppt_model', results)

            self.print_cached_values(processor)

            print('succeed')
            self.assertTrue(True)
        finally:
            processor.close()

    # def test_process_inverter_model(self):
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_inverter_model()
    #         self.print_read_result('process_inverter_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_storage_model(self):
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_storage_model()
    #         self.print_read_result('process_storage_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_mppt_model(self):
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_mppt_model()
    #         self.print_read_result('process_mppt_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_meter_model(self):
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_meter_model()
    #         self.print_read_result('process_meter_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
