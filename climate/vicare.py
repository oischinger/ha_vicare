"""
ViCare climate device.
"""

import logging
from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_AWAY_MODE,
    SUPPORT_HOLD_MODE, SUPPORT_OPERATION_MODE, SUPPORT_ON_OFF, STATE_OFF,
    STATE_HEAT, STATE_ECO, STATE_AUTO, STATE_UNKNOWN)
from homeassistant.const import (TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['PyViCare==0.0.22']

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE | SUPPORT_HOLD_MODE | SUPPORT_OPERATION_MODE | SUPPORT_ON_OFF
CONF_CIRCUIT = 'circuit'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_CIRCUIT, default=0): cv.positive_int
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    from PyViCare import ViCareSession
    t = ViCareSession(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), "/tmp/vicare_token.save", config.get(CONF_CIRCUIT))
    add_entities([
        ViCareClimate('vicare', t)
    ])


class ViCareClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, name, api):
        """Initialize the climate device."""
        self._name = name
        self._api = api
        self._support_flags = SUPPORT_FLAGS
        self._unit_of_measurement = TEMP_CELSIUS
        self._on = None
        self._away = None
        self._hold = None
        self._pre_hold = None
        self._target_temperature = None
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_ECO, STATE_AUTO]
        self._current_operation = "unknown"
        self._current_temperature = None

    def update(self):
        _room_temperature = self._api.getRoomTemperature() 
        if _room_temperature is not None and _room_temperature != "error":
            self._current_temperature = _room_temperature
        else:
            self._current_temperature = self._api.getBoilerTemperature()
        self._current_operation = self._api.getActiveProgram()
        self._target_temperature = self._api.getCurrentDesiredTemperature()
        self._away = self._api.getActiveProgram() == "holiday"
        _active_mode = self._api.getActiveMode()
        self._on = _active_mode == "dhwAndHeating" or _active_mode == "forcedReduced" or _active_mode == "forcedNormal"
        if _active_mode == "forcedReduced":
            self._hold = "away"
        elif _active_mode == "forcedNormal":
            self._hold = "home"
        else:
            self._pre_hold = _active_mode
            self._hold = "off"

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
        if self._current_operation.lower() == 'comfort':
            return STATE_HEAT
        elif self._current_operation.lower() == 'sparmodus':
            return STATE_ECO
        elif self._current_operation.lower() == 'eco':
            return STATE_ECO
        elif self._current_operation.lower() == 'normal':
            return STATE_AUTO
        elif self._current_operation.lower() == 'reduced':
            return STATE_AUTO
        elif self._current_operation.lower() == 'standby':
            return STATE_OFF
        else:
            return STATE_UNKNOWN

    def set_operation_mode(self, operation_mode):
        if operation_mode in self._operation_list:
            """ 1st deactivate current mode """
            self._api.deactivateProgram(self._current_operation)
            """ 2nd: set new mode """
            if operation_mode == STATE_HEAT:
                self._api.activateProgram("comfort")
            elif operation_mode == STATE_ECO:
                self._api.activateProgram("eco")
            elif operation_mode == STATE_AUTO:
                self._api.activateProgram("normal")
            elif operation_mode == STATE_OFF:
                self._api.activateProgram("standby")
            else:
                _LOGGER.error(
                    "An error occurred while setting operation mode. "
                    "Invalid operation mode: %s", operation_mode)
        else:
            _LOGGER.error(
                "An error occurred while setting operation mode. "
                "Invalid operation mode: %s", operation_mode)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    @property
    def current_hold_mode(self):
        """Return hold mode setting."""
        return self._hold

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

    def set_hold_mode(self, hold_mode):
        if hold_mode in ["away", "home"]:
            active_mode = self._api.getActiveMode()
            self.schedule_update_ha_state()
            if hold_mode == "away":
                success = self._api.setMode("forcedReduced")
            else:
                hold_mode == "home"
                success = self._api.setMode("forcedNormal")
            # PyViCare currently returns 'None' on no error, checking for both for future changes
            if success["error"] is None or success["error"] == 'None':
                self._hold = hold_mode
                if active_mode in ["standby", "dhw", "dhwAndHeating", "active"]:
                    self._pre_hold = active_mode
            else:
                _LOGGER.error("Failed to set hold mode on ViCare API to %s with status code %s and error %s", hold_mode, success["statusCode"], success["errror"])
        elif hold_mode == "off":
            if self._pre_hold is not None:
                success = self._api.setMode(self._pre_hold)
            else:
                _LOGGER.info("No stored pre hold mode found - switching to hot water and heating")
                success = self._api.setMode("dhwAndHeating")
            # PyViCare currently returns 'None' on no error, checking for both for future changes
            if not (success["error"] is None or success["error"] == 'None'):
                _LOGGER.error("Failed to restore from hold mode on ViCare API to %s with status code %s and error %s", self._pre_hold, success["statusCode"], success["errror"])
        else:
            _LOGGER.error("Unknown hold mode %s set - ignoring", hold_mode)

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
