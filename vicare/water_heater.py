"""Viessmann ViCare water_heater device."""
from contextlib import suppress
import logging

from PyViCare.PyViCareUtils import (
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.water_heater import (
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, TEMP_CELSIUS

from .const import (
    CONF_HEATING_TYPE,
    DOMAIN,
    VICARE_API,
    VICARE_CIRCUITS,
    VICARE_DEVICE_CONFIG,
    VICARE_NAME,
)

_LOGGER = logging.getLogger(__name__)

VICARE_MODE_DHW = "dhw"
VICARE_MODE_DHWANDHEATING = "dhwAndHeating"
VICARE_MODE_FORCEDREDUCED = "forcedReduced"
VICARE_MODE_FORCEDNORMAL = "forcedNormal"
VICARE_MODE_OFF = "standby"

VICARE_TEMP_WATER_MIN = 10
VICARE_TEMP_WATER_MAX = 60

OPERATION_MODE_ON = "on"
OPERATION_MODE_OFF = "off"

SUPPORT_FLAGS_HEATER = SUPPORT_TARGET_TEMPERATURE

VICARE_TO_HA_HVAC_DHW = {
    VICARE_MODE_DHW: OPERATION_MODE_ON,
    VICARE_MODE_DHWANDHEATING: OPERATION_MODE_ON,
    VICARE_MODE_FORCEDREDUCED: OPERATION_MODE_OFF,
    VICARE_MODE_FORCEDNORMAL: OPERATION_MODE_ON,
    VICARE_MODE_OFF: OPERATION_MODE_OFF,
}

HA_TO_VICARE_HVAC_DHW = {
    OPERATION_MODE_OFF: VICARE_MODE_OFF,
    OPERATION_MODE_ON: VICARE_MODE_DHW,
}


def _build_entity(name, vicare_api, circuit, device_config, heating_type):
    _LOGGER.debug("Found device %s", name)
    return ViCareWater(
        name,
        vicare_api,
        circuit,
        device_config,
        heating_type,
    )


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the ViCare climate platform."""
    name = hass.data[DOMAIN][config_entry.entry_id][VICARE_NAME]

    all_devices = [
        _build_entity(
            f"{name} Water",
            hass.data[DOMAIN][config_entry.entry_id][VICARE_API],
            circuit,
            hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
            hass.data[DOMAIN][config_entry.entry_id][CONF_HEATING_TYPE],
        )
        for circuit in hass.data[DOMAIN][config_entry.entry_id][VICARE_CIRCUITS]
    ]

    async_add_devices(all_devices)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Create the ViCare water_heater devices."""
    # Legacy setup. Remove after configuration.yaml deprecation end
    if discovery_info is None:
        return

    name = hass.data[DOMAIN][VICARE_NAME]

    async_add_entities(
        [
            _build_entity(
                f"{name} Water",
                hass.data[DOMAIN][VICARE_API],
                hass.data[DOMAIN][VICARE_DEVICE_CONFIG],
                hass.data[DOMAIN][CONF_HEATING_TYPE],
            )
            for circuit in hass.data[DOMAIN][VICARE_CIRCUITS]
        ]
    )


class ViCareWater(WaterHeaterEntity):
    """Representation of the ViCare domestic hot water device."""

    def __init__(self, name, api, circuit, device_config, heating_type):
        """Initialize the DHW water_heater device."""
        self._name = name
        self._state = None
        self._api = api
        self._circuit = circuit
        self._device_config = device_config
        self._attributes = {}
        self._target_temperature = None
        self._current_temperature = None
        self._current_mode = None
        self._heating_type = heating_type

    def update(self):
        """Let HA know there has been an update from the ViCare API."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._current_temperature = (
                    self._api.getDomesticHotWaterStorageTemperature()
                )

            with suppress(PyViCareNotSupportedFeatureError):
                self._target_temperature = (
                    self._api.getDomesticHotWaterDesiredTemperature()
                )

            with suppress(PyViCareNotSupportedFeatureError):
                self._current_mode = self._circuit.getActiveMode()

        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return f"{self._device_config.getConfig().serial}-{self._name}"

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self._device_config.getConfig().serial)},
            "name": self._device_config.getModel(),
            "manufacturer": "Viessmann",
            "model": (DOMAIN, self._device_config.getModel()),
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_HEATER

    @property
    def name(self):
        """Return the name of the water_heater device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

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
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._api.setDomesticHotWaterTemperature(temp)
            self._target_temperature = temp

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return VICARE_TEMP_WATER_MIN

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return VICARE_TEMP_WATER_MAX

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return VICARE_TO_HA_HVAC_DHW.get(self._current_mode)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return list(HA_TO_VICARE_HVAC_DHW)
