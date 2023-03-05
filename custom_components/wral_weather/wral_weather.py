"""Weather component that handles meteorological data from WRAL TV."""
import logging
import aiohttp
import datetime

ERRORS = (aiohttp.ClientError)
_LOGGER = logging.getLogger(__name__)


#  The following is a left over from the web page screen scraping.
#  Icons are still specified by legacy url and this search technique
#   can still be used for these urls.
#
#  Strings to search on to get particular weather data items
#    The first string gets you to a unique section within
#    the HTML page for the item of interest.
#
#    The second string gets you to the start of the field
#    for the item of interest
#
#    The third string gets you to the end of the
#    field for the item of interest
#
CURRENT_WEATHER_SEARCH_STRINGS = {
    'conditions': ["/images/wx", 'weather-', '.png'],
    }

FORECAST_DAY_SEARCH_STRINGS = {
    'conditions': ['inline-svg', 'weather-', '.svg'],
    }
#
# Setup a dictionary lookup to translate wind directions
#   to bearings in units of degrees
#
wind_direction2degrees = {
    'North': 0,
    'North Northeast': 23,
    'Northeast': 45,
    'East Northeast': 68,
    'East': 90,
    'East Southeast': 113,
    'Southeast': 135,
    'South Southeast': 158,
    'South': 180,
    'South Southwest': 203,
    'Southwest': 225,
    'West Southwest': 248,
    'West': 270,
    'West Northwest': 292.5,
    'Northwest': 315,
    'North Northwest': 338,
    }

#
# Setup a Ordered List of 16 Wind Directions
#   starting with North (0 degrees)
#   and continuing every 22.5 degrees.
#   Add one more North at the end to handle "next one".
wind_directions = (
    'North',
    'North Northeast',
    'Northeast',
    'East Northeast',
    'East',
    'East Southeast',
    'Southeast',
    'South Southeast',
    'South',
    'South Southwest',
    'Southwest',
    'West Southwest',
    'West',
    'West Northwest',
    'Northwest',
    'North Northwest',
    'North'
    )

NUM_FORECAST_DAYS = 7
DEFAULT_ZIPCODE = '27606'
DEFAULT_CITYID = 8111

# URLS used 
#   "city_search" is used to search for a city id based 
#      on zipcode (or city name)k
#   "weather_pre" gets current and forecast weather data
#     for the given city id
URLS = {
    "city_search_pre" : "https://webapi.wral.com/api/city/search?query=",
    "weather_pre" : "https://webapi.wral.com/api/weather?city=",
}

# The following is a left over from the web page screen scraping.
# Icons are still specified by legacy url and this search function
#   can still be used to find the icon name from these urls.
def search_for_item(scope_start, scope_end, category_search_string,
                    item_start_string, item_end_string, data, iterations=1):
    """
    Using dictionary of defined search string,
      search a webpage looking for particular strings.
    'scope_start' and 'scope_end' define start and ending positions
      within the page for searching for a defined parameter.
    'category_search_string' is a string that gets a section
      of the web page near the parameter of interest.
    'item_start', 'item_end' define the strings that
      are adjacent to the parameter of interest.
    'data' contains the web page to be searched.
    'iterations' is a parameter of interest that may show
      up multiple times on a page. This specifies
      which one in postional order to get.
    """
    position = scope_start
    for i in range(0, iterations):
        position = data[position:].find(category_search_string) + position
        if position == -1:
            _LOGGER.debug("Warning: Could not find category %s",
                          category_search_string)
            return None
        offset = data[position + len(category_search_string):]\
            .find(item_start_string)
        if offset == -1:
            _LOGGER.debug("could not find item start")
            return None
        item_start = position + len(category_search_string) + \
            offset + len(item_start_string)
        offset2 = data[item_start:].find(item_end_string)
        if offset2 == -1:
            _LOGGER.debug("could not find item end")
            return None
        item_end = item_start + offset2
        item_value = data[item_start:item_end]
        position = item_end
        if scope_end is not None:
            if position > scope_end:
                return None
    return item_value

def wind_degrees2direction(degrees):
    """
    Compute the direction of the wind ex. 'North','East", etc.
    from degrees where 'North' is 0 degrees.
    """
    quadrant = int(degrees/22.5)
    if (degrees % 22.5 > 11.25):
        quadrant = quadrant +1
    return wind_directions[quadrant] 

