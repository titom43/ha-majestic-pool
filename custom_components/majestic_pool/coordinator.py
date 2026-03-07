"""Coordinator for Majestic Pool integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DIAGNOSTIC_COMMANDS,
    CONF_POLL_INTERVAL,
    CONF_TEMPERATURE_COMMAND,
    DEFAULT_DIAGNOSTIC_COMMANDS,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TEMPERATURE_COMMAND,
    DOMAIN,
)
from .majestic_ble import MajesticBleHub

_LOGGER = logging.getLogger(__name__)


class MajesticCoordinator(DataUpdateCoordinator[dict[str, float | None]]):
    """Fetch data from Majestic controller."""

    def __init__(self, hass: HomeAssistant, hub: MajesticBleHub, config: dict) -> None:
        self.hub = hub
        self._temperature_cmd = int(
            config.get(CONF_TEMPERATURE_COMMAND, DEFAULT_TEMPERATURE_COMMAND)
        )
        diag_cmds = config.get(CONF_DIAGNOSTIC_COMMANDS, DEFAULT_DIAGNOSTIC_COMMANDS)
        self._diagnostic_cmds = [int(v) for v in diag_cmds if 0 <= int(v) <= 255]
        poll_interval = int(config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=max(5, poll_interval)),
        )

    async def _async_update_data(self) -> dict[str, float | None]:
        try:
            temperature = await self.hub.async_get_temperature(self._temperature_cmd)
            data: dict[str, float | str | None] = {"temperature_c": temperature}

            for cmd in self._diagnostic_cmds:
                try:
                    payload = await self.hub.async_send_command(
                        cmd,
                        b"",
                        expect_response=True,
                        response_timeout=4.0,
                    )
                    data[f"cmd_{cmd:02x}_payload_hex"] = payload.hex() if payload else ""
                except Exception:  # noqa: BLE001
                    data[f"cmd_{cmd:02x}_payload_hex"] = None

            return data
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err
