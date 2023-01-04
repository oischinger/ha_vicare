"""Test for ViCare."""
from __future__ import annotations

import sys
from typing import Final
from unittest.mock import patch

from homeassistant.components.vicare.const import CONF_HEATING_TYPE
from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME
import pytest
import pytest_homeassistant_custom_component.common

# Transparently rewrite HA Core imports to HA Custom Component imports
sys.modules["tests.common"] = pytest_homeassistant_custom_component.common

ENTRY_CONFIG: Final[dict[str, str]] = {
    CONF_USERNAME: "foo@bar.com",
    CONF_PASSWORD: "1234",
    CONF_CLIENT_ID: "5678",
    CONF_HEATING_TYPE: "auto",
}

MOCK_MAC = "B874241B7B9"


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


@pytest.fixture(name="entity_registry_enabled_by_default", autouse=True)
def entity_registry_enabled_by_default():
    """Test fixture that ensures all entities are enabled in the registry."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ) as mock_entity_registry_enabled_by_default:
        yield mock_entity_registry_enabled_by_default
