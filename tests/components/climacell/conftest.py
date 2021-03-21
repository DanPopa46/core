"""Configure py.test."""
from unittest.mock import patch

import pytest


@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


@pytest.fixture(name="climacell_config_flow_connect", autouse=True)
def climacell_config_flow_connect():
    """Mock valid climacell config flow setup."""
    with patch(
        "homeassistant.components.climacell.config_flow.ClimaCellV3.realtime",
        return_value={},
    ), patch(
        "homeassistant.components.climacell.config_flow.ClimaCellV4.realtime",
        return_value={},
    ):
        yield


@pytest.fixture(name="climacell_config_entry_update")
def climacell_config_entry_update_fixture():
    """Mock valid climacell config entry setup."""
    with patch(
        "homeassistant.components.climacell.ClimaCellV3.realtime",
        return_value={},
    ), patch(
        "homeassistant.components.climacell.ClimaCellV3.forecast_hourly",
        return_value=[],
    ), patch(
        "homeassistant.components.climacell.ClimaCellV3.forecast_daily",
        return_value=[],
    ), patch(
        "homeassistant.components.climacell.ClimaCellV3.forecast_nowcast",
        return_value=[],
    ), patch(
        "homeassistant.components.climacell.ClimaCellV4.realtime_and_all_forecasts",
        return_value={},
    ):
        yield
