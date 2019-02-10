"""
ViCare climate device.
"""

import logging

from homeassistant.components.climate import (
    ClimateDevice, SUPPORT_TARGET_TEMPERATURE, SUPPORT_AWAY_MODE,
    SUPPORT_HOLD_MODE, SUPPORT_OPERATION_MODE, SUPPORT_ON_OFF, STATE_OFF,
    STATE_HEAT, STATE_ECO, STATE_AUTO)
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE,
    CONF_USERNAME, CONF_PASSWORD, CONF_NAME, PRECISION_WHOLE)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['PyViCare==0.0.30']

CONF_CIRCUIT = 'circuit'

VICARE_MODE_DHW = 'dhw'
VICARE_MODE_DHWANDHEATING = 'dhwAndHeating'
VICARE_MODE_FORCEDREDUCED = 'forcedReduced'
VICARE_MODE_FORCEDNORMAL = 'forcedNormal'
VICARE_MODE_OFF = 'standby'

VICARE_PROGRAM_ACTIVE = 'active'
VICARE_PROGRAM_COMFORT = 'comfort'
VICARE_PROGRAM_ECO = 'eco'
VICARE_PROGRAM_EXTERNAL = 'external'
VICARE_PROGRAM_HOLIDAY = 'holiday'
VICARE_PROGRAM_NORMAL = 'normal'
VICARE_PROGRAM_REDUCED = 'reduced'
VICARE_PROGRAM_STANDBY = 'standby'

VICARE_HOLD_MODE_AWAY = 'away'
VICARE_HOLD_MODE_HOME = 'home'
VICARE_HOLD_MODE_OFF = 'off'

VICARE_TEMP_WATER_MIN = 10
VICARE_TEMP_WATER_MAX = 60
VICARE_TEMP_HEATING_MIN = 3
VICARE_TEMP_HEATING_MAX = 37

SUPPORT_FLAGS_HEATING = SUPPORT_TARGET_TEMPERATURE | SUPPORT_AWAY_MODE | SUPPORT_OPERATION_MODE | SUPPORT_ON_OFF | SUPPORT_HOLD_MODE
SUPPORT_FLAGS_WATER = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_ON_OFF

VALUE_UNKNOWN = 'unknown'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_CIRCUIT, default=-1): int,
    vol.Optional(CONF_NAME, default='ViCare'): cv.string
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    from PyViCare import ViCareSession
    if config.get(CONF_CIRCUIT) == -1:
        t = ViCareSession(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), "/tmp/vicare_token.save")
    else:
        t = ViCareSession(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), "/tmp/vicare_token.save", config.get(CONF_CIRCUIT))
    add_entities([
        ViCareClimate(hass, config.get(CONF_NAME) + ' Heating', t),
        ViCareWater(hass, config.get(CONF_NAME) + ' Water', t)
    ])


class ViCareClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, hass, name, api):
        """Initialize the climate device."""
        self._name = name
        self._api = api
        self._support_flags = SUPPORT_FLAGS_HEATING
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._on = None
        self._hold = None
        self._pre_hold = None
        self._target_temperature = None
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_ECO, STATE_AUTO]
        self._current_mode = VALUE_UNKNOWN
        self._current_temperature = None
        self._current_program = VALUE_UNKNOWN

    def update(self):
        _room_temperature = self._api.getRoomTemperature() 
        if _room_temperature is not None and _room_temperature != "error":
            self._current_temperature = _room_temperature
        else:
            self._current_temperature = self._api.getBoilerTemperature()
        self._current_program = self._api.getActiveProgram()
        self._target_temperature = self._api.getCurrentDesiredTemperature()
        self._current_mode = self._api.getActiveMode()
        self._on = (self._current_mode == VICARE_MODE_DHWANDHEATING or self._current_mode == VICARE_MODE_FORCEDREDUCED or self._current_mode == VICARE_MODE_FORCEDNORMAL)
        if self._current_mode == VICARE_MODE_FORCEDREDUCED:
            self._hold = VICARE_HOLD_MODE_AWAY
        elif self._current_mode == VICARE_MODE_FORCEDNORMAL:
            self._hold = VICARE_HOLD_MODE_HOME
        else:
            self._pre_hold = self._current_program
            self._hold = VICARE_HOLD_MODE_OFF

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
        if self._current_program == VICARE_PROGRAM_COMFORT:
            return STATE_HEAT
        elif self._current_program == VICARE_PROGRAM_ECO:
            return STATE_ECO
        elif self._current_program == VICARE_PROGRAM_NORMAL:
            return STATE_AUTO
        elif self._current_program == VICARE_PROGRAM_REDUCED:
            return STATE_AUTO
        elif self._current_program == VICARE_PROGRAM_STANDBY:
            return STATE_OFF
        else:
            return VALUE_UNKNOWN

    def set_operation_mode(self, operation_mode):
        if operation_mode in self._operation_list:
            """ 1st deactivate current mode """
            self._api.deactivateProgram(self._current_mode)
            """ 2nd: set new mode """
            if operation_mode == STATE_HEAT:
                self._api.activateProgram(VICARE_PROGRAM_COMFORT)
            elif operation_mode == STATE_ECO:
                self._api.activateProgram(VICARE_PROGRAM_ECO)
            elif operation_mode == STATE_AUTO:
                self._api.activateProgram(VICARE_PROGRAM_NORMAL)
            elif operation_mode == STATE_OFF:
                self._api.activateProgram(VICARE_PROGRAM_STANDBY)
            else:
                _LOGGER.error(
                    "An error occurred while setting operation mode. "
                    "Invalid operation mode: %s", operation_mode)
        else:
            _LOGGER.error(
                "An error occurred while setting operation mode. "
                "Invalid operation mode: %s", operation_mode)

        self.async_schedule_update_ha_state(True)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._hold == VICARE_HOLD_MODE_AWAY

    @property
    def current_hold_mode(self):
        """Return hold mode setting."""
        return self._hold

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._on

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return convert_temperature(VICARE_TEMP_HEATING_MIN, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return convert_temperature(VICARE_TEMP_HEATING_MAX, TEMP_CELSIUS, self.temperature_unit)

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self._api.setProgramTemperature(self._current_operation, self._target_temperature)
        self.schedule_update_ha_state()

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self.set_hold_mode(VICARE_HOLD_MODE_AWAY)
        self.schedule_update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self.set_hold_mode(VICARE_HOLD_MODE_OFF)
        self.schedule_update_ha_state()

    def set_hold_mode(self, hold_mode):
        if hold_mode in [VICARE_HOLD_MODE_AWAY, VICARE_HOLD_MODE_HOME]:
            active_mode = self._api.getActiveMode()
            self.schedule_update_ha_state()
            if hold_mode == VICARE_HOLD_MODE_AWAY:
                success = self._api.setMode(VICARE_MODE_FORCEDREDUCED)
            else:
                hold_mode == VICARE_HOLD_MODE_HOME
                success = self._api.setMode(VICARE_MODE_FORCEDNORMAL)
            # PyViCare currently returns 'None' on no error, checking for both for future changes
            if success["error"] is None or success["error"] == 'None':
                self._hold = hold_mode
                if active_mode in [VICARE_MODE_OFF, VICARE_MODE_DHW, VICARE_MODE_DHWANDHEATING, "active"]:
                    self._pre_hold = active_mode
            else:
                _LOGGER.error("Failed to set hold mode on ViCare API to %s with status code %s and error %s", hold_mode, success["statusCode"], success["error"])
        elif hold_mode == VICARE_HOLD_MODE_OFF:
            if self._pre_hold is not None:
                success = self._api.setMode(self._pre_hold)
            else:
                _LOGGER.info("No stored pre hold mode found - switching to hot water and heating")
                success = self._api.setMode(VICARE_MODE_DHWANDHEATING)
            # PyViCare currently returns 'None' on no error, checking for both for future changes
            if not (success["error"] is None or success["error"] == 'None'):
                _LOGGER.error("Failed to restore from hold mode on ViCare API to %s with status code %s and error %s", self._pre_hold, success["statusCode"], success["error"])
        else:
            _LOGGER.error("Unknown hold mode %s set - ignoring", hold_mode)

    def turn_on(self):
        """Turn on."""
        self._on = True
        self.schedule_update_ha_state()
        self._api.setMode(VICARE_MODE_DHWANDHEATING)

    def turn_off(self):
        """Turn off."""
        self._on = False
        self.schedule_update_ha_state()
        self._api.setMode(VICARE_MODE_OFF)


class ViCareWater(ClimateDevice):

    def __init__(self, hass, name, api):
        """Initialize the climate device."""
        self._name = name
        self._api = api
        self._support_flags = SUPPORT_FLAGS_WATER
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._target_temperature = None
        self._current_temperature = None

    def update(self):
        current_temperature = self._api.getDomesticHotWaterStorageTemperature() 
        if current_temperature is not None and current_temperature != "error":
            self._current_temperature = current_temperature
        else:
            self._current_temperature = -1

        self._target_temperature = self._api.getDomesticHotWaterConfiguredTemperature()

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

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        else:
            return
        
        self._api.setDomesticHotWaterTemperature(self._target_temperature)
                
        self.schedule_update_ha_state()
    
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return convert_temperature(VICARE_TEMP_WATER_MIN, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return convert_temperature(VICARE_TEMP_WATER_MAX, TEMP_CELSIUS, self.temperature_unit)

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

