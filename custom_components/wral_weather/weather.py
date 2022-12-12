"""Support for WRAL Weather service."""
from datetime import timedelta, datetime
import pytz
import logging

import aiohttp
from .wral_weather import WralWeather

import voluptuous as vol

from homeassistant.components.weather import (
    WeatherEntity,
    PLATFORM_SCHEMA,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_SPEED,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_TEMP_LOW,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_MODE,
    TEMP_FAHRENHEIT,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by WRAL Weather"

SCAN_INTERVAL = timedelta(minutes=15)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

CONF_ZIPCODE = "zipcode"

ATTR_FORECAST_DETAIL_DESCRIPTION = "detailed_description"
ATTR_FORECAST_PRECIP_PROB = "precipitation_probability"
ATTR_FORECAST_DAYTIME = "daytime"

WRAL_CONDITION_CLASSES = {
      "exceptional": ["very-cold", "very-hot", "freezing",
                      "frost", "humid", "smoke"],
      "snowy": ["snow", "day-chance-snow", "night-chance-snow",
                "snow-sleet", "day-chance-snow-sleet",
                "night-chance-snow-sleet"],
      "snowy-rainy": ["day-chance-sleet", "night-chance-sleet",
                      "day-chance-snow-and-sleet",
                      "night-chance-snow-and-sleet",
                      "rain-snow", "day-chance-rain-and-snow",
                      "night-chance-rain-and-snow",
                      "rain-sleet", "day-chance-rain-and-sleet",
                      "night-chance-rain-and-sleet", "sleet",
                      "freezing-rain", "day-chance-freezing-rain",
                      "night-chance-freezing-rain"],
      "hail": [],
      "lightning-rainy": ["thunderstorms-rain",
                          "day-chance-rain-and-tstorms",
                          "night-chance-rain-and-tstorms"],
      "lightning": ["thunderstorm", "day-chance-tstorm",
                    "night-chance-tstorm"],
      "pouring": [],
      "rainy": ["rain", "day-chance-rain", "night-chance-rain",
                "rain-showers", "day-chance-rain-showers",
                "night-chance-rain-showers",
                "drizzle", "day-chance-drizzle", "night-chance-drizzle"],
      "windy-variant": [],
      "windy": ["windy"],
      "fog": ["misc-fog"],
      "clear": ["day-clear", "night-clear",
                "day-dry", "night-dry"],
      "cloudy": ["cloudy", "day-mostly-cloudy", "night-mostly-cloudy"],
      "partlycloudy": ["day-mostly-clear", "night-mostly-clear",
                       "day-partly-cloudy", "night-partly-cloudy"
                       "day-haze", "night-haze",
                       "day-dust", "night-dust"],
    }

ERRORS = (aiohttp.ClientError)

FORECAST_MODE = ["daynight", "hourly"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_MODE, default="daynight"): vol.In(FORECAST_MODE),
        vol.Optional(CONF_ZIPCODE): cv.string,
    }
)


def wral2ha_condition(wral_cond):
    """
    Convert WRAL Condition (current or forecast)
    to HA hui-weather-forecast-card weatherIcons.
    """
    for key, value in WRAL_CONDITION_CLASSES.items():
        if wral_cond in value:
            break
    found = wral_cond.find("night")
    if found != -1:
        time = "night"
    else:
        time = "day"
    cond = key
    if cond == "clear":
        if time == "day":
            return "sunny"
        if time == "night":
            return "clear-night"
    return cond


