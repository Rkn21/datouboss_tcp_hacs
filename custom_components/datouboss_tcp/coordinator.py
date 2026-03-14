"""Coordinator for Datouboss TCP."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DatoubossConnectionError, DatoubossCommandError, DatoubossError, DatoubossTcpClient
from .const import (
    AC_INPUT_RANGE_REVERSE,
    BATTERY_TYPE_REVERSE,
    CHARGER_SOURCE_PRIORITY_REVERSE,
    INVERTER_MODE_MAP,
    MACHINE_TYPE_REVERSE,
    OUTPUT_SOURCE_PRIORITY_REVERSE,
    OUTPUT_MODE_REVERSE,
    PV_OK_CONDITION_REVERSE,
    TOPOLOGY_REVERSE,
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
        self.write_verify_delay = 1.0

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
        device_status_bits = parts[16] if len(parts) > 16 else None
        device_status_bits_2 = parts[20] if len(parts) > 20 else None
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
            "device_status_bits": device_status_bits,
            "device_status": self._parse_device_status_bits(device_status_bits),
            "fan_offset": parts[17] if len(parts) > 17 else None,
            "eeprom_version": parts[18] if len(parts) > 18 else None,
            "pv_output_power": self._to_int(parts, 19),
            "device_status_bits_2": device_status_bits_2,
            "device_status_2": self._parse_device_status_bits_2(device_status_bits_2),
        }
        return data

    def _parse_qpiri(self, payload: str) -> dict[str, Any]:
        parts = payload.lstrip("(").split()
        battery_type_code = self._normalize_protocol_code(
            parts[12] if len(parts) > 12 else None,
            width=1,
        )
        ac_input_range_code = self._normalize_protocol_code(
            parts[15] if len(parts) > 15 else None,
            width=2,
        )
        output_priority_code = self._normalize_protocol_code(
            parts[16] if len(parts) > 16 else None,
            width=2,
        )
        charge_priority_code = self._normalize_protocol_code(
            parts[17] if len(parts) > 17 else None,
            width=2,
        )
        machine_type_code = self._normalize_protocol_code(
            parts[19] if len(parts) > 19 else None,
            width=2,
        )
        topology_code = self._normalize_protocol_code(
            parts[20] if len(parts) > 20 else None,
            width=1,
        )
        output_mode_code = self._normalize_protocol_code(
            parts[21] if len(parts) > 21 else None,
            width=1,
        )
        pv_ok_condition_code = self._normalize_protocol_code(
            parts[23] if len(parts) > 23 else None,
            width=1,
        )

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
            "battery_type_code": battery_type_code,
            "battery_type": BATTERY_TYPE_REVERSE.get(battery_type_code, battery_type_code),
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
            "machine_type_code": machine_type_code,
            "machine_type": MACHINE_TYPE_REVERSE.get(machine_type_code, machine_type_code),
            "topology_code": topology_code,
            "topology": TOPOLOGY_REVERSE.get(topology_code, topology_code),
            "output_mode_code": output_mode_code,
            "output_mode": OUTPUT_MODE_REVERSE.get(output_mode_code, output_mode_code),
            "battery_redischarge_voltage": self._to_float(parts, 22),
            "pv_ok_condition_code": pv_ok_condition_code,
            "pv_ok_condition": PV_OK_CONDITION_REVERSE.get(
                pv_ok_condition_code, pv_ok_condition_code
            ),
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

    @staticmethod
    def _normalize_protocol_code(code: str | None, *, width: int) -> str | None:
        if code is None:
            return None

        normalized = code.strip()
        if not normalized:
            return None
        if normalized.isdigit():
            return normalized.zfill(width)
        return normalized

    @staticmethod
    def _parse_device_status_bits(bitfield: str | None) -> dict[str, Any] | None:
        if bitfield is None or len(bitfield) < 8:
            return None

        bits = {
            7: bitfield[0],
            6: bitfield[1],
            5: bitfield[2],
            4: bitfield[3],
            3: bitfield[4],
            2: bitfield[5],
            1: bitfield[6],
            0: bitfield[7],
        }
        charge_mode_bits = f"{bits[2]}{bits[1]}{bits[0]}"
        charge_mode_map = {
            "000": "inactive",
            "001": "ac_only",
            "010": "scc_only",
            "011": "scc_and_ac",
            "100": "charge_active_unknown_source",
            "101": "charge_active_ac_only",
            "110": "charge_active_scc_only",
            "111": "charge_active_scc_and_ac",
        }

        return {
            "bitfield": bitfield,
            "output_active": bits[4] == "1",
            "charge_active": bits[2] == "1",
            "scc_charging": bits[1] == "1",
            "ac_charging": bits[0] == "1",
            "charge_mode_bits": charge_mode_bits,
            "charge_mode": charge_mode_map.get(charge_mode_bits, "unknown"),
            "configuration_changed": bits[6] == "1",
            "sbu_priority_flag": bits[7] == "1",
            "flags": {
                "b7": bits[7],
                "b6": bits[6],
                "b5": bits[5],
                "b4": bits[4],
                "b3": bits[3],
                "b2": bits[2],
                "b1": bits[1],
                "b0": bits[0],
            },
        }

    @staticmethod
    def _parse_device_status_bits_2(bitfield: str | None) -> dict[str, Any] | None:
        if bitfield is None or len(bitfield) < 3:
            return None

        bits = {
            10: bitfield[0],
            9: bitfield[1],
            8: bitfield[2],
        }

        return {
            "bitfield": bitfield,
            "floating_mode": bits[10] == "1",
            "switch_on": bits[9] == "1",
            "dustproof_installed": bits[8] == "1",
            "flags": {
                "b10": bits[10],
                "b9": bits[9],
                "b8": bits[8],
            },
        }

    async def async_send_write_command(
        self,
        command: str,
        *,
        verify_applied_fn: Callable[[], bool] | None = None,
    ) -> str:
        """Send a write command and refresh sensors."""
        try:
            response = await self.client.send_command(command)
        except DatoubossConnectionError as err:
            if verify_applied_fn is None or not self._is_response_timeout_error(err):
                raise

            await asyncio.sleep(self.write_verify_delay)
            await self.async_refresh()
            if verify_applied_fn():
                _LOGGER.debug(
                    "Write command %s timed out waiting for an ACK but the new state was verified after refresh",
                    command,
                )
                return ""
            raise

        await self.async_refresh()
        return response.raw_payload

    @staticmethod
    def _is_response_timeout_error(err: DatoubossConnectionError) -> bool:
        return "Timeout while waiting for inverter response" in str(err)

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
