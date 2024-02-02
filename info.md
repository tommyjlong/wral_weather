# WRAL Weather

Custom integration for WRAL TV Weather for [Home Assistant](https://www.home-assistant.io/).

This provides weather data from WRAL TV Weather for a given
zipcode in the greater Raleigh-Durham-Chapel Hill, NC (USA) viewing area.  It provides, current observations, daily forecasts and hourly forecasts.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## Installation
This custom component can be installed using the Home Assistant Community Store (HACS) or installed manually.
### HACS Installation
This custom integration can be installed and managed using HACS. 
- Go to the HACS Settings, and under ADD CUSTOM RESPOSITORY, paste ```https://github.com/tommyjlong/wral_weather ```, and chose ```Integration``` for the Category.  Hit save, and a new entry titled **[integration] 
tommyjlong/wral_weather** should be created under CUSTOM REPOSITORY.  
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
* Zipcode: You should configure the zipcode for your area. By default, it uses the zipcode `27606` where the WRAL TV studio is located.
* Hours Forecast - Number of Hours:  WRAL provides nearly seven days worth of hourly forecasts. If you desire to see WRAL hourly forecasts, but don't need to see all of these, then configure this with a more reasonable limit.  Default is 24 hours.
 
Hit "SUBMIT".  Another pop up will show you that a device has been created and allow you to choose an HA Area if you desire.  Then hit "FINISH".

Note: That you can add another instance of the WRAL Integration by going to the HA Integration page, choosing the existing WRAL Integration, and click on "ADD ENTRY".  This time give it a different name for each additional instance.

## Sensor Enable
The WRAL Weather Integration also provides a variety of sensors that use the WRAL Weather data.  They are partially named in Home Assistant based on the zipcode configured earlier, for example `sensor.27606_xxxx`. By default all the sensors are disabled.  To enable one or more of them, go to the HA "Integration" page and click on the WRAL Integration and look where is shows "13 entities" and click on it.

A new page will appear showing all the sensors entities (as well as the one weather entity).  To enable a sensor(s), click on the box next to the sensor(s).  Then click on "ENABLE SELECTED".  A pop up will ask you to confirm, click on "ENABLE".  An pop up will now mention that it may take up to 30 seconds for HA to create the sensors and supply it with data, click "OK".
