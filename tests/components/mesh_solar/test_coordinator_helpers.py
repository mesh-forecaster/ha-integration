"""Tests for payload normalization helpers."""

from custom_components.mesh_solar.coordinator_helpers import (
    extract_first,
    normalize_forecast,
    normalize_periods,
)


def test_extract_first_handles_none_and_missing() -> None:
    """Helper returns an empty string for explicit null values."""
    assert extract_first({"Hash": None}, ("Hash", "hash")) == ""
    assert extract_first({}, ("Hash", "hash")) is None


def test_normalize_periods_handles_nested_forecast_payload() -> None:
    """Periods are normalized from mixed-case upstream payloads."""
    payload = {
        "Forecast": {
            "Periods": [
                {
                    "Id": 42,
                    "Period": "3",
                    "Date": "2026-03-07T10:00:00+00:00",
                    "Price": "12.50",
                    "ShouldImport": "true",
                    "Amount": "0.4",
                    "Battery": "67.5",
                    "BmsHoldPeriod": "false",
                    "BatteryManagementSystemState": "charging",
                },
                "ignore-me",
            ]
        }
    }

    assert normalize_periods(payload) == [
        {
            "id": "42",
            "period": 3,
            "date": "2026-03-07T10:00:00+00:00",
            "price": 12.5,
            "should_import": True,
            "amount": 0.4,
            "battery": 67.5,
            "bms_hold_period": False,
            "battery_management_system_state": "charging",
        }
    ]


def test_normalize_forecast_extracts_primary_fields() -> None:
    """Forecast normalization keeps the stable keys used by entities."""
    payload = {
        "forecastEntity": {
            "Id": "forecast-1",
            "RegistrationId": "registration-7",
            "Date": "2026-03-07T10:00:00+00:00",
            "Hash": "hash-123",
            "CurrentCapacity": "18.5",
            "MinCapacity": "10",
            "TargetCapacity": "55.5",
            "BatteryManagementSystemState": "hold",
            "ShouldImport": False,
            "CloudUpdateEnabled": "true",
            "RegistrationData": "reg-data",
            "TotalCost": "1.23",
            "ChargingCost": "0.45",
            "Saving": "0.78",
            "Periods": [{"Period": 1, "Date": "2026-03-07T10:00:00+00:00"}],
        }
    }

    assert normalize_forecast(payload) == {
        "id": "forecast-1",
        "registration_id": "registration-7",
        "date": "2026-03-07T10:00:00+00:00",
        "hash": "hash-123",
        "periods": [{"period": 1, "date": "2026-03-07T10:00:00+00:00"}],
        "current_capacity": 18.5,
        "min_capacity": 10.0,
        "target_capacity": 55.5,
        "battery_management_system_state": "hold",
        "should_import": False,
        "cloud_update_enabled": True,
        "registration_data": "reg-data",
        "total_cost": 1.23,
        "charging_cost": 0.45,
        "saving": 0.78,
    }
