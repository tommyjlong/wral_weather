# WRAL Weather

Custom integration for WRAL TV Weather for [Home Assistant](https://www.home-assistant.io/).

This provides weather data from WRAL TV Weather for a given latitude/longitude (or zipcode) in the greater Raleigh-Durham-Chapel Hill, NC (USA) viewing area.  It provides, current observations, daily forecasts and hourly forecasts.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## Installation
This custom component can be installed using the Home Assistant Marketplace (formerly HA Community Store (HACS)) or installed manually.
### Marketplace Installation
This custom integration can be installed and managed using Homeassistant's Marketplace. 
- Go to the Settings->Markplace, and click on the upper 3-dots, and select Custom repositories. Click "Add from link" and paste ```https://github.com/tommyjlong/wral_weather ```, and for the "Type", chose ```Integration```.  Hit save, and a new entry titled **[integration] 
tommyjlong/wral_weather** should be created under Custom repositories.  
- Click on the new entry and a page should appear which will allow you to install this.  Click on Install and wait to be told that HA needs to be restarted.  
- Restart HA.
### Manual Installation
* If you want to manually install, place the files located in the `custom_components/wral_weather/` folder into the `<path-to-haconfig>/custom_components/wral_weather/` directory.  Reboot HA.

## Configuration
### Integration Configuration
:warning: If you are already using this integration and running versions v0.2.2 or older, you will need to delete the wral weather configuration from `configuration.yaml`, and restart HA. Then proceed to install this newer integration as it uses the newer "config flow" install method but there is no code to migrate the data from the legacy YAML configuration. :warning:

Under Home Assistant's Integration page, choose + ADD Integrations, and click on the integration named "WRAL Weather".
A dialog box will pop up for you to configure.  
* Weather Entity Name: This is the name of the HA weather entity that gets created. It is recommended you leave the default name "WRAL Weather" as is, as this will create an entity `weather.wral_weather`.
* Zipcode: This is optional.  Starting in version 3.0, this integration will use your HA's Latitude/Longitude coordinates.  If this is not setup in your HA, then it will fallback to use your zipcode to get the latitude/longitude, in which case you should configure the zipcode for your area. By default, it uses the zipcode `27606` where the WRAL TV studio is located.  Note: there are additional weather sensors that can be enabled, and these sensors will use the zipcode as part of the entity's name.
* Hours Forecast - Number of Hours:  WRAL provides nearly three days worth of hourly forecasts. If you desire to see WRAL hourly forecasts, but don't need to see all of these, then configure this with a more reasonable limit.  Default is 24 hours.
 
Hit "SUBMIT".  Another pop up will show you that a device has been created and allow you to choose an HA Area if you desire.  Then hit "FINISH".

Note: That you can add another instance of the WRAL Integration by going to the HA Integration page, choosing the existing WRAL Integration, and click on "ADD ENTRY".  This time give it a different name for each additional instance.

## Sensor Enable
The WRAL Weather Integration also provides a variety of sensors that use the WRAL Weather data.  They are partially named in Home Assistant based on the zipcode configured earlier, for example `sensor.27606_xxxx`. By default all the sensors are disabled.  To enable one or more of them, go to the HA "Integration" page and click on the WRAL Integration and look where is shows "NN entities" (NN is some number) and click on it.

A Services/Device page will appear with a card showing all the sensor entities (which includes the one weather entity).  To enable a sensor(s), click "+NNN disabled entities" to see the list of disabled sensor(s).  Then click on one of the sensors and the HA entity card will pop up showing that it is disabled.  To enable it, click on the cog wheel and click on the "Enable" button.  A pop up will ask you to confirm, click on "ENABLE" and will next mention that it may take up to 30 seconds for HA to create the sensors and supply it with data, click "OK" (ignore the warning `This entity is no longer being provided by the wral_weather integration. If the entity is no longer in use, delete it in settings` as this will disappear after HA creates it).

## Lovelace Support
This custom weather platform works with standard HA weather-forecast card:
```
cards:
  - type: weather-forecast
    entity: weather.wral_weather
```
It also works with the custom animated [wral-weather-card](https://github.com/tommyjlong/wral-weather-card). Note: :warning: Older versions of this card will need to be upgraded. :warning: 

## Credits
The development of this Custom HA integration would not have been possible without having analyzed and reused various existing code, and in particular the modernized version of the nws weather integrations provided by HA as well as the `pynws` module developed by MatthewFlam (https://github.com/MatthewFlamm).

## Miscellaneous
The code is made up of various Python modules: 
* `wral_weather.py` : which interfaces directly with WRAL's weather website. Version 3.0 uses the WRAL weather version 2 API.
* The remaining Python and json files provides the WRAL weather platform and sensors for HA's weather integration.  

A companion Python application program ```app_wral.py``` was developed as a test and development vehicle for the `wral_weather.py`.  If you would like to play with it, simply place it and the `wral_weather.py` in the same directory and run it: ```$python3 app_wral.py```.

