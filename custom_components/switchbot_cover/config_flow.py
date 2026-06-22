from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_UP_SWITCH,
    CONF_DOWN_SWITCH,
    CONF_SENSOR,
    CONF_MOVEMENT_TIMEOUT,
    DEFAULT_MOVEMENT_TIMEOUT,
)


class SwitchBotCoverConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        errors: dict[str, str] = {}

        if user_input is not None:
            up = user_input[CONF_UP_SWITCH]
            down = user_input[CONF_DOWN_SWITCH]
            if up == down:
                errors["base"] = "same_switch"
            else:
                await self.async_set_unique_id(f"{up}_{down}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get("name", "SwitchBot Cover"),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): selector.TextSelector(),
                    vol.Required(CONF_UP_SWITCH): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch")
                    ),
                    vol.Required(CONF_DOWN_SWITCH): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="switch")
                    ),
                    vol.Optional(CONF_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(
                        CONF_MOVEMENT_TIMEOUT, default=DEFAULT_MOVEMENT_TIMEOUT
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=120, step=1, unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SwitchBotCoverOptionsFlow()


class SwitchBotCoverOptionsFlow(OptionsFlow):

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        data = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SENSOR,
                        default=data.get(CONF_SENSOR, ""),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(
                        CONF_MOVEMENT_TIMEOUT,
                        default=data.get(
                            CONF_MOVEMENT_TIMEOUT, DEFAULT_MOVEMENT_TIMEOUT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5, max=120, step=1, unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
        )
