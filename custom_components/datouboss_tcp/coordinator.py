"""Coordinator for Datouboss TCP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DatoubossCommandError, DatoubossError, DatoubossTcpClient
from .const import (
    AC_INPUT_RANGE_REVERSE,
    CHARGER_SOURCE_PRIORITY_REVERSE,
    INVERTER_MODE_MAP,
    OUTPUT_SOURCE_PRIORITY_REVERSE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DatoubossRuntimeData:
    """Runtime data stored on the config entry."""

    client: DatoubossTcpClient
    coordinator: "DatoubossCoordinator"


class DatoubossCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Datouboss polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: DatoubossTcpClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.client = client
        self.serial: str | None = None
        self.supported_total_charge_currents: list[int] = []
        self.supported_ac_charge_currents: list[int] = []

    async def _async_setup(self) -> None:
        """Fetch static-ish data once."""
        probe = await self.client.probe()
        self.serial = str(probe["serial"])

        try:
            self.supported_total_charge_currents = await self.client.fetch_supported_currents(
                "QMCHGCR"
            )
        except DatoubossError:
            _LOGGER.debug("QMCHGCR not supported by this inverter", exc_info=True)
            self.supported_total_charge_currents = []

        try:
            self.supported_ac_charge_currents = await self.client.fetch_supported_currents(
                "QMUCHGCR"
            )
        except DatoubossError:
            _LOGGER.debug("QMUCHGCR not supported by this inverter", exc_info=True)
            self.supported_ac_charge_currents = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the inverter."""
        try:
            qmod = await self.client.send_command("QMOD")
            qid = await self.client.send_command("QID")
            qpigs = await self.client.send_command("QPIGS")
            qpiri = await self.client.send_command("QPIRI")
            qpiws = await self.client.send_command("QPIWS")
        except DatoubossError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "qmod": self._parse_qmod(qmod.raw_payload),
            "qid": qid.raw_payload.lstrip("("),
            "qpigs": self._parse_qpigs(qpigs.raw_payload),
            "qpiri": self._parse_qpiri(qpiri.raw_payload),
            "qpiws": self._parse_qpiws(qpiws.raw_payload),
            "raw": {
                "QMOD": qmod.raw_payload,
                "QID": qid.raw_payload,
                "QPIGS": qpigs.raw_payload,
                "QPIRI": qpiri.raw_payload,
                "QPIWS": qpiws.raw_payload,
            },
        }

    def _parse_qmod(self, payload: str) -> dict[str, Any]:
        code = payload.lstrip("(")[:1]
        return {
            "code": code,
            "state": INVERTER_MODE_MAP.get(code, "unknown"),
        }

    def _parse_qpiws(self, payload: str) -> dict[str, Any]:
        bitfield = payload.lstrip("(")
        active = [idx for idx, value in enumerate(bitfield) if value == "1"]
        return {"bitfield": bitfield, "active_indexes": active}

    def _parse_qpigs(self, payload: str) -> dict[str, Any]:
        parts = payload.lstrip("(").split()
        data: dict[str, Any] = {
            "grid_voltage": self._to_float(parts, 0),
            "grid_frequency": self._to_float(parts, 1),
            "output_voltage": self._to_float(parts, 2),
            "output_frequency": self._to_float(parts, 3),
            "output_apparent_power": self._to_int(parts, 4),
            "output_active_power": self._to_int(parts, 5),
            "load_percent": self._to_int(parts, 6),
            "bus_voltage": self._to_int(parts, 7),
            "battery_voltage": self._to_float(parts, 8),
            "battery_charging_current": self._to_int(parts, 9),
            "battery_capacity": self._to_int(parts, 10),
            "heatsink_temperature": self._to_int(parts, 11),
            "pv_battery_current": self._to_float(parts, 12),
            "pv_input_voltage": self._to_float(parts, 13),
            "scc_battery_voltage": self._to_float(parts, 14),
            "battery_discharge_current": self._to_int(parts, 15),
            "device_status_bits": parts[16] if len(parts) > 16 else None,
            "fan_offset": parts[17] if len(parts) > 17 else None,
            "eeprom_version": parts[18] if len(parts) > 18 else None,
            "pv_output_power": self._to_int(parts, 19),
            "device_status_bits_2": parts[20] if len(parts) > 20 else None,
        }
        return data

    def _parse_qpiri(self, payload: str) -> dict[str, Any]:
        parts = payload.lstrip("(").split()
        output_priority_code = parts[16] if len(parts) > 16 else None
        charge_priority_code = parts[17] if len(parts) > 17 else None
        ac_input_range_code = parts[15] if len(parts) > 15 else None

        data: dict[str, Any] = {
            "grid_rating_voltage": self._to_float(parts, 0),
            "grid_rating_current": self._to_float(parts, 1),
            "ac_output_rating_voltage": self._to_float(parts, 2),
            "ac_output_rating_frequency": self._to_float(parts, 3),
            "ac_output_rating_current": self._to_float(parts, 4),
            "ac_output_rating_apparent_power": self._to_int(parts, 5),
            "ac_output_rating_active_power": self._to_int(parts, 6),
            "battery_rating_voltage": self._to_float(parts, 7),
            "battery_recharge_voltage": self._to_float(parts, 8),
            "battery_under_voltage": self._to_float(parts, 9),
            "battery_bulk_voltage": self._to_float(parts, 10),
            "battery_float_voltage": self._to_float(parts, 11),
            "battery_type": parts[12] if len(parts) > 12 else None,
            "max_ac_charge_current": self._to_int(parts, 13),
            "max_total_charge_current": self._to_int(parts, 14),
            "ac_input_range_code": ac_input_range_code,
            "ac_input_range": AC_INPUT_RANGE_REVERSE.get(ac_input_range_code, ac_input_range_code),
            "output_source_priority_code": output_priority_code,
            "output_source_priority": OUTPUT_SOURCE_PRIORITY_REVERSE.get(
                output_priority_code, output_priority_code
            ),
            "charger_source_priority_code": charge_priority_code,
            "charger_source_priority": CHARGER_SOURCE_PRIORITY_REVERSE.get(
                charge_priority_code, charge_priority_code
            ),
            "parallel_max_num": self._to_int(parts, 18),
            "machine_type": parts[19] if len(parts) > 19 else None,
            "topology": parts[20] if len(parts) > 20 else None,
            "output_mode": parts[21] if len(parts) > 21 else None,
            "battery_redischarge_voltage": self._to_float(parts, 22),
            "pv_ok_condition": parts[23] if len(parts) > 23 else None,
        }
        return data

    @staticmethod
    def _to_float(parts: list[str], index: int) -> float | None:
        try:
            return float(parts[index])
        except (IndexError, ValueError):
            return None

    @staticmethod
    def _to_int(parts: list[str], index: int) -> int | None:
        try:
            return int(parts[index])
        except (IndexError, ValueError):
            return None

    async def async_send_write_command(self, command: str) -> str:
        """Send a write command and refresh sensors."""
        response = await self.client.send_command(command)
        await self.async_refresh()
        return response.raw_payload

    async def async_send_raw_command(
        self,
        command: str,
        *,
        expect_response: bool = True,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Send any raw command and optionally refresh the coordinator."""
        response = await self.client.send_command(command, expect_response=expect_response)
        if refresh:
            await self.async_refresh()
        return {
            "command": command,
            "payload": response.raw_payload,
            "crc_ok": response.crc_ok,
            "raw_frame_hex": response.raw_frame_hex,
        }
