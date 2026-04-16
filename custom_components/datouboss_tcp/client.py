"""TCP client for Datouboss / Voltronic-compatible inverters."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

from .const import DEFAULT_PROTOCOL, PROTOCOL_AUTO, PROTOCOL_CLASSIC, PROTOCOL_VMII

_LOGGER = logging.getLogger(__name__)

_CRC_RESERVED_BYTES = {0x28, 0x0D, 0x0A}
_MODE_CODES = {"P", "S", "L", "B", "F", "D", "H"}


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

    def __init__(
        self,
        host: str,
        port: int,
        timeout: int,
        *,
        protocol_variant: str = DEFAULT_PROTOCOL,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._configured_protocol = protocol_variant
        self._detected_protocol: str | None = None
        self._model_name: str | None = None

    @property
    def protocol_variant(self) -> str:
        if self._configured_protocol != PROTOCOL_AUTO:
            return self._configured_protocol
        return self._detected_protocol or PROTOCOL_CLASSIC

    @property
    def model_name(self) -> str | None:
        return self._model_name

    async def ensure_protocol(self) -> str:
        """Resolve the protocol variant when auto-detection is enabled."""
        if self._configured_protocol != PROTOCOL_AUTO:
            return self._configured_protocol

        if self._detected_protocol is not None:
            return self._detected_protocol

        try:
            model = (await self.send_command("QMN")).raw_payload.lstrip("(").strip()
        except DatoubossError:
            self._detected_protocol = PROTOCOL_CLASSIC
            return self._detected_protocol

        self._model_name = model or None
        self._detected_protocol = (
            PROTOCOL_VMII if model.upper().startswith("VMII-") else PROTOCOL_CLASSIC
        )
        return self._detected_protocol

    @staticmethod
    def build_frame(command: str) -> bytes:
        """Build a complete inverter frame from an ASCII command."""
        payload = command.encode("ascii")
        crc = _protocol_crc_bytes(payload)
        return payload + crc + b"\r"

    @staticmethod
    def _split_frames(raw: bytes) -> list[bytes]:
        frames: list[bytes] = []
        for chunk in raw.split(b"\r"):
            if not chunk:
                continue
            frames.append(chunk + b"\r")
        return frames

    @staticmethod
    def _decode_frame(command: str, raw: bytes) -> CommandResponse | None:
        if len(raw) < 3 or not raw.endswith(b"\r"):
            return None

        payload = raw[:-3]
        rx_crc = int.from_bytes(raw[-3:-1], "big")
        calc_crc = int.from_bytes(_protocol_crc_bytes(payload), "big")
        return CommandResponse(
            command=command,
            raw_frame_hex=raw.hex(" "),
            raw_payload=payload.decode("ascii", errors="replace"),
            crc_ok=rx_crc == calc_crc,
        )

    @staticmethod
    def _payload_tokens(payload: str) -> list[str]:
        return payload.lstrip("(").split()

    @classmethod
    def _looks_like_numeric_list(cls, payload: str) -> bool:
        parts = cls._payload_tokens(payload)
        return len(parts) >= 2 and all(part.isdigit() for part in parts)

    @classmethod
    def _looks_like_status_payload(cls, payload: str) -> bool:
        parts = cls._payload_tokens(payload)
        if len(parts) < 21:
            return False
        try:
            float(parts[0])
            float(parts[1])
            float(parts[2])
            float(parts[3])
            int(parts[4])
            int(parts[5])
            int(parts[6])
            int(parts[7])
            float(parts[8])
            int(parts[9])
            int(parts[10])
            int(parts[11])
            float(parts[12])
            float(parts[13])
            float(parts[14])
            int(parts[15])
        except ValueError:
            return False
        return re.fullmatch(r"[01]{8}", parts[16]) is not None

    @classmethod
    def _looks_like_qpiri_payload(cls, payload: str) -> bool:
        parts = cls._payload_tokens(payload)
        if len(parts) < 24:
            return False
        try:
            float(parts[0])
            float(parts[1])
            float(parts[2])
            float(parts[3])
            float(parts[4])
            int(parts[5])
            int(parts[6])
            float(parts[7])
            float(parts[8])
            float(parts[9])
            float(parts[10])
            float(parts[11])
            int(parts[13])
            int(parts[14])
            int(parts[18])
            float(parts[22])
        except ValueError:
            return False
        return True

    @classmethod
    def _looks_like_qdi_payload(cls, payload: str) -> bool:
        parts = cls._payload_tokens(payload)
        if len(parts) < 25:
            return False
        try:
            float(parts[0])
            float(parts[1])
            int(parts[2])
            float(parts[3])
            float(parts[4])
            float(parts[5])
            float(parts[6])
            int(parts[7])
            for index in range(8, 22):
                int(parts[index])
            float(parts[22])
            int(parts[23])
            int(parts[24])
        except ValueError:
            return False
        return True

    @classmethod
    def _matches_command(cls, command: str, payload: str) -> bool:
        text = payload.lstrip("(").strip()

        if not text:
            return False

        if not command.startswith("Q"):
            return payload.startswith("(ACK") or payload.startswith("(NAK")

        if command == "QMOD":
            return text in _MODE_CODES
        if command in {"QID", "QSID"}:
            return text.isdigit() and len(text) >= 8
        if command == "QPI":
            return text.startswith("PI")
        if command == "QMN":
            return "-" in text and " " not in text
        if command == "QGMN":
            return cls._looks_like_status_payload(payload)
        if command in {"QPIGS", "QPIGS2"}:
            return cls._looks_like_status_payload(payload)
        if command == "QPIRI":
            return cls._looks_like_qpiri_payload(payload)
        if command == "QDI":
            return cls._looks_like_qdi_payload(payload)
        if command == "QPIWS":
            return re.fullmatch(r"[01]{16,64}", text) is not None
        if command in {"QMCHGCR", "QMUCHGCR", "QOPPT", "QCHPT"}:
            return cls._looks_like_numeric_list(payload)
        if command.startswith("QVFW"):
            return text.startswith(command.replace("Q", "VER"))
        if command == "VERFW":
            return text.startswith("VERFW")
        return False

    @classmethod
    def find_matching_response(
        cls,
        command: str,
        responses: list[CommandResponse],
    ) -> CommandResponse | None:
        for response in responses:
            if cls._matches_command(command, response.raw_payload):
                return response
        return None

    @staticmethod
    async def _read_until_idle(
        reader: asyncio.StreamReader,
        *,
        total_timeout: float,
        quiet_timeout: float,
    ) -> bytes:
        chunks: list[bytes] = []
        loop = asyncio.get_running_loop()
        deadline = loop.time() + total_timeout

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break

            wait_for = min(total_timeout if not chunks else quiet_timeout, remaining)
            try:
                data = await asyncio.wait_for(reader.read(4096), timeout=wait_for)
            except TimeoutError:
                break

            if not data:
                break
            chunks.append(data)

        return b"".join(chunks)

    async def _send_and_collect(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> list[CommandResponse]:
        frame = self.build_frame(command)
        effective_timeout = timeout or self._timeout
        quiet_timeout = min(0.2, max(0.05, effective_timeout / 10))
        preflush_timeout = min(0.3, max(0.1, effective_timeout / 8))

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
                stale = await self._read_until_idle(
                    reader,
                    total_timeout=preflush_timeout,
                    quiet_timeout=quiet_timeout,
                )
                if stale:
                    _LOGGER.debug(
                        "Discarded stale Datouboss data before %s: %s",
                        command,
                        stale.hex(" "),
                    )

                writer.write(frame)
                await asyncio.wait_for(writer.drain(), timeout=effective_timeout)

                raw = await self._read_until_idle(
                    reader,
                    total_timeout=effective_timeout,
                    quiet_timeout=quiet_timeout,
                )
            except (OSError, TimeoutError) as err:
                raise DatoubossConnectionError(
                    f"Timeout while waiting for inverter response to {command}"
                ) from err
            finally:
                writer.close()
                await writer.wait_closed()

        responses = [
            decoded
            for raw_frame in self._split_frames(raw)
            if (decoded := self._decode_frame(command, raw_frame)) is not None
        ]

        if responses:
            _LOGGER.debug(
                "Datouboss command=%s tx=%s rx_frames=%s",
                command,
                frame.hex(" "),
                [
                    {
                        "payload": response.raw_payload,
                        "crc_ok": response.crc_ok,
                        "raw": response.raw_frame_hex,
                    }
                    for response in responses
                ],
            )

        return responses

    async def send_command_bundle(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> list[CommandResponse]:
        """Send a command and return every frame received before the line goes idle."""
        responses = await self._send_and_collect(command, timeout=timeout)
        if not responses:
            raise DatoubossProtocolError("No response from inverter")
        return responses

    async def send_command(
        self,
        command: str,
        *,
        expect_response: bool = True,
        timeout: int | None = None,
    ) -> CommandResponse:
        """Send a command to the inverter and return the response."""
        if not expect_response:
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
                finally:
                    writer.close()
                    await writer.wait_closed()

            return CommandResponse(
                command=command,
                raw_frame_hex=frame.hex(" "),
                raw_payload="",
                crc_ok=True,
            )

        responses = await self._send_and_collect(command, timeout=timeout)
        if not responses:
            raise DatoubossProtocolError("No response from inverter")

        response = self.find_matching_response(command, responses)
        if response is None:
            if not command.startswith("Q"):
                raise DatoubossProtocolError(
                    f"No ACK/NAK response received for write command {command}"
                )
            response = responses[0]

        if command == "QMN":
            model = response.raw_payload.lstrip("(").strip()
            self._model_name = model or None
            if self._configured_protocol == PROTOCOL_AUTO and self._detected_protocol is None:
                self._detected_protocol = (
                    PROTOCOL_VMII
                    if model.upper().startswith("VMII-")
                    else PROTOCOL_CLASSIC
                )

        if response.raw_payload.startswith("(NAK"):
            raise DatoubossCommandError(f"Inverter rejected command {command}: {response.raw_payload}")

        return response

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
        await self.ensure_protocol()
        serial_payload = (await self.send_command("QID")).raw_payload.lstrip("(")
        serial = re.sub(r"\D", "", serial_payload) or serial_payload
        mode = (await self.send_command("QMOD")).raw_payload.lstrip("(")
        return {
            "serial": serial,
            "mode": mode,
            "model_name": self._model_name,
            "protocol_variant": self.protocol_variant,
        }
