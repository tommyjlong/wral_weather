"""Sensors for WRAL Weather Service."""
from __future__ import annotations

import logging #TJL Adder

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow
from homeassistant.util.unit_conversion import (
    DistanceConverter,
    PressureConverter,
    SpeedConverter,
)
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from . import WRALData, WralDataUpdateCoordinator, base_unique_id, device_info
#from .const import ATTRIBUTION, CONF_STATION, DOMAIN, OBSERVATION_VALID_TIME
from .const import (
    ATTRIBUTION, 
    CONF_STATION, 
    DOMAIN, 
    OBSERVATION_VALID_TIME,
    CONF_ZIPCODE  #TJL Adder
)

_LOGGER = logging.getLogger(__name__) #TJL Adder

PARALLEL_UPDATES = 0

#TJL Adder: tell each sensor what wral dictionary to use
CURRENT_DICT = "current_dict" 
FORECAST_DICT = "forecast" 
FORECAST_DICT_0 = "forecast-day-0" 


@dataclass
class WRALSensorEntityDescription(SensorEntityDescription):
    """Class describing WRAL Weather Sensor entities."""

    unit_convert: str | None = None

    #TJL Adder. Note: Type hint has to be incl or won't compile
    which_dict: str | None = None  


SENSOR_TYPES: tuple[WRALSensorEntityDescription, ...] = (
    WRALSensorEntityDescription(
       #key="dewpoint",
        key="current_dew_point",
        name="Dew Point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfTemperature.CELSIUS,
       #unit_convert=UnitOfTemperature.CELSIUS,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        unit_convert=UnitOfTemperature.FAHRENHEIT,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
        key="current_temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfTemperature.CELSIUS,
       #unit_convert=UnitOfTemperature.CELSIUS,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        unit_convert=UnitOfTemperature.FAHRENHEIT,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="windChill",
        key="current_wind_chill",
        name="Wind Chill",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfTemperature.CELSIUS,
       #unit_convert=UnitOfTemperature.CELSIUS,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        unit_convert=UnitOfTemperature.FAHRENHEIT,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="heatIndex",
        key="current_heat_index",
        name="Heat Index",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfTemperature.CELSIUS,
       #unit_convert=UnitOfTemperature.CELSIUS,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        unit_convert=UnitOfTemperature.FAHRENHEIT,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="relativeHumidity",
        key="current_relative_humidity",
        name="Relative Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        unit_convert=PERCENTAGE,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="windSpeed",
        key="current_wind_speed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        unit_convert=UnitOfSpeed.MILES_PER_HOUR,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="windGust",
        key="current_wind_gusts",
        name="Wind Gusts",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        unit_convert=UnitOfSpeed.MILES_PER_HOUR,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    # statistics currently doesn't handle circular statistics
    WRALSensorEntityDescription(
       #key="windDirection",
        key="current_wind_bearing",
        name="Wind Bearing",
        icon="mdi:compass-rose",
        native_unit_of_measurement=DEGREE,
        unit_convert=DEGREE,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="barometricPressure",
        key="current_pressure",
        name="Barometric Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfPressure.PA,
        native_unit_of_measurement=UnitOfPressure.INHG,
        unit_convert=UnitOfPressure.INHG,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(
       #key="visibility",
        key="current_visibility",
        name="Visibility",
        icon="mdi:eye",
        state_class=SensorStateClass.MEASUREMENT,
       #native_unit_of_measurement=UnitOfLength.METERS,
        native_unit_of_measurement=UnitOfLength.MILES,
        unit_convert=UnitOfLength.MILES,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(  #TJL ADDER
        key="current_hourly_precip",
        name="Hourly Precipitation",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cup-water",
        native_unit_of_measurement=UnitOfLength.INCHES,
        unit_convert=UnitOfLength.INCHES,
        which_dict=CURRENT_DICT,  #TJL Adder
    ),
    WRALSensorEntityDescription(  #TJL ADDER
        key="precipitation",
        name="Probability Precipitation",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        unit_convert=PERCENTAGE,
        which_dict=FORECAST_DICT_0,  #TJL Adder
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the WRAL weather platform."""
    wral_data: WRALData = hass.data[DOMAIN][entry.entry_id]
   #station = entry.data[CONF_STATION]
    zipcode = entry.data[CONF_ZIPCODE] #TJL Change

    async_add_entities(
        WRALSensor(
            hass=hass,
            entry_data=entry.data,
            wral_data=wral_data,
            description=description,
            zipcode=zipcode,
        )
        for description in SENSOR_TYPES
    )


class WRALSensor(CoordinatorEntity[WralDataUpdateCoordinator], SensorEntity):
    """An WRAL Sensor Entity."""

    entity_description: WRALSensorEntityDescription
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        hass: HomeAssistant,
        entry_data: MappingProxyType[str, Any],
        wral_data: WRALData,
        description: WRALSensorEntityDescription,
        zipcode: str,
    ) -> None:
        """Initialise the platform with a data instance."""
        super().__init__(wral_data.coordinator_observation)
       #self._wral = wral_data.api
        self._wral = wral_data.wral_api
       #self._latitude = entry_data[CONF_LATITUDE]
       #self._longitude = entry_data[CONF_LONGITUDE]
        self._zipcode = entry_data[CONF_ZIPCODE] #TJL Adder
        self.entity_description = description

        self._attr_name = f"{zipcode} {description.name}" #TJL station hass been set to zipcode
        if hass.config.units is US_CUSTOMARY_SYSTEM:
            self._attr_native_unit_of_measurement = description.unit_convert

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        if (self.entity_description.which_dict == CURRENT_DICT ): #TJL Adder
            dict_to_use = self._wral.curr_dict  #TJL Adder
        elif (self.entity_description.which_dict == FORECAST_DICT_0 ): #TJL Adder
            dict_to_use = self._wral.forecast_daily_list[0]  #TJL Adder
        else:
            dict_to_use = self._wral.curr_dict  #TJL Adder

       #observation = self._wral.curr_dict  #TJL Adder
        value = dict_to_use.get(self.entity_description.key)  #TJL Adder
        _LOGGER.debug("Getting Sensor value %s for %s", value, self.entity_description.key) #TJL Adder
        if (
            dict_to_use == None 
           #not (dict_to_use := self._wral.curr_dict)
            or (value := dict_to_use.get(self.entity_description.key)) is None
        ):
            return None

        # Set alias to unit property -> prevent unnecessary hasattr calls
        unit_of_measurement = self.native_unit_of_measurement

        #TJL CHANGE
       #if unit_of_measurement == UnitOfSpeed.MILES_PER_HOUR:
        if unit_of_measurement == UnitOfSpeed.KILOMETERS_PER_HOUR:
            return round(
                SpeedConverter.convert(
                    value, UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfSpeed.MILES_PER_HOUR
                )
            )
        #TJL CHANGE
       #if unit_of_measurement == UnitOfLength.MILES:
        if unit_of_measurement == UnitOfLength.METERS:
            return round(
                DistanceConverter.convert(
                    value, UnitOfLength.METERS, UnitOfLength.MILES
                )
            )
        #TJL CHANGE
       #if unit_of_measurement == UnitOfPressure.INHG:
        if unit_of_measurement == UnitOfPressure.PA:
            return round(
                PressureConverter.convert(
                    value, UnitOfPressure.PA, UnitOfPressure.INHG
                ),
                2,
            )
        #TJL CHANGE
       #if unit_of_measurement == UnitOfTemperature.CELSIUS:
        if unit_of_measurement == UnitOfTemperature.FAHRENHEIT:
            return round(value, 1)
        if unit_of_measurement == PERCENTAGE:
            return round(value)
        return value

    @property
    def unique_id(self) -> str:
        """Return a unique_id for this entity."""
       #return f"{base_unique_id(self._latitude, self._longitude, self._zipcode)}_{self.entity_description.key}"
        return f"{base_unique_id(self._zipcode)}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Return if state is available."""
        if self.coordinator.last_update_success_time:
            last_success_time = (
                utcnow() - self.coordinator.last_update_success_time
                < OBSERVATION_VALID_TIME
            )
        else:
            last_success_time = False
        return self.coordinator.last_update_success or last_success_time

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
       #return device_info(self._latitude, self._longitude)
       #return device_info(self._latitude, self._longitude, self._zipcode) #TJL CHANGE
        return device_info(self._zipcode) #TJL CHANGE
