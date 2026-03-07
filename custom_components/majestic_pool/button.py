"""Button entities for configured Majestic actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ACTION_COMMANDS, DOMAIN
from .coordinator import MajesticCoordinator
from .majestic_ble import MajesticBleHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    item = hass.data[DOMAIN][entry.entry_id]
    coordinator: MajesticCoordinator = item["coordinator"]
    hub: MajesticBleHub = item["hub"]

    cfg = {**entry.data, **entry.options}
    actions = cfg.get(CONF_ACTION_COMMANDS, [])

    entities: list[MajesticActionButton] = []
    for idx, action in enumerate(actions):
        label = str(action.get("label", f"Action {idx + 1}"))
        cmd = int(action.get("cmd", 0))
        payload = bytes.fromhex(str(action.get("payload", "")))
        entities.append(
            MajesticActionButton(
                coordinator=coordinator,
                hub=hub,
                entry=entry,
                unique_suffix=f"action_{idx}",
                label=label,
                cmd=cmd,
                payload=payload,
            )
        )

    entities.append(
        MajesticActionButton(
            coordinator=coordinator,
            hub=hub,
            entry=entry,
            unique_suffix="refresh",
            label="Refresh",
            cmd=-1,
            payload=b"",
        )
    )

    async_add_entities(entities)


class MajesticActionButton(CoordinatorEntity[MajesticCoordinator], ButtonEntity):
    """Fire-and-forget command button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MajesticCoordinator,
        hub: MajesticBleHub,
        entry: ConfigEntry,
        unique_suffix: str,
        label: str,
        cmd: int,
        payload: bytes,
    ) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._cmd = cmd
        self._payload = payload
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kuikoto / Soluwatt",
            "model": "Majestic Controller",
        }

    async def async_press(self) -> None:
        if self._cmd < 0:
            await self.coordinator.async_request_refresh()
            return

        await self._hub.async_send_command(
            self._cmd,
            self._payload,
            expect_response=False,
        )
        await self.coordinator.async_request_refresh()
