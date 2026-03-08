"""Tests for integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mesh_solar import async_setup_entry
from custom_components.mesh_solar.const import (
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    CONF_URL,
    DEFAULT_ENVIRONMENT,
    DOMAIN,
)


async def test_async_setup_entry_creates_coordinator_and_forwards_platforms(
    hass,
    mock_config_entry,
    entry_data: dict[str, str],
) -> None:
    """A valid entry creates the coordinator and forwards platform setup."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with (
        patch("custom_components.mesh_solar._ensure_local_docs", AsyncMock()) as mock_docs,
        patch(
            "custom_components.mesh_solar.MeshSolarCoordinator",
            return_value=coordinator,
        ) as mock_coordinator_class,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ) as mock_forward,
    ):
        result = await async_setup_entry(hass, mock_config_entry)

    assert result is True
    assert hass.data[DOMAIN][mock_config_entry.entry_id] is coordinator
    mock_docs.assert_awaited_once()
    mock_coordinator_class.assert_called_once_with(
        hass,
        mock_config_entry,
        entry_data[CONF_URL],
        entry_data[CONF_API_KEY],
        entry_data[CONF_BATTERY_CAPACITY_SENSOR],
        DEFAULT_ENVIRONMENT,
        initial_hash="",
        initial_registration="",
    )
    mock_forward.assert_awaited_once_with(
        mock_config_entry, ["binary_sensor", "sensor", "button"]
    )


async def test_async_setup_entry_raises_for_missing_required_values(hass) -> None:
    """Missing required configuration blocks entry setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Mesh Solar",
        data={
            CONF_URL: "",
            CONF_API_KEY: "api-key",
            CONF_BATTERY_CAPACITY_SENSOR: "sensor.battery_capacity",
            CONF_ENVIRONMENT: DEFAULT_ENVIRONMENT,
            CONF_HASH: "",
            CONF_REGISTRATION_DATA: "",
        },
        entry_id="missing-url",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.mesh_solar._ensure_local_docs", AsyncMock()):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)
