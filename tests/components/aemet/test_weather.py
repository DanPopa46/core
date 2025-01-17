"""The sensor tests for the AEMET OpenData platform."""
from unittest.mock import patch

import homeassistant.util.dt as dt_util
from .util import async_init_integration
from homeassistant.components.aemet.const import ATTRIBUTION
from homeassistant.components.weather import ATTR_CONDITION_PARTLYCLOUDY
from homeassistant.components.weather import ATTR_CONDITION_SNOWY
from homeassistant.components.weather import ATTR_FORECAST
from homeassistant.components.weather import ATTR_FORECAST_CONDITION
from homeassistant.components.weather import ATTR_FORECAST_PRECIPITATION
from homeassistant.components.weather import ATTR_FORECAST_PRECIPITATION_PROBABILITY
from homeassistant.components.weather import ATTR_FORECAST_TEMP
from homeassistant.components.weather import ATTR_FORECAST_TEMP_LOW
from homeassistant.components.weather import ATTR_FORECAST_TIME
from homeassistant.components.weather import ATTR_FORECAST_WIND_BEARING
from homeassistant.components.weather import ATTR_FORECAST_WIND_SPEED
from homeassistant.components.weather import ATTR_WEATHER_HUMIDITY
from homeassistant.components.weather import ATTR_WEATHER_PRESSURE
from homeassistant.components.weather import ATTR_WEATHER_TEMPERATURE
from homeassistant.components.weather import ATTR_WEATHER_WIND_BEARING
from homeassistant.components.weather import ATTR_WEATHER_WIND_SPEED
from homeassistant.const import ATTR_ATTRIBUTION


async def test_aemet_weather(hass):
    """Test states of the weather."""

    now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
    with patch("homeassistant.util.dt.now",
               return_value=now), patch("homeassistant.util.dt.utcnow",
                                        return_value=now):
        await async_init_integration(hass)

    state = hass.states.get("weather.aemet_daily")
    assert state
    assert state.state == ATTR_CONDITION_SNOWY
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_WEATHER_HUMIDITY) == 99.0
    assert state.attributes.get(ATTR_WEATHER_PRESSURE) == 1004.4
    assert state.attributes.get(ATTR_WEATHER_TEMPERATURE) == -0.7
    assert state.attributes.get(ATTR_WEATHER_WIND_BEARING) == 90.0
    assert state.attributes.get(ATTR_WEATHER_WIND_SPEED) == 15
    forecast = state.attributes.get(ATTR_FORECAST)[0]
    assert forecast.get(ATTR_FORECAST_CONDITION) == ATTR_CONDITION_PARTLYCLOUDY
    assert forecast.get(ATTR_FORECAST_PRECIPITATION) is None
    assert forecast.get(ATTR_FORECAST_PRECIPITATION_PROBABILITY) == 30
    assert forecast.get(ATTR_FORECAST_TEMP) == 4
    assert forecast.get(ATTR_FORECAST_TEMP_LOW) == -4
    assert (forecast.get(ATTR_FORECAST_TIME) == dt_util.parse_datetime(
        "2021-01-10 00:00:00+00:00").isoformat())
    assert forecast.get(ATTR_FORECAST_WIND_BEARING) == 45.0
    assert forecast.get(ATTR_FORECAST_WIND_SPEED) == 20

    state = hass.states.get("weather.aemet_hourly")
    assert state is None
