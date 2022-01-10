import datetime
import logging

from .fronmod_config import FronmodConfig, FronmodConfKey
from .fronmod_exception import FronmodException
from .mobu import MobuBatch, MobuFlag, MobuItem, MobuResult
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder

from ..time_utils import TimeUtils

_logger = logging.getLogger(__name__)


class FronmodReader:

    def __init__(self, config, print_registers=False):
        self._url = config[FronmodConfKey.HOST]
        self._port = config[FronmodConfKey.PORT]
        self._print_registers = print_registers

        self._client = None

        self._last_read = None
        self._last_register = None
        self._last_logged = False

        logging.getLogger("pymodbus").setLevel(logging.WARNING)

    def open(self):
        if not self._client:
            self._client = ModbusClient(self._url, port=self._port)
            self._client.connect()
            _logger.debug("connected")

    def is_open(self) -> bool:
        if self._client is None:
            return False
        if not self._client.is_socket_open():
            return False
        return True

    def close(self):
        if self._client:
            _logger.debug("closing")
            self._client.close()
            self._client = None

    def _extract(self, read_item: MobuItem, registers):
        if read_item.offset == 0:
            decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=FronmodConfig.BYTEORDER)
        else:
            offset = read_item.offset
            if read_item.flags & MobuFlag.INT16:
                buffer = registers[offset:offset + 1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
            elif read_item.flags & MobuFlag.UINT16:
                buffer = registers[offset:offset + 1]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
            elif read_item.flags & MobuFlag.FLOAT32:
                buffer = registers[offset:offset + 2]
                decoder = BinaryPayloadDecoder.fromRegisters(buffer, byteorder=FronmodConfig.BYTEORDER)
            else:
                decoder = None  # error

        result = MobuResult(read_item.name)

        if read_item.flags & MobuFlag.INT16:
            result.value = decoder.decode_16bit_int()
        elif read_item.flags & MobuFlag.UINT16:
            result.value = decoder.decode_16bit_uint()
            if result.value == 0xffff:
                result.value = 0  # strange behavior with RAW_MPPT_MOD_POWER + RAW_MPPT_BAT_POWER
        elif read_item.flags & MobuFlag.FLOAT32:
            result.value = decoder.decode_32bit_float()
        elif read_item.flags & MobuFlag.STRING8:
            raise NotImplementedError()
        else:
            raise ValueError()

        result.ready = True
        return result

    def _read_remote_registers(self, read: MobuBatch):
        self._last_read = None
        self._last_register = None
        self._last_logged = False

        if self._client is None:
            raise FronmodException('ModbusClient is None!')
        if not self.is_open():
            raise FronmodException('ModbusClient is not open!')

        time_start = datetime.datetime.now()
        response = self._client.read_holding_registers(read.pos, read.length, unit=read.unit_id)
        diff_seconds = (datetime.datetime.now() - time_start).total_seconds()
        if diff_seconds > 0.3:
            _logger.debug('read_holding_registers <pos=%d, l=%d, unit=%d> took %fs',
                          read.pos, read.length, read.unit_id, diff_seconds)

        if response.isError():
            _logger.error('read_holding_registers failed - response: %s', str(response))
            raise FronmodException('read_holding_registers failed!')

        self._last_read = read
        self._last_register = response.registers

        if self._print_registers:
            print('response.registers: ', response.registers)
        return response.registers

    def read(self, read: MobuBatch):
        time_start = TimeUtils.now()

        registers = self._read_remote_registers(read)

        results = {}
        for item in read.items:
            if item.offset is not None:
                result = self._extract(item, registers)
                if results.get(item.name) is not None:
                    raise FronmodException('wrong configuration - duplicate read names!')
            else:
                result = MobuResult(item.name)  # empty result!

            result.item = item
            results[item.name] = result

        _logger.debug("read batch '%s' (%.1fs)", read.name, (TimeUtils.now() - time_start).total_seconds())
        return results

    def log_last_registers(self):
        if not self._last_logged:
            _logger.warning('log_last_registers ({}): {}', self._last_read, self._last_register)
            self._last_logged = True
