"""Switch platform for Datouboss TCP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN, QFLAG_COMMANDS
from .coordinator import DatoubossRuntimeData


@dataclass(frozen=True, kw_only=True)
class DatoubossSwitchDescription(SwitchEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]
    turn_on_command_fn: Callable[[dict[str, Any]], str]
    turn_off_command_fn: Callable[[dict[str, Any]], str]
    available_fn: Callable[[dict[str, Any]], bool] | None = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


SWITCHES: tuple[DatoubossSwitchDescription, ...] = (
    DatoubossSwitchDescription(
        key="buzzer_alarm",
        translation_key="buzzer_alarm",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("buzzer_alarm"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["buzzer_alarm"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["buzzer_alarm"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="overload_bypass",
        translation_key="overload_bypass",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("overload_bypass"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["overload_bypass"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["overload_bypass"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="lcd_auto_return",
        translation_key="lcd_auto_return",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("lcd_auto_return"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["lcd_auto_return"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["lcd_auto_return"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="overload_auto_restart",
        translation_key="overload_auto_restart",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("overload_auto_restart"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["overload_auto_restart"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["overload_auto_restart"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="over_temperature_auto_restart",
        translation_key="over_temperature_auto_restart",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("over_temperature_auto_restart"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["over_temperature_auto_restart"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["over_temperature_auto_restart"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="backlight",
        translation_key="backlight",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("backlight"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["backlight"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["backlight"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="primary_source_interrupt_beep",
        translation_key="primary_source_interrupt_beep",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("primary_source_interrupt_beep"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["primary_source_interrupt_beep"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["primary_source_interrupt_beep"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="fault_code_record",
        translation_key="fault_code_record",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qflag"].get("flags", {}).get("fault_code_record"),
        turn_on_command_fn=lambda data: QFLAG_COMMANDS["fault_code_record"][0],
        turn_off_command_fn=lambda data: QFLAG_COMMANDS["fault_code_record"][1],
        available_fn=lambda data: bool(data["qflag"].get("flags")),
        attributes_fn=lambda data: data["qflag"],
    ),
    DatoubossSwitchDescription(
        key="battery_equalization",
        translation_key="battery_equalization",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qbeqi"].get("enabled"),
        turn_on_command_fn=lambda data: "PBEQE1",
        turn_off_command_fn=lambda data: "PBEQE0",
        available_fn=lambda data: bool(data["qbeqi"]),
        attributes_fn=lambda data: data["qbeqi"],
    ),
    DatoubossSwitchDescription(
        key="battery_equalization_active_now",
        translation_key="battery_equalization_active_now",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data["qbeqi"].get("active_now"),
        turn_on_command_fn=lambda data: "PBEQA1",
        turn_off_command_fn=lambda data: "PBEQA0",
        available_fn=lambda data: bool(data["qbeqi"]),
        attributes_fn=lambda data: data["qbeqi"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime: DatoubossRuntimeData = entry.runtime_data
    async_add_entities(DatoubossSwitch(runtime, entry, description) for description in SWITCHES)


class DatoubossSwitch(CoordinatorEntity, SwitchEntity):
    entity_description: DatoubossSwitchDescription
    has_entity_name = True

    def __init__(self, runtime: DatoubossRuntimeData, entry: ConfigEntry, description: DatoubossSwitchDescription) -> None:
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
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        if self.entity_description.available_fn is None:
            return super().available
        return super().available and self.entity_description.available_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.turn_on_command_fn(self.coordinator.data)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.turn_off_command_fn(self.coordinator.data)
        )