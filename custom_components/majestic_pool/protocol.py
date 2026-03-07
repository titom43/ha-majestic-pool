"""Majestic BLE packet protocol helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MajesticPacket:
    """Decoded Majestic packet."""

    cmd: int
    payload: bytes


def calc_crc(packet_without_crc: bytes) -> int:
    """Compute protocol CRC.

    CRC = ((sum(bytes) & 0xFF) ^ 0xFF) + 1
    """
    return (((sum(packet_without_crc) & 0xFF) ^ 0xFF) + 1) & 0xFF


def build_packet(cmd: int, payload: bytes = b"") -> bytes:
    """Build raw packet bytes [size, cmd, payload..., crc]."""
    if not 0 <= cmd <= 0xFF:
        raise ValueError("cmd must be in range 0..255")

    body = bytes([0, cmd]) + payload
    size = len(body) + 1
    packet_no_crc = bytes([size]) + body[1:]
    crc = calc_crc(packet_no_crc)
    return packet_no_crc + bytes([crc])


def encode_packet_ascii(cmd: int, payload: bytes = b"") -> bytes:
    """Encode packet to ASCII format used on BLE UART.

    Example: :0302fb
    """
    raw = build_packet(cmd, payload)
    return f":{raw.hex()}".encode("ascii")


def decode_packet_ascii(frame: str) -> MajesticPacket | None:
    """Decode one ASCII frame `:<hex...>` into a packet."""
    if not frame or not frame.startswith(":"):
        return None

    hex_payload = frame[1:]
    if len(hex_payload) % 2 != 0:
        return None

    try:
        raw = bytes.fromhex(hex_payload)
    except ValueError:
        return None

    if len(raw) < 3:
        return None

    size = raw[0]
    if size != len(raw):
        return None

    packet_no_crc = raw[:-1]
    crc = raw[-1]
    if calc_crc(packet_no_crc) != crc:
        return None

    cmd = raw[1]
    payload = raw[2:-1]
    return MajesticPacket(cmd=cmd, payload=payload)


def extract_ascii_frames(buffer: str) -> tuple[list[str], str]:
    """Extract complete `:<hex...>` frames from a running ASCII buffer."""
    frames: list[str] = []

    while True:
        start = buffer.find(":")
        if start < 0:
            return frames, ""
        if start > 0:
            buffer = buffer[start:]

        if len(buffer) < 3:
            return frames, buffer

        size_hex = buffer[1:3]
        try:
            size = int(size_hex, 16)
        except ValueError:
            buffer = buffer[1:]
            continue

        expected_len = 1 + (size * 2)
        if len(buffer) < expected_len:
            return frames, buffer

        frame = buffer[:expected_len]
        frames.append(frame)
        buffer = buffer[expected_len:]
