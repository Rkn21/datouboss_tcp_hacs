"""Number platform for Datouboss TCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN
from .coordinator import DatoubossRuntimeData


@dataclass(frozen=True, kw_only=True)
class DatoubossNumberDescription(NumberEntityDescription):
    value_fn: Callable[[dict[str, Any]], float | None]
    command_fn: Callable[[float], str]


NUMBERS: tuple[DatoubossNumberDescription, ...] = (
    DatoubossNumberDescription(
        key="battery_under_voltage_setting",
        translation_key="battery_under_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=42.0,
        native_max_value=48.0,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qpiri"].get("battery_under_voltage"),
        command_fn=lambda value: f"PSDV{value:.1f}",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Datouboss numbers."""
    runtime: DatoubossRuntimeData = entry.runtime_data
    async_add_entities(
        DatoubossNumber(runtime, entry, description) for description in NUMBERS
    )


class DatoubossNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Datouboss writable number."""

    entity_description: DatoubossNumberDescription
    has_entity_name = True

    def __init__(
        self,
        runtime: DatoubossRuntimeData,
        entry: ConfigEntry,
        description: DatoubossNumberDescription,
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
    def native_value(self) -> float | None:
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None:
            return None
        return float(value)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data["qpiri"].get("battery_type") == "user"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {
            "battery_type": self.coordinator.data["qpiri"].get("battery_type"),
            "battery_type_code": self.coordinator.data["qpiri"].get("battery_type_code"),
            "supported_range": [42.0, 48.0],
            "requires_battery_type": "user",
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.command_fn(value)
        )