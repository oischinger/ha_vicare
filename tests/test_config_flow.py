"""Test the ViCare config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow, setup
from homeassistant.components.vicare.const import CONF_HEATING_TYPE, DOMAIN
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)

from . import create_mock_client

from tests.common import MockConfigEntry


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.vicare.async_setup_entry",
        return_value=True,
    ), patch(
        "homeassistant.components.vicare.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.vicare.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "foo@bar.com",
                CONF_PASSWORD: "1234",
                CONF_CLIENT_ID: "5678",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == "ViCare"
    assert result2["data"] == {
        CONF_USERNAME: "foo@bar.com",
        CONF_PASSWORD: "1234",
        CONF_CLIENT_ID: "5678",
        CONF_HEATING_TYPE: "auto",
        CONF_SCAN_INTERVAL: 60,
        CONF_NAME: "ViCare",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import(hass):
    """Test that the import works."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    with patch(
        "homeassistant.components.vicare.async_setup_entry",
        return_value=True,
    ), patch(
        "homeassistant.components.vicare.async_setup", return_value=True
    ) as mock_setup, patch(
        "homeassistant.components.vicare.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                CONF_USERNAME: "foo@bar.com",
                CONF_PASSWORD: "1234",
                CONF_CLIENT_ID: "5678",
                CONF_HEATING_TYPE: "generic",
                CONF_SCAN_INTERVAL: 60,
                CONF_NAME: "ViCare Test",
            },
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "Configuration.yaml"
        assert result["data"] == {
            CONF_USERNAME: "foo@bar.com",
            CONF_PASSWORD: "1234",
            CONF_CLIENT_ID: "5678",
            CONF_HEATING_TYPE: "auto",
            CONF_SCAN_INTERVAL: 60,
            CONF_NAME: "ViCare Test",
        }

        await hass.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1
