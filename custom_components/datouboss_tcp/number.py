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
    available_fn: Callable[[dict[str, Any]], bool] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


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
        available_fn=lambda data: data["qpiri"].get("battery_type") == "user",
        attributes_fn=lambda data: {
            "battery_type": data["qpiri"].get("battery_type"),
            "battery_type_code": data["qpiri"].get("battery_type_code"),
            "supported_range": [42.0, 48.0],
            "requires_battery_type": "user",
        },
    ),
    DatoubossNumberDescription(
        key="battery_recharge_voltage_setting",
        translation_key="battery_recharge_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=44.0,
        native_max_value=51.0,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qpiri"].get("battery_recharge_voltage"),
        command_fn=lambda value: f"PBCV{value:.1f}",
        available_fn=lambda data: data["qpiri"].get("battery_type") == "user",
    ),
    DatoubossNumberDescription(
        key="battery_redischarge_voltage_setting",
        translation_key="battery_redischarge_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=48.0,
        native_max_value=58.0,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qpiri"].get("battery_redischarge_voltage"),
        command_fn=lambda value: f"PBDV{value:.1f}",
        available_fn=lambda data: data["qpiri"].get("battery_type") == "user",
    ),
    DatoubossNumberDescription(
        key="battery_bulk_voltage_setting",
        translation_key="battery_bulk_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=48.0,
        native_max_value=58.4,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qpiri"].get("battery_bulk_voltage"),
        command_fn=lambda value: f"PCVV{value:.1f}",
        available_fn=lambda data: data["qpiri"].get("battery_type") == "user",
    ),
    DatoubossNumberDescription(
        key="battery_float_voltage_setting",
        translation_key="battery_float_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=48.0,
        native_max_value=58.4,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qpiri"].get("battery_float_voltage"),
        command_fn=lambda value: f"PBFT{value:.1f}",
        available_fn=lambda data: data["qpiri"].get("battery_type") == "user",
    ),
    DatoubossNumberDescription(
        key="battery_equalization_time_setting",
        translation_key="battery_equalization_time_setting",
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=999,
        native_step=1,
        mode=NumberMode.BOX,
        value_fn=lambda data: _to_float_value(data["qbeqi"].get("equalization_time_minutes")),
        command_fn=lambda value: f"PBEQT{int(round(value)):03d}",
        available_fn=lambda data: bool(data["qbeqi"]),
        attributes_fn=lambda data: {"unit": "minutes"},
    ),
    DatoubossNumberDescription(
        key="battery_equalization_period_setting",
        translation_key="battery_equalization_period_setting",
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=999,
        native_step=1,
        mode=NumberMode.BOX,
        value_fn=lambda data: _to_float_value(data["qbeqi"].get("equalization_period_days")),
        command_fn=lambda value: f"PBEQP{int(round(value)):03d}",
        available_fn=lambda data: bool(data["qbeqi"]),
        attributes_fn=lambda data: {"unit": "days"},
    ),
    DatoubossNumberDescription(
        key="battery_equalization_voltage_setting",
        translation_key="battery_equalization_voltage_setting",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=48.0,
        native_max_value=61.0,
        native_step=0.1,
        mode=NumberMode.BOX,
        value_fn=lambda data: data["qbeqi"].get("equalization_voltage"),
        command_fn=lambda value: f"PBEQV{value:.2f}",
        available_fn=lambda data: bool(data["qbeqi"]),
    ),
    DatoubossNumberDescription(
        key="battery_equalization_timeout_setting",
        translation_key="battery_equalization_timeout_setting",
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=999,
        native_step=1,
        mode=NumberMode.BOX,
        value_fn=lambda data: _to_float_value(data["qbeqi"].get("equalization_timeout_minutes")),
        command_fn=lambda value: f"PBEQOT{int(round(value)):03d}",
        available_fn=lambda data: bool(data["qbeqi"]),
        attributes_fn=lambda data: {"unit": "minutes"},
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
        if self.entity_description.available_fn is None:
            return super().available
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.command_fn(value)
        )


def _to_float_value(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)