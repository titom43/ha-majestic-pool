"""Switch entities for Majestic Pool."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SWITCH_DEFINITIONS, DOMAIN
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

    entities: list[MajesticGenericSwitch] = []
    for idx, sw in enumerate(cfg.get(CONF_SWITCH_DEFINITIONS, [])):
        entities.append(
            MajesticGenericSwitch(
                coordinator=coordinator,
                hub=hub,
                entry=entry,
                unique_suffix=f"switch_{idx}",
                label=str(sw.get("label", f"Switch {idx + 1}")),
                on_cmd=int(sw.get("on_cmd", 0)),
                on_payload=bytes.fromhex(str(sw.get("on_payload", ""))),
                off_cmd=int(sw.get("off_cmd", 0)),
                off_payload=bytes.fromhex(str(sw.get("off_payload", ""))),
                state_cmd=int(sw["state_cmd"]) if sw.get("state_cmd") is not None else None,
                on_value=(str(sw["on_value"]).lower() if sw.get("on_value") else None),
            )
        )

    async_add_entities(entities)


class MajesticGenericSwitch(CoordinatorEntity[MajesticCoordinator], SwitchEntity):
    """Configurable switch mapped to BLE commands."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MajesticCoordinator,
        hub: MajesticBleHub,
        entry: ConfigEntry,
        unique_suffix: str,
        label: str,
        on_cmd: int,
        on_payload: bytes,
        off_cmd: int,
        off_payload: bytes,
        state_cmd: int | None,
        on_value: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._on_cmd = on_cmd
        self._on_payload = on_payload
        self._off_cmd = off_cmd
        self._off_payload = off_payload
        self._state_cmd = state_cmd
        self._on_value = on_value
        self._is_on_internal = False

        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kuikoto / Soluwatt",
            "model": "Majestic Controller",
        }

    @property
    def assumed_state(self) -> bool:
        return self._state_cmd is None or self._on_value is None

    @property
    def is_on(self) -> bool:
        if self._state_cmd is not None and self._on_value:
            raw = self.coordinator.data.get(f"cmd_{self._state_cmd:02x}_payload_hex")
            if isinstance(raw, str):
                return self._on_value in raw.lower()
        return self._is_on_internal

    async def async_turn_on(self, **kwargs) -> None:
        await self._hub.async_send_command(self._on_cmd, self._on_payload, expect_response=False)
        self._is_on_internal = True
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._hub.async_send_command(
            self._off_cmd,
            self._off_payload,
            expect_response=False,
        )
        self._is_on_internal = False
        await self.coordinator.async_request_refresh()
