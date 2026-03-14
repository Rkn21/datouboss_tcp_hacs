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
    ATTR_EXPECT_RESPONSE,
    ATTR_MODE,
    ATTR_REFRESH,
    CHARGER_SOURCE_PRIORITY_MAP,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    OUTPUT_SOURCE_PRIORITY_MAP,
    PLATFORMS,
    SERVICE_REFRESH,
    SERVICE_SEND_COMMAND,
    SERVICE_SET_AC_INPUT_RANGE,
    SERVICE_SET_CHARGER_SOURCE_PRIORITY,
    SERVICE_SET_MAX_AC_CHARGE_CURRENT,
    SERVICE_SET_MAX_TOTAL_CHARGE_CURRENT,
    SERVICE_SET_OUTPUT_SOURCE_PRIORITY,
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


def _get_loaded_runtime_data(hass: HomeAssistant, config_entry_id: str) -> DatoubossRuntimeData:
    entry = hass.config_entries.async_get_entry(config_entry_id)
    if entry is None:
        raise ServiceValidationError("Config entry not found")
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError("Config entry is not loaded")
    return cast(DatoubossRuntimeData, entry.runtime_data)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Datouboss TCP services."""

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
