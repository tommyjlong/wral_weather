"""Weather component that handles meteorological data from WRAL TV."""
import logging
import aiohttp

ERRORS = (aiohttp.ClientError)
_LOGGER = logging.getLogger(__name__)


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
    'conditions': ["/images\\/wx\\", 'weather-', '.svg'],
    'temperature': ['>Temperature<\\/h3>', '>', '&'],
    'dew_point': ['>Dew Point<\\/h3>', '>', '&'],
    'rel_humidity': ['>Relative Humidity<\\/h3>', '>', '%'],
    'wind': ['>Wind<\\/h3>', '>', '<'],
    'wind_chill': ['>Wind Chill<\\/h3>', '>', '&'],
    'pressure': ['>Pressure<\\/h3>', '>', '<']
    }

FORECAST_DAY_SEARCH_STRINGS = {
    'which_day': ['<h4 class=\\"h-6 w-one time\\"', '>', '<'],
    'conditions': ['inline-svg', 'weather-', '.svg'],
    'high_temp': ['<div class=\\"temperature\\">', '\\"high\\">', '<'],
    'low_temp': ['<div class=\\"temperature\\">', '\\"low\\">', '<'],
    'detailed_day': ['"detailed-item day', '>', '<'],
    'detailed_night': ['"detailed-item night', '>', '<'],
    'sunrise': ['>Sunrise<\\/h6>', '>', '<'],
    'sunset': ['>Sunset<\\/h6>', '>', '<'],
    'precip': ['>Precip<\\/h6>', '>', '<'],
    'wind': ['>Wind<\\/h6>', '>', '<'],
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

# List of discovered conditions found thus far from web page
#   day-clear
#   day-mostly-clear  night-mostly-clear
#   day-partly-cloudy night-partly-cloudy
#   day-mostly-cloudy night-mostly-cloudy
#   cloudy
#   drizzle
#   rain-showers
#   thunderstorms-rain
#   misc-fog

NUM_FORECAST_DAYS = 7
DEFAULT_ZIPCODE = '27606'

# URLS used and other URLs of interest:
#
# FULL CURRENT: "https://www.wral.com/weather_current_conditions/13264720/
#                 ?location=ZIPCODE&action=update_location"
# FULL FORECAST: "https://www.wral.com/weather/
#                 ?location=ZIPCODE&action=update_location",
# TEST URLS:
#   "current_pre": "https://www.wral.com/test_for_failure",
#   "current_pre": "https://www.test_for_failure",
#   "forecast_pre": "https://www.wral.com/test_for_failure",
#   "forecast_pre": "https://www.test_for_failure.com",
URLS = {
    "forecast_pre": "https://www.wral.com/weather/?location=",
    "forecast_post": "&action=update_location",
    "current_pre": "https://www.wral.com/\
                    weather_current_conditions/13264720/?location=",
    "current_post": "&action=update_location"
}


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


def split_wind_info(curr_wind):
    """
    Split the wind information into speed, direction and bearing
    Wind string is something like:
      Calm
      North Northeast 11 mph
      Northeast 11 mph
    """
    speed = None
    direction = None
    bearing = None

    wind_info = curr_wind.split(' ')
    word_count = len(wind_info)

    if word_count == 0:
        return speed, direction
    if (wind_info[0]) == "Calm":
        speed = 0
        return speed, direction, bearing
    if wind_info[word_count-2].isdigit:
        speed = int(wind_info[word_count - 2])
    if word_count == 4:
        direction = wind_info[0] + " " + wind_info[1]
    else:
        direction = wind_info[0]

    bearing = wind_direction2degrees[direction]

    return (speed, direction, bearing)


def clean_up_numeric(string2number):
    """
    Assuming the string has only one number (integer or float, or negative)
    remove any other and extraneous characters from the string.
    Ex. sometimes results are ' 38&deg etc'
    """
    if string2number is not None:
        string2number = ''.join((ch if ch in '-0123456789.' else '')
                                for ch in string2number)
        string2number = string2number.strip()
        if string2number == '.' or string2number == '-' or string2number == '':
            return None
        if '.' in string2number:
            string2number = float(string2number)
        else:
            string2number = int(string2number)

    return string2number


def parse_current_conditions(curr_data):
    """
    Search and Parse the Current Conditions web page for
    the current condition items of interest.
    The Current Condtion web page will contain data from both a given zip code
    and from the WRAL studio.  This routine only gets the former.
    """
    curr_dict = {}
    cwss = CURRENT_WEATHER_SEARCH_STRINGS
    curr_conditions = search_for_item(0, None, cwss['conditions'][0],
                                      cwss['conditions'][1],
                                      cwss['conditions'][2],
                                      curr_data)
    curr_dict["current_conditions"] = curr_conditions

    # Get the Current Temperature
    curr_temp = search_for_item(0,
                                None,
                                cwss['temperature'][0],
                                cwss['temperature'][1],
                                cwss['temperature'][2],
                                curr_data)
    curr_temp = clean_up_numeric(curr_temp)
    curr_dict["current_temperature"] = curr_temp

    # Get the Current Dew Point Temperature
    curr_dew_point = search_for_item(0,
                                     None,
                                     cwss['dew_point'][0],
                                     cwss['dew_point'][1],
                                     cwss['dew_point'][2],
                                     curr_data)
    curr_dew_point = clean_up_numeric(curr_dew_point)
    curr_dict["current_dew_point"] = curr_dew_point

    # Get the Current Humidity
    curr_rel_humidity = search_for_item(0,
                                        None,
                                        cwss['rel_humidity'][0],
                                        cwss['rel_humidity'][1],
                                        cwss['rel_humidity'][2],
                                        curr_data)
    curr_rel_humidity = clean_up_numeric(curr_rel_humidity)
    curr_dict["current_relative_humidity"] = curr_rel_humidity

    # Get the Current Wind Speed and Direction
    curr_wind = search_for_item(0,
                                None,
                                cwss['wind'][0],
                                cwss['wind'][1],
                                cwss['wind'][2],
                                curr_data)
    curr_wind_speed, curr_wind_direction, curr_wind_bearing = \
        split_wind_info(curr_wind)
    curr_dict["current_wind_speed"] = curr_wind_speed
    curr_dict["current_wind_direction"] = curr_wind_direction
    curr_dict["current_wind_bearing"] = curr_wind_bearing

    # Get the Current Wind Chill.
    # Note: This is sometimes absent when wind speed is low.
    curr_wind_chill = search_for_item(0,
                                      None,
                                      cwss['wind_chill'][0],
                                      cwss['wind_chill'][1],
                                      cwss['wind_chill'][2],
                                      curr_data)
    curr_wind_chill = clean_up_numeric(curr_wind_chill)
    curr_dict["current_wind_chill"] = curr_wind_chill

    # Get the Current Pressure
    curr_pressure = search_for_item(0,
                                    None,
                                    cwss['pressure'][0],
                                    cwss['pressure'][1],
                                    cwss['pressure'][2],
                                    curr_data)
    curr_pressure = clean_up_numeric(curr_pressure)
    curr_dict["current_pressure"] = curr_pressure

    return curr_dict


def parse_forecast(forecast_day_data):
    """
    Search and Parse the 7 Day Forecast web page.
    """

    fdss = FORECAST_DAY_SEARCH_STRINGS
    day_dict = {}
    forecast_list = []

    data = forecast_day_data
    scope_start = 0
    iterations = NUM_FORECAST_DAYS
    start_search = scope_start

    start_day = '<li class=\\"weather-row'  # escape
    end_day = start_day

    for i in range(0, iterations):
        offset = data[start_search:].find(start_day)
        if offset == -1:
            _LOGGER.debug("Can not find start of given day")
            break
        else:
            day_start = offset + start_search
            cat_start = day_start
        day_end = data[day_start+len(start_day):].find(end_day)
        if day_end == -1:
            _LOGGER.debug("Can not find end of given day")
        else:
            day_end = day_end + len(end_day) + day_start

        start_search = day_end - 3
        cat_end = None

        # re-init data_dict to empty.
        # Otherwise the append to forecast will mess up
        day_dict = {}

        # Find day N by name (3 chars)
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['which_day'][0],
                                 fdss['which_day'][1],
                                 fdss['which_day'][2],
                                 forecast_day_data, 1)
        day_dict["which_day"] = result

        # Find forecast condition for day N. Ex. clear-night
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['conditions'][0],
                                 fdss['conditions'][1],
                                 fdss['conditions'][2],
                                 forecast_day_data, 1)
        day_dict["condition"] = result

        # Find forecast high temperature for day N.
        # Note: at current night this is not made available
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['high_temp'][0],
                                 fdss['high_temp'][1],
                                 fdss['high_temp'][2],
                                 forecast_day_data, 1)
        result = clean_up_numeric(result)
        day_dict["high_temperature"] = result

        # Find forecast low temperature for day N.
        result = search_for_item(cat_start,
                                 cat_end, fdss['low_temp'][0],
                                 fdss['low_temp'][1],
                                 fdss['low_temp'][2],
                                 forecast_day_data, 1)
        result = clean_up_numeric(result)
        day_dict["low_temperature"] = result

        # Find forecast day descriptions for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['detailed_day'][0],
                                 fdss['detailed_day'][1],
                                 fdss['detailed_day'][2],
                                 forecast_day_data, 1)
        day_dict["detailed_day"] = result

        # Find forecast night descriptions for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['detailed_night'][0],
                                 fdss['detailed_night'][1],
                                 fdss['detailed_night'][2],
                                 forecast_day_data, 1)
        day_dict["detailed_night"] = result

        # Combine forecast day and night descriptions for day N into one.
        day_dict["detailed_description"] = \
            day_dict["detailed_day"] + "For the night: " + \
            day_dict["detailed_night"]
        del day_dict["detailed_day"]
        del day_dict["detailed_night"]

        # Find forecast Sunrise for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['sunrise'][0],
                                 fdss['sunrise'][1],
                                 fdss['sunrise'][2],
                                 forecast_day_data, 1)
        day_dict["sunrise"] = result

        # Find forecast Sunset for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['sunset'][0],
                                 fdss['sunset'][1],
                                 fdss['sunset'][2],
                                 forecast_day_data, 1)
        day_dict["sunset"] = result

        # Find forecast precipitation probability for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['precip'][0],
                                 fdss['precip'][1],
                                 fdss['precip'][2],
                                 forecast_day_data, 1)
        result = clean_up_numeric(result)
        day_dict["precipitation"] = result

        # Find forecast wind information for day N.
        result = search_for_item(cat_start,
                                 cat_end,
                                 fdss['wind'][0],
                                 fdss['wind'][1],
                                 fdss['wind'][2],
                                 forecast_day_data, 1)
        forecast_wind_speed, forecast_wind_direction,\
            forecast_wind_bearing =\
            split_wind_info(result)
        day_dict["wind_speed"] = forecast_wind_speed
        day_dict["wind_direction"] = forecast_wind_direction
        day_dict["wind_bearing"] = forecast_wind_bearing

        forecast_list.append(day_dict)

    return forecast_list


