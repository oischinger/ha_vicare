"""The ViCare integration."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
import logging
import typing

from PyViCare.PyViCare import PyViCare
from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareUtils import (
    PyViCareInvalidDataError,
    PyViCareRateLimitError,
    PyViCareInvalidCredentialsError,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.storage import STORAGE_DIR
import requests

from .const import (
    CONF_HEATING_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HEATING_TYPE_TO_CREATOR_METHOD,
    PLATFORMS,
    VICARE_API,
    VICARE_DEVICE_CONFIG,
    HeatingType,
)

if typing.TYPE_CHECKING:
    from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig


_LOGGER = logging.getLogger(__name__)


class ViCareError(Exception):
    """A typed exception to identify errors raised from ViCare code"""


class ViCareEntity:
    """Abstract base entity class for ViCare entities"""

    _logger: 'logging.Logger' # using the logger from the inheriting class
    _device_config: 'PyViCareDeviceConfig'

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_config.getConfig().serial)},
            name=self._device_config.getModel(),
            manufacturer="Viessmann",
            model=self._device_config.getModel(),
            configuration_url="https://developer.viessmann.com/",
        )

    def _internal_update(self):
        """virtual abstract: override to actually do the update"""
        raise NotImplementedError()

    def update(self):
        """Let HA know there has been an update from the ViCare API."""
        with managed_exceptions(self._logger):
            self._internal_update()


@dataclass()
class ViCareRequiredKeysMixin:
    """Mixin for required keys."""

    value_getter: Callable[[Device], bool]


@dataclass()
class ViCareRequiredKeysMixinWithSet:
    """Mixin for required keys with setter."""

    value_getter: Callable[[Device], bool]
    value_setter: Callable[[Device], bool]


@contextmanager
def managed_exceptions(logger: 'logging.Logger'):
    try:
        yield
    except requests.exceptions.ConnectionError:
        logger.error("Unable to retrieve data from ViCare server")
    except PyViCareRateLimitError as limit_exception:
        logger.error("Vicare API rate limit exceeded: %s", limit_exception)
    except PyViCareInvalidDataError as invalid_data_exception:
        logger.error("Invalid data from Vicare server: %s", invalid_data_exception)
    except ValueError:
        logger.error("Unable to decode data from ViCare server")
    except ViCareError as error:
        logger.error("ViCare error: %s", str(error))
    except Exception as error:
        if logger.isEnabledFor(logging.DEBUG):
            raise error
        else:
            logger.error("Unexpected %s: %s", type(error).__name__, str(error))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    _LOGGER.debug("Setting up ViCare component")

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {}

    try:
        await hass.async_add_executor_job(setup_vicare_api, hass, entry)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except PyViCareInvalidCredentialsError as auth_error:
        raise ConfigEntryAuthFailed from auth_error
    except Exception as error:
        raise ConfigEntryNotReady from error



def vicare_login(hass, entry_data):
    """Login via PyVicare API."""
    vicare_api = PyViCare()
    vicare_api.setCacheDuration(DEFAULT_SCAN_INTERVAL)
    vicare_api.initWithCredentials(
        entry_data[CONF_USERNAME],
        entry_data[CONF_PASSWORD],
        entry_data[CONF_CLIENT_ID],
        hass.config.path(STORAGE_DIR, "vicare_token.save"),
    )
    return vicare_api


def setup_vicare_api(hass, entry):
    """Set up PyVicare API."""
    vicare_api = vicare_login(hass, entry.data)

    for device in vicare_api.devices:
        _LOGGER.info(
            "Found device: %s (online: %s)", device.getModel(), str(device.isOnline())
        )

    # Currently we only support a single device
    device = vicare_api.devices[0]
    hass.data[DOMAIN][entry.entry_id][VICARE_DEVICE_CONFIG] = device
    hass.data[DOMAIN][entry.entry_id][VICARE_API] = getattr(
        device,
        HEATING_TYPE_TO_CREATOR_METHOD[HeatingType(entry.data[CONF_HEATING_TYPE])],
    )()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload ViCare config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
