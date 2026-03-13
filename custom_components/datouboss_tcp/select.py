"""Select platform for Datouboss TCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AC_INPUT_RANGE_MAP,
    BATTERY_TYPE_MAP,
    CHARGER_SOURCE_PRIORITY_MAP,
    CONF_SERIAL,
    DOMAIN,
    OUTPUT_FREQUENCY_MAP,
    OUTPUT_SOURCE_PRIORITY_MAP,
    OUTPUT_VOLTAGE_MAP,
)
from .coordinator import DatoubossRuntimeData


@dataclass(frozen=True, kw_only=True)
class DatoubossSelectDescription(SelectEntityDescription):
    current_option_fn: Callable[[Any], str | None]
    command_fn: Callable[[str], str]
    options_fn: Callable[[Any], list[str]]
    attributes_fn: Callable[[Any], dict[str, Any] | None] | None = None
    available_fn: Callable[[Any], bool] | None = None


SELECTS: tuple[DatoubossSelectDescription, ...] = (
    DatoubossSelectDescription(
        key="battery_type_setting",
        translation_key="battery_type_setting",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: coordinator.data["qpiri"].get("battery_type"),
        command_fn=lambda option: f"PBT{BATTERY_TYPE_MAP[option]}",
        options_fn=lambda coordinator: list(BATTERY_TYPE_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "code": coordinator.data["qpiri"].get("battery_type_code"),
            "options": list(BATTERY_TYPE_MAP.keys()),
        },
        available_fn=lambda coordinator: coordinator.data["qpiri"].get("battery_type") in BATTERY_TYPE_MAP,
    ),
    DatoubossSelectDescription(
        key="output_source_priority",
        translation_key="output_source_priority",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: coordinator.data["qpiri"].get("output_source_priority"),
        command_fn=lambda option: f"POP{OUTPUT_SOURCE_PRIORITY_MAP[option]}",
        options_fn=lambda coordinator: list(OUTPUT_SOURCE_PRIORITY_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "code": coordinator.data["qpiri"].get("output_source_priority_code"),
            "options": list(OUTPUT_SOURCE_PRIORITY_MAP.keys()),
        },
    ),
    DatoubossSelectDescription(
        key="charger_source_priority",
        translation_key="charger_source_priority",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: coordinator.data["qpiri"].get("charger_source_priority"),
        command_fn=lambda option: f"PCP{CHARGER_SOURCE_PRIORITY_MAP[option]}",
        options_fn=lambda coordinator: list(CHARGER_SOURCE_PRIORITY_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "code": coordinator.data["qpiri"].get("charger_source_priority_code"),
            "options": list(CHARGER_SOURCE_PRIORITY_MAP.keys()),
        },
    ),
    DatoubossSelectDescription(
        key="output_voltage_setting",
        translation_key="output_voltage_setting",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: _format_integerish_option(
            coordinator.data["qpiri"].get("ac_output_rating_voltage")
        ),
        command_fn=lambda option: OUTPUT_VOLTAGE_MAP[option],
        options_fn=lambda coordinator: list(OUTPUT_VOLTAGE_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "current_voltage": coordinator.data["qpiri"].get("ac_output_rating_voltage"),
        },
    ),
    DatoubossSelectDescription(
        key="output_frequency_setting",
        translation_key="output_frequency_setting",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: _format_integerish_option(
            coordinator.data["qpiri"].get("ac_output_rating_frequency")
        ),
        command_fn=lambda option: OUTPUT_FREQUENCY_MAP[option],
        options_fn=lambda coordinator: list(OUTPUT_FREQUENCY_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "current_frequency": coordinator.data["qpiri"].get("ac_output_rating_frequency"),
        },
    ),
    DatoubossSelectDescription(
        key="ac_input_range",
        translation_key="ac_input_range",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: coordinator.data["qpiri"].get("ac_input_range"),
        command_fn=lambda option: f"PGR{AC_INPUT_RANGE_MAP[option]}",
        options_fn=lambda coordinator: list(AC_INPUT_RANGE_MAP.keys()),
        attributes_fn=lambda coordinator: {
            "code": coordinator.data["qpiri"].get("ac_input_range_code"),
            "options": list(AC_INPUT_RANGE_MAP.keys()),
        },
    ),
    DatoubossSelectDescription(
        key="max_ac_charge_current",
        translation_key="max_ac_charge_current",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: str(coordinator.data["qpiri"].get("max_ac_charge_current")),
        command_fn=lambda option: f"MUCHGC{int(option):03d}",
        options_fn=lambda coordinator: [str(value) for value in (coordinator.supported_ac_charge_currents or [2, 10, 20, 30, 40, 50, 60])],
        attributes_fn=lambda coordinator: {
            "supported_values": coordinator.supported_ac_charge_currents or [2, 10, 20, 30, 40, 50, 60],
        },
    ),
    DatoubossSelectDescription(
        key="max_total_charge_current",
        translation_key="max_total_charge_current",
        entity_category=EntityCategory.CONFIG,
        current_option_fn=lambda coordinator: str(coordinator.data["qpiri"].get("max_total_charge_current")),
        command_fn=lambda option: f"MCHGC{int(option):03d}",
        options_fn=lambda coordinator: [str(value) for value in (coordinator.supported_total_charge_currents or [10, 20, 30, 40, 50, 60, 80, 100])],
        attributes_fn=lambda coordinator: {
            "supported_values": coordinator.supported_total_charge_currents or [10, 20, 30, 40, 50, 60, 80, 100],
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Datouboss selects."""
    runtime: DatoubossRuntimeData = entry.runtime_data
    async_add_entities(
        DatoubossSelect(runtime, entry, description) for description in SELECTS
    )


class DatoubossSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Datouboss writable select."""

    entity_description: DatoubossSelectDescription
    has_entity_name = True

    def __init__(
        self,
        runtime: DatoubossRuntimeData,
        entry: ConfigEntry,
        description: DatoubossSelectDescription,
    ) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self.entity_description = description
        serial = entry.data.get(CONF_SERIAL, entry.entry_id)
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="Datouboss",
            model="Voltronic-compatible inverter",
            name=entry.title,
            serial_number=entry.data.get(CONF_SERIAL),
        )

    @property
    def current_option(self) -> str | None:
        value = self.entity_description.current_option_fn(self.coordinator)
        if value is None:
            return None
        return str(value)

    @property
    def options(self) -> list[str]:
        return self.entity_description.options_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator)
        return None

    @property
    def available(self) -> bool:
        if self.entity_description.available_fn is None:
            return super().available
        return super().available and self.entity_description.available_fn(self.coordinator)

    async def async_select_option(self, option: str) -> None:
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.command_fn(option)
        )


def _format_integerish_option(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value)
