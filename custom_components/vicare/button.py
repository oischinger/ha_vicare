"""Viessmann ViCare button device."""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import logging

from PyViCare.PyViCareUtils import PyViCareNotSupportedFeatureError
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ViCareEntity, ViCareRequiredKeysMixinWithSet, managed_exceptions
from .const import DOMAIN, VICARE_API, VICARE_DEVICE_CONFIG, VICARE_NAME

_LOGGER = logging.getLogger(__name__)

BUTTON_DHW_ACTIVATE_ONETIME_CHARGE = "activate_onetimecharge"


@dataclass
class ViCareButtonEntityDescription(
    ButtonEntityDescription, ViCareRequiredKeysMixinWithSet
):
    """Describes ViCare button entity."""


BUTTON_DESCRIPTIONS: tuple[ViCareButtonEntityDescription, ...] = (
    ViCareButtonEntityDescription(
        key=BUTTON_DHW_ACTIVATE_ONETIME_CHARGE,
        name="Activate one-time charge",
        icon="mdi:shower-head",
        entity_category=EntityCategory.CONFIG,
        value_getter=lambda api: api.getOneTimeCharge(),
        value_setter=lambda api: api.activateOneTimeCharge(),
    ),
)


def _build_entity(name, vicare_api, device_config, description):
    """Create a ViCare button entity."""
    with managed_exceptions(_LOGGER):
        _LOGGER.debug("Found device %s", name)
        try:
            description.value_getter(vicare_api)
            _LOGGER.debug("Found entity %s", name)
            return ViCareButton(
                name,
                vicare_api,
                device_config,
                description,
            )
        except PyViCareNotSupportedFeatureError:
            _LOGGER.info("Feature not supported %s", name)
            return None
        except AttributeError:
            _LOGGER.debug("Attribute Error %s", name)
            return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the ViCare button entities."""
    name = VICARE_NAME
    api = hass.data[DOMAIN][config_entry.entry_id][VICARE_API]

    entities = []

    for description in BUTTON_DESCRIPTIONS:
        entity = await hass.async_add_executor_job(
            _build_entity,
            f"{name} {description.name}",
            api,
            hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
            description,
        )
        if entity is not None:
            entities.append(entity)

    async_add_entities(entities)


class ViCareButton(ViCareEntity, ButtonEntity):
    """Representation of a ViCare button."""
    _logger = _LOGGER

    entity_description: ViCareButtonEntityDescription

    def __init__(
        self, name, api, device_config, description: ViCareButtonEntityDescription
    ):
        """Initialize the button."""
        self.entity_description = description
        self._device_config = device_config
        self._api = api

    def press(self) -> None:
        """Handle the button press."""
        with managed_exceptions(_LOGGER):
            with suppress(PyViCareNotSupportedFeatureError):
                self.entity_description.value_setter(self._api)

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        tmp_id = (
            f"{self._device_config.getConfig().serial}-{self.entity_description.key}"
        )
        if hasattr(self._api, "id"):
            return f"{tmp_id}-{self._api.id}"
        return tmp_id
