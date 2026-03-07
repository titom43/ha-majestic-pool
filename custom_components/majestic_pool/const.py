"""Constants for the Majestic Pool integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "majestic_pool"
NAME = "Majestic Pool"

CONF_POLL_INTERVAL = "poll_interval"
CONF_TEMPERATURE_COMMAND = "temperature_command"
CONF_ACTION_COMMANDS = "action_commands"
CONF_DIAGNOSTIC_COMMANDS = "diagnostic_commands"

DEFAULT_POLL_INTERVAL = 30
DEFAULT_TEMPERATURE_COMMAND = 0x02
DEFAULT_DIAGNOSTIC_COMMANDS = [0x03, 0x04, 0x64, 0x6E]

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"

ATTR_ENTRY_ID = "entry_id"
ATTR_COMMAND = "command"
ATTR_PAYLOAD = "payload"
