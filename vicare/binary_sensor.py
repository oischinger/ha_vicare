"""Viessmann ViCare sensor device."""
from contextlib import suppress
import logging

from PyViCare.PyViCareUtils import PyViCareNotSupportedFeatureError, PyViCareRateLimitError
import requests

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_POWER,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME

from . import VICARE_API, VICARE_NAME
from .const import CONF_HEATING_TYPE, DOMAIN, HeatingType

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"

SENSOR_CIRCULATION_PUMP_ACTIVE = "circulationpump_active"

# gas sensors
SENSOR_BURNER_ACTIVE = "burner_active"

# heatpump sensors
SENSOR_COMPRESSOR_ACTIVE = "compressor_active"

SENSOR_TYPES = {
    SENSOR_CIRCULATION_PUMP_ACTIVE: {
        CONF_NAME: "Circulation pump active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCirculationPumpActive(),
    },
    # gas sensors
    SENSOR_BURNER_ACTIVE: {
        CONF_NAME: "Burner active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getBurnerActive(),
    },
    # heatpump sensors
    SENSOR_COMPRESSOR_ACTIVE: {
        CONF_NAME: "Compressor active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCompressorActive(),
    },
}

SENSORS_GENERIC = [SENSOR_CIRCULATION_PUMP_ACTIVE]

SENSORS_BY_HEATINGTYPE = {
    HeatingType.gas: [SENSOR_BURNER_ACTIVE],
    HeatingType.heatpump: [
        SENSOR_COMPRESSOR_ACTIVE,
    ],
    HeatingType.fuelcell: [SENSOR_BURNER_ACTIVE],
}


def _build_entity(name, vicare_api, sensor):
    _LOGGER.debug("Found device %s", name)
    return ViCareBinarySensor(
        name,
        vicare_api,
        sensor,
    )


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Create the ViCare binary sensor devices."""
    vicare_api = hass.data[DOMAIN][VICARE_API]
    heating_type = hass.data[DOMAIN][CONF_HEATING_TYPE]
    name = hass.data[DOMAIN][VICARE_NAME]

    sensors = SENSORS_GENERIC.copy()

    if heating_type != HeatingType.generic:
        sensors.extend(SENSORS_BY_HEATINGTYPE[heating_type])

    all_devices = [
        _build_entity(f"{name} {SENSOR_TYPES[sensor][CONF_NAME]}", vicare_api, sensor)
        for sensor in sensors
    ]

    async_add_devices(all_devices)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the ViCare binary sensor devices."""
    # Legacy setup. Remove after configuration.yaml deprecation end
    if discovery_info is None:
        return

    vicare_api = hass.data[DOMAIN][VICARE_API]
    heating_type = hass.data[DOMAIN][CONF_HEATING_TYPE]
    name = hass.data[DOMAIN][VICARE_NAME]

    sensors = SENSORS_GENERIC.copy()

    if heating_type != HeatingType.generic:
        sensors.extend(SENSORS_BY_HEATINGTYPE[heating_type])

    add_entities(
        [
            ViCareBinarySensor(
                f"{name} {SENSOR_TYPES[sensor][CONF_NAME]}", vicare_api, sensor
            )
            for sensor in sensors
        ]
    )


class ViCareBinarySensor(BinarySensorEntity):
    """Representation of a ViCare sensor."""

    def __init__(self, name, api, sensor_type):
        """Initialize the sensor."""
        self._sensor = SENSOR_TYPES[sensor_type]
        self._name = name
        self._api = api.asGazBoiler()
        self._device_config = api
        self._sensor_type = sensor_type
        self._state = None

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self._name)},
            "name": self.name,
            "manufacturer": "Viessmann",
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return f"{self._device_config.getModel()}-{self._name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._sensor[CONF_DEVICE_CLASS]

    def update(self):
        """Update state of sensor."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._state = self._sensor[CONF_GETTER](self._api)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
