"""Tests for config and options flows."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mesh_solar.const import (
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    CONF_URL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_ENVIRONMENT_LABEL,
    DOMAIN,
    SANDBOX_ENVIRONMENT,
)


async def test_user_flow_creates_entry_with_normalized_data(hass) -> None:
    """The user flow trims inputs and stores Live as the empty environment."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: " https://example.com/api/Forecast_Get?code=user-code ",
            CONF_API_KEY: " api-key ",
            CONF_BATTERY_CAPACITY_SENSOR: " sensor.battery_capacity ",
            CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT_LABEL,
            CONF_HASH: " hash-value ",
            CONF_REGISTRATION_DATA: " reg-value ",
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Mesh Solar"
    assert result["data"] == {
        CONF_URL: "https://example.com/api/Forecast_Get?code=user-code",
        CONF_API_KEY: "api-key",
        CONF_BATTERY_CAPACITY_SENSOR: "sensor.battery_capacity",
        CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT,
        CONF_HASH: " hash-value ",
        CONF_REGISTRATION_DATA: " reg-value ",
    }


async def test_options_flow_updates_entry_data_and_clears_duplicate_options(hass) -> None:
    """Options flow writes authoritative values back into entry.data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Mesh Solar",
        data={
            CONF_URL: "https://example.com/original",
            CONF_API_KEY: "original-key",
            CONF_BATTERY_CAPACITY_SENSOR: "sensor.original_capacity",
            CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT,
            CONF_HASH: "",
            CONF_REGISTRATION_DATA: "",
        },
        options={
            CONF_URL: "https://example.com/legacy-option",
            CONF_API_KEY: "legacy-option-key",
        },
        entry_id="options-entry",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "https://example.com/updated",
            CONF_API_KEY: "updated-key",
            CONF_BATTERY_CAPACITY_SENSOR: "sensor.updated_capacity",
            CONF_ENVIRONMENT: SANDBOX_ENVIRONMENT,
            CONF_HASH: "new-hash",
            CONF_REGISTRATION_DATA: "new-registration",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.data == {
        CONF_URL: "https://example.com/updated",
        CONF_API_KEY: "updated-key",
        CONF_BATTERY_CAPACITY_SENSOR: "sensor.updated_capacity",
        CONF_ENVIRONMENT: SANDBOX_ENVIRONMENT,
        CONF_HASH: "new-hash",
        CONF_REGISTRATION_DATA: "new-registration",
    }
    assert entry.options == {}


async def test_user_flow_rejects_invalid_url(hass) -> None:
    """The user flow validates forecast URLs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "not-a-url",
            CONF_API_KEY: "api-key",
            CONF_BATTERY_CAPACITY_SENSOR: "sensor.battery_capacity",
            CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT_LABEL,
            CONF_HASH: "",
            CONF_REGISTRATION_DATA: "",
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_URL: "invalid_url"}


async def test_user_flow_rejects_invalid_entity_id(hass) -> None:
    """The user flow validates the battery capacity entity ID."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "https://example.com/api/Forecast_Get?code=user-code",
            CONF_API_KEY: "api-key",
            CONF_BATTERY_CAPACITY_SENSOR: "not an entity",
            CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT_LABEL,
            CONF_HASH: "",
            CONF_REGISTRATION_DATA: "",
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_BATTERY_CAPACITY_SENSOR: "invalid_entity_id"}
