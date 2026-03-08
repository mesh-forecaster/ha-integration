from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from ..entity import MeshSolarEntity
from .helpers import build_unique_id, display_suffix, environment_label, normalized


class BatteryManagementSystemStateSensor(MeshSolarEntity, SensorEntity):
    """Expose the active BMS state derived from the current forecast period."""

    _period_duration = timedelta(minutes=30)

    def __init__(self, coordinator, entry_id: str, environment: str) -> None:
        super().__init__(coordinator)
        self._environment = normalized(environment)
        self._attr_name = f"Mesh Solar BMS State{display_suffix(self._environment)}"
        self._attr_unique_id = build_unique_id(
            self._environment, entry_id, "bms_state"
        )

    @property
    def native_value(self) -> StateType:
        forecast_state = self._extract_forecast_state()
        if forecast_state is not None:
            return forecast_state
        period, _ = self._select_relevant_period()
        if not period:
            return None
        value = (
            period.get("battery_management_system_state")
            or period.get("batteryManagementSystemState")
            or period.get("bms_state")
        )
        if value in (None, ""):
            return None
        return str(value).strip()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period, start = self._select_relevant_period()
        attrs: dict[str, Any] = {
            "environment": environment_label(self._environment),
        }
        forecast_state = self._extract_forecast_state()
        if forecast_state not in (None, ""):
            attrs["forecast_state"] = forecast_state
        if not period:
            return attrs

        if start:
            attrs["period_start"] = start.isoformat()
            end = start + self._period_duration
            attrs["period_end"] = end.isoformat()

        for key in (
            "id",
            "period",
            "date",
            "price",
            "should_import",
            "amount",
            "battery",
            "bms_hold_period",
        ):
            value = period.get(key)
            if value not in (None, ""):
                attrs[key] = value

        return attrs

    def _select_relevant_period(self) -> tuple[dict[str, Any] | None, datetime | None]:
        periods = self._extract_periods()
        if not periods:
            return None, None

        now = dt_util.utcnow()
        current: dict[str, Any] | None = None
        current_start: datetime | None = None
        upcoming: dict[str, Any] | None = None
        upcoming_start: datetime | None = None

        for period in periods:
            if not isinstance(period, dict):
                continue
            start_raw = period.get("date")
            start = self._parse_datetime(start_raw)
            if start is None:
                continue
            if start <= now < start + self._period_duration:
                if current_start is None or start > current_start:
                    current = period
                    current_start = start
            elif start > now:
                if upcoming_start is None or start < upcoming_start:
                    upcoming = period
                    upcoming_start = start
            elif start <= now and current_start is None:
                current = period
                current_start = start

        if current:
            return current, current_start
        if upcoming:
            return upcoming, upcoming_start

        return None, None

    def _extract_periods(self) -> list[dict]:
        forecast = getattr(self.coordinator, "forecast", None)
        periods = forecast.get("periods") if isinstance(forecast, dict) else None
        if not isinstance(periods, list) or not periods:
            periods = getattr(self.coordinator, "forecast_periods", None) or []
        return periods

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return dt_util.as_utc(value)
        if isinstance(value, (int, float)):
            return dt_util.utc_from_timestamp(float(value))
        parsed = dt_util.parse_datetime(str(value))
        if parsed is None:
            return None
        return dt_util.as_utc(parsed)

    def _extract_forecast_state(self) -> StateType:
        forecast = getattr(self.coordinator, "forecast", None)
        if not isinstance(forecast, dict):
            return None
        value = forecast.get("battery_management_system_state")
        if value in (None, ""):
            value = forecast.get("BatteryManagementSystemState") or forecast.get(
                "batteryManagementSystemState"
            )
        if value in (None, ""):
            return None
        return str(value).strip()
