import asyncio
import aiohttp
from datetime import timedelta, datetime
import pytz
import logging
import sys
from wral_weather import WralWeather

ZIPCODE = '27513'

# Setup Logger for wral_weather.
#   Use the same Logger for this app.
#   If you want to see output from the
#   wral_weather.py debug and this app's debug
#   then change the _LOGGER.setLevel from NOTSET to DEBUG.
_LOGGER = logging.getLogger('wral_weather')
formatter = \
    logging.Formatter('%(levelname)s %(asctime)s %(filename)s - %(message)s')
handler1 = logging.StreamHandler(sys.stdout)
handler1.setFormatter(formatter)
handler1.setLevel(logging.DEBUG)
_LOGGER.addHandler(handler1)
_LOGGER.setLevel(logging.DEBUG)

# The following dictionary is needed for HA
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


def wral2ha_condition(wral_cond):
    """
    Convert WRAL Condition (current or forecast) to
    HA hui-weather-forecast-card weatherIcons.
    """
    for key, value in WRAL_CONDITION_CLASSES.items():
        if wral_cond in value:
            break
    found = wral_cond.find("night")
    if found != -1:
        time = "night"
    else:
        time = "day"
    _LOGGER.debug("Icon Day or Night: %s", time)
    cond = key
    if cond == "clear":
        if time == "day":
            return "sunny"
        if time == "night":
            return "clear-night"
    return cond


def forecast_day2iso(day, offset_from_today):
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
    _LOGGER.debug("Current Day: %s", current_day_name)
    _LOGGER.debug("Num days from today: %i", offset_from_today)
    offset_datetime = today + timedelta(days=offset_from_today)
    offset_day_name = (offset_datetime.strftime("%A"))[:3]
    _LOGGER.debug("Offset Day Name: %s", offset_day_name)

    if offset_day_name == day:
        tempstring = offset_datetime.strftime("%Y-%m-%d") + "T05:00:00"
        _LOGGER.debug("%s", tempstring)
        temp_datetime = datetime.strptime(tempstring, "%Y-%m-%dT%H:%M:%S")
        utc_datetime_iso = pytz.utc.localize(temp_datetime).isoformat()
        _LOGGER.debug("%s", utc_datetime_iso)
        return utc_datetime_iso
    else:
        utc_datetime_iso = pytz.utc.localize(today).isoformat()
        return utc_datetime_iso

def forecast_hour2iso(hour):
    """
       Convert WRAL forecast hour string to time in UTC ISO format.
       This is for use with HA.
    """
    tz = datetime.now().astimezone().tzinfo
    return datetime.fromtimestamp(hour, tz).isoformat()

