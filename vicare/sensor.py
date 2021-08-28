"""Viessmann ViCare sensor device."""
from contextlib import suppress
import logging

from PyViCare.PyViCareUtils import (
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TIME_HOURS,
)

from .const import (
    CONF_HEATING_TYPE,
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
        CONF_NAME: "Outside Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.getOutsideTemperature(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    # gas sensors
    {
        CONF_NAME: "Boiler Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.getBoilerTemperature(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    {
        CONF_NAME: "Burner modulation",
        CONF_ICON: "mdi:percent",
        CONF_UNIT_OF_MEASUREMENT: PERCENTAGE,
        CONF_GETTER: lambda api: api.getBurnerModulation(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Hot water gas consumption today",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionDomesticHotWaterToday(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Hot water gas consumption this week",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionDomesticHotWaterThisWeek(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Hot water gas consumption this month",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionDomesticHotWaterThisMonth(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Hot water gas consumption this year",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionDomesticHotWaterThisYear(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Heating gas consumption today",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionHeatingToday(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Heating gas consumption this week",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionHeatingThisWeek(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Heating gas consumption this month",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionHeatingThisMonth(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Heating gas consumption this year",
        CONF_ICON: "mdi:power",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getGasConsumptionHeatingThisYear(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Burner Starts",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.getBurnerStarts(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Burner Hours",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getBurnerHours(),
        CONF_DEVICE_CLASS: None,
    },
    # heatpump sensors
    {
        CONF_NAME: "Return Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.getReturnTemperature(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    # fuelcell sensors
    {
        CONF_NAME: "Power production current",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: POWER_WATT,
        CONF_GETTER: lambda api: api.getPowerProductionCurrent(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
    },
    {
        CONF_NAME: "Power production today",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getPowerProductionToday(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
    },
    {
        CONF_NAME: "Power production this week",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getPowerProductionThisWeek(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
    },
    {
        CONF_NAME: "Power production this month",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getPowerProductionThisMonth(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
    },
    {
        CONF_NAME: "Power production this year",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        CONF_GETTER: lambda api: api.getPowerProductionThisYear(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
    },
]

CIRCUIT_SENSORS = [
    {
        CONF_NAME: "Supply Temperature",
        CONF_ICON: None,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        CONF_GETTER: lambda api: api.getSupplyTemperature(),
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
    },
    # heatpump sensors
    {
        CONF_NAME: "Compressor Starts",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_GETTER: lambda api: api.getCompressorStarts(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHours(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours Load Class 1",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHoursLoadClass1(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours Load Class 2",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHoursLoadClass2(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours Load Class 3",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHoursLoadClass3(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours Load Class 4",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHoursLoadClass4(),
        CONF_DEVICE_CLASS: None,
    },
    {
        CONF_NAME: "Compressor Hours Load Class 5",
        CONF_ICON: "mdi:counter",
        CONF_UNIT_OF_MEASUREMENT: TIME_HOURS,
        CONF_GETTER: lambda api: api.getCompressorHoursLoadClass5(),
        CONF_DEVICE_CLASS: None,
    },
]


def _build_entity(name, vicare_api, device_config, sensor):
    _LOGGER.debug("Found device %s", name)
    try:
        sensor[CONF_GETTER](vicare_api)
        _LOGGER.debug("Found entity %s", name)
        return ViCareSensor(
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
    """Create the ViCare sensor devices."""
    heating_type = hass.data[DOMAIN][config_entry.entry_id][CONF_HEATING_TYPE]
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
    """Create the ViCare sensor devices."""
    # Legacy setup. Remove after configuration.yaml deprecation end
    if discovery_info is None:
        return

    heating_type = hass.data[DOMAIN][CONF_HEATING_TYPE]
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


class ViCareSensor(SensorEntity):
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
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._sensor[CONF_ICON]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._sensor[CONF_UNIT_OF_MEASUREMENT]

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
