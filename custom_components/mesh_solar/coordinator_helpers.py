from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal

from .models import ForecastData, ForecastPeriod, MeshSolarSnapshot


def extract_first(payload: Mapping[str, object], keys: Iterable[str]) -> object | None:
    """Return the first matching value from a payload."""
    for key in keys:
        if key in payload:
            value = payload[key]
            if value is None:
                return ""
            return value
    return None


def normalize_periods(payload: Mapping[str, object] | None) -> list[ForecastPeriod]:
    """Normalize forecast periods into the integration's stable shape."""
    if not isinstance(payload, Mapping):
        return []

    raw_periods: object | None = None
    for key in ("Periods", "periods", "forecastPeriods", "ForecastPeriods"):
        if key in payload:
            raw_periods = payload.get(key)
            break

    if raw_periods is None:
        forecast_container = _extract_forecast_source(payload)
        if forecast_container is not payload:
            for key in ("Periods", "periods", "forecastPeriods", "ForecastPeriods"):
                if key in forecast_container:
                    raw_periods = forecast_container.get(key)
                    break

    if not isinstance(raw_periods, list):
        return []

    normalized_periods: list[ForecastPeriod] = []
    for item in raw_periods:
        if not isinstance(item, Mapping):
            continue

        period: ForecastPeriod = {}
        _add_if_value(period, "id", _coerce_str(extract_first(item, ("Id", "id"))))
        _add_if_value(
            period,
            "period",
            _coerce_int(extract_first(item, ("Period", "period", "index"))),
        )
        _add_if_value(
            period,
            "date",
            _coerce_datetime(extract_first(item, ("Date", "date", "start"))),
        )
        _add_if_value(
            period,
            "price",
            _coerce_float(extract_first(item, ("Price", "price"))),
        )
        _add_if_value(
            period,
            "should_import",
            _coerce_bool(
                extract_first(item, ("ShouldImport", "shouldImport", "should_import"))
            ),
        )
        _add_if_value(
            period,
            "amount",
            _coerce_float(extract_first(item, ("Amount", "amount"))),
        )
        _add_if_value(
            period,
            "battery",
            _coerce_float(extract_first(item, ("Battery", "battery"))),
        )
        _add_if_value(
            period,
            "bms_hold_period",
            _coerce_bool(
                extract_first(
                    item,
                    (
                        "BmsHoldPeriod",
                        "bmsHoldPeriod",
                        "bms_hold_period",
                        "bmsholdperiod",
                    ),
                )
            ),
        )
        _add_if_value(
            period,
            "battery_management_system_state",
            _coerce_str(
                extract_first(
                    item,
                    (
                        "BatteryManagementSystemState",
                        "batteryManagementSystemState",
                        "battery_management_system_state",
                    ),
                )
            ),
        )
        if period:
            normalized_periods.append(period)

    return normalized_periods