def wral_forecast_day2iso(day, offset_from_today):
    """
       Convert WRAL forecast day string to time in UTC ISO format.
       Pass in that day's day string and how many days from today.
       Check to make sure the day string being converted is
       the correct day from today. If not, then force to be current time.
       The incoming day string is assumed to be 3 alpha Chars.
       This is for use with HA.
    """
    today = datetime.now()
    current_day_name = (today.strftime("%A"))[:3]
    offset_datetime = today + timedelta(days=offset_from_today)
    offset_day_name = (offset_datetime.strftime("%A"))[:3]
    if offset_day_name == day:
        tempstring = offset_datetime.strftime("%Y-%m-%d") + "T05:00:00"
        temp_datetime = datetime.strptime(tempstring, "%Y-%m-%dT%H:%M:%S")
        utc_datetime_iso = pytz.utc.localize(temp_datetime).isoformat()
        return utc_datetime_iso
    else:
        utc_datetime_iso = pytz.utc.localize(today).isoformat()
        return utc_datetime_iso


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the WRAL Weather platform."""

    mode = config[CONF_MODE]
    zipcode = config.get(CONF_ZIPCODE)

    websession = async_get_clientsession(hass)

    _LOGGER.debug("Setting up WRAL Platform. Zipcode: %s", zipcode)
    wral = WralWeather(websession, zipcode)

    async_add_entities([WRAL_Weather(wral, mode, hass.config.units,
                                     config)], True)


class WRAL_Weather(WeatherEntity):
    """HA Class for WRAL Weather."""

    def __init__(self, wral, mode, units, config):
        """
        Initialise the platform with a data instance
        and optional configs.
        """
        self.wral = wral
        if config.get(CONF_NAME) is None:
            self.wral_name = "WRAL Weather"
        else:
            self.wral_name = config.get(CONF_NAME)
       #self.is_metric = units.is_metric
        self.mode = mode

        self._wral_forecast = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Update Condition."""

        _LOGGER.debug("Updating WRAL observation")
        try:
            await self.wral.update_observation()
            _LOGGER.debug("wral Curr Dict %s", self.wral.curr_dict)
        except ERRORS as status:
            _LOGGER.error("Error Updating WRAL Observation")
            self.wral.curr_dict = None

        _LOGGER.debug("Updating WRAL Forecast")
        try:
            await self.wral.update_forecast()
            self._wral_forecast = self.wral.forecast_list
            _LOGGER.debug("WRAL Forecast Lib List %s",
                          self.wral.forecast_list)
        except ERRORS as status:
            _LOGGER.error("Error Updating WRAL Forecast")
            self._wral_forecast = None

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def name(self):
        """Return the name of the entity."""
        return self.wral_name

    @property
    def temperature(self):
        """Return the current temperature."""
        if self.wral.curr_dict:
            wral_curr_temp = self.wral.curr_dict.get("current_temperature")
            _LOGGER.debug("WRAL Curr Temp %d", wral_curr_temp)
            return wral_curr_temp
        else:
            return None

    @property
    def pressure(self):
        """Return the current pressure."""
        if self.wral.curr_dict:
            wral_curr_press = self.wral.curr_dict.get("current_pressure")
            _LOGGER.debug("WRAL Curr Presssure %f", wral_curr_press)
            return wral_curr_press
        else:
            return None

    @property
    def humidity(self):
        """Return the current humidity."""
        if self.wral.curr_dict:
            wral_curr_hum =\
                self.wral.curr_dict.get("current_relative_humidity")
            _LOGGER.debug("WRAL Curr Relative Humidity %d", wral_curr_hum)
            return wral_curr_hum
        else:
            return None

    @property
    def wind_speed(self):
        """Return the current wind speed."""
        if self.wral.curr_dict:
            wral_curr_ws = self.wral.curr_dict.get("current_wind_speed")
            _LOGGER.debug("WRAL Curr Wind Speed %d", wral_curr_ws)
            return round(wral_curr_ws)
        else:
            return None

    @property
    def wind_bearing(self):
        """Return the current wind bearing (degrees)."""
        if self.wral.curr_dict:
            wral_curr_wb = self.wral.curr_dict.get("current_wind_bearing")
            _LOGGER.debug("WRAL Curr Wind Bearing %d", wral_curr_wb)
            return wral_curr_wb
        else:
            return None

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def condition(self):
        """Return current condition."""
        if self.wral.curr_dict:
            wral_cond = self.wral.curr_dict.get("current_conditions")
            _LOGGER.debug("WRAL Curr Condition %s", wral_cond)
            wral_ha_cond = wral2ha_condition(wral_cond)
            _LOGGER.debug("WRAL Curr HA Condition %s", wral_ha_cond)
            return wral_ha_cond
        else:
            return None

    @property
    def visibility(self):
        """Return visibility(Not supported by WRAL)."""
        return None

    @property
    def forecast(self):
        """Return forecast."""

        if self._wral_forecast is None:
            return None
        wral_forecast = []
        i = 0
        for wral_forecast_entry in self._wral_forecast:
            data = {
                ATTR_FORECAST_DETAIL_DESCRIPTION: wral_forecast_entry.get(
                    "detailed_description"
                ),
                ATTR_FORECAST_TEMP:
                    wral_forecast_entry.get("high_temperature"),
                ATTR_FORECAST_TEMP_LOW:
                    wral_forecast_entry.get("low_temperature"),
                ATTR_FORECAST_WIND_BEARING:
                    wral_forecast_entry.get("wind_bearing"),
                ATTR_FORECAST_WIND_SPEED:
                    wral_forecast_entry.get("wind_speed"),
                ATTR_FORECAST_PRECIP_PROB:
                    wral_forecast_entry.get("precipitation"),
            }
            temp_day = wral_forecast_entry.get("which_day")
            iso_day = wral_forecast_day2iso(temp_day, i)
            data[ATTR_FORECAST_TIME] = iso_day
            # _LOGGER.debug("ISO Day: %s", iso_day)
            wral_cond = wral_forecast_entry.get("condition")
            wral_ha_cond = wral2ha_condition(wral_cond)
            data[ATTR_FORECAST_CONDITION] = wral_ha_cond

            wral_forecast.append(data)
            i = i + 1

        _LOGGER.debug("WRAL Forecast List for HA %s", wral_forecast)

        return wral_forecast