async def main():
# Reference for Apparent Temperature:
# https://digital.weather.gov/staticpages/definitions.php

    async with aiohttp.ClientSession() as client:
        wral = WralWeather(client, zipcode=ZIPCODE)
        results = await wral.update_observation_and_forecast()

        curr_cond = wral.curr_dict["current_icon_conditions"]
        print('Current WRAL Condition:    ',
              wral.curr_dict["current_conditions"])
        print('Current WRAL IconCondition:',
              wral.curr_dict["current_icon_conditions"])
        curr_ha_cond = wral2ha_condition(curr_cond)
        print('Current HA Condition:      ', curr_ha_cond)
        print('Current Temperature:       ',
              wral.curr_dict["current_temperature"])
        print('Current Dew Point:         ',
              wral.curr_dict["current_dew_point"])
        print('Current Relative Humidity: ',
              wral.curr_dict["current_relative_humidity"])
        print('Current Wind Direction:    ',
              wral.curr_dict["current_wind_direction"])
        print('Current Wind Speed:        ',
              wral.curr_dict["current_wind_speed"])
        print('Current Wind Gusts:        ',
              wral.curr_dict["current_wind_gusts"])
        print('Current Wind Bearing:      ',
              wral.curr_dict["current_wind_bearing"])
        print('Current Wind Chill:        ',
              wral.curr_dict["current_wind_chill"])
        print('Current Heat Index:        ',
              wral.curr_dict["current_heat_index"])
        print('Current Pressure:          ',
              wral.curr_dict["current_pressure"])
        print('Current Visibility:        ',
              wral.curr_dict["current_visibility"])
        print('Current Hourly Precip:     ',
              wral.curr_dict["current_hourly_precip"])
        _LOGGER.debug("Current Dictionary: %s", wral.curr_dict)
        print('')

        i = 0
        for todays_forecast in wral.forecast_daily_list:
            _LOGGER.debug("Today's Forecast %s ", todays_forecast)
            print("Day  ", i, "  Which Day      ",
                  todays_forecast["which_day"])
           #iso_day = forecast_day2iso(todays_forecast["which_day"], i)
           #_LOGGER.debug("Day %i Which ISO Day %s ", i, iso_day)
            print("Day  ", i, "  Datetime       ", 
                 todays_forecast["which_day_dt"])
            print("Day  ", i, "  Condition      ",
                  todays_forecast["condition"])
            print("Day  ", i, "  Icon Condition ",
                  todays_forecast["icon_condition"])
            forecast_cond = todays_forecast["icon_condition"]
            forecast_ha_cond = wral2ha_condition(forecast_cond)
            print("Day  ", i, "  HA Condition   ", forecast_ha_cond)
            print("Day  ", i, "  High Temp      ",
                  todays_forecast["high_temperature"])
            print("Day  ", i, "  Low Temp       ",
                  todays_forecast["low_temperature"])
            print("Day  ", i, "  Sunrise        ",
                  todays_forecast["sunrise"])
            print("Day  ", i, "  Sunset:        ",
                  todays_forecast["sunset"])
            print("Day  ", i, "  Precip Prob    ",
                  todays_forecast["precipitation"])
            print("Day  ", i, "  Wind Direction ",
                  todays_forecast["wind_direction"])
            print("Day  ", i, "  Wind Speed     ",
                  todays_forecast["wind_speed"])
            print("Day  ", i, "  Wind Bearing   ",
                  todays_forecast["wind_bearing"])
            print("Day  ", i, "  Heat Index     ",
                  todays_forecast["heat_index"])
            print("Day  ", i, "  Wind Chill     ",
                  todays_forecast["wind_chill"])
            print("Day  ", i, "  Dew Point      ",
                  todays_forecast["dew_point"])
            print("Day  ", i, "  Details:       ")
            print(" -", todays_forecast["detailed_description"])
            print("")
            i = i + 1

        i = 0
        for hours_forecast in wral.forecast_hourly_list:
            _LOGGER.debug("Today's Hourly Forecast %s ", hours_forecast)
            print("Hour ", i, "  Which Hour DT  ",
                  hours_forecast["which_hour_dt"])
            print("Hour ", i, "  Condition      ",
                  hours_forecast["condition"])
            print("Hour ", i, "  Icon Condition ",
                  hours_forecast["icon_condition"])
            forecast_cond = hours_forecast["icon_condition"]
            forecast_ha_cond = wral2ha_condition(forecast_cond)
            print("Hour ", i, "  HA Condition   ", forecast_ha_cond)
            print("Hour ", i, "  Temperature    ",
                  hours_forecast["temperature"])
            print("Hour ", i, "  Precip Prob    ",
                  hours_forecast["precipitation"])
            print("Hour ", i, "  Wind Direction ",
                  hours_forecast["wind_direction"])
            print("Hour ", i, "  Wind Speed     ",
                  hours_forecast["wind_speed"])
            print("Hour ", i, "  Wind Bearing   ",
                  hours_forecast["wind_bearing"])
            print("Hour ", i, "  Humidity       ",
                  hours_forecast["humidity"])
            print("Hour ", i, "  Dew Point      ",
                  hours_forecast["dew_point"])
            print("Hour ", i, "  Heat Index     ",
                  hours_forecast["heat_index"])
            print("Hour ", i, "  Wind Chill     ",
                  hours_forecast["wind_chill"])
            print("Hour ", i, "  Cloud Cover    ",
                  hours_forecast["cloud_cover"])

            #Compute Apparent Temperature            
            if hours_forecast["temperature"] <= 50:
                apparent_temp = hours_forecast["wind_chill"]
            elif hours_forecast["temperature"] > 80:
                apparent_temp = hours_forecast["heat_index"]
            else:
                apparent_temp = hours_forecast["temperature"]
            print("Hour ", i, "  Apparent Temp  ",
                   apparent_temp)

            print("")
            i = i + 1

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

_LOGGER.debug("Finished Running App")
