"""Support for WRAL weather service."""
from __future__ import annotations  #TJL Must keep at the beginning of the file

import logging #TJL Adder
from datetime import timedelta, datetime #TJL Adder
import pytz  #TJL Adder

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_IS_DAYTIME,
    ATTR_FORECAST_NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW, #TJL ADDER
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_CLOUD_COVERAGE,  #TJL Adder
    ATTR_FORECAST_NATIVE_APPARENT_TEMP,  #TJL Adder
    DOMAIN as WEATHER_DOMAIN,
    CoordinatorWeatherEntity,
    Forecast,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    CONF_NAME,  #TJL adder
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow
from homeassistant.util.unit_conversion import SpeedConverter, TemperatureConverter

from . import WRALData, base_unique_id, device_info
from .const import (
    ATTR_FORECAST_DETAILED_DESCRIPTION,
    ATTRIBUTION,
    CONDITION_CLASSES,
    DAYNIGHT,
    DOMAIN,
    FORECAST_VALID_TIME,
    HOURLY,
    DAILY, #TJL Adder
    OBSERVATION_VALID_TIME,
    CONF_ZIPCODE, #TJL Adder
    CONF_NUM_HRS, #TJL Adder
)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__) #TJL Adder

#TJL ADDER
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

#TJL ADDER
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

