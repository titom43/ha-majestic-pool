"""Config flow for Majestic Pool."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_ACTION_COMMANDS,
    CONF_DIAGNOSTIC_COMMANDS,
    CONF_POLL_INTERVAL,
    CONF_TEMPERATURE_COMMAND,
    DEFAULT_DIAGNOSTIC_COMMANDS,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_TEMPERATURE_COMMAND,
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
                    CONF_TEMPERATURE_COMMAND, default=DEFAULT_TEMPERATURE_COMMAND
                ): vol.All(int, vol.Range(min=0, max=255)),
                vol.Optional(CONF_ACTION_COMMANDS, default=""): str,
                vol.Optional(
                    CONF_DIAGNOSTIC_COMMANDS,
                    default=_cmd_list_to_text(DEFAULT_DIAGNOSTIC_COMMANDS),
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
                    default=cfg.get(
                        CONF_TEMPERATURE_COMMAND,
                        DEFAULT_TEMPERATURE_COMMAND,
                    ),
                ): vol.All(int, vol.Range(min=0, max=255)),
                vol.Optional(
                    CONF_ACTION_COMMANDS,
                    default=_actions_to_text(cfg.get(CONF_ACTION_COMMANDS, [])),
                ): str,
                vol.Optional(
                    CONF_DIAGNOSTIC_COMMANDS,
                    default=_cmd_list_to_text(
                        cfg.get(CONF_DIAGNOSTIC_COMMANDS, DEFAULT_DIAGNOSTIC_COMMANDS)
                    ),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
