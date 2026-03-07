"""Coordinator for Majestic Pool integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONNECT_ON_DEMAND,
    CONF_DIAGNOSTIC_COMMANDS,
    CONF_ENABLE_TEMPERATURE_POLL,
    CONF_POLL_INTERVAL,
    CONF_TEMPERATURE_COMMAND,
    DEFAULT_CONNECT_ON_DEMAND,
    DEFAULT_DIAGNOSTIC_COMMANDS,
    DEFAULT_ENABLE_TEMPERATURE_POLL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TEMPERATURE_COMMAND,
    DOMAIN,
)
from .majestic_ble import MajesticBleHub

_LOGGER = logging.getLogger(__name__)


class MajesticCoordinator(DataUpdateCoordinator[dict[str, float | str | None]]):
    """Fetch data from Majestic controller."""

    def __init__(self, hass: HomeAssistant, hub: MajesticBleHub, config: dict) -> None:
        self.hub = hub
        self._temperature_cmd = int(
            config.get(CONF_TEMPERATURE_COMMAND, DEFAULT_TEMPERATURE_COMMAND)
        )
        self._enable_temperature_poll = bool(
            config.get(CONF_ENABLE_TEMPERATURE_POLL, DEFAULT_ENABLE_TEMPERATURE_POLL)
        )
        self._connect_on_demand = bool(
            config.get(CONF_CONNECT_ON_DEMAND, DEFAULT_CONNECT_ON_DEMAND)
        )
        diag_cmds = config.get(CONF_DIAGNOSTIC_COMMANDS, DEFAULT_DIAGNOSTIC_COMMANDS)
        self._diagnostic_cmds = [int(v) for v in diag_cmds if 0 <= int(v) <= 255]
        poll_interval = int(config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=(
                timedelta(seconds=max(5, poll_interval))
                if self._enable_temperature_poll
                else None
            ),
        )

    async def _async_update_data(self) -> dict[str, float | str | None]:
        try:
            data: dict[str, float | str | None] = {"temperature_c": None}

            if self._connect_on_demand:
                await self.hub.async_connect()

            try:
                temperature = await self.hub.async_get_temperature(self._temperature_cmd)
                data["temperature_c"] = temperature

                for cmd in self._diagnostic_cmds:
                    try:
                        payload = await self.hub.async_send_command(
                            cmd,
                            b"",
                            expect_response=True,
                            response_timeout=4.0,
                            disconnect_after=False,
                        )
                        data[f"cmd_{cmd:02x}_payload_hex"] = payload.hex() if payload else ""
                    except Exception:  # noqa: BLE001
                        data[f"cmd_{cmd:02x}_payload_hex"] = None
            finally:
                if self._connect_on_demand:
                    await self.hub.async_disconnect()

            return data
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err