def parse_current_conditions(curr_json):
    """
    Get the Current Conditions from the 
      'currentObservations' JSON data.
      Note: some of the numbers are strings, so need to convert.
    """
    curr_dict = {}

    # Get Current Conditions
    #  JSON data contains both a current Conditions string,
    #  and current conditons icon (which appears to be the same
    #  same as Legacy) which can also provide 'night' 'day' differentials.
    #  The legacy icon uses a URL that has a string nearly identical
    #  to the old way of parsing, so we'll use the old way 
    #  of parsing to find the name of this icon.
    curr_dict["current_conditions"] = curr_json['skyCondition']
    cwss = CURRENT_WEATHER_SEARCH_STRINGS
    curr_icon = curr_json['icon']
    curr_icon_condition = search_for_item(0, None, cwss['conditions'][0],
                                      cwss['conditions'][1],
                                      cwss['conditions'][2],
                                      curr_icon)
    curr_dict["current_icon_conditions"]= curr_icon_condition

    # Get the Current Temperature
    curr_dict["current_temperature"] = int(curr_json['temperature'])

    # Get the Current Dew Point Temperature
    curr_dict["current_dew_point"] = int(curr_json['dewPoint'])

    # Get the Current Humidity
    curr_dict["current_relative_humidity"] = curr_json['relativeHumidity']

    # Get the Current Wind Speed and Direction
    #   New API does not provide wind direction string
    #   so we'll compute one.
    #  Note: 'windDirection' is in degrees but can be None.
    curr_dict['current_wind_speed'] =  int(curr_json['windSpeed'])
    curr_dict['current_wind_direction'] = None
    wind_dir = curr_json['windDirection']
    if ( wind_dir != None):
        wind_dir =  int(wind_dir)
        curr_dict['current_wind_direction'] =  \
                 wind_degrees2direction(wind_dir)
    curr_dict['current_wind_bearing'] = wind_dir

    # Get the Current Wind Chill/Heat Index. 
    #  Note: Could possibly be empty string
    wc = curr_json['windChill']
    if ( wc.isnumeric() ):
        curr_dict["current_wind_chill"] = int(wc)
    else:
        curr_dict["current_wind_chill"] = None
    hi = curr_json['heatIndex']
    if ( hi.isnumeric() ):
        curr_dict["current_heat_index"] = int(hi)
    else:
        curr_dict["current_heat_index"] = None

    # Get the Current Pressure
    curr_dict["current_pressure"] = float(curr_json['pressure'])

    # Get the Current visibility
    curr_dict["current_visibility"] = float(curr_json['visibility'])

    return curr_dict


