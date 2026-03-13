"""Constants for the Datouboss TCP integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "datouboss_tcp"
PLATFORMS = ["sensor", "select", "binary_sensor", "number", "switch"]

DEFAULT_NAME = "Datouboss Inverter"
DEFAULT_PORT = 8886
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_TIMEOUT = 5

CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_SERIAL = "serial"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_COMMAND = "command"
ATTR_MODE = "mode"
ATTR_AMPS = "amps"
ATTR_DAYS = "days"
ATTR_ENABLED = "enabled"
ATTR_MINUTES = "minutes"
ATTR_VOLTAGE = "voltage"
ATTR_REFRESH = "refresh"
ATTR_EXPECT_RESPONSE = "expect_response"

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"
SERVICE_SET_OUTPUT_SOURCE_PRIORITY = "set_output_source_priority"
SERVICE_SET_CHARGER_SOURCE_PRIORITY = "set_charger_source_priority"
SERVICE_SET_AC_INPUT_RANGE = "set_ac_input_range"
SERVICE_SET_BACKLIGHT = "set_backlight"
SERVICE_SET_BATTERY_BULK_VOLTAGE = "set_battery_bulk_voltage"
SERVICE_SET_BATTERY_EQUALIZATION = "set_battery_equalization"
SERVICE_SET_BATTERY_EQUALIZATION_ACTIVE_NOW = "set_battery_equalization_active_now"
SERVICE_SET_BATTERY_EQUALIZATION_PERIOD = "set_battery_equalization_period"
SERVICE_SET_BATTERY_EQUALIZATION_TIME = "set_battery_equalization_time"
SERVICE_SET_BATTERY_EQUALIZATION_TIMEOUT = "set_battery_equalization_timeout"
SERVICE_SET_BATTERY_EQUALIZATION_VOLTAGE = "set_battery_equalization_voltage"
SERVICE_SET_BATTERY_FLOAT_VOLTAGE = "set_battery_float_voltage"
SERVICE_SET_BATTERY_RECHARGE_VOLTAGE = "set_battery_recharge_voltage"
SERVICE_SET_BATTERY_REDISCHARGE_VOLTAGE = "set_battery_redischarge_voltage"
SERVICE_SET_BATTERY_TYPE = "set_battery_type"
SERVICE_SET_MAX_AC_CHARGE_CURRENT = "set_max_ac_charge_current"
SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT = "set_max_total_charge_current"
SERVICE_SET_BATTERY_UNDER_VOLTAGE = "set_battery_under_voltage"
SERVICE_SET_BUZZER_ALARM = "set_buzzer_alarm"
SERVICE_SET_FAULT_CODE_RECORD = "set_fault_code_record"
SERVICE_SET_LCD_AUTO_RETURN = "set_lcd_auto_return"
SERVICE_SET_OUTPUT_FREQUENCY = "set_output_frequency"
SERVICE_SET_OUTPUT_VOLTAGE = "set_output_voltage"
SERVICE_SET_OVERLOAD_AUTO_RESTART = "set_overload_auto_restart"
SERVICE_SET_OVERLOAD_BYPASS = "set_overload_bypass"
SERVICE_SET_OVER_TEMPERATURE_AUTO_RESTART = "set_over_temperature_auto_restart"
SERVICE_SET_PRIMARY_SOURCE_INTERRUPT_BEEP = "set_primary_source_interrupt_beep"

OUTPUT_SOURCE_PRIORITY_MAP = {
    "utility_first": "00",
    "solar_first": "01",
    "sbu_priority": "02",
}
OUTPUT_SOURCE_PRIORITY_REVERSE = {value: key for key, value in OUTPUT_SOURCE_PRIORITY_MAP.items()}

CHARGER_SOURCE_PRIORITY_MAP = {
    "utility_first": "00",
    "solar_first": "01",
    "solar_and_utility": "02",
    "solar_only": "03",
}
CHARGER_SOURCE_PRIORITY_REVERSE = {value: key for key, value in CHARGER_SOURCE_PRIORITY_MAP.items()}

AC_INPUT_RANGE_MAP = {
    "appliance": "00",
    "ups": "01",
}
AC_INPUT_RANGE_REVERSE = {value: key for key, value in AC_INPUT_RANGE_MAP.items()}

BATTERY_TYPE_REVERSE = {
    "0": "agm",
    "1": "flooded",
    "2": "user",
    "3": "lithium",
}
BATTERY_TYPE_MAP = {
    "agm": "00",
    "flooded": "01",
    "user": "02",
}

MACHINE_TYPE_REVERSE = {
    "00": "grid_tie",
    "01": "off_grid",
    "10": "hybrid",
}

TOPOLOGY_REVERSE = {
    "0": "transformerless",
    "1": "transformer",
}

OUTPUT_MODE_REVERSE = {
    "0": "single_machine",
    "1": "parallel_output",
    "2": "phase_1_of_3_phase",
    "3": "phase_2_of_3_phase",
    "4": "phase_3_of_3_phase",
}

PV_OK_CONDITION_REVERSE = {
    "0": "pv_ok_if_one_inverter_has_pv",
    "1": "pv_ok_if_all_inverters_have_pv",
}

OUTPUT_VOLTAGE_MAP = {
    "220": "V220",
    "230": "V230",
    "240": "V240",
}

OUTPUT_FREQUENCY_MAP = {
    "50": "F50",
    "60": "F60",
}

QFLAG_ENTITY_MAP = {
    "A": "buzzer_alarm",
    "B": "overload_bypass",
    "K": "lcd_auto_return",
    "U": "overload_auto_restart",
    "V": "over_temperature_auto_restart",
    "X": "backlight",
    "Y": "primary_source_interrupt_beep",
    "Z": "fault_code_record",
}

QFLAG_COMMANDS = {
    "buzzer_alarm": ("PEA", "PDA"),
    "overload_bypass": ("PEB", "PDB"),
    "lcd_auto_return": ("PEK", "PDK"),
    "overload_auto_restart": ("PEU", "PDU"),
    "over_temperature_auto_restart": ("PEV", "PDV"),
    "backlight": ("PEX", "PDX"),
    "primary_source_interrupt_beep": ("PEY", "PDY"),
    "fault_code_record": ("PEZ", "PDZ"),
}

INVERTER_MODE_MAP = {
    "P": "power_on",
    "S": "standby",
    "L": "line",
    "B": "battery",
    "F": "fault",
    "H": "power_saving",
}

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
