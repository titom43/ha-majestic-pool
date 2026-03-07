"""Config flow for Majestic Pool."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_ACTION_COMMANDS,
    CONF_CONNECT_ON_DEMAND,
    CONF_DEVICE_NAME_PREFIX,
    CONF_ENABLE_PAIRING_PROBE,
    CONF_DIAGNOSTIC_COMMANDS,
    CONF_ENABLE_TEMPERATURE_POLL,
    CONF_PAIRING_TIMEOUT,
    CONF_POLL_INTERVAL,
    CONF_SWITCH_DEFINITIONS,
    CONF_TEMPERATURE_COMMAND,
    CONF_VALUE_SENSOR_DEFINITIONS,
    DEFAULT_ACTION_COMMANDS,
    DEFAULT_CONNECT_ON_DEMAND,
    DEFAULT_DEVICE_NAME_PREFIX,
    DEFAULT_ENABLE_PAIRING_PROBE,
    DEFAULT_DIAGNOSTIC_COMMANDS,
    DEFAULT_ENABLE_TEMPERATURE_POLL,
    DEFAULT_PAIRING_TIMEOUT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SWITCH_DEFINITIONS,
    DEFAULT_TEMPERATURE_COMMAND,
    DEFAULT_VALUE_SENSOR_DEFINITIONS,
    DOMAIN,
    NAME,
)


def _parse_actions(raw: str) -> list[dict[str, object]]:
    """Parse action list from text.

    Format:
    Label:cmd_hex[:payload_hex],Label2:7a
    """
    actions: list[dict[str, object]] = []
    if not raw.strip():
        return actions

    for item in raw.split(","):
        part = item.strip()
        if not part:
            continue

        fields = [f.strip() for f in part.split(":")]
        if len(fields) < 2:
            continue

        label = fields[0]
        try:
            cmd = int(fields[1], 16)
        except ValueError:
            continue

        payload = b""
        if len(fields) >= 3 and fields[2]:
            try:
                payload = bytes.fromhex(fields[2])
            except ValueError:
                payload = b""

        actions.append({"label": label, "cmd": cmd, "payload": payload.hex()})

    return actions


def _actions_to_text(actions: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for action in actions:
        label = str(action.get("label", "Action"))
        cmd = int(action.get("cmd", 0))
        payload = str(action.get("payload", ""))
        if payload:
            chunks.append(f"{label}:{cmd:02x}:{payload}")
        else:
            chunks.append(f"{label}:{cmd:02x}")
    return ", ".join(chunks)


def _parse_cmd_list(raw: str) -> list[int]:
    if not raw.strip():
        return []
    out: list[int] = []
    for item in raw.split(","):
        part = item.strip().lower()
        if not part:
            continue
        if part.startswith("0x"):
            part = part[2:]
        try:
            out.append(int(part, 16))
        except ValueError:
            continue
    return [v for v in out if 0 <= v <= 255]


def _cmd_list_to_text(values: list[int]) -> str:
    return ", ".join(f"{v:02x}" for v in values)


def _parse_switches(raw: str) -> list[dict[str, object]]:
    """Parse switches from:
    Label|on_cmd|on_payload|off_cmd|off_payload|state_cmd|on_value, ...
    """
    switches: list[dict[str, object]] = []
    if not raw.strip():
        return switches

    for item in raw.split(","):
        part = item.strip()
        if not part:
            continue
        fields = [f.strip() for f in part.split("|")]
        if len(fields) < 4:
            continue
        try:
            label = fields[0]
            on_cmd = int(fields[1], 16)
            on_payload = bytes.fromhex(fields[2]) if fields[2] else b""
            off_cmd = int(fields[3], 16)
            off_payload = bytes.fromhex(fields[4]) if len(fields) > 4 and fields[4] else b""
            state_cmd = int(fields[5], 16) if len(fields) > 5 and fields[5] else None
            on_value = fields[6].lower() if len(fields) > 6 and fields[6] else None
        except ValueError:
            continue
        switches.append(
            {
                "label": label,
                "on_cmd": on_cmd,
                "on_payload": on_payload.hex(),
                "off_cmd": off_cmd,
                "off_payload": off_payload.hex(),
                "state_cmd": state_cmd,
                "on_value": on_value,
            }
        )
    return switches


def _switches_to_text(items: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for it in items:
        chunks.append(
            "|".join(
                [
                    str(it.get("label", "Switch")),
                    f"{int(it.get('on_cmd', 0)):02x}",
                    str(it.get("on_payload", "")),
                    f"{int(it.get('off_cmd', 0)):02x}",
                    str(it.get("off_payload", "")),
                    f"{int(it.get('state_cmd')):02x}" if it.get("state_cmd") is not None else "",
                    str(it.get("on_value", "")),
                ]
            )
        )
    return ", ".join(chunks)


def _parse_value_sensors(raw: str) -> list[dict[str, object]]:
    """Parse value sensors from: Label|cmd|index|scale."""
    sensors: list[dict[str, object]] = []
    if not raw.strip():
        return sensors
    for item in raw.split(","):
        part = item.strip()
        if not part:
            continue
        fields = [f.strip() for f in part.split("|")]
        if len(fields) < 3:
            continue
        try:
            label = fields[0]
            cmd = int(fields[1], 16)
            index = int(fields[2])
            scale = float(fields[3]) if len(fields) > 3 and fields[3] else 1.0
        except ValueError:
            continue
        sensors.append({"label": label, "cmd": cmd, "index": index, "scale": scale})
    return sensors


def _value_sensors_to_text(items: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for it in items:
        chunks.append(
            "|".join(
                [
                    str(it.get("label", "Value")),
                    f"{int(it.get('cmd', 0)):02x}",
                    str(int(it.get("index", 0))),
                    str(float(it.get("scale", 1.0))),
                ]
            )
        )
    return ", ".join(chunks)


class MajesticPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Majestic Pool config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip()
            await self.async_set_unique_id(address.lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_ADDRESS: address,
                    CONF_POLL_INTERVAL: user_input[CONF_POLL_INTERVAL],
                    CONF_TEMPERATURE_COMMAND: user_input[CONF_TEMPERATURE_COMMAND],
                    CONF_ACTION_COMMANDS: _parse_actions(user_input[CONF_ACTION_COMMANDS]),
                    CONF_DIAGNOSTIC_COMMANDS: _parse_cmd_list(
                        user_input[CONF_DIAGNOSTIC_COMMANDS]
                    ),
                    CONF_ENABLE_TEMPERATURE_POLL: user_input[CONF_ENABLE_TEMPERATURE_POLL],
                    CONF_CONNECT_ON_DEMAND: user_input[CONF_CONNECT_ON_DEMAND],
                    CONF_ENABLE_PAIRING_PROBE: user_input[CONF_ENABLE_PAIRING_PROBE],
                    CONF_PAIRING_TIMEOUT: user_input[CONF_PAIRING_TIMEOUT],
                    CONF_DEVICE_NAME_PREFIX: user_input[CONF_DEVICE_NAME_PREFIX].strip(),
                    CONF_SWITCH_DEFINITIONS: _parse_switches(
                        user_input[CONF_SWITCH_DEFINITIONS]
                    ),
                    CONF_VALUE_SENSOR_DEFINITIONS: _parse_value_sensors(
                        user_input[CONF_VALUE_SENSOR_DEFINITIONS]
                    ),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=NAME): str,
                vol.Required(CONF_ADDRESS): str,
                vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
                    int, vol.Range(min=5, max=300)
                ),
                vol.Required(
                    CONF_TEMPERATURE_COMMAND,
                    default=DEFAULT_TEMPERATURE_COMMAND,
                ): vol.All(int, vol.Range(min=0, max=255)),
                vol.Optional(
                    CONF_ACTION_COMMANDS,
                    default=_actions_to_text(DEFAULT_ACTION_COMMANDS),
                ): str,
                vol.Optional(
                    CONF_DIAGNOSTIC_COMMANDS,
                    default=_cmd_list_to_text(DEFAULT_DIAGNOSTIC_COMMANDS),
                ): str,
                vol.Required(
                    CONF_ENABLE_TEMPERATURE_POLL,
                    default=DEFAULT_ENABLE_TEMPERATURE_POLL,
                ): bool,
                vol.Required(
                    CONF_CONNECT_ON_DEMAND,
                    default=DEFAULT_CONNECT_ON_DEMAND,
                ): bool,
                vol.Required(
                    CONF_ENABLE_PAIRING_PROBE,
                    default=DEFAULT_ENABLE_PAIRING_PROBE,
                ): bool,
                vol.Required(
                    CONF_PAIRING_TIMEOUT,
                    default=DEFAULT_PAIRING_TIMEOUT,
                ): vol.All(int, vol.Range(min=5, max=180)),
                vol.Required(
                    CONF_DEVICE_NAME_PREFIX,
                    default=DEFAULT_DEVICE_NAME_PREFIX,
                ): str,
                vol.Optional(
                    CONF_SWITCH_DEFINITIONS,
                    default=_switches_to_text(DEFAULT_SWITCH_DEFINITIONS),
                ): str,
                vol.Optional(
                    CONF_VALUE_SENSOR_DEFINITIONS,
                    default=_value_sensors_to_text(DEFAULT_VALUE_SENSOR_DEFINITIONS),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MajesticPoolOptionsFlow(config_entry)


class MajesticPoolOptionsFlow(config_entries.OptionsFlow):
    """Majestic Pool options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_POLL_INTERVAL: user_input[CONF_POLL_INTERVAL],
                    CONF_TEMPERATURE_COMMAND: user_input[CONF_TEMPERATURE_COMMAND],
                    CONF_ACTION_COMMANDS: _parse_actions(user_input[CONF_ACTION_COMMANDS]),
                    CONF_DIAGNOSTIC_COMMANDS: _parse_cmd_list(
                        user_input[CONF_DIAGNOSTIC_COMMANDS]
                    ),
                    CONF_ENABLE_TEMPERATURE_POLL: user_input[CONF_ENABLE_TEMPERATURE_POLL],
                    CONF_CONNECT_ON_DEMAND: user_input[CONF_CONNECT_ON_DEMAND],
                    CONF_ENABLE_PAIRING_PROBE: user_input[CONF_ENABLE_PAIRING_PROBE],
                    CONF_PAIRING_TIMEOUT: user_input[CONF_PAIRING_TIMEOUT],
                    CONF_DEVICE_NAME_PREFIX: user_input[CONF_DEVICE_NAME_PREFIX].strip(),
                    CONF_SWITCH_DEFINITIONS: _parse_switches(
                        user_input[CONF_SWITCH_DEFINITIONS]
                    ),
                    CONF_VALUE_SENSOR_DEFINITIONS: _parse_value_sensors(
                        user_input[CONF_VALUE_SENSOR_DEFINITIONS]
                    ),
                },
            )

        cfg = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLL_INTERVAL,
                    default=cfg.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                ): vol.All(int, vol.Range(min=5, max=300)),
                vol.Required(
                    CONF_TEMPERATURE_COMMAND,
                    default=cfg.get(CONF_TEMPERATURE_COMMAND, DEFAULT_TEMPERATURE_COMMAND),
                ): vol.All(int, vol.Range(min=0, max=255)),
                vol.Optional(
                    CONF_ACTION_COMMANDS,
                    default=_actions_to_text(
                        cfg.get(CONF_ACTION_COMMANDS, DEFAULT_ACTION_COMMANDS)
                    ),
                ): str,
                vol.Optional(
                    CONF_DIAGNOSTIC_COMMANDS,
                    default=_cmd_list_to_text(
                        cfg.get(CONF_DIAGNOSTIC_COMMANDS, DEFAULT_DIAGNOSTIC_COMMANDS)
                    ),
                ): str,
                vol.Required(
                    CONF_ENABLE_TEMPERATURE_POLL,
                    default=cfg.get(
                        CONF_ENABLE_TEMPERATURE_POLL,
                        DEFAULT_ENABLE_TEMPERATURE_POLL,
                    ),
                ): bool,
                vol.Required(
                    CONF_CONNECT_ON_DEMAND,
                    default=cfg.get(CONF_CONNECT_ON_DEMAND, DEFAULT_CONNECT_ON_DEMAND),
                ): bool,
                vol.Required(
                    CONF_ENABLE_PAIRING_PROBE,
                    default=cfg.get(
                        CONF_ENABLE_PAIRING_PROBE, DEFAULT_ENABLE_PAIRING_PROBE
                    ),
                ): bool,
                vol.Required(
                    CONF_PAIRING_TIMEOUT,
                    default=cfg.get(CONF_PAIRING_TIMEOUT, DEFAULT_PAIRING_TIMEOUT),
                ): vol.All(int, vol.Range(min=5, max=180)),
                vol.Required(
                    CONF_DEVICE_NAME_PREFIX,
                    default=cfg.get(CONF_DEVICE_NAME_PREFIX, DEFAULT_DEVICE_NAME_PREFIX),
                ): str,
                vol.Optional(
                    CONF_SWITCH_DEFINITIONS,
                    default=_switches_to_text(
                        cfg.get(CONF_SWITCH_DEFINITIONS, DEFAULT_SWITCH_DEFINITIONS)
                    ),
                ): str,
                vol.Optional(
                    CONF_VALUE_SENSOR_DEFINITIONS,
                    default=_value_sensors_to_text(
                        cfg.get(
                            CONF_VALUE_SENSOR_DEFINITIONS,
                            DEFAULT_VALUE_SENSOR_DEFINITIONS,
                        )
                    ),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
