# wral weather

Custom integration for WRAL TV Weather for Home Assistant.

This provides weather data from WRAL TV Weather for a given
zipcode in the greater Raleigh-Durham-Chapel Hill, NC (USA) viewing area.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## Installation

* This custom integration can be installed and managed using HACS.  TO BE COMPLETED
* If you want to manually install, place files in the `custom_components/wral_weather/` folder into `path/to/haconfig/custom_components/wral_weather/`

## Detailed Configuration
Simply specify in Home Assistant under the weather component to use the ```wral_weather ``` platform and provide your local zipcode.
```
weather:
  - platform: wral_weather
    name: "WRAL Weather"
    zipcode: 'YOUR_ZIPCODE'

```
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
which can be found here:
Add link

# Credits
This component could not have been developed without
having analyzed the code for nws weather and pynws developed by 
MatthewFlam (https://github.com/MatthewFlamm )
