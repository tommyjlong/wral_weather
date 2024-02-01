"""The WRAL Weather integration."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import datetime
import logging
import aiohttp #TJL Adder
from typing import TYPE_CHECKING

from .wral_weather import WralWeather  #TJL Adder

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import debounce
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator
from homeassistant.util.dt import utcnow

from .const import CONF_STATION, DOMAIN, UPDATE_TIME_PERIOD, CONF_ZIPCODE

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]

ERRORS = (aiohttp.ClientError) #TJL adder

DEFAULT_SCAN_INTERVAL = datetime.timedelta(minutes=10)
FAILED_SCAN_INTERVAL = datetime.timedelta(minutes=1)
DEBOUNCE_TIME = 60  # in seconds

#TJL CHANGE
#def base_unique_id(latitude: float, longitude: float, zipcode: int) -> str:
def base_unique_id( zipcode: int) -> str:
    """Return unique id for entries in configuration."""
   #return f"{latitude}_{longitude}"
    return f"{zipcode}"


@dataclass
class WRALData:
    """Data for the National Weather Service integration."""

    wral_api: WralWeather #TJL Adder
    coordinator_observation: WralDataUpdateCoordinator
    coordinator_forecast_twice_daily: WralDataUpdateCoordinator
    coordinator_forecast_hourly: WralDataUpdateCoordinator
    coordinator_forecast_daily: WralDataUpdateCoordinator #TJL Adder


class WralDataUpdateCoordinator(TimestampDataUpdateCoordinator[None]):
    """WRAL data update coordinator.

    Implements faster data update intervals for failed updates and exposes a last successful update time.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        *,
        name: str,
        update_interval: datetime.timedelta,
        failed_update_interval: datetime.timedelta,
        update_method: Callable[[], Awaitable[None]] | None = None,
        request_refresh_debouncer: debounce.Debouncer | None = None,
    ) -> None:
        """Initialize WRAL coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
            update_method=update_method,
            request_refresh_debouncer=request_refresh_debouncer,
        )
        self.failed_update_interval = failed_update_interval

    @callback
    def _schedule_refresh(self) -> None:
        """Schedule a refresh."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        # We _floor_ utcnow to create a schedule on a rounded second,
        # minimizing the time between the point and the real activation.
        # That way we obtain a constant update frequency,
        # as long as the update process takes less than a second
        if self.last_update_success:
            if TYPE_CHECKING:
                # the base class allows None, but this one doesn't
                assert self.update_interval is not None
            update_interval = self.update_interval
        else:
            update_interval = self.failed_update_interval
        self._unsub_refresh = async_track_point_in_utc_time(
            self.hass,
            self._handle_refresh_interval,
            utcnow().replace(microsecond=0) + update_interval,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a National Weather Service entry."""
   #latitude = entry.data[CONF_LATITUDE]
   #longitude = entry.data[CONF_LONGITUDE]
   #api_key = entry.data[CONF_API_KEY]
   #station = entry.data[CONF_STATION]

    client_session = async_get_clientsession(hass)

    #setup WRAL
    zipcode = entry.data[CONF_ZIPCODE]
    _LOGGER.debug("Setting up WRAL Service. Zipcode: %s", zipcode)
    wral_session = async_get_clientsession(hass)
    wral_inst = WralWeather(wral_session, zipcode)

    async def update_observation() -> None:
        """Retrieve recent observations."""

        #Get Data from WRAL web API
        _LOGGER.debug("Updating WRAL Weather Data")
        try:
            await wral_inst.update_observation_and_forecast()
            _LOGGER.debug("wral Curr Dict %s", wral_inst.curr_dict)
           #self._wral_forecast = self.wral.forecast_list
            _LOGGER.debug("WRAL Forecast List %s",
                          wral_inst.forecast_daily_list)
        except ERRORS as status:
            _LOGGER.error("Error Updating WRAL Weather Data")
           #wral.curr_dict = None
           #self._wral_forecast = None

    async def place_holder() -> None:
        """Place holder for future outside world retrieval forecasts."""
        return None

    coordinator_observation = WralDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"WRAL observation for {zipcode}",
        update_method=update_observation,
        update_interval=DEFAULT_SCAN_INTERVAL,
        failed_update_interval=FAILED_SCAN_INTERVAL,
        request_refresh_debouncer=debounce.Debouncer(
            hass, _LOGGER, cooldown=DEBOUNCE_TIME, immediate=True
        ),
    )

    coordinator_forecast_twice_daily = WralDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"WRAL forecast twice_daily for {zipcode}",
       #update_method=wral_data.update_forecast,
        update_method=place_holder,
        update_interval=DEFAULT_SCAN_INTERVAL,
        failed_update_interval=FAILED_SCAN_INTERVAL,
        request_refresh_debouncer=debounce.Debouncer(
            hass, _LOGGER, cooldown=DEBOUNCE_TIME, immediate=True
        ),
    )

    coordinator_forecast_hourly = WralDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"WRAL forecast hourly for {zipcode}",
       #update_method=wral_data.update_forecast_hourly,
        update_method=place_holder,
        update_interval=DEFAULT_SCAN_INTERVAL,
        failed_update_interval=FAILED_SCAN_INTERVAL,
        request_refresh_debouncer=debounce.Debouncer(
            hass, _LOGGER, cooldown=DEBOUNCE_TIME, immediate=True
        ),
    )

    #TJL Adder: 
    # fetching from WRAL web site currently not needed here
    #   as this data is updated in "observation" coordinator
    coordinator_forecast_daily = WralDataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"WRAL forecast daily for {zipcode}",
       #update_method=wral_inst.update_observation_and_forecast,
        update_method=place_holder,
        update_interval=DEFAULT_SCAN_INTERVAL,
        failed_update_interval=FAILED_SCAN_INTERVAL,
        request_refresh_debouncer=debounce.Debouncer(
            hass, _LOGGER, cooldown=DEBOUNCE_TIME, immediate=True
        ),
    )

    wral_hass_data = hass.data.setdefault(DOMAIN, {})
    wral_hass_data[entry.entry_id] = WRALData(
       #wral_data,
        wral_inst, #TJL Adder
        coordinator_observation,
        coordinator_forecast_twice_daily,
        coordinator_forecast_hourly,
        coordinator_forecast_daily, #TJL Adder
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator_observation.async_refresh()
    await coordinator_forecast_twice_daily.async_refresh()
    await coordinator_forecast_hourly.async_refresh()
    await coordinator_forecast_daily.async_refresh()  #Not needed

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN)
    return unload_ok


#def device_info(latitude: float, longitude: float, zipcode: int) -> DeviceInfo:
def device_info(zipcode: int) -> DeviceInfo:
    """Return device registry information."""
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
       #identifiers={(DOMAIN, base_unique_id(latitude, longitude))},
       #identifiers={(DOMAIN, base_unique_id(latitude, longitude, zipcode))},
        identifiers={(DOMAIN, base_unique_id(zipcode))},
        manufacturer="ABC Weather Service",
       #name=f"ABC WS: {latitude}, {longitude}",
        name=f"ABC WS: {zipcode}",
    )
