"""Test ViCare binary sensors."""

from unittest.mock import MagicMock

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant


@pytest.mark.freeze_time("2022-04-19 07:53:05")
@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.vicare_burner_active",
        "sensor.vicare_circulation_pump_active",
        "sensor.vicare_dhw_charging_active",
        "sensor.vicare_dhw_circulation_pump_active",
        "sensor.vicare_dhw_pump_active",
        "sensor.vicare_frost_protection_active",
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
