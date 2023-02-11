"""Test for ViCare."""
from __future__ import annotations

import sys
from typing import Final

import pytest_homeassistant_custom_component.common

from homeassistant.components.vicare.const import CONF_HEATING_TYPE
from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME

# Transparently rewrite HA Core imports to HA Custom Component imports
sys.modules["tests.common"] = pytest_homeassistant_custom_component.common

ENTRY_CONFIG: Final[dict[str, str]] = {
    CONF_USERNAME: "foo@bar.com",
    CONF_PASSWORD: "1234",
    CONF_CLIENT_ID: "5678",
    CONF_HEATING_TYPE: "auto",
}

MOCK_MAC = "B874241B7B9"

# When running tests with HA Core ViCare:
# MODULE = "homeassistant.components.vicare"

# When running tests with Custom ViCare Integration:
MODULE = "custom_components.vicare"
