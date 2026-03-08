from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from ..entity import MeshSolarEntity
from .helpers import (
    build_unique_id,
    display_suffix,
    environment_label,
    extract_from_payload,
    normalized,
)


class ForecastDetailSensor(MeshSolarEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id, environment):
        super().__init__(coordinator)
        self._environment = normalized(environment)
        self._attr_name = f"Mesh Solar Forecast Diagnostics{display_suffix(self._environment)}"
        self._attr_unique_id = build_unique_id(self._environment, entry_id, "forecast_diagnostics")

    @property
    def native_value(self):
        forecast = getattr(self.coordinator, "forecast", None) or {}
        periods = forecast.get("periods") if isinstance(forecast, dict) else None
        if not isinstance(periods, list) or not periods:
            periods = getattr(self.coordinator, "forecast_periods", None) or []
        if not periods:
            return None
        return len(periods)

    @property
    def extra_state_attributes(self):
        forecast = getattr(self.coordinator, "forecast", None) or {}
        periods = forecast.get("periods") if isinstance(forecast, dict) else None
        if not isinstance(periods, list) or not periods:
            periods = getattr(self.coordinator, "forecast_periods", None) or []
        periods_payload = [dict(period) for period in periods]
        attrs = {
            "environment": environment_label(self._environment),
            "period_count": len(periods_payload),
        }
        if isinstance(forecast, dict) and forecast:
            forecast_detail = {
                key: value
                for key, value in forecast.items()
                if key != "periods"
            }
            if periods_payload:
                forecast_detail["periods"] = periods_payload
            if forecast_detail:
                attrs["forecast"] = forecast_detail
        data = self.coordinator.data or {}
        forecast_date = (
            (forecast.get("date") if isinstance(forecast, dict) else None)
            or extract_from_payload(
                data,
                ("Date", "date", "forecastDate", "forecast_date"),
            )
        )
        if forecast_date not in (None, ""):
            attrs["forecast_date"] = str(forecast_date).strip()
        forecast_hash = getattr(self.coordinator, "last_hash", None)
        if forecast_hash:
            attrs["forecast_hash"] = forecast_hash
        currency = getattr(self.coordinator, "currency", None)
        if currency:
            attrs["currency"] = currency
        target_capacity = (
            (forecast.get("target_capacity") if isinstance(forecast, dict) else None)
            if forecast
            else None
        )
        if target_capacity in (None, ""):
            target_capacity = getattr(self.coordinator, "target_capacity", None)
        if target_capacity not in (None, ""):
            attrs["target_capacity"] = target_capacity
        return attrs
