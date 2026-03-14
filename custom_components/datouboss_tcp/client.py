"""TCP client for Datouboss / Voltronic-compatible inverters."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)

_CRC_RESERVED_BYTES = {0x28, 0x0D, 0x0A}


class DatoubossError(Exception):
    """Base exception for Datouboss integration."""


class DatoubossConnectionError(DatoubossError):
    """Raised when the TCP connection fails."""


class DatoubossProtocolError(DatoubossError):
    """Raised when the inverter response is malformed."""


class DatoubossCommandError(DatoubossError):
    """Raised when a write command is rejected by the inverter."""


@dataclass(slots=True)
class CommandResponse:
    """Parsed inverter response."""

    command: str
    raw_frame_hex: str
    raw_payload: str
    crc_ok: bool


def _crc_xmodem(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _protocol_crc_bytes(payload: bytes) -> bytes:
    """Return CRC16/XMODEM bytes with Voltronic reserved-byte escaping applied."""
    crc = _crc_xmodem(payload).to_bytes(2, "big")
    return bytes(
        byte + 1 if byte in _CRC_RESERVED_BYTES else byte
        for byte in crc
    )


class DatoubossTcpClient:
    """Minimal TCP client for a transparent serial bridge."""

    def __init__(self, host: str, port: int, timeout: int) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._lock = asyncio.Lock()

    @staticmethod
    def build_frame(command: str) -> bytes:
        """Build a complete inverter frame from an ASCII command."""
        payload = command.encode("ascii")
        crc = _protocol_crc_bytes(payload)
        return payload + crc + b"\r"

    async def send_command(
        self,
        command: str,
        *,
        expect_response: bool = True,
        timeout: int | None = None,
    ) -> CommandResponse:
        """Send a command to the inverter and return the response."""
        frame = self.build_frame(command)
        effective_timeout = timeout or self._timeout

        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self._host, self._port),
                    timeout=effective_timeout,
                )
            except (OSError, TimeoutError) as err:
                raise DatoubossConnectionError(
                    f"Unable to connect to {self._host}:{self._port}"
                ) from err

            try:
                writer.write(frame)
                await asyncio.wait_for(writer.drain(), timeout=effective_timeout)

                if not expect_response:
                    return CommandResponse(
                        command=command,
                        raw_frame_hex=frame.hex(" "),
                        raw_payload="",
                        crc_ok=True,
                    )

                raw = await asyncio.wait_for(reader.readuntil(b"\r"), timeout=effective_timeout)
            except asyncio.IncompleteReadError as err:
                raise DatoubossProtocolError("Incomplete response from inverter") from err
            except asyncio.LimitOverrunError as err:
                raise DatoubossProtocolError("Response too large") from err
            except (OSError, TimeoutError) as err:
                raise DatoubossConnectionError(
                    f"Timeout while waiting for inverter response to {command}"
                ) from err
            finally:
                writer.close()
                await writer.wait_closed()

        if len(raw) < 3 or not raw.endswith(b"\r"):
            raise DatoubossProtocolError("Invalid response terminator")

        payload = raw[:-3]
        rx_crc = int.from_bytes(raw[-3:-1], "big")
        calc_crc = int.from_bytes(_protocol_crc_bytes(payload), "big")
        crc_ok = rx_crc == calc_crc

        payload_text = payload.decode("ascii", errors="replace")
        _LOGGER.debug(
            "Datouboss command=%s tx=%s rx=%s payload=%s crc_ok=%s",
            command,
            frame.hex(" "),
            raw.hex(" "),
            payload_text,
            crc_ok,
        )

        if payload_text.startswith("(NAK"):
            raise DatoubossCommandError(f"Inverter rejected command {command}: {payload_text}")

        return CommandResponse(
            command=command,
            raw_frame_hex=raw.hex(" "),
            raw_payload=payload_text,
            crc_ok=crc_ok,
        )

    async def fetch_supported_currents(self, command: str) -> list[int]:
        """Fetch supported current values from QMCHGCR/QMUCHGCR."""
        response = await self.send_command(command)
        values: list[int] = []
        for chunk in response.raw_payload.lstrip("(").split():
            if chunk.isdigit():
                values.append(int(chunk))
        return values

    async def probe(self) -> dict[str, Any]:
        """Probe the inverter and return basic information."""
        serial = (await self.send_command("QID")).raw_payload.lstrip("(")
        mode = (await self.send_command("QMOD")).raw_payload.lstrip("(")
        return {"serial": serial, "mode": mode}
