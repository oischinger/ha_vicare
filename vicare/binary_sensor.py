"""Viessmann ViCare sensor device."""
from contextlib import suppress
import logging

from PyViCare.PyViCareUtils import (
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_POWER,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME

from .const import (
    DOMAIN,
    VICARE_API,
    VICARE_CIRCUITS,
    VICARE_DEVICE_CONFIG,
    VICARE_NAME,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"

GLOBAL_SENSORS = [
    {
        CONF_NAME: "Circulation pump active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCirculationPumpActive(),
    },
    {
        CONF_NAME: "Burner active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getBurnerActive(),
    },
]

CIRCUIT_SENSORS = [
    {
        CONF_NAME: "Compressor active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCompressorActive(),
    },
]


def _build_entity(name, vicare_api, device_config, sensor):
    try:
        sensor[CONF_GETTER](vicare_api)
        _LOGGER.debug("Found entity %s", name)
        return ViCareBinarySensor(
            name,
            vicare_api,
            device_config,
            sensor,
        )
    except PyViCareNotSupportedFeatureError:
        _LOGGER.warn("Feature not supported %s", name)
        return None
    except AttributeError:
        _LOGGER.debug("Attribute Error %s", name)
        return None



async def async_setup_entry(hass, config_entry, async_add_devices):
    """Create the ViCare binary sensor devices."""
    name = hass.data[DOMAIN][config_entry.entry_id][VICARE_NAME]

    all_devices = []
    for sensor in GLOBAL_SENSORS:
        entity = _build_entity(
            f"{name} {sensor[CONF_NAME]}",
            hass.data[DOMAIN][config_entry.entry_id][VICARE_API],
            hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
            sensor,
        )
        if entity != None:
            all_devices.append(entity)

    for sensor in CIRCUIT_SENSORS:
        for circuit in hass.data[DOMAIN][config_entry.entry_id][VICARE_CIRCUITS]:
            suffix = ""
            if len(hass.data[DOMAIN][config_entry.entry_id][VICARE_CIRCUITS]) > 1:
                suffix = f" {circuit.id}"
            entity = _build_entity(
                f"{name} {sensor[CONF_NAME]}{suffix}",
                circuit,
                hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
                sensor,
            )
            if entity != None:
                all_devices.append(entity)

    async_add_devices(all_devices)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the ViCare binary sensor devices."""
    # Legacy setup. Remove after configuration.yaml deprecation end
    if discovery_info is None:
        return

    name = hass.data[DOMAIN][VICARE_NAME]

    add_entities(
        [
            _build_entity(
                f"{name} {sensor[CONF_NAME]}",
                hass.data[DOMAIN][VICARE_API],
                hass.data[DOMAIN][VICARE_DEVICE_CONFIG],
                sensor,
            )
            for sensor in GLOBAL_SENSORS
        ]
    )


class ViCareBinarySensor(BinarySensorEntity):
    """Representation of a ViCare sensor."""

    def __init__(self, name, api, device_config, sensor):
        """Initialize the sensor."""
        self._sensor = sensor
        self._name = name
        self._api = api
        self._device_config = device_config
        self._state = None

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
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return f"{self._device_config.getConfig().serial}-{self._name}"

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