def parse_forecast(forecast_day_data):
    """
    Get the 7 Day Forecast from the 
      'forecastDetails' JSON data list of days.
      Note: there is also "hours" data for the next
        7 days or so, but this data is ignored
    """

    fdss = FORECAST_DAY_SEARCH_STRINGS
    day_dict = {}
    forecast_list = []

    iterations = NUM_FORECAST_DAYS

    cwss = CURRENT_WEATHER_SEARCH_STRINGS

    for i in range(0, iterations):
        forecast_dayN_data = forecast_day_data['forecastDetails'][i]
        _LOGGER.debug("========Forecast Day %i Details======== ", i)
        _LOGGER.debug("%s", forecast_dayN_data)
        _LOGGER.debug("")

        # re-init data_dict to empty.
        # Otherwise the append to forecast will mess up
        day_dict = {}
        day_timestamp = forecast_dayN_data['forecastDate']['timestamp']
        dt_object = datetime.datetime.fromtimestamp(day_timestamp)
        day_dict["which_day"] = dt_object.strftime("%a")


        # Find forecast Condition for day N. Ex. clear-night
        #   JSON data contains both a Forecast conditions string,
        #   and Forecast conditons icon (which appears to be the same
        #   same as Legacy).
        #   The legacy icon uses a URL that has a string nearly identical
        #   to the old way of parsing, so we'll use the old way
        #   of parsing to find the name of this icon.
        # Note: I find from time to time that parameters
        #   that should contain a string numeric value are sometimes empty string
        #   for example forecast low temperature.
        day_day_icon = forecast_dayN_data['dayIcon']
        day_icon_condition = search_for_item(0, None, cwss['conditions'][0],
                                      cwss['conditions'][1],
                                      cwss['conditions'][2],
                                      day_day_icon)
        day_dict["icon_condition"]= day_icon_condition
        day_dict["condition"] = forecast_dayN_data['dayCondition']

        # Find forecast high temperature for day N.
        temp_data = forecast_dayN_data['high']
        if ( temp_data.isnumeric() ):
            day_dict["high_temperature"] = int(temp_data)
        else:
            day_dict["high_temperature"] = 0

        # Find forecast low temperature for day N.
        temp_data = forecast_dayN_data['low']
        if ( temp_data.isnumeric() ):
            day_dict["low_temperature"] = int(temp_data)
        else:
            day_dict["low_temperature"] = 0

        # Find forecast day descriptions for day N.
        day_dict["detailed_day"] = forecast_dayN_data['textDay']

        # Find forecast night descriptions for day N.
        day_dict["detailed_night"] = forecast_dayN_data['textNight']

        # Combine forecast day and night descriptions for day N into one.
        day_dict["detailed_description"] = \
            day_dict["detailed_day"] + "For the night: " + \
            day_dict["detailed_night"]
        del day_dict["detailed_day"]
        del day_dict["detailed_night"]

        # Find forecast Sunrise for day N.
        day_dict["sunrise"] = forecast_dayN_data['sunrise']['string']

        # Find forecast Sunset for day N.
        day_dict["sunset"] = forecast_dayN_data['sunset']['string']

        # Find forecast precipitation probability for day N.
        day_dict["precipitation"] = int(forecast_dayN_data['dayPop'])

        # Find forecast wind information for day N.
        #   Note: New API does not provide a wind bearing in degrees
        #     so we'll compute one.
        temp_data = forecast_dayN_data['windSpeed']
        if ( temp_data.isnumeric() ):
            day_dict["wind_speed"] = int(temp_data)
        else:
            day_dict["wind_speed"] = 0
        day_dict["wind_direction"] = forecast_dayN_data['windDirection']
        day_dict["wind_bearing"] = \
                wind_direction2degrees[day_dict['wind_direction']]

        forecast_list.append(day_dict)

    return forecast_list


class WralWeather:
    """WRAL object for gleaning and storing information from Web page"""
    def __init__(self, session, zipcode='27606'):
        _LOGGER.debug("Initing wral zipcode: %s", zipcode)
        if zipcode is None:
            self.zipcode = DEFAULT_ZIPCODE
        else:
            self.zipcode = zipcode
        self.client = session
        self._get_city_url = URLS['city_search_pre'] + self.zipcode
        self._get_weather_url = URLS['weather_pre']
        self.curr_dict = {}
        self.forecast_list = []

    async def update_observation_and_forecast(self):
        """Retrieve Current Observation Web page"""

        _LOGGER.debug("First query for city id ... ")
        async with self.client.get(self._get_city_url) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get City ID %s", status)
                city_id = DEFAULT_CITYID
            finally:
                _LOGGER.debug("Getting City ID..Status= %s",
                              resp.status)
                city_json = await resp.json()
                _LOGGER.debug("city_json: %s", city_json)
                city_id = city_json['data'][0]['id']

            _LOGGER.debug("city_id %s", city_id)

        _LOGGER.debug("Now query for weather... ")
        self._get_weather_url = URLS['weather_pre'] + city_id
        async with self.client.get(self._get_weather_url) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get Weather %s", status)
            finally:
                _LOGGER.debug("Getting Weather..Status= %s",
                              resp.status)
            weather_json = await resp.json()
            current_json = weather_json['data']['currentObservations']
            _LOGGER.debug("========Update Current Observations======== ")
            _LOGGER.debug("current_json: %s", current_json)
            _LOGGER.debug("")

            self.curr_dict = parse_current_conditions(current_json)

            #Process 7 day Forecast
            _LOGGER.debug("========Update Forecasts========")
            forecast_day_json = weather_json['data']['forecast']
            self.forecast_list = parse_forecast(forecast_day_json)

            return True