class WralWeather:
    """WRAL object for gleaning and storing information from Web page"""
    def __init__(self, session, zipcode='27606'):
        _LOGGER.debug("Initing wral: %s", zipcode)
        if zipcode is None:
            self.zipcode = DEFAULT_ZIPCODE
        else:
            self.zipcode = zipcode
        self.client = session
        self._get_current_url = URLS['current_pre'] + \
            self.zipcode + URLS['current_post']
        self._get_forecast_url = URLS['forecast_pre'] + \
            self.zipcode + URLS['forecast_post']
        self.curr_dict = {}
        self.forecast_list = []

    async def update_observation(self):
        """Retrieve Current Observation Web page"""
        _LOGGER.debug("update current observation... ")

        async with self.client.get(self._get_current_url) as resp:
            _LOGGER.debug("Got current observation... Status %s", resp.status)
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get Current Observation %s", status)
            finally:
                _LOGGER.debug("Updating Current Observation..Status= %s",
                              resp.status)
            curr_data = await resp.text()
            self.curr_dict = parse_current_conditions(curr_data)
            return curr_data

    async def update_forecast(self):
        """Retrieve 7 day Forecast Web page"""
        _LOGGER.debug("update forecasts ... ")

        async with self.client.get(self._get_forecast_url) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                _LOGGER.debug("Failed to get Forecast from website %s", status)
            finally:
                _LOGGER.debug("Updating Forecast..Status= %s",
                              resp.status)
            forecast_day_data = await resp.text()
            self.forecast_list = parse_forecast(forecast_day_data)
            return forecast_day_data
