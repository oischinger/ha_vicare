# The domain of your component. Equal to the filename of your component.
import logging
import sys
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['PyViCare==0.0.21']
_LOGGER = logging.getLogger(__name__)

CONF_USER = 'user'
CONF_PASSWORD = 'password'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the ViCare component."""
    from PyViCare import ViCareSession
    t = ViCareSession(config.get(CONF_USER), config.get(CONF_PASSWORD), "/tmp/vicare_token.save")
    add_devices([ViCareSensor(t, "BoilerTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "Programs", ""),
                 ViCareSensor(t, "ActiveProgram", ""),
                 ViCareSensor(t, "Modes", ""),
                 ViCareSensor(t, "ActiveMode", ""),
                 ViCareSensor(t, "CurrentDesiredTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "OutsideTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "RoomTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "SupplyTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "DomesticHotWaterStorageTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "HeatingCurveSlope", ""),
                 ViCareSensor(t, "HeatingCurveShift", ""),
                 ViCareSensor(t, "MonthSinceLastService", ""),
                 ViCareSensor(t, "LastServiceDate", ""),
                 ViCareSensor(t, "GasConsumptionHeatingDays", ""),
                 ViCareSensor(t, "GasConsumptionHeatingToday", 'kWh'),
                 ViCareSensor(t, "GasConsumptionHeatingWeeks", ""),
                 ViCareSensor(t, "GasConsumptionHeatingThisWeek", 'kWh'),
                 ViCareSensor(t, "GasConsumptionHeatingMonths", ""),
                 ViCareSensor(t, "GasConsumptionHeatingThisMonth", 'kWh'),
                 ViCareSensor(t, "GasConsumptionHeatingYears", ""),
                 ViCareSensor(t, "GasConsumptionHeatingThisYear", 'kWh'),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterDays", ""),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterToday", 'kWh'),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterWeeks", ""),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterThisWeek", 'kWh'),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterMonths", ""),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterThisMonth", 'kWh'),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterYears", ""),
                 ViCareSensor(t, "GasConsumptionDomesticHotWaterThisYear", 'kWh'),
                 ViCareSensor(t, "DomesticHotWaterConfiguredTemperature", TEMP_CELSIUS),
                 ViCareSensor(t, "CurrentPower", 'kW')])
    return True


class ViCareSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, api, sensor_name, unit):
        """Initialize the sensor."""
        self._state = None
        self._api = api
        self._unit = unit
        self._device_state_attributes = {}
        self.sensorName = sensor_name

    @property
    def name(self):
        """Return the name of the sensor."""
        return "vicare_" + self.sensorName

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    def update(self):
        from PyViCare import ViCareSession
        api_method = getattr(ViCareSession, "get" + self.sensorName)
        self._state = api_method(self._api)
