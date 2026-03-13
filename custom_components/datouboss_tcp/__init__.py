"""Datouboss TCP integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .client import DatoubossError, DatoubossTcpClient
from .const import (
    AC_INPUT_RANGE_MAP,
    ATTR_AMPS,
    ATTR_COMMAND,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DAYS,
    ATTR_ENABLED,
    ATTR_EXPECT_RESPONSE,
    ATTR_MINUTES,
    ATTR_MODE,
    ATTR_REFRESH,
    ATTR_VOLTAGE,
    BATTERY_TYPE_MAP,
    CHARGER_SOURCE_PRIORITY_MAP,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    OUTPUT_FREQUENCY_MAP,
    OUTPUT_SOURCE_PRIORITY_MAP,
    OUTPUT_VOLTAGE_MAP,
    PLATFORMS,
    QFLAG_COMMANDS,
    SERVICE_REFRESH,
    SERVICE_SEND_COMMAND,
    SERVICE_SET_AC_INPUT_RANGE,
    SERVICE_SET_BACKLIGHT,
    SERVICE_SET_BATTERY_BULK_VOLTAGE,
    SERVICE_SET_BATTERY_EQUALIZATION,
    SERVICE_SET_BATTERY_EQUALIZATION_ACTIVE_NOW,
    SERVICE_SET_BATTERY_EQUALIZATION_PERIOD,
    SERVICE_SET_BATTERY_EQUALIZATION_TIME,
    SERVICE_SET_BATTERY_EQUALIZATION_TIMEOUT,
    SERVICE_SET_BATTERY_EQUALIZATION_VOLTAGE,
    SERVICE_SET_BATTERY_FLOAT_VOLTAGE,
    SERVICE_SET_BATTERY_RECHARGE_VOLTAGE,
    SERVICE_SET_BATTERY_REDISCHARGE_VOLTAGE,
    SERVICE_SET_BATTERY_TYPE,
    SERVICE_SET_BATTERY_UNDER_VOLTAGE,
    SERVICE_SET_BUZZER_ALARM,
    SERVICE_SET_CHARGER_SOURCE_PRIORITY,
    SERVICE_SET_FAULT_CODE_RECORD,
    SERVICE_SET_LCD_AUTO_RETURN,
    SERVICE_SET_MAX_AC_CHARGE_CURRENT,
    SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT,
    SERVICE_SET_OUTPUT_FREQUENCY,
    SERVICE_SET_OUTPUT_SOURCE_PRIORITY,
    SERVICE_SET_OUTPUT_VOLTAGE,
    SERVICE_SET_OVERLOAD_AUTO_RESTART,
    SERVICE_SET_OVERLOAD_BYPASS,
    SERVICE_SET_OVER_TEMPERATURE_AUTO_RESTART,
    SERVICE_SET_PRIMARY_SOURCE_INTERRUPT_BEEP,
)
from .coordinator import DatoubossCoordinator, DatoubossRuntimeData

_LOGGER = logging.getLogger(__name__)

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Optional(ATTR_EXPECT_RESPONSE, default=True): cv.boolean,
        vol.Optional(ATTR_REFRESH, default=False): cv.boolean,
    }
)

REFRESH_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIG_ENTRY_ID): str})

SET_MODE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_CONFIG_ENTRY_ID): str, vol.Required(ATTR_MODE): cv.string}
)

SET_AMPS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_AMPS): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
    }
)

SET_BATTERY_UNDER_VOLTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_VOLTAGE): vol.All(vol.Coerce(float), vol.Range(min=42.0, max=48.0)),
    }
)

SET_ENABLED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_ENABLED): cv.boolean,
    }
)

SET_BATTERY_RECHARGE_VOLTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_VOLTAGE): vol.All(vol.Coerce(float), vol.Range(min=44.0, max=51.0)),
    }
)

SET_BATTERY_REDISCHARGE_VOLTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_VOLTAGE): vol.Any(
            vol.All(vol.Coerce(float), vol.Equal(0.0)),
            vol.All(vol.Coerce(float), vol.Range(min=48.0, max=58.0)),
        ),
    }
)

SET_BATTERY_CHARGE_VOLTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_VOLTAGE): vol.All(vol.Coerce(float), vol.Range(min=48.0, max=58.4)),
    }
)

SET_EQUALIZATION_VOLTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_VOLTAGE): vol.All(vol.Coerce(float), vol.Range(min=48.0, max=61.0)),
    }
)

SET_MINUTES_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
    }
)

SET_DAYS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_DAYS): vol.All(vol.Coerce(int), vol.Range(min=0, max=999)),
    }
)


def _get_loaded_runtime_data(hass: HomeAssistant, config_entry_id: str) -> DatoubossRuntimeData:
    entry = hass.config_entries.async_get_entry(config_entry_id)
    if entry is None:
        raise ServiceValidationError("Config entry not found")
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError("Config entry is not loaded")
    return cast(DatoubossRuntimeData, entry.runtime_data)


def _require_user_battery(runtime: DatoubossRuntimeData) -> None:
    if runtime.coordinator.data["qpiri"].get("battery_type") != "user":
        raise ServiceValidationError(
            "This setting can only be changed when battery type is set to user"
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Datouboss TCP services."""

    def build_toggle_service(on_command: str, off_command: str):
        async def async_toggle(call: ServiceCall) -> ServiceResponse:
            runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
            enabled = bool(call.data[ATTR_ENABLED])
            payload = await runtime.coordinator.async_send_write_command(
                on_command if enabled else off_command
            )
            return {"payload": payload, "enabled": enabled}

        return async_toggle

    def build_mode_service(
        mapping: dict[str, str],
        command_prefix: str = "",
        *,
        formatter: callable | None = None,
    ):
        async def async_set_mode(call: ServiceCall) -> ServiceResponse:
            runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
            mode = call.data[ATTR_MODE]
            if mode not in mapping:
                raise ServiceValidationError(
                    f"Invalid mode '{mode}'. Valid values: {', '.join(mapping)}"
                )
            command_value = mapping[mode]
            command = formatter(mode, command_value) if formatter else f"{command_prefix}{command_value}"
            payload = await runtime.coordinator.async_send_write_command(command)
            return {"payload": payload, "mode": mode}

        return async_set_mode

    def build_voltage_service(
        command_template: str,
        *,
        require_user_battery: bool = False,
    ):
        async def async_set_voltage(call: ServiceCall) -> ServiceResponse:
            runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
            if require_user_battery:
                _require_user_battery(runtime)
            voltage = round(float(call.data[ATTR_VOLTAGE]), 1)
            payload = await runtime.coordinator.async_send_write_command(
                command_template.format(voltage=voltage)
            )
            return {"payload": payload, "voltage": voltage}

        return async_set_voltage

    def build_integer_service(attr_name: str, command_template: str, response_key: str):
        async def async_set_integer(call: ServiceCall) -> ServiceResponse:
            runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
            value = int(call.data[attr_name])
            payload = await runtime.coordinator.async_send_write_command(
                command_template.format(value=value)
            )
            return {"payload": payload, response_key: value}

        return async_set_integer

    async def async_send_command(call: ServiceCall) -> ServiceResponse | None:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        result = await runtime.coordinator.async_send_raw_command(
            call.data[ATTR_COMMAND],
            expect_response=call.data[ATTR_EXPECT_RESPONSE],
            refresh=call.data[ATTR_REFRESH],
        )
        if call.return_response:
            return result
        return None

    async def async_refresh(call: ServiceCall) -> ServiceResponse:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        await runtime.coordinator.async_refresh()
        return {"refreshed": True}

    async_set_output_source_priority = build_mode_service(
        OUTPUT_SOURCE_PRIORITY_MAP,
        "POP",
    )
    async_set_charger_source_priority = build_mode_service(
        CHARGER_SOURCE_PRIORITY_MAP,
        "PCP",
    )
    async_set_ac_input_range = build_mode_service(AC_INPUT_RANGE_MAP, "PGR")
    async_set_battery_type = build_mode_service(BATTERY_TYPE_MAP, "PBT")
    async_set_output_voltage = build_mode_service(
        OUTPUT_VOLTAGE_MAP,
        formatter=lambda mode, command: command,
    )
    async_set_output_frequency = build_mode_service(
        OUTPUT_FREQUENCY_MAP,
        formatter=lambda mode, command: command,
    )

    async def async_set_max_ac_charge_current(call: ServiceCall) -> ServiceResponse:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        amps = int(call.data[ATTR_AMPS])
        payload = await runtime.coordinator.async_send_write_command(f"MUCHGC{amps:03d}")
        return {"payload": payload, "amps": amps}

    async def async_set_max_total_charge_current(call: ServiceCall) -> ServiceResponse:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        amps = int(call.data[ATTR_AMPS])
        payload = await runtime.coordinator.async_send_write_command(f"MCHGC{amps:03d}")
        return {"payload": payload, "amps": amps}

    async_set_battery_under_voltage = build_voltage_service(
        "PSDV{voltage:.1f}",
        require_user_battery=True,
    )
    async_set_battery_recharge_voltage = build_voltage_service(
        "PBCV{voltage:.1f}",
        require_user_battery=True,
    )
    async_set_battery_redischarge_voltage = build_voltage_service(
        "PBDV{voltage:.1f}",
        require_user_battery=True,
    )
    async_set_battery_bulk_voltage = build_voltage_service(
        "PCVV{voltage:.1f}",
        require_user_battery=True,
    )
    async_set_battery_float_voltage = build_voltage_service(
        "PBFT{voltage:.1f}",
        require_user_battery=True,
    )
    async_set_battery_equalization_voltage = build_voltage_service("PBEQV{voltage:.2f}")

    async_set_battery_equalization_time = build_integer_service(
        ATTR_MINUTES,
        "PBEQT{value:03d}",
        "minutes",
    )
    async_set_battery_equalization_timeout = build_integer_service(
        ATTR_MINUTES,
        "PBEQOT{value:03d}",
        "minutes",
    )
    async_set_battery_equalization_period = build_integer_service(
        ATTR_DAYS,
        "PBEQP{value:03d}",
        "days",
    )

    async_set_buzzer_alarm = build_toggle_service(*QFLAG_COMMANDS["buzzer_alarm"])
    async_set_overload_bypass = build_toggle_service(*QFLAG_COMMANDS["overload_bypass"])
    async_set_lcd_auto_return = build_toggle_service(*QFLAG_COMMANDS["lcd_auto_return"])
    async_set_overload_auto_restart = build_toggle_service(*QFLAG_COMMANDS["overload_auto_restart"])
    async_set_over_temperature_auto_restart = build_toggle_service(
        *QFLAG_COMMANDS["over_temperature_auto_restart"]
    )
    async_set_backlight = build_toggle_service(*QFLAG_COMMANDS["backlight"])
    async_set_primary_source_interrupt_beep = build_toggle_service(
        *QFLAG_COMMANDS["primary_source_interrupt_beep"]
    )
    async_set_fault_code_record = build_toggle_service(*QFLAG_COMMANDS["fault_code_record"])
    async_set_battery_equalization = build_toggle_service("PBEQE1", "PBEQE0")
    async_set_battery_equalization_active_now = build_toggle_service("PBEQA1", "PBEQA0")

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            async_send_command,
            schema=SEND_COMMAND_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            async_refresh,
            schema=REFRESH_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_OUTPUT_SOURCE_PRIORITY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_OUTPUT_SOURCE_PRIORITY,
            async_set_output_source_priority,
            schema=SET_MODE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CHARGER_SOURCE_PRIORITY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CHARGER_SOURCE_PRIORITY,
            async_set_charger_source_priority,
            schema=SET_MODE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_AC_INPUT_RANGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_AC_INPUT_RANGE,
            async_set_ac_input_range,
            schema=SET_MODE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_MAX_AC_CHARGE_CURRENT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_MAX_AC_CHARGE_CURRENT,
            async_set_max_ac_charge_current,
            schema=SET_AMPS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT,
            async_set_max_total_charge_current,
            schema=SET_AMPS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BATTERY_UNDER_VOLTAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BATTERY_UNDER_VOLTAGE,
            async_set_battery_under_voltage,
            schema=SET_BATTERY_UNDER_VOLTAGE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    mode_services = (
        (SERVICE_SET_BATTERY_TYPE, async_set_battery_type),
        (SERVICE_SET_OUTPUT_VOLTAGE, async_set_output_voltage),
        (SERVICE_SET_OUTPUT_FREQUENCY, async_set_output_frequency),
    )
    for service_name, handler in mode_services:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(
                DOMAIN,
                service_name,
                handler,
                schema=SET_MODE_SCHEMA,
                supports_response=SupportsResponse.ONLY,
            )

    enabled_services = (
        (SERVICE_SET_BUZZER_ALARM, async_set_buzzer_alarm),
        (SERVICE_SET_OVERLOAD_BYPASS, async_set_overload_bypass),
        (SERVICE_SET_LCD_AUTO_RETURN, async_set_lcd_auto_return),
        (SERVICE_SET_OVERLOAD_AUTO_RESTART, async_set_overload_auto_restart),
        (SERVICE_SET_OVER_TEMPERATURE_AUTO_RESTART, async_set_over_temperature_auto_restart),
        (SERVICE_SET_BACKLIGHT, async_set_backlight),
        (SERVICE_SET_PRIMARY_SOURCE_INTERRUPT_BEEP, async_set_primary_source_interrupt_beep),
        (SERVICE_SET_FAULT_CODE_RECORD, async_set_fault_code_record),
        (SERVICE_SET_BATTERY_EQUALIZATION, async_set_battery_equalization),
        (SERVICE_SET_BATTERY_EQUALIZATION_ACTIVE_NOW, async_set_battery_equalization_active_now),
    )
    for service_name, handler in enabled_services:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(
                DOMAIN,
                service_name,
                handler,
                schema=SET_ENABLED_SCHEMA,
                supports_response=SupportsResponse.ONLY,
            )

    voltage_services = (
        (SERVICE_SET_BATTERY_RECHARGE_VOLTAGE, async_set_battery_recharge_voltage, SET_BATTERY_RECHARGE_VOLTAGE_SCHEMA),
        (SERVICE_SET_BATTERY_REDISCHARGE_VOLTAGE, async_set_battery_redischarge_voltage, SET_BATTERY_REDISCHARGE_VOLTAGE_SCHEMA),
        (SERVICE_SET_BATTERY_BULK_VOLTAGE, async_set_battery_bulk_voltage, SET_BATTERY_CHARGE_VOLTAGE_SCHEMA),
        (SERVICE_SET_BATTERY_FLOAT_VOLTAGE, async_set_battery_float_voltage, SET_BATTERY_CHARGE_VOLTAGE_SCHEMA),
        (SERVICE_SET_BATTERY_EQUALIZATION_VOLTAGE, async_set_battery_equalization_voltage, SET_EQUALIZATION_VOLTAGE_SCHEMA),
    )
    for service_name, handler, schema in voltage_services:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(
                DOMAIN,
                service_name,
                handler,
                schema=schema,
                supports_response=SupportsResponse.ONLY,
            )

    minute_services = (
        (SERVICE_SET_BATTERY_EQUALIZATION_TIME, async_set_battery_equalization_time),
        (SERVICE_SET_BATTERY_EQUALIZATION_TIMEOUT, async_set_battery_equalization_timeout),
    )
    for service_name, handler in minute_services:
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(
                DOMAIN,
                service_name,
                handler,
                schema=SET_MINUTES_SCHEMA,
                supports_response=SupportsResponse.ONLY,
            )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BATTERY_EQUALIZATION_PERIOD):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BATTERY_EQUALIZATION_PERIOD,
            async_set_battery_equalization_period,
            schema=SET_DAYS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Datouboss TCP config entry."""
    client = DatoubossTcpClient(
        entry.options.get(CONF_HOST, entry.data[CONF_HOST]),
        entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT)),
        entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
    )
    coordinator = DatoubossCoordinator(
        hass,
        client=client,
        name=entry.title,
        update_interval=timedelta(
            seconds=entry.options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        ),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except DatoubossError as err:
        raise ConfigEntryNotReady(str(err)) from err
    except HomeAssistantError:
        raise
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = DatoubossRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
