"""The ViCare integration."""
import enum
import logging

from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareGazBoiler import GazBoiler
from PyViCare.PyViCareHeatPump import HeatPump
import voluptuous as vol

from homeassistant.const import (
    ATTR_COMMAND,
    ATTR_ENTITY_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR

_LOGGER = logging.getLogger(__name__)

VICARE_PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

DOMAIN = "vicare"
PYVICARE_ERROR = "error"
VICARE_API = "api"
VICARE_NAME = "name"
VICARE_HEATING_TYPE = "heating_type"

CONF_CIRCUIT = "circuit"
CONF_HEATING_TYPE = "heating_type"
DEFAULT_HEATING_TYPE = "generic"

SERVICE_VICARE_MODE = "vicare_mode"

SERVICE_VICARE_MODE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_ids, vol.Required(ATTR_COMMAND): cv.string}
)

class HeatingType(enum.Enum):
    """Possible options for heating type."""

    generic = "generic"
    gas = "gas"
    heatpump = "heatpump"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
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
    conf = config[DOMAIN]
    params = {"token_file": hass.config.path(STORAGE_DIR, "vicare_token.save")}
    if conf.get(CONF_CIRCUIT) is not None:
        params["circuit"] = conf[CONF_CIRCUIT]

    params["cacheDuration"] = conf.get(CONF_SCAN_INTERVAL)

    heating_type = conf[CONF_HEATING_TYPE]

    try:
        if heating_type == HeatingType.gas:
            vicare_api = GazBoiler(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.heatpump:
            vicare_api = HeatPump(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        else:
            vicare_api = Device(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
    except AttributeError:
        _LOGGER.error(
            "Failed to create PyViCare API client. Please check your credentials"
        )
        return False

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["entities"] = {}
    hass.data[DOMAIN]["entities"]["climate"] = []
    hass.data[DOMAIN][VICARE_API] = vicare_api
    hass.data[DOMAIN][VICARE_NAME] = conf[CONF_NAME]
    hass.data[DOMAIN][VICARE_HEATING_TYPE] = heating_type

    for platform in VICARE_PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, {}, config)

    def service_vicare_mode(service):
        """Dispatch service calls to target entities."""
        cmd = service.data[ATTR_COMMAND]
        entity_id = service.data[ATTR_ENTITY_ID]
        target_devices = [
            dev
            for dev in hass.data[DOMAIN]["entities"]["climate"]
            if dev.entity_id in entity_id
        ]

        for target_device in target_devices:
            target_device.vicare_mode(cmd)

    hass.services.register(
        DOMAIN,
        SERVICE_VICARE_MODE,
        service_vicare_mode,
        schema=SERVICE_VICARE_MODE_SCHEMA,
    )
    return True
