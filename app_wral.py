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
handler1.setLevel(logging.NOTSET)
_LOGGER.addHandler(handler1)
_LOGGER.setLevel(logging.NOTSET)

# The following dictionary is needed for HA
WRAL_CONDITION_CLASSES = {
      "exceptional": [],
      "snowy": [],
      "snowy-rainy": [],
      "hail": [],
      "lightning-rainy": ["thunderstorms-rain"],
      "lightning": [],
      "pouring": [],
      "rainy": ["rain", "rain-showers", "day-chance-rain",
                "night-chance-rain"],
      "windy-variant": [],
      "windy": [],
      "fog": ["mist-fog", "misc-fog"],
      "clear": ["day-clear", "night-clear"],
      "cloudy": ["cloudy", "day-mostly-cloudy", "night-mostly-cloudy",
                 "overcast"],
      "partlycloudy": ["day-mostly-clear", "night-mostly-clear",
                       "day-partly-cloudy", "night-partly-cloudy"],
    }


# day-clear
# night-clear
# day-mostly-clear
# day-partly-cloudy
# day-mostly-cloudy
# cloudy
# drizzle
# day-chance-rain
# rain-showers
# misc-fog
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
    _LOGGER.debug("Time: %s", time)
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


async def main():
    async with aiohttp.ClientSession() as client:
        wral = WralWeather(client, zipcode=ZIPCODE)
        curr_data = await wral.update_observation()

        curr_cond = wral.curr_dict["current_conditions"]
        print('Current Conditions', wral.curr_dict["current_conditions"])
        curr_ha_cond = wral2ha_condition(curr_cond)
        print('Current HA Conditions ', curr_ha_cond)
        print('Current Temp', wral.curr_dict["current_temperature"])
        print('Current Dew Point', wral.curr_dict["current_dew_point"])
        print('Current Relative Humidity',
              wral.curr_dict["current_relative_humidity"])
        print('Current Wind Direction',
              wral.curr_dict["current_wind_direction"])
        print('Current Wind Speed', wral.curr_dict["current_wind_speed"])
        print('Current Wind Bearing', wral.curr_dict["current_wind_bearing"])
        print('Current Wind Chill', wral.curr_dict["current_wind_chill"])
        print('Current Pressure', wral.curr_dict["current_pressure"])
        _LOGGER.debug("Current Dictionary: %s", wral.curr_dict)
        print('')

        # Dont create another session object,
        #   as one object is a connection pool.
        # async with aiohttp.ClientSession() as client2:
        forecast_data = await wral.update_forecast()
        i = 0
        for todays_forecast in wral.forecast_list:
            _LOGGER.debug("Today's Forecast %s ", todays_forecast)
            print("Day  ", i, "  Which Day      ",
                  todays_forecast["which_day"])
            iso_day = forecast_day2iso(todays_forecast["which_day"], i)
            _LOGGER.debug("Day %i Which ISO Day %s ", i, iso_day)
            print("Day  ", i, "  Condition      ",
                  todays_forecast["condition"])
            forecast_cond = todays_forecast["condition"]
            forecast_ha_cond = wral2ha_condition(forecast_cond)
            print("Day  ", i, "  HA Conditions  ", forecast_ha_cond)
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
            print("Day  ", i, "  Details:       ")
            print(" -", todays_forecast["detailed_description"])
            print("")
            i = i + 1

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

_LOGGER.debug("Finished Running App")
