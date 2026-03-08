"""Tests for the update coordinator."""

from unittest.mock import AsyncMock

from custom_components.mesh_solar.const import (
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    SANDBOX_ENVIRONMENT,
)
from custom_components.mesh_solar.coordinator import MeshSolarCoordinator


async def test_coordinator_updates_cached_values_from_api(
    hass,
    mock_config_entry,
    entry_data: dict[str, str],
    aioclient_mock,
) -> None:
    """Coordinator normalizes payload data and persists cached values."""
    hass.states.async_set(entry_data["battery_capacity_sensor"], "53")

    coordinator = MeshSolarCoordinator(
        hass,
        mock_config_entry,
        entry_data["url"],
        entry_data["api_key"],
        entry_data["battery_capacity_sensor"],
        SANDBOX_ENVIRONMENT,
        initial_hash="old-hash",
        initial_registration="old-registration",
    )

    url = coordinator._build_request_url("53")
    aioclient_mock.get(
        url,
        json={
            "Hash": "new-hash",
            "RegistrationData": "new-registration",
            "Currency": "GBP",
            "TargetCapacity": "57.5",
            "Forecast": {
                "Date": "2026-03-07T10:00:00+00:00",
                "Periods": [
                    {
                        "Period": 1,
                        "Date": "2026-03-07T10:00:00+00:00",
                        "BatteryManagementSystemState": "charging",
                    }
                ],
            },
        },
    )

    data = await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert data["Hash"] == "new-hash"
    assert coordinator.last_hash == "new-hash"
    assert coordinator.registration_data == "new-registration"
    assert coordinator.currency == "GBP"
    assert coordinator.target_capacity == 57.5
    assert coordinator.forecast["date"] == "2026-03-07T10:00:00+00:00"
    assert coordinator.forecast_periods == [
        {
            "period": 1,
            "date": "2026-03-07T10:00:00+00:00",
            "battery_management_system_state": "charging",
        }
    ]
    assert mock_config_entry.data[CONF_HASH] == "new-hash"
    assert mock_config_entry.data[CONF_REGISTRATION_DATA] == "new-registration"


async def test_clear_registration_data_persists_and_refreshes(
    hass,
    mock_config_entry,
    entry_data: dict[str, str],
) -> None:
    """Manual clear removes cached registration data and requests a refresh."""
    coordinator = MeshSolarCoordinator(
        hass,
        mock_config_entry,
        entry_data["url"],
        entry_data["api_key"],
        entry_data["battery_capacity_sensor"],
        SANDBOX_ENVIRONMENT,
        initial_hash="existing-hash",
        initial_registration="cached-registration",
    )
    coordinator.async_request_refresh = AsyncMock()

    await coordinator.async_clear_registration_data()
    await hass.async_block_till_done()

    assert coordinator.registration_data == ""
    assert mock_config_entry.data[CONF_REGISTRATION_DATA] == ""
    coordinator.async_request_refresh.assert_awaited_once()
