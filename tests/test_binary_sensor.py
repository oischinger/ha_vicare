"""Test ViCare binary sensors."""

from unittest.mock import MagicMock

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant


@pytest.mark.freeze_time("2022-04-19 07:53:05")
@pytest.mark.parametrize(
    "entity_id",
    [
        "binary_sensor.vicare_burner_active",
        "binary_sensor.vicare_circulation_pump_active",
        "binary_sensor.vicare_dhw_charging_active",
        "binary_sensor.vicare_dhw_circulation_pump_active",
        "binary_sensor.vicare_dhw_pump_active",
        "binary_sensor.vicare_frost_protection_active",
    ],
)
async def test_binary_sensors(
    hass: HomeAssistant,
    mock_vicare_gas_boiler: MagicMock,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test the ViCare Gas Boiler sensor."""
    state = hass.states.get(entity_id)
    assert state == snapshot
