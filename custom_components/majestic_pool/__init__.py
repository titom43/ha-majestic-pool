"""Majestic Pool integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    ATTR_PAYLOAD,
    CONF_CONNECT_ON_DEMAND,
    CONF_DEBUG_BLE,
    CONF_DEVICE_NAME_PREFIX,
    CONF_ENABLE_PAIRING_PROBE,
    CONF_ENABLE_TEMPERATURE_POLL,
    CONF_PAIRING_TIMEOUT,
    DEFAULT_ENABLE_PAIRING_PROBE,
    DEFAULT_DEBUG_BLE,
    DEFAULT_PAIRING_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    SERVICE_REFRESH,
    SERVICE_SEND_COMMAND,
)
from .coordinator import MajesticCoordinator
from .majestic_ble import MajesticBleHub


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up integration via UI only."""
    hass.data.setdefault(DOMAIN, {})

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            _make_service_send_command_handler(hass),
            schema=vol.Schema(
                {
                    vol.Optional(ATTR_ENTRY_ID): cv.string,
                    vol.Required(ATTR_COMMAND): vol.All(int, vol.Range(min=0, max=255)),
                    vol.Optional(ATTR_PAYLOAD, default=[]): vol.Any(
                        [vol.All(int, vol.Range(min=0, max=255))],
                        cv.string,
                    ),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            _make_service_refresh_handler(hass),
            schema=vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string}),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one config entry."""
    config = {**entry.data, **entry.options}
    hub = MajesticBleHub(
        config[CONF_ADDRESS],
        enable_pairing_probe=bool(
            config.get(CONF_ENABLE_PAIRING_PROBE, DEFAULT_ENABLE_PAIRING_PROBE)
        ),
        pairing_timeout=float(config.get(CONF_PAIRING_TIMEOUT, DEFAULT_PAIRING_TIMEOUT)),
        device_name_prefix=str(config.get(CONF_DEVICE_NAME_PREFIX, "KKTO_")),
        debug_ble=bool(config.get(CONF_DEBUG_BLE, DEFAULT_DEBUG_BLE)),
    )
    coordinator = MajesticCoordinator(hass, hub, config)

    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
        "config": config,
    }

    if config.get(CONF_ENABLE_TEMPERATURE_POLL, True):
        await coordinator.async_config_entry_first_refresh()
    else:
        coordinator.async_set_updated_data({"temperature_c": None})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    item = hass.data[DOMAIN].pop(entry.entry_id, None)

    if item and (hub := item.get("hub")):
        await hub.async_disconnect()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry after options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _get_target_entry_id(hass: HomeAssistant, call: ServiceCall) -> str:
    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id:
        if entry_id not in hass.data[DOMAIN]:
            raise HomeAssistantError(f"Unknown {DOMAIN} entry_id: {entry_id}")
        return entry_id

    if len(hass.data[DOMAIN]) == 1:
        return next(iter(hass.data[DOMAIN]))

    raise HomeAssistantError(
        "Multiple Majestic entries configured, please provide entry_id"
    )


def _parse_payload(raw: Any) -> bytes:
    if isinstance(raw, str):
        raw = raw.strip()
        return bytes.fromhex(raw) if raw else b""
    if isinstance(raw, list):
        return bytes(int(v) for v in raw)
    raise HomeAssistantError("payload must be hex string or list of bytes")


def _make_service_send_command_handler(hass: HomeAssistant):
    async def _handler(call: ServiceCall) -> None:
        entry_id = _get_target_entry_id(hass, call)
        item = hass.data[DOMAIN][entry_id]
        hub: MajesticBleHub = item["hub"]
        config: dict[str, Any] = item.get("config", {})
        cmd = int(call.data[ATTR_COMMAND])
        payload = _parse_payload(call.data.get(ATTR_PAYLOAD, []))
        await hub.async_send_command(
            cmd,
            payload,
            expect_response=False,
            disconnect_after=bool(config.get(CONF_CONNECT_ON_DEMAND, True)),
        )

    return _handler


def _make_service_refresh_handler(hass: HomeAssistant):
    async def _handler(call: ServiceCall) -> None:
        entry_id = _get_target_entry_id(hass, call)
        coordinator: MajesticCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        await coordinator.async_request_refresh()

    return _handler
