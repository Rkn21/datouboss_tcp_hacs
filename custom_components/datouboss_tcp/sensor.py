"""Sensor platform for Datouboss TCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfFrequency, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN
from .coordinator import DatoubossRuntimeData


@dataclass(frozen=True, kw_only=True)
class DatoubossSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


SENSORS: tuple[DatoubossSensorDescription, ...] = (
    DatoubossSensorDescription(
        key="mode",
        translation_key="mode",
        icon="mdi:transmission-tower",
        value_fn=lambda data: data["qmod"].get("state"),
        attributes_fn=lambda data: {"code": data["qmod"].get("code")},
    ),
    DatoubossSensorDescription(
        key="serial_number",
        translation_key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
        value_fn=lambda data: data.get("qid"),
    ),
    DatoubossSensorDescription(
        key="grid_voltage",
        translation_key="grid_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("grid_voltage"),
    ),
    DatoubossSensorDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("grid_frequency"),
    ),
    DatoubossSensorDescription(
        key="output_voltage",
        translation_key="output_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("output_voltage"),
    ),
    DatoubossSensorDescription(
        key="output_frequency",
        translation_key="output_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("output_frequency"),
    ),
    DatoubossSensorDescription(
        key="output_apparent_power",
        translation_key="output_apparent_power",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        value_fn=lambda data: data["qpigs"].get("output_apparent_power"),
    ),
    DatoubossSensorDescription(
        key="output_active_power",
        translation_key="output_active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("output_active_power"),
    ),
    DatoubossSensorDescription(
        key="load_percent",
        translation_key="load_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda data: data["qpigs"].get("load_percent"),
    ),
    DatoubossSensorDescription(
        key="bus_voltage",
        translation_key="bus_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("bus_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("battery_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_charging_current",
        translation_key="battery_charging_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("battery_charging_current"),
    ),
    DatoubossSensorDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-medium",
        value_fn=lambda data: data["qpigs"].get("battery_capacity"),
    ),
    DatoubossSensorDescription(
        key="battery_discharge_current",
        translation_key="battery_discharge_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("battery_discharge_current"),
    ),
    DatoubossSensorDescription(
        key="heatsink_temperature",
        translation_key="heatsink_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("heatsink_temperature"),
    ),
    DatoubossSensorDescription(
        key="pv_battery_current",
        translation_key="pv_battery_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("pv_battery_current"),
    ),
    DatoubossSensorDescription(
        key="pv_input_voltage",
        translation_key="pv_input_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("pv_input_voltage"),
    ),
    DatoubossSensorDescription(
        key="scc_battery_voltage",
        translation_key="scc_battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("scc_battery_voltage"),
    ),
    DatoubossSensorDescription(
        key="pv_output_power",
        translation_key="pv_output_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["qpigs"].get("pv_output_power"),
    ),
    DatoubossSensorDescription(
        key="device_status_bits",
        translation_key="device_status_bits",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:dip-switch",
        value_fn=lambda data: data["qpigs"].get("device_status_bits"),
    ),
    DatoubossSensorDescription(
        key="device_status_bits_2",
        translation_key="device_status_bits_2",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:dip-switch",
        value_fn=lambda data: data["qpigs"].get("device_status_bits_2"),
    ),
    DatoubossSensorDescription(
        key="fan_offset",
        translation_key="fan_offset",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:fan",
        value_fn=lambda data: data["qpigs"].get("fan_offset"),
    ),
    DatoubossSensorDescription(
        key="eeprom_version",
        translation_key="eeprom_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn=lambda data: data["qpigs"].get("eeprom_version"),
    ),
    DatoubossSensorDescription(
        key="warnings_bitfield",
        translation_key="warnings_bitfield",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-outline",
        value_fn=lambda data: data["qpiws"].get("bitfield"),
        attributes_fn=lambda data: {
            "active_indexes": data["qpiws"].get("active_indexes", [])
        },
    ),
    DatoubossSensorDescription(
        key="grid_rating_voltage",
        translation_key="grid_rating_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("grid_rating_voltage"),
    ),
    DatoubossSensorDescription(
        key="grid_rating_current",
        translation_key="grid_rating_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("grid_rating_current"),
    ),
    DatoubossSensorDescription(
        key="ac_output_rating_voltage",
        translation_key="ac_output_rating_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("ac_output_rating_voltage"),
    ),
    DatoubossSensorDescription(
        key="ac_output_rating_frequency",
        translation_key="ac_output_rating_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("ac_output_rating_frequency"),
    ),
    DatoubossSensorDescription(
        key="ac_output_rating_current",
        translation_key="ac_output_rating_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("ac_output_rating_current"),
    ),
    DatoubossSensorDescription(
        key="ac_output_rating_apparent_power",
        translation_key="ac_output_rating_apparent_power",
        native_unit_of_measurement="VA",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:flash",
        value_fn=lambda data: data["qpiri"].get("ac_output_rating_apparent_power"),
    ),
    DatoubossSensorDescription(
        key="ac_output_rating_active_power",
        translation_key="ac_output_rating_active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("ac_output_rating_active_power"),
    ),
    DatoubossSensorDescription(
        key="battery_rating_voltage",
        translation_key="battery_rating_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_rating_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_recharge_voltage",
        translation_key="battery_recharge_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_recharge_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_under_voltage",
        translation_key="battery_under_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_under_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_bulk_voltage",
        translation_key="battery_bulk_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_bulk_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_float_voltage",
        translation_key="battery_float_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_float_voltage"),
    ),
    DatoubossSensorDescription(
        key="battery_type",
        translation_key="battery_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery-cog",
        value_fn=lambda data: data["qpiri"].get("battery_type"),
    ),
    DatoubossSensorDescription(
        key="parallel_max_num",
        translation_key="parallel_max_num",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:call-split",
        value_fn=lambda data: data["qpiri"].get("parallel_max_num"),
    ),
    DatoubossSensorDescription(
        key="machine_type",
        translation_key="machine_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
        value_fn=lambda data: data["qpiri"].get("machine_type"),
    ),
    DatoubossSensorDescription(
        key="topology",
        translation_key="topology",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:sitemap",
        value_fn=lambda data: data["qpiri"].get("topology"),
    ),
    DatoubossSensorDescription(
        key="output_mode",
        translation_key="output_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:export",
        value_fn=lambda data: data["qpiri"].get("output_mode"),
    ),
    DatoubossSensorDescription(
        key="battery_redischarge_voltage",
        translation_key="battery_redischarge_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["qpiri"].get("battery_redischarge_voltage"),
    ),
    DatoubossSensorDescription(
        key="pv_ok_condition",
        translation_key="pv_ok_condition",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:solar-power-variant",
        value_fn=lambda data: data["qpiri"].get("pv_ok_condition"),
    ),
    DatoubossSensorDescription(
        key="qpigs_snapshot",
        translation_key="qpigs_snapshot",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:database-eye",
        value_fn=lambda data: len(data["qpigs"]),
        attributes_fn=lambda data: data["qpigs"],
    ),
    DatoubossSensorDescription(
        key="qpiri_snapshot",
        translation_key="qpiri_snapshot",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:database-eye",
        value_fn=lambda data: len(data["qpiri"]),
        attributes_fn=lambda data: data["qpiri"],
    ),
    DatoubossSensorDescription(
        key="raw_payloads",
        translation_key="raw_payloads",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:code-json",
        value_fn=lambda data: len(data["raw"]),
        attributes_fn=lambda data: data["raw"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Datouboss sensors."""
    runtime: DatoubossRuntimeData = entry.runtime_data
    async_add_entities(
        DatoubossSensor(runtime, entry, description) for description in SENSORS
    )


class DatoubossSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Datouboss sensor."""

    entity_description: DatoubossSensorDescription
    has_entity_name = True

    def __init__(
        self,
        runtime: DatoubossRuntimeData,
        entry: ConfigEntry,
        description: DatoubossSensorDescription,
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
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None
