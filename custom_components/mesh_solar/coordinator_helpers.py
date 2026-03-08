from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional


def extract_first(payload: dict, keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        if key in payload:
            value = payload[key]
            if value is None:
                return ""
            return value
    return None


def normalize_periods(payload: dict | None) -> list[dict]:
    if not isinstance(payload, dict):
        return []

    raw_periods = None
    for key in ("Periods", "periods", "forecastPeriods", "ForecastPeriods"):
        if key in payload:
            raw_periods = payload.get(key)
            break

    if raw_periods is None:
        forecast_container = None
        for key in ("Forecast", "forecast", "forecastEntity"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                forecast_container = candidate
                break
        if isinstance(forecast_container, dict):
            for key in ("Periods", "periods", "forecastPeriods", "ForecastPeriods"):
                if key in forecast_container:
                    raw_periods = forecast_container.get(key)
                    break

    if not isinstance(raw_periods, list):
        return []

    normalized: list[dict] = []
    for item in raw_periods:
        if not isinstance(item, dict):
            continue

        entry = {
            "id": _coerce_str(
                extract_first(item, ("Id", "id"))
            ),
            "period": _coerce_int(
                extract_first(item, ("Period", "period", "index"))
            ),
            "date": _coerce_datetime(
                extract_first(item, ("Date", "date", "start"))
            ),
            "price": _coerce_float(
                extract_first(item, ("Price", "price"))
            ),
            "should_import": _coerce_bool(
                extract_first(item, ("ShouldImport", "shouldImport", "should_import"))
            ),
            "amount": _coerce_float(
                extract_first(item, ("Amount", "amount"))
            ),
            "battery": _coerce_float(
                extract_first(item, ("Battery", "battery"))
            ),
            "bms_hold_period": _coerce_bool(
                extract_first(
                    item,
                    ("BmsHoldPeriod", "bmsHoldPeriod", "bms_hold_period", "bmsholdperiod"),
                )
            ),
            "battery_management_system_state": _coerce_str(
                extract_first(
                    item,
                    (
                        "BatteryManagementSystemState",
                        "batteryManagementSystemState",
                        "battery_management_system_state",
                    ),
                )
            ),
        }

        filtered = {
            key: value
            for key, value in entry.items()
            if value is not None and (not isinstance(value, str) or value.strip() != "")
        }
        if filtered:
            normalized.append(filtered)

    return normalized


def normalize_forecast(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}

    forecast_source = payload
    for key in ("Forecast", "forecast", "forecastEntity"):
        candidate = payload.get(key)
        if isinstance(candidate, dict):
            forecast_source = candidate
            break

    normalized: dict = {}

    _add_if_value(
        normalized,
        "id",
        _coerce_str(extract_first(forecast_source, ("Id", "id"))),
    )

    _add_if_value(
        normalized,
        "registration_id",
        _coerce_str(extract_first(forecast_source, ("RegistrationId", "registrationId", "registration_id"))),
    )

    _add_if_value(
        normalized,
        "date",
        _coerce_datetime(extract_first(forecast_source, ("Date", "date", "forecastDate", "forecast_date"))),
    )

    _add_if_value(
        normalized,
        "hash",
        _coerce_str(extract_first(forecast_source, ("Hash", "hash", "forecastHash", "forecast_hash"))),
    )

    periods = normalize_periods(forecast_source)
    if periods:
        normalized["periods"] = periods

    _add_if_value(
        normalized,
        "current_capacity",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "CurrentCapacity",
                    "currentCapacity",
                    "current_capacity",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "min_capacity",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "MinCapacity",
                    "minCapacity",
                    "min_capacity",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "target_capacity",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "TargetCapacity",
                    "targetCapacity",
                    "target_capacity",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "battery_management_system_state",
        _coerce_str(
            extract_first(
                forecast_source,
                (
                    "BatteryManagementSystemState",
                    "batteryManagementSystemState",
                    "battery_management_system_state",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "should_import",
        _coerce_bool(
            extract_first(
                forecast_source,
                (
                    "ShouldImport",
                    "shouldImport",
                    "should_import",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "cloud_update_enabled",
        _coerce_bool(
            extract_first(
                forecast_source,
                (
                    "CloudUpdateEnabled",
                    "cloudUpdateEnabled",
                    "cloud_update_enabled",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "registration_data",
        _coerce_str(
            extract_first(
                forecast_source,
                (
                    "RegistrationData",
                    "registrationData",
                    "registration_data",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "total_cost",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "TotalCost",
                    "totalCost",
                    "total_cost",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "charging_cost",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "ChargingCost",
                    "chargingCost",
                    "charging_cost",
                ),
            )
        ),
    )

    _add_if_value(
        normalized,
        "saving",
        _coerce_float(
            extract_first(
                forecast_source,
                (
                    "Saving",
                    "saving",
                    "savings",
                ),
            )
        ),
    )

    return normalized


def _coerce_int(value) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def _coerce_float(value) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value) -> Optional[bool]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return value != 0
    if isinstance(value, str):
        candidate = value.strip().lower()
        if not candidate:
            return None
        if candidate in ("true", "t", "yes", "y", "1", "on"):
            return True
        if candidate in ("false", "f", "no", "n", "0", "off"):
            return False
    return None


def _coerce_datetime(value) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        candidate = value.strip()
        return candidate or None
    return str(value)


def _coerce_str(value) -> Optional[str]:
    if value in (None, ""):
        return None
    return str(value).strip()


def _add_if_value(target: dict, key: str, value):
    if value is None:
        return
    if isinstance(value, str) and value.strip() == "":
        return
    target[key] = value
