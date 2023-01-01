"""Test the ViCare config flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_outside_temperature(
    hass: HomeAssistant,
    entity_registry_enabled_by_default: AsyncMock,
    init_integration: MockConfigEntry,
    mock_vicare: MagicMock,
) -> None:
    state = hass.states.get("sensor.vicare_outside_temperature")
    assert state
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TEMPERATURE
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "ViCare Outside Temperature"
