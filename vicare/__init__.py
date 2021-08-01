"""The ViCare integration."""
import logging

from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareFuelCell import FuelCell
from PyViCare.PyViCareGazBoiler import GazBoiler
from PyViCare.PyViCareHeatPump import HeatPump
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    CONF_CIRCUIT,
    CONF_HEATING_TYPE,
    DEFAULT_HEATING_TYPE,
    DOMAIN,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

VICARE_API = "api"
VICARE_NAME = "name"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    cv.time_period, lambda value: value.total_seconds()
                ),
                vol.Optional(CONF_CIRCUIT): int,
                vol.Optional(CONF_NAME, default="ViCare"): cv.string,
                vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): cv.enum(
                    HeatingType
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Create the ViCare component."""
    if config.get(DOMAIN) is None:
        # Setup via UI. No need to continue yaml-based setup
        return True

    conf = config[DOMAIN]
    params = {"token_file": hass.config.path(STORAGE_DIR, "vicare_token.save")}
    if conf.get(CONF_CIRCUIT) is not None:
        params["circuit"] = conf[CONF_CIRCUIT]

    params["cacheDuration"] = conf.get(CONF_SCAN_INTERVAL)
    params["client_id"] = conf.get(CONF_CLIENT_ID)
    heating_type = conf[CONF_HEATING_TYPE]

    try:
        if heating_type == HeatingType.gas:
            vicare_api = GazBoiler(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.heatpump:
            vicare_api = HeatPump(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.fuelcell:
            vicare_api = FuelCell(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        else:
            vicare_api = Device(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
    except AttributeError:
        _LOGGER.error(
            "Failed to create PyViCare API client. Please check your credentials"
        )
        return False

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][VICARE_API] = vicare_api
    hass.data[DOMAIN][VICARE_NAME] = conf[CONF_NAME]
    hass.data[DOMAIN][CONF_HEATING_TYPE] = heating_type

    for platform in PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, {}, config)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    _LOGGER.debug("Setting up ViCare component")

    params = {"token_file": hass.config.path(STORAGE_DIR, "vicare_token.save")}
    if entry.data.get(CONF_CIRCUIT) is not None:
        params["circuit"] = entry.data[CONF_CIRCUIT]

    params["cacheDuration"] = entry.data[CONF_SCAN_INTERVAL]
    params["client_id"] = entry.data[CONF_CLIENT_ID]

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][VICARE_NAME] = entry.data[CONF_NAME]
    if entry.data.get(CONF_HEATING_TYPE) is not None:
        hass.data[DOMAIN][CONF_HEATING_TYPE] = HeatingType[
            entry.data[CONF_HEATING_TYPE]
        ]
    else:
        hass.data[DOMAIN][CONF_HEATING_TYPE] = DEFAULT_HEATING_TYPE

    # For previous config entries where unique_id is None
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=entry.data[CONF_USERNAME]
        )

    await hass.async_add_executor_job(setup_vicare_api, hass, entry, params)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    # TODO: await async_setup_services(hass)

    return True


def setup_vicare_api(hass, entry, params):
    """Set up PyVicare API."""
    heating_type = hass.data[DOMAIN][CONF_HEATING_TYPE]
    try:
        if heating_type == HeatingType.gas:
            vicare_api = GazBoiler(
                entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], **params
            )
        elif heating_type == HeatingType.heatpump:
            vicare_api = HeatPump(
                entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], **params
            )
        elif heating_type == HeatingType.fuelcell:
            vicare_api = FuelCell(
                entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], **params
            )
        else:
            vicare_api = Device(
                entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], **params
            )
    except AttributeError as ex:
        raise ConfigEntryAuthFailed from ex
    hass.data[DOMAIN][VICARE_API] = vicare_api
