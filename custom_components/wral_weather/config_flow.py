"""Config flow for WRAL Weather integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from .wral_weather import WralWeather  #TJL Change
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import base_unique_id
from .const import CONF_STATION, DOMAIN, CONF_ZIPCODE, CONF_NUM_HRS

_LOGGER = logging.getLogger(__name__)


async def validate_input(
    hass: core.HomeAssistant, data: dict[str, Any]
) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
   #latitude = data[CONF_LATITUDE]
   #longitude = data[CONF_LONGITUDE]
   #api_key = data[CONF_API_KEY]
   #station = data.get(CONF_STATION)
    name = data.get(CONF_NAME)
    zipcode = data.get(CONF_ZIPCODE)
    num_hrs = data.get(CONF_NUM_HRS)

   #client_session = async_get_clientsession(hass)
   #ha_api_key = f"{api_key} homeassistant"
   #wral_session = async_get_clientsession(hass)
   #wral_inst = WralWeather(wral_session, zipcode)
  
   #TJL I decided not to try and connect to WRAL at this point
   # as we already have an error log for periodidic updates in init.

    return {"title": name}  #TJL Change


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WRAL Weather."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

       #latitude = self.hass.config.latitude
       #lontitude = self.hass.config.longitude

        if user_input is not None:
            await self.async_set_unique_id(
               #base_unique_id(user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE])
               #base_unique_id(user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE], user_input[CONF_ZIPCODE]) #TJL CHANGE
               #base_unique_id(latitude, longitude, user_input[CONF_ZIPCODE]) #TJL CHANGE
                base_unique_id(user_input[CONF_ZIPCODE]) #TJL CHANGE
            )
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
               #user_input[CONF_STATION] = info["title"]
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
               #vol.Required(CONF_API_KEY): str,
               #vol.Required(
               #    CONF_LATITUDE, default=self.hass.config.latitude
               #): cv.latitude,
               #vol.Required(
               #    CONF_LONGITUDE, default=self.hass.config.longitude
               #): cv.longitude,
               #vol.Optional(CONF_STATION): str,
                vol.Optional(CONF_NAME, default="WRAL Weather"): str,
                vol.Optional(CONF_ZIPCODE, default="27606"): str,
                vol.Optional(CONF_NUM_HRS, default="24"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
