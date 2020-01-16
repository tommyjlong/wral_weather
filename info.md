# WRAL Weather

Custom component for WRAL Weather for Home Assistant.

## Sample configuration
```
weather:
  - platform: wral_weather
    name: "WRAL Weather"
    zipcode: '27513'
```

See [README](README.md) for more info on configuration.

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

TO BE DONE Add link


