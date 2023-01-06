"""Fixtures for LaMetric integration tests."""
from __future__ import annotations

from collections.abc import Generator
import json
import os
from unittest.mock import MagicMock, patch

from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig
from PyViCare.PyViCareService import (
    ViCareDeviceAccessor,
    buildSetPropertyUrl,
    readFeature,
)
from homeassistant.components.vicare.const import DOMAIN
from homeassistant.core import HomeAssistant
import pytest

from . import ENTRY_CONFIG

from tests.common import MockConfigEntry


def readJson(fileName):
    """Read filte to json."""
    test_filename = os.path.join(os.path.dirname(__file__), fileName)
    with open(test_filename, mode="rb") as json_file:
        return json.load(json_file)


class MockPyViCare:
    """Mocked PyVicare class based on a json dump."""

    def __init__(self, fixtures) -> None:
        """Init a single device from json dump."""
        self.devices = []
        for fixture in fixtures:
            self.devices.append(
                PyViCareDeviceConfig(ViCareServiceMock(fixture), "Vitodens", "online")
            )

    def initWithCredentials(
        self, username: str, password: str, client_id: str, token_file: str
    ):
        """Stub oauth login."""
        None


class ViCareServiceMock:
    """PyVicareService mock using a json dump."""

    def __init__(self, fixture):
        """Initialize the mock from a json dump."""
        testData = readJson(fixture)
        self.testData = testData

        self.accessor = ViCareDeviceAccessor("[id]", "[serial]", "[deviceid]")
        self.setPropertyData = []

    def getProperty(self, property_name):
        """Read a property from a json dump."""
        entities = self.testData["data"]
        value = readFeature(entities, property_name)
        print("Read: ", property_name, value)
        return value

    def setProperty(self, property_name, action, data):
        """Set a property to its internal data structure."""
        self.setPropertyData.append(
            {
                "url": buildSetPropertyUrl(self.accessor, property_name, action),
                "property_name": property_name,
                "action": action,
                "data": data,
            }
        )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="ViCare",
        data=ENTRY_CONFIG,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the ViCare integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry


@pytest.fixture
async def mock_vicare_gas_boiler() -> Generator[MagicMock, None, None]:
    """Return a mocked ViCare API representing a gas boiler device."""
    fixtures = ["fixtures/Vitodens300W.json"]
    with patch(
        "homeassistant.components.vicare.vicare_login",
        return_value=MockPyViCare(fixtures),
    ) as vicare_mock:
        vicare = vicare_mock.return_value
        yield vicare
