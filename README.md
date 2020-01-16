# WRAL Weather

Custom integration for WRAL TV Weather for Home Assistant.

This provides weather data from WRAL TV Weather for a given
zipcode in the greater Raleigh-Durham-Chapel Hill, NC (USA) viewing area.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

### :warning: Some Data Unknowns
The data is collected from WRAL.com's web page, and not all data enumerations are known as this information is not published.
Over time, as new enumerations are learned, this application will be updated.

## Installation

* This custom integration can be installed and managed using HACS. 
Go to the HACS Settings, and under ADD CUSTOM RESPOSITORY, paste ```https://github.com/tommyjlong/wral_weather ```, and chose ```Integration``` for the Category.  Hit save, and reboot HA.
* If you want to manually install, place files in the `custom_components/wral_weather/` folder into `<path-to-haconfig>/custom_components/wral_weather/`

## Detailed Configuration
Simply specify in Home Assistant under the weather component to use the ```wral_weather ``` platform and provide your local zipcode.
```
weather:
  - platform: wral_weather
    name: "WRAL Weather"
    zipcode: 'YOUR_ZIPCODE'

```
* ```name``` is optional.  It is used as the name of the component as well as the Friendly name.  By default the name is "WRAL Weather".
Using the default, the component willl show up as the entity ```weather.wral_weather```
* ```zipcode``` is optional.  However it is highly recommended to use the your zipcode.  By default, it uses the zipcode of the WRAL TV studio.
## Change log
* 0.1.0
  * Initial Release

# Lovelace Support
This custom weather platform works with standard HA weather-forecast card:
```
cards:
  - type: weather-forecast
    entity: weather.wral_weather
```
It also works with the custom wral-weather-card
which can be found here: TO BE DONE, Add link

# Credits
The development of this Custom Component may not have been possible without
having analyzed various existing code, and in particular the nws weather and pynws developed by 
MatthewFlam (https://github.com/MatthewFlamm )