#TJL ADDER
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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the WRAL weather platform."""
    entity_registry = er.async_get(hass)
    wral_data: WRALData = hass.data[DOMAIN][entry.entry_id]

    entities = [WRALWeather(entry.data, wral_data, DAYNIGHT)]

    async_add_entities(entities, False)


def _calculate_unique_id(entry_data: MappingProxyType[str, Any], mode: str) -> str:
    """Calculate unique ID."""
   #latitude = entry_data[CONF_LATITUDE]
   #longitude = entry_data[CONF_LONGITUDE]
   #return f"{base_unique_id(latitude, longitude)}_{mode}"
    zipcode = entry_data[CONF_ZIPCODE] #TJL Adder
   #return f"{base_unique_id(latitude, longitude, zipcode)}_{mode}" #TJL Change
    return f"{base_unique_id(zipcode)}_{mode}" #TJL Change


class WRALWeather(CoordinatorWeatherEntity):
    """Representation of a weather condition."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False
    _attr_supported_features = (
       #WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_TWICE_DAILY  | WeatherEntityFeature.FORECAST_DAILY
       #WeatherEntityFeature.FORECAST_DAILY #TJL reduce to only daily forecast
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY 
    )


    def __init__(
        self,
        entry_data: MappingProxyType[str, Any],
        wral_data: WRALData,
        mode: str,
    ) -> None:
        """Initialise the platform with a data instance and station name."""
        super().__init__(
            observation_coordinator=wral_data.coordinator_observation,
            hourly_coordinator=wral_data.coordinator_forecast_hourly,
            twice_daily_coordinator=wral_data.coordinator_forecast_twice_daily,
            hourly_forecast_valid=FORECAST_VALID_TIME,
            twice_daily_forecast_valid=FORECAST_VALID_TIME,
            daily_coordinator=wral_data.coordinator_forecast_daily, #TJL Adder
            daily_forecast_valid=OBSERVATION_VALID_TIME, #TJL Adder
        )

        self.wral = wral_data.wral_api  #TJL Adder
        self.zipcode = entry_data[CONF_ZIPCODE] #TJL Adder
        self.wral_name = entry_data[CONF_NAME]
        self.mode = mode

       #self.observation: dict[str, Any] | None = None  #TJL CHANGE wral now doing
        self._forecast_hourly: list[dict[str, Any]] | None = None
       #self._forecast_legacy: list[dict[str, Any]] | None = None
        self._forecast_twice_daily: list[dict[str, Any]] | None = None
        self._forecast_daily: list[dict[str, Any]] | None = None #TJL Adder

        self._attr_unique_id = _calculate_unique_id(entry_data, mode)

    async def async_added_to_hass(self) -> None:
        """Set up a listener and load data."""
        await super().async_added_to_hass()
        # Load initial data from coordinators
        _LOGGER.debug("Load initial data from coordinators") #TJL Adder
        self._handle_coordinator_update()
        self._handle_hourly_forecast_coordinator_update()
        self._handle_twice_daily_forecast_coordinator_update()
       #self._handle_legacy_forecast_coordinator_update()  #TJL Remove legacy
        self._handle_daily_forecast_coordinator_update() #TJL Adder

    @callback
    def _handle_coordinator_update(self) -> None:
        """Load data from integration."""
        _LOGGER.debug("Handling Coordinator Update") #TJL Adder
        self._forecast_daily = self.wral.forecast_daily_list #TJL Adder to refresh HA state
        self._forecast_hourly = self.wral.forecast_hourly_list #TJL Adder to refresh HA state
        self.async_write_ha_state()

    @callback
    def _handle_hourly_forecast_coordinator_update(self) -> None:
        """Handle updated data from the hourly forecast coordinator."""
        _LOGGER.debug("Handling Coordinator Hourly") #TJL Adder
       #TJL This for some reason only gets called a couple of times a day randomly
        self._forecast_hourly = self.wral.forecast_hourly_list #TJL Adder

    @callback
    def _handle_twice_daily_forecast_coordinator_update(self) -> None:
        """Handle updated data from the twice daily forecast coordinator."""
        _LOGGER.debug("Handling Coordinator Twice Daily") #TJL Adder
       #TJL Place holder for twice daily. WRAL currently does not provide.
       #self._forecast_twice_daily = self.wral.forecast_twicedaily 

    @callback #TJL Adder
    def _handle_daily_forecast_coordinator_update(self) -> None:
        """Handle updated data from the daily forecast coordinator."""
        _LOGGER.debug("Handling Coordinator Daily") #TJL Adder
       #TJL This for some reason only gets called a couple of times a day randomly
        self._forecast_daily = self.wral.forecast_daily_list


    @property
    def name(self) -> str:
        """Return the name of the station."""
       #return f"{self.station} {self.mode.title()}"
        return f"{self.wral_name}" #TJL Change

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.wral.curr_dict:
            wral_curr_temp = self.wral.curr_dict.get("current_temperature")
            _LOGGER.debug("WRAL Curr Temp %d", wral_curr_temp)
            return wral_curr_temp
        else:
            return None


    @property
    def native_temperature_unit(self) -> str:
        """Return the current temperature unit."""
       #return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT  #TJL CHANGE

    @property  #TJL ADDER
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        if self.wral.curr_dict:
            temperature = self.wral.curr_dict.get("current_temperature")
            heat_index = self.wral.curr_dict.get("current_heat_index")
            wind_chill = self.wral.curr_dict.get("current_wind_chill")
            if heat_index == None:
               heat_index = temperature
            if wind_chill == None:
               wind_chill = temperature
            if temperature <= 50:
                apparent_temp = wind_chill
            elif temperature > 80:
                apparent_temp = heat_index
            else:
                apparent_temp = temperature
        else:
            apparent_temp = None
            
        _LOGGER.debug("WRAL Curr Apparent Temp %d", apparent_temp)
        return apparent_temp

    @property  #TJL ADDER
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed in native units."""
        if self.wral.curr_dict:
            gust = self.wral.curr_dict.get("current_wind_gusts")
        else:
            gust = None

        _LOGGER.debug("WRAL Curr Wind Gusts %d", gust)
        return gust

    @property
    def native_pressure(self) -> int | None:
        """Return the current pressure."""
      # TJL CHANGE
        if self.wral.curr_dict:
            wral_curr_press = self.wral.curr_dict.get("current_pressure")
            _LOGGER.debug("WRAL Curr Presssure %f", wral_curr_press)
            return wral_curr_press
        else:
            return None


    @property
    def native_pressure_unit(self) -> str:
        """Return the current pressure unit."""
       #return UnitOfPressure.PA
        return UnitOfPressure.INHG #TJL CHANGE

    @property
    def humidity(self) -> float | None:
        """Return the name of the sensor."""
      # TJL CHANGE
        if self.wral.curr_dict:
            wral_curr_hum =\
                self.wral.curr_dict.get("current_relative_humidity")
            _LOGGER.debug("WRAL Curr Relative Humidity %d", wral_curr_hum)
            return wral_curr_hum
        else:
            return None


    @property
    def native_wind_speed(self) -> float | None:
        """Return the current windspeed."""
      # TJL CHANGE
        if self.wral.curr_dict:
            wral_curr_ws = self.wral.curr_dict.get("current_wind_speed")
            _LOGGER.debug("WRAL Curr Wind Speed %d", wral_curr_ws)
            return round(wral_curr_ws)
        else:
            return None

    @property
    def native_wind_speed_unit(self) -> str:
        """Return the current windspeed."""
       #return UnitOfSpeed.KILOMETERS_PER_HOUR
        return UnitOfSpeed.MILES_PER_HOUR

    @property
    def wind_bearing(self) -> int | None:
        """Return the current wind bearing (degrees)."""
      # TJL CHANGE
        if self.wral.curr_dict:
            wral_curr_wb = self.wral.curr_dict.get("current_wind_bearing")
            _LOGGER.debug("WRAL Curr Wind Bearing %d", wral_curr_wb)
            return wral_curr_wb
        else:
            return None


    @property
    def condition(self) -> str | None:
        """Return current condition."""
        if self.wral.curr_dict:
            wral_cond = self.wral.curr_dict.get("current_icon_conditions")
            _LOGGER.debug("WRAL Curr Icon Condition %s", wral_cond)
            wral_ha_cond = wral2ha_condition(wral_cond)
            _LOGGER.debug("WRAL Curr HA Condition %s", wral_ha_cond)
            return wral_ha_cond
        else:
            return None

    @property
    def native_visibility(self) -> int | None:
        """Return visibility."""
      # TJL CHANGE
        if self.wral.curr_dict:
            wral_curr_visib = self.wral.curr_dict.get("current_visibility")
            _LOGGER.debug("WRAL Curr Visibility %f", wral_curr_visib)
            return wral_curr_visib
        else:
            return None


    @property
    def native_visibility_unit(self) -> str:
        """Return visibility unit."""
      # return UnitOfLength.METERS
        return UnitOfLength.MILES

    def _forecast(
        self, generic_forecast: list[dict[str, Any]] | None, mode: str
    ) -> list[Forecast] | None:
        """Return forecast."""
        _LOGGER.debug("_forecast. Mode: %s", mode) #TJL Adder
        if generic_forecast is None:
            return None
        forecast: list[Forecast] = []

        #TJL Adder
        wral_forecast = []
        i = 0
        if mode == DAILY:
            _LOGGER.debug("Building WRAL daily forecast for HA") #TJL Adder
            for forecast_entry in generic_forecast:
                data = {
                    ATTR_FORECAST_DETAILED_DESCRIPTION: forecast_entry.get(
                        "detailed_description"
                    ),
                    ATTR_FORECAST_NATIVE_TEMP:
                        forecast_entry.get("high_temperature"),
                    ATTR_FORECAST_NATIVE_TEMP_LOW:
                        forecast_entry.get("low_temperature"),
                    ATTR_FORECAST_WIND_BEARING:
                        forecast_entry.get("wind_bearing"),
                    ATTR_FORECAST_NATIVE_WIND_SPEED:
                        forecast_entry.get("wind_speed"),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY:
                        forecast_entry.get("precipitation"),
                }
                temp_day = forecast_entry.get("which_day")
               #iso_day = wral_forecast_day2iso(temp_day, i)
                iso_day = forecast_entry.get("which_day_dt")
                data[ATTR_FORECAST_TIME] = iso_day
                # _LOGGER.debug("ISO Day: %s", iso_day)
                wral_cond = forecast_entry.get("icon_condition")
                wral_ha_cond = wral2ha_condition(wral_cond)
                data[ATTR_FORECAST_CONDITION] = wral_ha_cond

                wral_forecast.append(data)
                i = i + 1
            _LOGGER.debug("WRAL Daily Forecast List for HA %s", wral_forecast)

            return wral_forecast
    
        #TJL Adder
        if mode == HOURLY:
            _LOGGER.debug("Building WRAL hourly forecast for HA") #TJL Adder
            for forecast_entry in generic_forecast:
                data = {
                    ATTR_FORECAST_TIME:
                        forecast_entry.get("which_hour_dt"),
                    ATTR_FORECAST_NATIVE_TEMP:
                        forecast_entry.get("temperature"),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY:
                        forecast_entry.get("precipitation"),
                    ATTR_FORECAST_NATIVE_WIND_SPEED:
                        forecast_entry.get("wind_speed"),
                    ATTR_FORECAST_WIND_BEARING:
                        forecast_entry.get("wind_bearing"),
                    ATTR_FORECAST_HUMIDITY: 
                        forecast_entry.get("humidity"),
                    ATTR_FORECAST_NATIVE_DEW_POINT:
                        forecast_entry.get("dew_point"),
                    ATTR_FORECAST_CLOUD_COVERAGE:
                        forecast_entry.get("cloud_cover"),
                }

                #Convert condition to HA condition
                wral_cond = forecast_entry.get("icon_condition")
                wral_ha_cond = wral2ha_condition(wral_cond)
                data[ATTR_FORECAST_CONDITION] = wral_ha_cond

                #Compute Apparent Temperature
                temperature = forecast_entry.get("temperature")
                heat_index = forecast_entry.get("heat_index")
                wind_chill = forecast_entry.get("wind_chill")
                if temperature <= 50:
                    apparent_temp = wind_chill
                elif temperature > 80:
                    apparent_temp = heat_index
                else:
                    apparent_temp = temperature
                data[ATTR_FORECAST_NATIVE_APPARENT_TEMP] = apparent_temp

                wral_forecast.append(data)
                i = i + 1
            _LOGGER.debug("WRAL Hourly Forecast List for HA %s", wral_forecast)

            return wral_forecast

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        _LOGGER.debug("async forecast hourly") #TJL Adder
        return self._forecast(self._forecast_hourly, HOURLY)

    @callback
    def _async_forecast_twice_daily(self) -> list[Forecast] | None:
        """Return the twice daily forecast in native units."""
        _LOGGER.debug("async forecast twice daily") #TJL Adder
        return self._forecast(self._forecast_twice_daily, DAYNIGHT)

    @callback #TJL ADDER
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        _LOGGER.debug("async forecast daily") #TJL Adder
        return self._forecast(self._forecast_daily, DAILY)

    @property
    def available(self) -> bool:
        """Return if state is available."""
        _LOGGER.debug("Checking weather entity for availability") #TJL Adder
        last_success = (
            self.coordinator.last_update_success
          # and self.coordinator_forecast_legacy.last_update_success  #TJL Change
        )
        if (
            self.coordinator.last_update_success_time
          # and self.coordinator_forecast_legacy.last_update_success_time  #TJL Change
        ):
            last_success_time = (
                utcnow() - self.coordinator.last_update_success_time
                < OBSERVATION_VALID_TIME
          #     and utcnow() - self.coordinator_forecast_legacy.last_update_success_time  #TJL Change
          #     < FORECAST_VALID_TIME
            )
        else:
            last_success_time = False
        return last_success or last_success_time

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self.coordinator.async_request_refresh()
      # await self.coordinator_forecast_legacy.async_request_refresh() #TJL Change

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self.mode == DAYNIGHT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
       #return device_info(self.latitude, self.longitude)
       #return device_info(self.latitude, self.longitude, self.zipcode) #TJL CHANGE
        return device_info(self.zipcode) #TJL CHANGE


