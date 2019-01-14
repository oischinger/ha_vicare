"""
ViCare climate device.
"""
from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_AWAY_MODE,
    SUPPORT_OPERATION_MODE,SUPPORT_ON_OFF)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE

REQUIREMENTS = ['PyViCare==0.0.7']
from PyViCare import ViCareSession

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE | SUPPORT_OPERATION_MODE | SUPPORT_ON_OFF

CONF_USER = 'user'
CONF_PASSWORD = 'password'

def setup_platform(hass, config, add_entities, discovery_info=None):
    t = ViCareSession(config.get(CONF_USER), config.get(CONF_PASSWORD), "/tmp/vicare_token.save")
    add_entities([
        DemoClimate('vicare', t)
    ])


class DemoClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, name, api):
        """Initialize the climate device."""
        self._name = name
        self._api = api
        self._support_flags = SUPPORT_FLAGS
        self._unit_of_measurement = TEMP_CELSIUS
        self._on = None
        self._away = None
        self._target_temperature = None
        self._operation_list = None
        self._current_operation = None
        self._current_temperature = None

    def update(self):
        _room_temperature = self._api.getRoomTemperature() 
        if _room_temperature != None and _room_temperature != "error":
            self._current_temperature = _room_temperature
        else:
            self._current_temperature = self._api.getBoilerTemperature()
        self._current_operation = self._api.getActiveProgram()
        self._operation_list = self._api.getPrograms()
        self._target_temperature = self._api.getCurrentDesiredTemperature()
        self._away = self._api.getActiveProgram() == "holiday"
        _active_mode = self._api.getActiveMode()
        self._on = _active_mode == "dhwAndHeating" or _active_mode == "forcedReduced" or _active_mode == "forcedNormal"

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._on

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self._api.setProgramTemperature(self._current_operation, self._target_temperature)
        self.schedule_update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation = operation_mode
        self.schedule_update_ha_state()
        self._api.activateProgram(operation_mode)

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._away = True
        self.schedule_update_ha_state()
        self._api.setMode("holiday")

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._away = False
        self.schedule_update_ha_state()
        self._api.setMode("normal")

    def turn_on(self):
        """Turn on."""
        self._on = True
        self.schedule_update_ha_state()
        self._api.setMode("dhwAndHeating")

    def turn_off(self):
        """Turn off."""
        self._on = False
        self.schedule_update_ha_state()
        self._api.setMode("standby")

