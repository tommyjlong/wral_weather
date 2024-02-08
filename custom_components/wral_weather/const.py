"""Constants for National Weather Service Integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_WINDY_VARIANT,
)

DOMAIN = "wral_weather"

CONF_ZIPCODE = "zipcode" # tjl adder
CONF_NUM_HRS = "num_hrs" # tjl adder

ATTRIBUTION = "Data provided by WRAL Weather"

ATTR_FORECAST_DETAILED_DESCRIPTION: Final = "detailed_description"

CONDITION_CLASSES: dict[str, list[str]] = {
    ATTR_CONDITION_EXCEPTIONAL: [
        "Tornado",
        "Hurricane conditions",
        "Tropical storm conditions",
        "Dust",
        "Smoke",
        "Haze",
        "Hot",
        "Cold",
    ],
    ATTR_CONDITION_SNOWY: ["Snow", "Sleet", "Snow/sleet", "Blizzard"],
    ATTR_CONDITION_SNOWY_RAINY: [
        "Rain/snow",
        "Rain/sleet",
        "Freezing rain/snow",
        "Freezing rain",
        "Rain/freezing rain",
    ],
    ATTR_CONDITION_HAIL: [],
    ATTR_CONDITION_LIGHTNING_RAINY: [
        "Thunderstorm (high cloud cover)",
        "Thunderstorm (medium cloud cover)",
        "Thunderstorm (low cloud cover)",
    ],
    ATTR_CONDITION_LIGHTNING: [],
    ATTR_CONDITION_POURING: [],
    ATTR_CONDITION_RAINY: [
        "Rain",
        "Rain showers (high cloud cover)",
        "Rain showers (low cloud cover)",
    ],
    ATTR_CONDITION_WINDY_VARIANT: ["Mostly cloudy and windy", "Overcast and windy"],
    ATTR_CONDITION_WINDY: [
        "Fair/clear and windy",
        "A few clouds and windy",
        "Partly cloudy and windy",
    ],
    ATTR_CONDITION_FOG: ["Fog/mist"],
    "clear": ["Fair/clear"],  # sunny and clear-night
    ATTR_CONDITION_CLOUDY: ["Mostly cloudy", "Overcast"],
    ATTR_CONDITION_PARTLYCLOUDY: ["A few clouds", "Partly cloudy"],
}

DAYNIGHT = "daynight"
HOURLY = "hourly"
DAILY = "daily" #TJL ADDER

OBSERVATION_VALID_TIME = timedelta(minutes=20)
FORECAST_VALID_TIME = timedelta(minutes=45)
# A lot of stations update once hourly plus some wiggle room
UPDATE_TIME_PERIOD = timedelta(minutes=70)
