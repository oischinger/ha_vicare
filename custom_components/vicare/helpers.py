"""Helpers for ViCare integration."""
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig

from homeassistant.core import callback


@callback
def get_unique_id(
    _device_config: PyViCareDeviceConfig, entity_key: str, sub_id=None
) -> str:
    """Return unique ID for this device."""
    tmp_id = (
        f"{_device_config.getConfig().serial}-{_device_config.getId()}-{entity_key}"
    )
    if sub_id is not None:
        return f"{tmp_id}-{sub_id}"
    return tmp_id
