"""Config flow for ViCare integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.dhcp import MAC_ADDRESS
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import format_mac

from .const import (
    CONF_HEATING_TYPE,
    DEFAULT_HEATING_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ViCare."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Invoke when a user initiates a flow via the user interface."""

        data_schema = {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_CLIENT_ID): cv.string,
            vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): vol.In(
                [DEFAULT_HEATING_TYPE, "gas", "heatpump", "fuelcell"]
            ),
            vol.Optional(CONF_NAME, default="ViCare"): cv.string,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=30)
            ),
        }

        if user_input is not None:
            unique_id = f"{user_input[CONF_USERNAME]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))

    async def async_step_dhcp(self, discovery_info):
        """Invoke when a Viessmann MAC address is discovered on the network."""
        formatted_mac = format_mac(discovery_info[MAC_ADDRESS])

        await self.async_set_unique_id(format_mac(formatted_mac))
        self._abort_if_unique_id_configured()

        return await self.async_step_user()
