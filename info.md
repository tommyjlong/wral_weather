# WRAL Weather

Custom integration for WRAL TV Weather for [Home Assistant](https://www.home-assistant.io/). 

## Sample configuration
```
weather:
  - platform: wral_weather
    name: "WRAL Weather"
    zipcode: '27607'
```
- ```name```: is optional, but can be used to change the entity name.  
- ```zipcode```: should be your local zipcode within the WRAL TV viewing area.

See [README](https://github.com/tommyjlong/wral_weather/blob/master/README.md) for more details on configuration.

# Lovelace Support
This custom weather platform works with the standard HA weather-forecast card:
```
cards:
  - type: weather-forecast
    entity: weather.wral_weather
```

It also works with the custom animated [wral-weather-card](https://github.com/tommyjlong/wral-weather-card).

