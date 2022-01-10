from enum import Enum
from typing import List, Set

from .mobu import MobuBatch, MobuFlag, MobuItem
from pymodbus.constants import Endian


class FronmodConfKey:
    HOST = "host"
    PORT = "port"


FRONMOD_JSONSCHEMA = {
    "type": "object",
    "properties": {
        FronmodConfKey.HOST: {"type": "string", "minLength": 1},
        FronmodConfKey.PORT: {"type": "integer"},
    },
    "additionalProperties": False,
    "required": [FronmodConfKey.HOST, FronmodConfKey.PORT],
}


class FronmodDelivery(Enum):
    QUICK = "quick"
    MEDIUM = "medium"
    SLOW = "slow"


class FronmodItem:
    """
    no enum to avoid explicit cast to string or `.value` access

    will appear in JSON
    """

    # inverter
    INV_AC_ENERGY_TOT = 'invAcEnergyTot'
    INV_EFFICIENCY = 'invEfficiency'
    INV_STATE_CODE = 'invStateCode'  # Fronius state
    INV_STATE_TEXT = 'invStateText'  # Fronius state
    INV_AC_POWER = 'invAcPower'
    INV_DC_POWER = 'invDcPower'

    # storage
    BAT_FILL_LEVEL = 'batFillLevel'
    BAT_STATE_CODE = 'batStateCode'
    RAW_BAT_FILL_LEVEL = 'rawBatFillState'
    RAW_BAT_FILL_LEVEL_SF = 'rawBatFillStateSf'
    BAT_STATE_TEXT = 'batStateText'

    # mppt
    MPPT_BAT_STATE_CODE = 'mpptBatStateCode'
    MPPT_BAT_STATE_TEXT = 'mpptBatStateText'
    MPPT_MOD_STATE_CODE = 'mpptModStateCode'
    MPPT_MOD_STATE_TEXT = 'mpptModStateText'
    MPPT_MOD_VOLTAGE = 'mpptModVoltage'
    RAW2_MPPT_BAT_POWER = 'raw2BatPower'
    RAW_MPPT_BAT_POWER = 'rawMpptBattPower'
    RAW_MPPT_MOD_POWER = 'rawMpptModPower'
    RAW_MPPT_MOD_VOLTAGE = 'rawMpptModVoltage'
    RAW_MPPT_POWER_SF = 'rawMpptPowerSfBase'
    RAW_MPPT_VOLTAGE_SF = 'rawMpptVoltageSfBase'
    MPPT_BAT_POWER = 'mpptBatPower'
    MPPT_MOD_POWER = 'mpptModPower'

    # meter
    MET_AC_FREQUENCY = 'metFrequency'
    MET_AC_POWER = 'metAcPower'  # W
    MET_ENERGY_EXP_TOT = 'metEnergyExpTot'
    MET_ENERGY_IMP_TOT = 'metEnergyImpTot'

    # eflow
    EFLOW_BAT_IN = 'eflowBatIn'
    EFLOW_BAT_OUT = 'eflowBatOut'
    EFLOW_INV_AC_IN = 'eflowInvAcIn'
    EFLOW_INV_AC_OUT = 'eflowInvAcOut'
    EFLOW_INV_DC_IN = 'eflowInvDcIn'
    EFLOW_INV_DC_OUT = 'eflowInvDcOut'
    EFLOW_MOD_OUT = 'eflowModOut'

    # comprehensive
    SELF_CONSUMPTION = 'selfConsumption'  # = -1.0 * (RKEY_INV_AC_POWER + ITEM_MET_AC_POWER)

    @classmethod
    def get_items(cls) -> List[str]:
        items = []

        for attr in dir(cls):
            if attr.startswith("_"):
                continue
            real_attr = getattr(cls, attr)
            if not isinstance(real_attr, str):
                continue
            if callable(real_attr):
                continue
            items.append(attr)

        return items


