"""Test ViCare sensors."""

from unittest.mock import MagicMock

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant


@pytest.mark.freeze_time("2022-04-19 07:53:05")
@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.vicare_outside_temperature",
        "sensor.vicare_boiler_temperature",
        "sensor.vicare_hot_water_max_temperature",
        "sensor.vicare_hot_water_min_temperature",
        "sensor.vicare_burner_hours",
        "sensor.vicare_burner_modulation",
        "sensor.vicare_burner_starts",
        "sensor.vicare_energy_consumption_this_month",
        "sensor.vicare_energy_consumption_this_year",
        "sensor.vicare_energy_consumption_today",
        "sensor.vicare_heating_gas_consumption_this_month",
        "sensor.vicare_heating_gas_consumption_this_week",
        "sensor.vicare_heating_gas_consumption_this_year",
        "sensor.vicare_heating_gas_consumption_today",
        "sensor.vicare_hot_water_gas_consumption_this_month",
        "sensor.vicare_hot_water_gas_consumption_this_week",
        "sensor.vicare_hot_water_gas_consumption_this_year",
        "sensor.vicare_hot_water_gas_consumption_today",
        "sensor.vicare_power_consumption_this_week",
    ],
)
async def test_gas_boiler_sensors(
    hass: HomeAssistant,
    mock_vicare_gas_boiler: MagicMock,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test the ViCare Gas Boiler sensors."""
    state = hass.states.get(entity_id)
    assert state == snapshot


@pytest.mark.freeze_time("2022-04-19 07:53:05")
@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.vicare_room_temperature",
        "sensor.vicare_room_humidity",
    ],
)
async def test_room_sensor_sensors(
    hass: HomeAssistant,
    mock_vicare_room_sensor: MagicMock,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test the ViCare Room Sensor sensors."""
    state = hass.states.get(entity_id)
    assert state == snapshot
