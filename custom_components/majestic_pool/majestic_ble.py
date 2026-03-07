"""BLE client for Majestic pool controller."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from .protocol import decode_packet_ascii, encode_packet_ascii, extract_ascii_frames

_LOGGER = logging.getLogger(__name__)

UUID_SERVICE = "569a1101-b87f-490c-92cb-11ba5ea5167c"
UUID_RX = "569a2000-b87f-490c-92cb-11ba5ea5167c"
UUID_TX = "569a2001-b87f-490c-92cb-11ba5ea5167c"


@dataclass(slots=True)
class MajesticState:
    """Current known data from the controller."""

    temperature_c: float | None = None


class MajesticBleHub:
    """Stateful BLE hub handling transport and commands."""

    def __init__(self, address: str) -> None:
        self.address = address
        self._client: BleakClient | None = None
        self._tx_char: BleakGATTCharacteristic | None = None
        self._rx_char: BleakGATTCharacteristic | None = None
        self._buffer = ""
        self._rx_queue: asyncio.Queue[tuple[int, bytes]] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.state = MajesticState()

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def async_connect(self) -> None:
        """Connect and subscribe to notifications."""
        if self.is_connected:
            return

        client = BleakClient(self.address)
        await client.connect()
        await client.get_services()

        service = client.services.get_service(UUID_SERVICE)
        if service is None:
            await client.disconnect()
            raise RuntimeError(f"Majestic BLE service not found: {UUID_SERVICE}")

        tx_char = service.get_characteristic(UUID_TX)
        rx_char = service.get_characteristic(UUID_RX)
        if tx_char is None or rx_char is None:
            await client.disconnect()
            raise RuntimeError("Majestic TX/RX characteristics not found")

        self._client = client
        self._tx_char = tx_char
        self._rx_char = rx_char
        await client.start_notify(rx_char, self._handle_notification)

    async def async_disconnect(self) -> None:
        """Disconnect the BLE client."""
        if self._client is None:
            return

        try:
            if self._rx_char is not None:
                await self._client.stop_notify(self._rx_char)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Failed stopping notifications", exc_info=True)

        try:
            await self._client.disconnect()
        finally:
            self._client = None
            self._tx_char = None
            self._rx_char = None
            self._buffer = ""

    def _handle_notification(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Process fragmented BLE notifications and push complete frames."""
        chunk = bytes(data).decode("ascii", errors="ignore")
        if not chunk:
            return

        self._buffer += chunk
        frames, rest = extract_ascii_frames(self._buffer)
        self._buffer = rest

        for frame in frames:
            packet = decode_packet_ascii(frame)
            if packet is None:
                continue
            self._rx_queue.put_nowait((packet.cmd, packet.payload))

    async def async_send_command(
        self,
        cmd: int,
        payload: bytes = b"",
        expect_response: bool = True,
        response_timeout: float = 8.0,
    ) -> bytes | None:
        """Send one command and optionally wait matching response by cmd."""
        async with self._lock:
            await self.async_connect()
            assert self._client is not None
            assert self._tx_char is not None

            while not self._rx_queue.empty():
                self._rx_queue.get_nowait()

            encoded = encode_packet_ascii(cmd, payload)
            _LOGGER.debug("Sending cmd=%s payload=%s raw=%s", cmd, payload.hex(), encoded)
            await self._client.write_gatt_char(self._tx_char, encoded, response=True)

            if not expect_response:
                return None

            def _match(item: tuple[int, bytes]) -> bool:
                return item[0] == cmd

            return await self._wait_for(_match, timeout=response_timeout)

    async def _wait_for(
        self, predicate: Callable[[tuple[int, bytes]], bool], timeout: float
    ) -> bytes:
        """Wait for first queue item matching predicate."""
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError("Timeout waiting Majestic BLE response")

            item = await asyncio.wait_for(self._rx_queue.get(), timeout=remaining)
            if predicate(item):
                return item[1]

    async def async_get_temperature(self, cmd: int) -> float | None:
        """Query and decode pool temperature."""
        payload = await self.async_send_command(cmd, b"", expect_response=True)
        if payload is None:
            return None

        value = _decode_temperature(payload)
        self.state.temperature_c = value
        return value


def _decode_temperature(payload: bytes) -> float | None:
    """Heuristic parser for temperature response.

    Known example payload from reverse notes: 000114020000 -> 20C.
    """
    if not payload:
        return None

    candidates = [b for b in payload if 0 <= b <= 60]
    if not candidates:
        return None

    # Prefer plausible water temperature range first.
    plausible = [b for b in candidates if 5 <= b <= 45]
    if plausible:
        return float(max(plausible))

    return float(max(candidates))
