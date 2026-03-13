"""Config flow for Datouboss TCP."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .client import DatoubossError, DatoubossTcpClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    CONF_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


TIMEOUT_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=1,
        max=60,
        step=1,
        mode=selector.NumberSelectorMode.SLIDER,
        unit_of_measurement="s",
    )
)

SCAN_INTERVAL_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=2,
        max=3600,
        step=1,
        mode=selector.NumberSelectorMode.SLIDER,
        unit_of_measurement="s",
    )
)


class DatoubossConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Datouboss TCP."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            timeout = user_input[CONF_TIMEOUT]
            client = DatoubossTcpClient(host, port, timeout)

            try:
                probe = await client.probe()
                serial = probe["serial"] or f"{host}:{port}"
            except DatoubossError:
                _LOGGER.debug("Datouboss probe failed", exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                data = {
                    **user_input,
                    CONF_SERIAL: serial,
                }
                return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): TIMEOUT_SELECTOR,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "DatoubossOptionsFlow":
        return DatoubossOptionsFlow()


class DatoubossOptionsFlow(config_entries.OptionsFlowWithReload):
    """Datouboss options flow."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options_schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
                vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): TIMEOUT_SELECTOR,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema,
                {
                    CONF_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ),
                    CONF_TIMEOUT: self.config_entry.options.get(
                        CONF_TIMEOUT,
                        self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ),
                },
            ),
        )