class FronmodConfig:
    BYTEORDER = Endian.Big

    TICK_COUNTER = 4

    # Common & Inverter Model (ab Seite 29)
    INVERTER_START = 40070  # start pos
    INVERTER_BATCH = MobuBatch(1, "inverter", INVERTER_START, 60, [
        # fronius: 40092 40093 2 R 0x03 W float32 W AC Power value
        # openhab: "WR-Ausgangsleistung  (AC) [%,.0f W]"
        MobuItem(40092 - INVERTER_START, MobuFlag.FLOAT32 | MobuFlag.Q_QUICK, FronmodItem.INV_AC_POWER),
        # fronius: 40102 40103 2 R 0x03 WH float32 Wh AC Lifetime
        # openhab: "valPvInvAcEnergyTot [%,.0f Wh]"
        MobuItem(40102 - INVERTER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, FronmodItem.INV_AC_ENERGY_TOT),
        # fronius: 40108 40109 2 R 0x03 DCW float32 W DC Power value | Total DC power of all available MPPT
        # openhab: "WR-Eingangsleistung (DC) [%,.0f W]
        MobuItem(40108 - INVERTER_START, MobuFlag.FLOAT32 | MobuFlag.Q_QUICK, FronmodItem.INV_DC_POWER),
        # fronius: 40119 40119 1 R 0x03 StVnd enum16 Enumerated Vendor Defined Operating State 2)
        # openhab: Number valPvInvFroniusState   "WR-Fronius-Status [MAP(pv_state_inv_fronius.map):%s]"
        MobuItem(40119 - INVERTER_START, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, FronmodItem.INV_STATE_CODE),

        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.INV_EFFICIENCY),

        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.SELF_CONSUMPTION),

        MobuItem(None, MobuFlag.Q_MEDIUM, FronmodItem.INV_STATE_TEXT),
    ])

    # Basic Storage Control Model (IC124) (ab Seite 52)
    STORAGE_START = 40313
    STORAGE_BATCH = MobuBatch(1, "storage", STORAGE_START, 26, [
        # fronius: 9 9 1 R 0x03 ChaState uint16 % AhrRtg ChaState_SF
        MobuItem(9, MobuFlag.UINT16, FronmodItem.RAW_BAT_FILL_LEVEL),
        # fronius: 23 23 1 R 0x03 0x06 0x10 ChaState_SF sunssf Scale factor for available energy percent.
        MobuItem(23, MobuFlag.INT16, FronmodItem.RAW_BAT_FILL_LEVEL_SF),
        # openhab: Number valPvBatFillState "Batterie-Ladung [%.0f %%]" <battery> (gRawPvMod, gPers5Minutes)
        MobuItem(None, MobuFlag.Q_SLOW, FronmodItem.BAT_FILL_LEVEL),
        # Number valPvBatState "Batterie-Status [MAP(pv_state_batt.map):%s]"
        #  {modbus = "<[storage:11:valueType=uint16]"} // 40303 + 12
        MobuItem(12, MobuFlag.UINT16 | MobuFlag.Q_SLOW, FronmodItem.BAT_STATE_CODE),

        MobuItem(None, MobuFlag.Q_SLOW, FronmodItem.BAT_STATE_TEXT),
    ])

    # Multiple MPPT Inverter Extension Model (I160) (ab Seite 57)
    MPPT_START = 40263
    MPPT_BATCH = MobuBatch(1, "mppt", MPPT_START, 48, [
        # fronius: 4 4 1 R 0x03 DCV_SF sunssf Voltage Scale Factor
        # openhab: Number rawPvMpptVoltageSfBase   "rawPvMpptVoltageSfBase [%d]" {modbus="<[mppt:3:valueType=int16]"}
        MobuItem(4, MobuFlag.INT16, FronmodItem.RAW_MPPT_VOLTAGE_SF),
        # fronius: 5 5 1 R 0x03 DCW_SF sunssf Power Scale Factor
        # openhab: Number rawPvMpptPowerSfBase     "rawPvMpptPowerSfBase [%d]" {modbus="<[mppt:4:valueType=int16]"}
        MobuItem(5, MobuFlag.INT16, FronmodItem.RAW_MPPT_POWER_SF),
        # fronius: 21 21 1 R 0x03 1_DCV uint16 V DCV_SF DC Voltage
        # Number rawPvMpptModVoltage "rawPvMpptModVoltage [%d]"   {modbus="<[mppt:20:valueType=uint16]"}
        MobuItem(21, MobuFlag.UINT16, FronmodItem.RAW_MPPT_MOD_VOLTAGE),
        # fronius: 22 22 1 R 0x03 1_DCW uint16 W DCW_SF DC Power
        # Number rawPvMpptModPower "rawPvMpptModPower [%d]"  {modbus="<[mppt:21:valueType=uint16]"}
        MobuItem(22, MobuFlag.UINT16, FronmodItem.RAW_MPPT_MOD_POWER),
        # fronius: 28 28 1 R 0x03 1_DCSt enum16 Operating State
        # Number valPvMpptModState "MPPT-Modul-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:27]"}
        MobuItem(28, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, FronmodItem.MPPT_MOD_STATE_CODE),
        # fronius: 42 42 1 R 0x03 - 2_DCW - uint16 - W - DCW_SF - DC Power
        # Number rawPvMpptBattPower  "rawPvMpptBattPower [%d]"  {modbus="<[mppt:41:valueType=uint16]"}
        MobuItem(42, MobuFlag.UINT16, FronmodItem.RAW_MPPT_BAT_POWER),
        # fronius: 8 48 1 R 0x03 2_DCSt enum16 Operating State
        # openhab: Number valPvMpptBatState "MPPT-Batterie-Status [MAP(pv_state_mppt.map):%s]" {modbus="<[mppt:47]"}
        MobuItem(48, MobuFlag.INT16 | MobuFlag.Q_MEDIUM, FronmodItem.MPPT_BAT_STATE_CODE),

        MobuItem(None, MobuFlag.NONE, FronmodItem.RAW2_MPPT_BAT_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.MPPT_BAT_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.MPPT_MOD_POWER),
        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.MPPT_MOD_VOLTAGE),
        MobuItem(None, MobuFlag.Q_MEDIUM, FronmodItem.MPPT_BAT_STATE_TEXT),
        MobuItem(None, MobuFlag.Q_MEDIUM, FronmodItem.MPPT_MOD_STATE_TEXT),
    ])

    # Meter Model (ab Seite 62)
    METER_START = 40094  # 40070
    METER_BATCH = MobuBatch(240, "meter", METER_START, 50, [
        # 40096 40097 2 R 0x03 Hz float32 Hz AC Frequency value
        # Number valPvMetAcFrequency   "valPvMetAcFrequency [%.2f]"  {modbus="<[met_40096:0:valueType=float32]"}
        MobuItem(40096 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, FronmodItem.MET_AC_FREQUENCY),
        # 40098 40099 2 R 0x03 W float32 W AC Power value
        # Number valPvMetAcPower  "Netz-Leistung (- Einspeisen) [%,.0f W]"  {modbus="<[met_40098:0:valueType=float32]"}
        MobuItem(40098 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_QUICK, FronmodItem.MET_AC_POWER),
        # 40130 40131 2 R 0x03 TotWhExp float32 Wh Total Watt-hours Exported
        # Number valPvMetEnergyExpTot "valPvMetEnergyExpTot [%d Wh]"   {modbus="<[met_40130:0:valueType=float32]"}
        MobuItem(40130 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, FronmodItem.MET_ENERGY_EXP_TOT),
        # 40138 40139 2 R 0x03 TotWhImp float32 Wh Total Watt-hours Imported
        # Number valPvMetEnergyImpTot    "valPvMetEnergyImpTot [%d Wh]"  {modbus="<[met_40138:0:valueType=float32]"}
        MobuItem(40138 - METER_START, MobuFlag.FLOAT32 | MobuFlag.Q_MEDIUM, FronmodItem.MET_ENERGY_IMP_TOT),

        MobuItem(None, MobuFlag.Q_QUICK, FronmodItem.SELF_CONSUMPTION),
    ])

    @classmethod
    def get_item_keys(cls, delivery: FronmodDelivery) -> Set[str]:
        if delivery == FronmodDelivery.QUICK:
            delivery_flag = MobuFlag.Q_QUICK
        elif delivery == FronmodDelivery.MEDIUM:
            delivery_flag = MobuFlag.Q_MEDIUM
        elif delivery == FronmodDelivery.SLOW:
            delivery_flag = MobuFlag.Q_SLOW
        else:
            raise ValueError("wrong FronmodDelivery type!")

        item_keys = set()

        batches = [cls.INVERTER_BATCH, cls.MPPT_BATCH, cls.STORAGE_BATCH, cls.METER_BATCH]
        for batch in batches:
            for item in batch.items:
                if item.flags & delivery_flag:
                    item_keys.add(item.name)

        return item_keys

    @classmethod
    def list_items(cls, delivery: FronmodDelivery) -> str:
        item_set = cls.get_item_keys(delivery)
        item_list = list(item_set)
        item_list.sort()
        return ", ".join(item_list)

    @classmethod
    def format_inv_sun_spec_state(cls, code: int) -> str:
        """former: pv_state_inv_sunspec.map"""
        if code is None:
            return None

        text = f"({code}) "
        if code == 1:
            text += "OFF"
        elif code == 2:
            text += "AUTO-SHUTDOWN"
        elif code == 3:
            text += "RUN-UP"
        elif code == 4:
            text += "NORMAL"
        elif code == 5:
            text += "POWER REDUCTION"
        elif code == 6:
            text += "SWITCH-OFF"
        elif code == 7:
            text += "ERROR"
        elif code == 8:
            text += "STANDBY"
        else:
            text += "?"
        return text

    @classmethod
    def format_inv_fronius_state(cls, code: int) -> str:
        """former: pv_state_inv_fronius.map"""
        if code is None:
            return None

        if 1 <= code <= 8:
            return cls.format_inv_sun_spec_state(code)

        text = f"({code}) "
        if code == 9:
            text += "NO SOLARNET COMMUNICATION"
        elif code == 10:
            text += "NO COMMUNICATION"
        elif code == 11:
            text += "OVER-CURRENT SOLARNET SOCKET"
        elif code == 12:
            text += "UPDATE"
        elif code == 13:
            text += "AFCI EVENT (ARC)"
        else:
            text += "?"
        return text

    @classmethod
    def format_bat_state(cls, code: int) -> str:
        """former: pv_state_batt.map"""
        if code is None:
            return None

        text = f"({code}) "
        if code == 1:
            text += "OFF"
        elif code == 2:
            text += "EMPTY"
        elif code == 3:
            text += "DISCHARGE"
        elif code == 4:
            text += "CHARGING"
        elif code == 5:
            text += "FULL"
        elif code == 6:
            text += "HOLDING"
        elif code == 7:
            text += "TESTING"
        else:
            text += "?"
        return text

    @classmethod
    def format_mptt_state(cls, code: int) -> str:
        """former: pv_state_mppt.map"""
        if code is None:
            return None

        text = f"({code}) "
        if code == 1:
            text += "OFF"
        elif code == 2:
            text += "IN OPERATION (NO FEED-IN)"
        elif code == 3:
            text += "RUN-UP"
        elif code == 4:
            text += "NORMAL"
        elif code == 5:
            text += "POWER REDUCTION"
        elif code == 6:
            text += "SWITCH-OFF"
        elif code == 7:
            text += "ERROR"
        elif code == 8:
            text += "STANDBY"
        elif code == 65535:
            text += "(0xFFFF) ?"
        else:
            text += "?"
        return text
