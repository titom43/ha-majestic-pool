"""Sensor entities for Majestic Pool."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VALUE_SENSOR_DEFINITIONS, DOMAIN
from .coordinator import MajesticCoordinator

KNOWN_DIAGNOSTIC_COMMANDS: dict[int, str] = {
    0x03: "Program Mode And Shutter Raw",
    0x04: "Light Parameters Raw",
    0x64: "RF Status Raw",
    0x6E: "Warning Raw",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cfg = {**entry.data, **entry.options}
    coordinator: MajesticCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = [MajesticTemperatureSensor(coordinator, entry)]
    for cmd, label in KNOWN_DIAGNOSTIC_COMMANDS.items():
        entities.append(MajesticRawPayloadSensor(coordinator, entry, cmd, label))
    for idx, definition in enumerate(cfg.get(CONF_VALUE_SENSOR_DEFINITIONS, [])):
        entities.append(
            MajesticValueSensor(
                coordinator,
                entry,
                idx,
                str(definition.get("label", f"Value {idx + 1}")),
                int(definition.get("cmd", 0)),
                int(definition.get("index", 0)),
                float(definition.get("scale", 1.0)),
            )
        )
    async_add_entities(entities)


class MajesticTemperatureSensor(CoordinatorEntity[MajesticCoordinator], SensorEntity):
    """Pool temperature sensor."""

    _attr_has_entity_name = True
    _attr_name = "Water Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: MajesticCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_temperature"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kuikoto / Soluwatt",
            "model": "Majestic Controller",
        }

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("temperature_c")


class MajesticRawPayloadSensor(CoordinatorEntity[MajesticCoordinator], SensorEntity):
    """Raw payload hex for one diagnostic command."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: MajesticCoordinator,
        entry: ConfigEntry,
        cmd: int,
        label: str,
    ) -> None:
        super().__init__(coordinator)
        self._cmd = cmd
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_cmd_{cmd:02x}_raw"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kuikoto / Soluwatt",
            "model": "Majestic Controller",
        }
        self._attr_icon = "mdi:code-json"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get(f"cmd_{self._cmd:02x}_payload_hex")


class MajesticValueSensor(CoordinatorEntity[MajesticCoordinator], SensorEntity):
    """Numeric value extracted from a payload byte."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MajesticCoordinator,
        entry: ConfigEntry,
        index: int,
        label: str,
        cmd: int,
        byte_index: int,
        scale: float,
    ) -> None:
        super().__init__(coordinator)
        self._cmd = cmd
        self._byte_index = byte_index
        self._scale = scale
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_value_{index}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kuikoto / Soluwatt",
            "model": "Majestic Controller",
        }
        self._attr_icon = "mdi:gauge"
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(f"cmd_{self._cmd:02x}_payload_hex")
        if not isinstance(raw, str) or len(raw) < (self._byte_index + 1) * 2:
            return None
        try:
            payload = bytes.fromhex(raw)
        except ValueError:
            return None
        if self._byte_index < 0 or self._byte_index >= len(payload):
            return None
        return float(payload[self._byte_index]) * self._scale
