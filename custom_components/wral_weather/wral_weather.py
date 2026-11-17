"""Weather component that handles meteorological data from WRAL TV."""
import logging
import aiohttp
import datetime
import pytz

ERRORS = (aiohttp.ClientError)
_LOGGER = logging.getLogger(__name__)

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

NUM_FORECAST_DAYS = 7  #v2 API supports today + 6 additional days
NUM_FORECAST_HOURS = 12
DEFAULT_ZIPCODE = '27606'
#add v2 API defaults
DEFAULT_LAT  = 35.7796   #Downtown Raleigh
DEFAULT_LONG = -78.6382  #Downtown Raleigh
DEFAULT_UNITS = "imperial"  #can be "metric"

# URLS used 
#   "curr_conditions_pre" gets the current observations
#   "zip_search_pre" is used to search for a latitude/longitude based 
#      on zipcode. (Can also get a city from this, but not used)
#   "forecast_hourly_pre" gets hourly forecast weather data for given lat/long
#   "forecast_daily_pre" gets daily forecast weather data for given lat/long
URLS = {
    "curr_conditions_pre": "https://api.wral.com/wxdata/v2/conditions/",
    "zip_search_pre"     : "https://api.wral.com/geo/v1/zips/",
    "forecast_daily_pre" : "https://api.wral.com/wxdata/v2/forecast/daily/",
    "forecast_hourly_pre": "https://api.wral.com/wxdata/v2/forecast/hourly/",
}

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
    """
    curr_dict = {}

    # Current Conditions (code/label/Icon)
    #  JSON data contains both a current conditions "code" (Ex. "clear-day"), 
    #    and a "label" ("Clear").
    #  The "code" is nearly identical to v1 APIs current conditions "icon".
    #    (which itself is the same as pre-v1 API). 
    #    This also provides 'night' vs. 'day' differentials.
    curr_code_condition = curr_json['condition']['code']
    curr_dict["current_conditions"]       = curr_code_condition #v2
    curr_dict["current_code_conditions"]  = curr_code_condition #v2
    curr_dict["current_label_conditions"] = curr_json['condition']['label'] 

    # Get the Current Temperature
    curr_dict["current_temperature"] = int(curr_json['temperature'])

    # Get the Current Dew Point Temperature
    curr_dict["current_dew_point"] = int(curr_json['dew_point']) 

    # Get the Current Humidity
    curr_dict["current_relative_humidity"] = curr_json['humidity_pct']

    # Get the Current Wind Speed, Direction, and Gusts
    #  v2 Direction is in degrees (i.e. "bearing") and cardinal (ex."SW")
    #  Will continue using legacy Direction string: "North", "North Northeast", etc.
    wind_speed = curr_json['wind']['speed']
    if ( wind_speed != None):
        curr_dict['current_wind_speed'] = wind_speed #numeric
    else:
        curr_dict['current_wind_speed'] = 0
    
    curr_dict['current_wind_direction'] = None    
    wind_dir = curr_json['wind']['direction_deg']
    if ( wind_dir != None ):
        if ( wind_dir < 0 or wind_dir > 360 ):
            wind_dir = 0
        else:
            curr_dict['current_wind_direction'] =  \
                 wind_degrees2direction(wind_dir)  #direction is like North, South,...
    else:
        wind_dir = 0

    curr_dict['current_wind_bearing'] = wind_dir  #bearing is in degrees
    curr_dict['current_wind_cardinal'] = curr_json['wind']['direction_cardinal']

    wind_gusts = curr_json['wind']['gust']
    if ( wind_gusts != None):
        curr_dict['current_wind_gusts'] = wind_gusts
    else:
        curr_dict['current_wind_gusts'] = 0
        
    # Get the Current Wind Chill/Heat Index. 
    #  v2 only provides "feels like" (no longer head index, wind chill)
    #  Note: Could possibly be empty string
    wc = curr_json['feels_like']
    if ( wc != None ):
        curr_dict["current_wind_chill"] = wc
    else:
        curr_dict["current_wind_chill"] = None
    hi = wc
    if ( hi != None ):
        curr_dict["current_heat_index"] = hi
    else:
        curr_dict["current_heat_index"] = None

    # Get the Current Hourly Precipitation
    #  v2 no longer provides this, but does provide last_hour (so use this)
    #  Note: Could possibly be None (in which case, make it 0)
    precip_last_hour  = curr_json['precipitation']['last_hour']
    precip_chance_pct = curr_json['precipitation']['chance_pct']
    precip_amount     = curr_json['precipitation']['amount']
    if( precip_last_hour != None):
        curr_dict["current_hourly_precip"] = float(precip_last_hour)
    else:
        curr_dict["current_hourly_precip"] = float(0)

    # Get the Current Barometric Pressure
    curr_dict["current_pressure"] = float(curr_json['pressure']['value'])

    # Get the Current visibility
    curr_dict["current_visibility"] = float(curr_json['visibility'])

    return curr_dict


def parse_forecast_daily(forecast_day_data):
    """
    Get the 7 Day Forecast from the 
      'periods' JSON data list of days.
    """

    day_dict = {}
    forecast_daily_list = []

    iterations = NUM_FORECAST_DAYS

    for i in range(0, iterations):
        forecast_dayN_data = forecast_day_data['periods'][i]

        _LOGGER.debug("========Forecast Day %i Details======== ", i)
        _LOGGER.debug("%s", forecast_dayN_data)
        _LOGGER.debug("")

        # re-init data_dict to empty.
        # Otherwise the append to forecast will mess up
        day_dict = {}

        #convert v2 date string to iso timezone aware
        date_str = forecast_dayN_data['date'] #ex. "2026-11-11"
        dt_local = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        day_timestamp = dt_local.timestamp()
#       day_timestamp = forecast_dayN_data['forecastDate']['timestamp']
        dt_object = datetime.datetime.fromtimestamp(day_timestamp)
##      date_str = forecast_dayN_data['date']
##      dt_object = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        day_dict["which_day"] = dt_object.strftime("%a")
        tz = datetime.datetime.now().astimezone().tzinfo
        day_dict["which_day_dt"] = datetime.datetime.fromtimestamp(day_timestamp, tz).isoformat()
##      # Convert to ISO 8601 string
##      day_dict["which_day_dt"] = dt_object.isoformat()

        # Find forecast Condition for day N. Ex. clear-night
        #   JSON data contains both a Forecast conditions code,
        #   and Forecast conditons label The code is the key indicator
        day_dict["condition_code"]= forecast_dayN_data['day']['condition']['code']
        day_dict["condition"]= day_dict["condition_code"]
        day_dict["condition_label"] = forecast_dayN_data['day']['condition']['label']

        # Find forecast high temperature for day N.
        temp_data = forecast_dayN_data['high']
        if ( temp_data != None ):
            day_dict["high_temperature"] = temp_data
        else:
            day_dict["high_temperature"] = 0

        # Find forecast low temperature for day N.
        temp_data = forecast_dayN_data['low']
        if ( temp_data != None ):
            day_dict["low_temperature"] = temp_data
        else:
            day_dict["low_temperature"] = 0

        # Find forecast day descriptions for day N.
        #  Note: v2 API some days returns null
        temp_txt = forecast_dayN_data['day']['narrative']
        if( temp_txt != None ):
            day_dict["detailed_day"] = forecast_dayN_data['day']['narrative']
        else:
            day_dict["detailed_day"] = "No Forecast. "

        # Find forecast night descriptions for day N.
        #  Note: v2 API some days returns null
        temp_txt = forecast_dayN_data['night']['narrative']
        if( temp_txt != None ):
            day_dict["detailed_night"] = forecast_dayN_data['night']['narrative']
        else:
            day_dict["detailed_night"] = "No forecast. "

        # Combine forecast day and night descriptions for day N into one.
        day_dict["detailed_description"] = \
            "For the day: " + day_dict["detailed_day"] + " "\
            "For the night: " + \
            day_dict["detailed_night"]
        del day_dict["detailed_day"]
        del day_dict["detailed_night"]

        # Find forecast Sunrise for day N.
        # v2 no longer supports.  Here for historic reasons
        day_dict["sunrise"] = "Unsupported"

        # Find forecast Sunset for day N.
        # v2 no longer supports.  Here for historic reasons
        day_dict["sunset"] = "Unsupported"

        # Find forecast precipitation probability for day N.
        day_dict["precipitation"] = int(forecast_dayN_data['day']['precipitation']['chance_pct'])

        # Get the Forecast Wind Speed, Direction, and Gusts for day N.
        #  v2 Direction is in degrees (i.e. "bearing") and cardinal (ex."SW")
        #  Will continue using legacy Direction string: "North", "North Northeast", etc.
        wind_data = forecast_dayN_data['day']['wind']
        if ( wind_data['speed'] != None ):
            day_dict['wind_speed'] = wind_data['speed']
        else:
            day_dict["wind_speed"] = 0


        day_dict['wind_direction'] = None    
        wind_dir = forecast_dayN_data['day']['wind']['direction_deg']
        if ( wind_dir != None ):
            if ( wind_dir < 0 or wind_dir > 360 ):
                wind_dir = 0
            else:
                day_dict['wind_direction'] =  \
                     wind_degrees2direction(wind_dir)  #direction is like North, South,...
        else:
            wind_dir = 0

        day_dict["wind_bearing"]   = forecast_dayN_data['day']['wind']['direction_deg']
        day_dict['wind_cardinal']  = forecast_dayN_data['day']['wind']['direction_cardinal'] #Ex. "NNW"

        # Get the Forecast Day Humidity
        #  new for v2
        day_dict["relative_humidity"] = forecast_dayN_data['day']['humidity_pct']

        # Find Heat Index for day N.
        temp_data = forecast_dayN_data['day']['heat_index']
        if ( temp_data != None ):
            day_dict["heat_index"] = temp_data
        else:
            day_dict["heat_index"] = day_dict["high_temperature"]

        # Find Wind Chill for day N.
        temp_data = forecast_dayN_data['day']['wind_chill']
        if ( temp_data != None ):
            day_dict["wind_chill"] = temp_data
        else:
            day_dict["wind_chill"] = day_dict["low_temperature"]

        # Find Dew Point for day N.
        temp_data = forecast_dayN_data['day']['dew_point']
        if ( temp_data != None ):
            day_dict["dew_point"] = temp_data
        else:
            day_dict["dew_point"] = 0

        forecast_daily_list.append(day_dict)

    return forecast_daily_list


def parse_forecast_hourly(forecast_hour_data):
    """
    Get the N Hour Forecast from the 
      'periods' JSON data list of hours.
    """

    hour_dict = {}
    forecast_hourly_list = []

    iterations = NUM_FORECAST_HOURS


    for i in range(0, iterations):
        forecast_hourN_data = forecast_hour_data['periods'][i]
        _LOGGER.debug("========Forecast Hour %i Details======== ", i)
        _LOGGER.debug("%s", forecast_hourN_data)
        _LOGGER.debug("")

        # re-init data_dict to empty.
        # Otherwise the append to forecast will mess up
        hour_dict = {}
        date_str = forecast_hourN_data['time'] #"2026-11-12T02:00:00Z" iso timezone unaware
        utc_dt = datetime.datetime.fromisoformat(date_str)
        dt_local = utc_dt.astimezone()

##      dt_local = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        hour_timestamp = dt_local.timestamp()
#       hour_timestamp = forecast_hourN_data['forecastDate']['timestamp']
    
        tz = datetime.datetime.now().astimezone().tzinfo
       #dt_object = datetime.datetime.fromtimestamp(hour_timestamp)
       #hour_dict["which_hour"] = dt_object.strftime("%a")
        hour_dict["which_hour_dt"] = datetime.datetime.fromtimestamp(hour_timestamp, tz).isoformat()

        # Find forecast Condition for hour N. Ex. clear-night
        #   JSON data contains both a Forecast conditions code,
        #   and Forecast conditons label The code is the key indicator
        hour_dict["condition"]= forecast_hourN_data['condition']['code']
        hour_dict["condition_code"] = hour_dict["condition"]
        hour_dict["condition_label"] = forecast_hourN_data['condition']['label']

        # Find forecast temperature for hour N.
        temp_data = forecast_hourN_data['temperature']
        if ( temp_data != None ):
            hour_dict["temperature"] = temp_data
        else:
            hour_dict["temperature"] = 0

        # Find forecast precipitation probability for hour N.
        hour_dict["precipitation"] = int(forecast_hourN_data['precipitation']['chance_pct'])

        # Find forecast wind information for hour N.
        #   Note: v1 API does not provide a wind bearing in degrees
        #     so we'll compute one.
#       temp_data = forecast_hourN_data['windSpeed']
#       if ( temp_data.isnumeric() ):
#           hour_dict["wind_speed"] = int(temp_data)
#       else:
#           hour_dict["wind_speed"] = 0
#       hour_dict["wind_direction"] = forecast_hourN_data['windDirection']
#       hour_dict["wind_bearing"] = \
#               wind_direction2degrees[hour_dict['wind_direction']]
        wind_data = forecast_hourN_data['wind']
        if ( wind_data['speed'] != None ):
            hour_dict['wind_speed'] = wind_data['speed']
        else:
            hour_dict["wind_speed"] = 0

        hour_dict['wind_direction'] = None    
        wind_dir = forecast_hourN_data['wind']['direction_deg']
        if ( wind_dir != None ):
            if ( wind_dir < 0 or wind_dir > 360 ):
                wind_dir = 0
            else:
                hour_dict['wind_direction'] =  \
                     wind_degrees2direction(wind_dir)  #direction is like North, South,...
        else:
            wind_dir = 0

        hour_dict["wind_bearing"]   = forecast_hourN_data['wind']['direction_deg']
        hour_dict['wind_cardinal']  = forecast_hourN_data['wind']['direction_cardinal'] #Ex. "NNW"



#       hour_dict['wind_direction'] = forecast_hourN_data['wind']['direction_cardinal']
#       hour_dict["wind_bearing"]   = forecast_hourN_data['wind']['direction_deg']
#
#       # Find forecast humidity for hour N.
        hour_dict["humidity"] = forecast_hourN_data['humidity_pct']
 
        # Find forecast dewpoint for hour N.
        temp_data = forecast_hourN_data['dew_point']
        if ( temp_data != None ):
            hour_dict["dew_point"] = temp_data
        else:
            hour_dict["dew_point"] = 0

        # Find forecast heat index  for hour N.
        temp_data = forecast_hourN_data['heat_index']
        if ( temp_data != None ):
            hour_dict["heat_index"] = temp_data
        else:
            hour_dict["heat_index"] = hour_dict["temperature"]

        # Find forecast wind chill (an int not a string) for hour N.
        temp_data = forecast_hourN_data['wind_chill']
        if ( temp_data != None ):
            hour_dict["wind_chill"] = temp_data
        else:
            hour_dict["wind_chill"] = hour_dict["temperature"]

        # Find forecast cloud cover for hour N.
        temp_data = forecast_hourN_data['cloud_cover_pct']
        if ( temp_data != None ):
            hour_dict["cloud_cover"] = int(temp_data)
        else:
            hour_dict["cloud_cover"] = 0

        forecast_hourly_list.append(hour_dict)

    return forecast_hourly_list

class WralWeather:
    """WRAL object for gleaning and storing information from Web page"""
    def __init__(self, session, latitude, longitude, zipcode='27606'):

        _LOGGER.debug("Initing wral zipcode: %s", zipcode)
        if zipcode is None:
            self.zipcode = DEFAULT_ZIPCODE
        else:
            self.zipcode = zipcode

        self.latitude = latitude
        self.longitude = longitude
        _LOGGER.debug("Initing wral lat: %s long: %s", self.latitude, self.longitude)

        if latitude is not None:
            self.latitude = f"{latitude:.6f}"
#       else:
#           self.latitude =  f"{DEFAULT_LAT:.4f}"
        
        if longitude is not None:
            self.longitude = f"{longitude:.6f}"
#       else:
#           self.longitude = f"{DEFAULT_LONG:.4f}"


        self.client = session

       #self._get_city_url = URLS['city_search_pre'] + self.zipcode
        self._get_zip_url = URLS['zip_search_pre'] + self.zipcode + "/cities"
       #self._get_weather_url = URLS['weather_pre']
       #self._get_curr_cond = URLS['curr_conditions_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude
       #self._get_forecast_daily  = URLS['forecast_daily_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude
       #self._get_forecast_hourly = URLS['forecast_hourly_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude
        self.curr_dict = {}
        self.forecast_daily_list = []
        self.forecast_hourly_list = []

    async def update_observation_and_forecast(self):
        if( (self.latitude is None) or (self.longitude is None) ):
            # The following can be used to query for latitude/longitude based on zip code
            _LOGGER.debug("Incomplete lat/long. Need to query for latitude/longitude based on zip code ... ")
            async with self.client.get(self._get_zip_url) as resp:
                try:
                    # assert resp.status == 200
                    resp.raise_for_status()
                except ERRORS as status:
                    # except:
                    _LOGGER.debug("Failed to get Lat/Long from Zipcode %s", status)
                    zip2latitude  = DEFAULT_LAT
                    zip2lontitude = DEFAULT_LONG
                    self.longitude = f"{zip2longitude:.6f}"
                    self.latitude =  f"{zip2latitude:.6f}"
                finally:
                    _LOGGER.debug("Got Lat/Lon from Zipcode ..Status= %s",
                                  resp.status)
                    zip_json = await resp.json()
                    _LOGGER.debug("zip_json: %s", zip_json)
                    zip2latitude  = zip_json['centroid']['lat']
                    zip2longitude = zip_json['centroid']['lon']
                    self.longitude = f"{zip2longitude:.6f}"
                    self.latitude =  f"{zip2latitude:.6f}"
                _LOGGER.debug("Found latitude=%f longitude=%f", zip2latitude, zip2longitude)

        self._get_curr_cond = URLS['curr_conditions_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude
       #_LOGGER.debug("Curr Cond URL %s",self._get_curr_cond)
        self._get_forecast_daily  = URLS['forecast_daily_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude
        self._get_forecast_hourly = URLS['forecast_hourly_pre'] + "point?lat=" + self.latitude + "&lon=" + self.longitude


        """Retrieve Current Observation Web page"""
        _LOGGER.debug("v2 API query for current... ")

        async with self.client.get(self._get_curr_cond) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get v2 Current %s", status)
            finally:
                _LOGGER.debug("Getting v2 Current..Status= %s",
                              resp.status)
            resp = await resp.json()
            current_v2_json = resp['data']['observation']
            _LOGGER.debug("========Update Current v2 Observations======== ")
            _LOGGER.debug("current_v2_json: %s", current_v2_json)
            _LOGGER.debug("")
           #self.curr_dict = parse_current_conditions(current_json)
            self.curr_dict = parse_current_conditions(current_v2_json)

#       _LOGGER.debug("First query for city id ... ")
#       async with self.client.get(self._get_city_url) as resp:
#           try:
#               # assert resp.status == 200
#               resp.raise_for_status()
#           except ERRORS as status:
#               # except:
#               _LOGGER.debug("Failed to get City ID %s", status)
#               city_id = DEFAULT_CITYID
#           finally:
#               _LOGGER.debug("Getting City ID..Status= %s",
#                             resp.status)
#               city_json = await resp.json()
#               _LOGGER.debug("city_json: %s", city_json)
#               city_id = city_json['data'][0]['id']
#           _LOGGER.debug("city_id %s", city_id)


#       _LOGGER.debug("Now query for weather... ")
#       self._get_weather_url = URLS['weather_pre'] + city_id
#       async with self.client.get(self._get_weather_url) as resp:
#           try:
#               # assert resp.status == 200
#               resp.raise_for_status()
#           except ERRORS as status:
#               # except:
#               _LOGGER.debug("Failed to get Weather %s", status)
#           finally:
#               _LOGGER.debug("Getting Weather..Status= %s",
#                             resp.status)
#           weather_json = await resp.json()
#           current_json = weather_json['data']['currentObservations']
#           _LOGGER.debug("========Update Current Observations======== ")
#           _LOGGER.debug("current_json: %s", current_json)



        _LOGGER.debug("v2 API query for daily... ")
        
        async with self.client.get(self._get_forecast_daily) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get v2 Forecast Daily %s", status)
            finally:
                _LOGGER.debug("Getting v2 Forecast Daily..Status= %s",
                              resp.status)
            resp = await resp.json()
            forecast_day_v2_json = resp['data']


#           #Process 7 day Forecast
            _LOGGER.debug("========Update Daily Forecasts========")
#           forecast_day_json = weather_json['data']['forecast']
#           self.forecast_daily_list = parse_forecast_daily(forecast_day_json)
            self.forecast_daily_list = parse_forecast_daily(forecast_day_v2_json)



        _LOGGER.debug("v2 API query for hourly... ")
        
        async with self.client.get(self._get_forecast_hourly) as resp:
            try:
                # assert resp.status == 200
                resp.raise_for_status()
            except ERRORS as status:
                # except:
                _LOGGER.debug("Failed to get v2 Forecast Hourly %s", status)
            finally:
                _LOGGER.debug("Getting v2 Forecast Hourly..Status= %s",
                              resp.status)
            resp = await resp.json()
            forecast_hour_v2_json = resp['data']

            #Process Hourly Forecast
            _LOGGER.debug("========Update Hourly Forecasts========")
#           forecast_hour_json = weather_json['data']['forecast']
#           self.forecast_hourly_list = parse_forecast_hourly(forecast_hour_json)
            self.forecast_hourly_list = parse_forecast_hourly(forecast_hour_v2_json)

            return True
