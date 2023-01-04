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
import pytest
import pytest_asyncio
from homeassistant.components.vicare.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import ENTRY_CONFIG

from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Automatically enable loading custom integrations in all tests."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield

@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[AsyncMock, None, None]:
    """Test fixture that ensures all entities are enabled in the registry."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ) as mock_entity_registry_enabled_by_default:
        yield mock_entity_registry_enabled_by_default

def readJson(fileName):
    test_filename = os.path.join(os.path.dirname(__file__), fileName)
    with open(test_filename, mode="rb") as json_file:
        return json.load(json_file)


class MockPyViCare:
    def __init__(self) -> None:
        self.devices = [
            PyViCareDeviceConfig(
                ViCareServiceMock("fixtures/Vitodens300W.json"), "Vitodens", "online"
            )
        ]

    def initWithCredentials(
        self, username: str, password: str, client_id: str, token_file: str
    ):
        None


def MockCircuitsData(circuits):
    return {
        "properties": {"enabled": {"value": circuits}},
        "feature": "heating.circuits",
    }


class ViCareServiceMock:
    def __init__(self, filename, rawInput=None):
        if rawInput is None:
            testData = readJson(filename)
            self.testData = testData
        else:
            self.testData = rawInput

        self.accessor = ViCareDeviceAccessor("[id]", "[serial]", "[deviceid]")
        self.setPropertyData = []

    def getProperty(self, property_name):
        entities = self.testData["data"]
        return readFeature(entities, property_name)

    def setProperty(self, property_name, action, data):
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
        data=ENTRY_CONFIG,
    )


@pytest.fixture
def mock_vicare() -> Generator[MagicMock, None, None]:
    """Return a mocked ViCare client."""
    with patch(
        "homeassistant.components.vicare.vicare_login", return_value=MockPyViCare()
    ), patch(
        "PyViCare.PyViCareCachedService",
        return_value=ViCareServiceMock("fixtures/Vitodens300W.json"),
    ) as vicare_mock:
        vicare = vicare_mock.return_value
        yield vicare


@pytest_asyncio.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_vicare: MagicMock
) -> MockConfigEntry:
    """Set up the ViCare integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
