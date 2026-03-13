"""Constants for the Datouboss TCP integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "datouboss_tcp"
PLATFORMS = ["sensor", "select", "binary_sensor"]

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
ATTR_REFRESH = "refresh"
ATTR_EXPECT_RESPONSE = "expect_response"

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"
SERVICE_SET_OUTPUT_SOURCE_PRIORITY = "set_output_source_priority"
SERVICE_SET_CHARGER_SOURCE_PRIORITY = "set_charger_source_priority"
SERVICE_SET_AC_INPUT_RANGE = "set_ac_input_range"
SERVICE_SET_MAX_AC_CHARGE_CURRENT = "set_max_ac_charge_current"
SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT = "set_max_total_charge_current"

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

INVERTER_MODE_MAP = {
    "P": "power_on",
    "S": "standby",
    "L": "line",
    "B": "battery",
    "F": "fault",
    "H": "power_saving",
}

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
