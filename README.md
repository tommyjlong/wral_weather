# WRAL Weather

Custom integration for WRAL TV Weather for [Home Assistant](https://www.home-assistant.io/).

This provides weather data from WRAL TV Weather for a given
zipcode in the greater Raleigh-Durham-Chapel Hill, NC (USA) viewing area.

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

## Detailed Configuration
Under Home Assistant's weather integration, specify the ```wral_weather ``` platform and provide your local zipcode.
```
weather:
  - platform: wral_weather
    name: "WRAL Weather"
    zipcode: 'YOUR_ZIPCODE'

```
* ```name``` is optional.  It is used as the name of the entity as well as the Friendly name.  By default the name is "WRAL Weather".
Using the default name, the entity will show up as: ```weather.wral_weather```
* ```zipcode``` is optional.  However it is highly recommended to use your zipcode.  By default, it uses the zipcode where the WRAL TV studio is located.
## Change log
* 0.1.0
  * Initial Release

## Lovelace Support
This custom weather platform works with standard HA weather-forecast card:
```
cards:
  - type: weather-forecast
    entity: weather.wral_weather
```
It also works with the custom animated [wral-weather-card](https://github.com/tommyjlong/wral-weather-card).

## Credits
The development of this Custom Component may not have been possible without
having analyzed various existing code, and in particular the nws weather and pynws developed by 
MatthewFlam (https://github.com/MatthewFlamm).

## Miscellaneous
The code is made up of two separate Python modules: 
- ```wral_weather.py``` : which interfaces directly with WRAL's weather website.
- ```weather.py``` : which provides the WRAL platform for HA's weather integration.  It gets its data from ```wral_weather.py```.

A companion Python application program ```app_wral.py``` was developed as a test and development vehicle for the ```wral_weather.py```.  If you would like to play with it, simply place it and the ```wral_weather.py``` in the same directory and run it: ```$python3 app_wral.py```.
