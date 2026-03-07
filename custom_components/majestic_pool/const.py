"""Constants for the Majestic Pool integration."""

from __future__ import annotations

from homeassistant.const import CONF_ADDRESS as HA_CONF_ADDRESS, Platform

DOMAIN = "majestic_pool"
NAME = "Majestic Pool"

# Backward compatibility for older module imports.
CONF_ADDRESS = HA_CONF_ADDRESS
CONF_POLL_INTERVAL = "poll_interval"
CONF_TEMPERATURE_COMMAND = "temperature_command"
CONF_ACTION_COMMANDS = "action_commands"
CONF_DIAGNOSTIC_COMMANDS = "diagnostic_commands"
CONF_SWITCH_DEFINITIONS = "switch_definitions"
CONF_VALUE_SENSOR_DEFINITIONS = "value_sensor_definitions"
CONF_ENABLE_TEMPERATURE_POLL = "enable_temperature_poll"
CONF_CONNECT_ON_DEMAND = "connect_on_demand"
CONF_ENABLE_PAIRING_PROBE = "enable_pairing_probe"
CONF_PAIRING_TIMEOUT = "pairing_timeout"
CONF_DEVICE_NAME_PREFIX = "device_name_prefix"
CONF_DEBUG_BLE = "debug_ble"

DEFAULT_POLL_INTERVAL = 30
DEFAULT_TEMPERATURE_COMMAND = 0x02
DEFAULT_DIAGNOSTIC_COMMANDS = [0x03, 0x04, 0x64, 0x65, 0x66, 0x6E]
DEFAULT_ENABLE_TEMPERATURE_POLL = True
DEFAULT_CONNECT_ON_DEMAND = True
DEFAULT_ENABLE_PAIRING_PROBE = False
DEFAULT_PAIRING_TIMEOUT = 8
DEFAULT_DEVICE_NAME_PREFIX = "KKTO_"
DEFAULT_DEBUG_BLE = False

# Reverse-engineered defaults from Majestic app (still user-overridable in UI).
DEFAULT_ACTION_COMMANDS = [
    {"label": "Sortie 0x1E ON", "cmd": 0x1E, "payload": "01"},
    {"label": "Sortie 0x1E OFF", "cmd": 0x1E, "payload": "00"},
    {"label": "Sortie 0x06 ON", "cmd": 0x06, "payload": "01"},
    {"label": "Sortie 0x06 OFF", "cmd": 0x06, "payload": "00"},
]

DEFAULT_SWITCH_DEFINITIONS = [
    {"label": "Sortie 0x1E", "on_cmd": 0x1E, "on_payload": "01", "off_cmd": 0x1E, "off_payload": "00"},
    {"label": "Sortie 0x06", "on_cmd": 0x06, "on_payload": "01", "off_cmd": 0x06, "off_payload": "00"},
]

DEFAULT_VALUE_SENSOR_DEFINITIONS = [
    # Command 0x65 appears to carry current-related values; scale is empirical.
    {"label": "Courant pompe", "cmd": 0x65, "index": 0, "scale": 0.1},
    {"label": "Courant booster", "cmd": 0x65, "index": 1, "scale": 0.1},
]

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SWITCH]

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"

ATTR_ENTRY_ID = "entry_id"
ATTR_COMMAND = "command"
ATTR_PAYLOAD = "payload"
