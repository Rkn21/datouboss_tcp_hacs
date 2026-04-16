"""Constants for the Datouboss TCP integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "datouboss_tcp"
PLATFORMS = ["sensor", "select", "binary_sensor", "number", "switch"]

DEFAULT_NAME = "Datouboss Inverter"
DEFAULT_PORT = 8886
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_TIMEOUT = 5
DEFAULT_PROTOCOL = "auto"

CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_SERIAL = "serial"
CONF_PROTOCOL = "protocol_variant"

PROTOCOL_AUTO = "auto"
PROTOCOL_CLASSIC = "classic"
PROTOCOL_VMII = "vmii_max"

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
OUTPUT_SOURCE_PRIORITY_OPTIONS_CLASSIC = list(OUTPUT_SOURCE_PRIORITY_MAP.keys())
OUTPUT_SOURCE_PRIORITY_OPTIONS_VMII = [
    "utility_first",
    "solar_first",
]

CHARGER_SOURCE_PRIORITY_MAP = {
    "utility_first": "00",
    "solar_first": "01",
    "solar_and_utility": "02",
    "solar_only": "03",
}
CHARGER_SOURCE_PRIORITY_REVERSE = {value: key for key, value in CHARGER_SOURCE_PRIORITY_MAP.items()}
CHARGER_SOURCE_PRIORITY_OPTIONS_CLASSIC = list(CHARGER_SOURCE_PRIORITY_MAP.keys())
CHARGER_SOURCE_PRIORITY_OPTIONS_VMII = [
    "utility_first",
    "solar_first",
    "solar_and_utility",
    "solar_only",
]

AC_INPUT_RANGE_MAP = {
    "APL (20ms/90-280 Vac)": "00",
    "UPS (10ms/170-280 Vac)": "01",
}
AC_INPUT_RANGE_REVERSE = {value: key for key, value in AC_INPUT_RANGE_MAP.items()}

BATTERY_TYPE_REVERSE = {
    "0": "agm",
    "1": "flooded",
    "2": "custom",
    "3": "lithium",
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

INVERTER_MODE_MAP = {
    "P": "power_on",
    "S": "standby",
    "L": "line",
    "B": "battery",
    "F": "fault",
    "H": "power_saving",
}

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
