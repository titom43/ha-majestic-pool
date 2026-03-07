"""Constants for the Majestic Pool integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "majestic_pool"
NAME = "Majestic Pool"

CONF_POLL_INTERVAL = "poll_interval"
CONF_TEMPERATURE_COMMAND = "temperature_command"
CONF_ACTION_COMMANDS = "action_commands"
CONF_DIAGNOSTIC_COMMANDS = "diagnostic_commands"
CONF_SWITCH_DEFINITIONS = "switch_definitions"
CONF_VALUE_SENSOR_DEFINITIONS = "value_sensor_definitions"
CONF_ENABLE_TEMPERATURE_POLL = "enable_temperature_poll"
CONF_CONNECT_ON_DEMAND = "connect_on_demand"

DEFAULT_POLL_INTERVAL = 30
DEFAULT_TEMPERATURE_COMMAND = 0x22
DEFAULT_DIAGNOSTIC_COMMANDS = [0x2D, 0x27, 0x03, 0x04, 0x64, 0x6E]
DEFAULT_ENABLE_TEMPERATURE_POLL = True
DEFAULT_CONNECT_ON_DEMAND = True

# Reverse-engineered defaults from Majestic app (still user-overridable in UI).
DEFAULT_ACTION_COMMANDS = [
    {"label": "Projecteur toggle", "cmd": 0x23, "payload": ""},
    {"label": "Pompe manuel", "cmd": 0x35, "payload": ""},
    {"label": "Pompe auto", "cmd": 0x36, "payload": ""},
    {"label": "Pompe boost", "cmd": 0x37, "payload": ""},
]

DEFAULT_SWITCH_DEFINITIONS = [
    # Stateless toggle command.
    {"label": "Projecteur", "on_cmd": 0x23, "on_payload": "", "off_cmd": 0x23, "off_payload": ""},
    # Auto/manual modeled as on/off.
    {"label": "Pompe Auto", "on_cmd": 0x36, "on_payload": "", "off_cmd": 0x35, "off_payload": ""},
]

DEFAULT_VALUE_SENSOR_DEFINITIONS = [
    # Command 0x27 = Pump/Booster currents. Scale is currently empirical.
    {"label": "Courant pompe", "cmd": 0x27, "index": 0, "scale": 0.1},
    {"label": "Courant booster", "cmd": 0x27, "index": 1, "scale": 0.1},
]

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SWITCH]

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"

ATTR_ENTRY_ID = "entry_id"
ATTR_COMMAND = "command"
ATTR_PAYLOAD = "payload"
