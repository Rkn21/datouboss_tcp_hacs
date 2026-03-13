"""Binary sensor platform for Datouboss TCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN
from .coordinator import DatoubossRuntimeData


@dataclass(frozen=True, kw_only=True)
class DatoubossBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


BINARY_SENSORS: tuple[DatoubossBinarySensorDescription, ...] = (
    DatoubossBinarySensorDescription(
        key="output_active",
        translation_key="output_active",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: _get_status_value(data, "device_status", "output_active"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="charge_active",
        translation_key="charge_active",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: _get_status_value(data, "device_status", "charge_active"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="scc_charging",
        translation_key="scc_charging",
        value_fn=lambda data: _get_status_value(data, "device_status", "scc_charging"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="ac_charging",
        translation_key="ac_charging",
        value_fn=lambda data: _get_status_value(data, "device_status", "ac_charging"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="configuration_changed",
        translation_key="configuration_changed",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _get_status_value(data, "device_status", "configuration_changed"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="sbu_priority_flag",
        translation_key="sbu_priority_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _get_status_value(data, "device_status", "sbu_priority_flag"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits", "device_status"),
    ),
    DatoubossBinarySensorDescription(
        key="floating_mode",
        translation_key="floating_mode",
        value_fn=lambda data: _get_status_value(data, "device_status_2", "floating_mode"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits_2", "device_status_2"),
    ),
    DatoubossBinarySensorDescription(
        key="switch_on",
        translation_key="switch_on",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: _get_status_value(data, "device_status_2", "switch_on"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits_2", "device_status_2"),
    ),
    DatoubossBinarySensorDescription(
        key="dustproof_installed",
        translation_key="dustproof_installed",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _get_status_value(data, "device_status_2", "dustproof_installed"),
        attributes_fn=lambda data: _get_status_attributes(data, "device_status_bits_2", "device_status_2"),
    ),
)


def _get_status_value(
    data: dict[str, Any],
    status_key: str,
    field_name: str,
) -> bool | None:
    status = data["qpigs"].get(status_key)
    if status is None:
        return None
    value = status.get(field_name)
    if isinstance(value, bool):
        return value
    return None


def _get_status_attributes(
    data: dict[str, Any],
    bitfield_key: str,
    status_key: str,
) -> dict[str, Any] | None:
    status = data["qpigs"].get(status_key)
    if status is None:
        return None
    return {
        "bitfield": data["qpigs"].get(bitfield_key),
        **status,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Datouboss binary sensors."""
    runtime: DatoubossRuntimeData = entry.runtime_data
    async_add_entities(
        DatoubossBinarySensor(runtime, entry, description)
        for description in BINARY_SENSORS
    )


class DatoubossBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Datouboss binary sensor."""

    entity_description: DatoubossBinarySensorDescription
    has_entity_name = True

    def __init__(
        self,
        runtime: DatoubossRuntimeData,
        entry: ConfigEntry,
        description: DatoubossBinarySensorDescription,
    ) -> None:
        super().__init__(runtime.coordinator)
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
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None