def normalize_forecast(payload: Mapping[str, object] | None) -> ForecastData:
    """Normalize a forecast payload into the integration's stable shape."""
    if not isinstance(payload, Mapping):
        return {}

    forecast_source = _extract_forecast_source(payload)
    normalized: ForecastData = {}

    _add_if_value(
        normalized,
        "id",
        _coerce_str(extract_first(forecast_source, ("Id", "id"))),
    )
    _add_if_value(
        normalized,
        "registration_id",
        _coerce_str(
            extract_first(
                forecast_source,
                ("RegistrationId", "registrationId", "registration_id"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "date",
        _coerce_datetime(
            extract_first(
                forecast_source,
                ("Date", "date", "forecastDate", "forecast_date"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "hash",
        _coerce_str(
            extract_first(
                forecast_source,
                ("Hash", "hash", "forecastHash", "forecast_hash"),
            )
        ),
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
                ("CurrentCapacity", "currentCapacity", "current_capacity"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "min_capacity",
        _coerce_float(
            extract_first(
                forecast_source,
                ("MinCapacity", "minCapacity", "min_capacity"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "target_capacity",
        _coerce_float(
            extract_first(
                forecast_source,
                ("TargetCapacity", "targetCapacity", "target_capacity"),
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
                ("ShouldImport", "shouldImport", "should_import"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "cloud_update_enabled",
        _coerce_bool(
            extract_first(
                forecast_source,
                ("CloudUpdateEnabled", "cloudUpdateEnabled", "cloud_update_enabled"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "registration_data",
        _coerce_str(
            extract_first(
                forecast_source,
                ("RegistrationData", "registrationData", "registration_data"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "total_cost",
        _coerce_float(
            extract_first(
                forecast_source,
                ("TotalCost", "totalCost", "total_cost"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "charging_cost",
        _coerce_float(
            extract_first(
                forecast_source,
                ("ChargingCost", "chargingCost", "charging_cost"),
            )
        ),
    )
    _add_if_value(
        normalized,
        "saving",
        _coerce_float(
            extract_first(forecast_source, ("Saving", "saving", "savings"))
        ),
    )

    return normalized


def build_snapshot(payload: Mapping[str, object] | None) -> MeshSolarSnapshot:
    """Build the coordinator snapshot from a raw API payload."""
    if not isinstance(payload, Mapping):
        return MeshSolarSnapshot()

    forecast = dict(normalize_forecast(payload))
    periods = forecast.get("periods") or normalize_periods(payload)
    if periods:
        forecast["periods"] = periods

    forecast_hash = _coerce_str(
        extract_first(payload, ("Hash", "hash", "forecastHash", "forecast_hash"))
    ) or forecast.get("hash")
    registration_data = _coerce_str(
        extract_first(
            payload,
            ("RegistrationData", "registrationData", "registration_data"),
        )
    ) or forecast.get("registration_data")
    should_import = _coerce_bool(
        extract_first(payload, ("ShouldImport", "shouldImport", "should_import"))
    )
    if should_import is None:
        should_import = forecast.get("should_import")
    total_cost = _coerce_float(
        extract_first(payload, ("TotalCost", "totalCost", "total_cost"))
    )
    if total_cost is None:
        total_cost = forecast.get("total_cost")
    charging_cost = _coerce_float(
        extract_first(payload, ("ChargingCost", "chargingCost", "charging_cost"))
    )
    if charging_cost is None:
        charging_cost = forecast.get("charging_cost")
    saving = _coerce_float(
        extract_first(payload, ("Saving", "saving", "savings"))
    )
    if saving is None:
        saving = forecast.get("saving")
    target_capacity = _coerce_float(
        extract_first(payload, ("TargetCapacity", "targetCapacity", "target_capacity"))
    )
    if target_capacity is None:
        target_capacity = forecast.get("target_capacity")
    currency = _coerce_str(
        extract_first(payload, ("currency", "Currency", "currencyCode", "CurrencyCode"))
    )

    _add_if_value(forecast, "hash", forecast_hash)
    _add_if_value(forecast, "registration_data", registration_data)
    _add_if_value(forecast, "should_import", should_import)
    _add_if_value(forecast, "total_cost", total_cost)
    _add_if_value(forecast, "charging_cost", charging_cost)
    _add_if_value(forecast, "saving", saving)
    _add_if_value(forecast, "target_capacity", target_capacity)

    return MeshSolarSnapshot(
        forecast=forecast,
        forecast_periods=periods,
        currency=currency,
        target_capacity=target_capacity,
        should_import=should_import,
        total_cost=total_cost,
        charging_cost=charging_cost,
        saving=saving,
        forecast_hash=forecast_hash,
        registration_data=registration_data,
    )


def _extract_forecast_source(payload: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("Forecast", "forecast", "forecastEntity"):
        candidate = payload.get(key)
        if isinstance(candidate, Mapping):
            return candidate
    return payload


def _coerce_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def _coerce_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: object) -> bool | None:
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


def _coerce_datetime(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        candidate = value.strip()
        return candidate or None
    return str(value)


def _coerce_str(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip()


def _add_if_value(target: dict[str, object], key: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, str) and value.strip() == "":
        return
    target[key] = value
