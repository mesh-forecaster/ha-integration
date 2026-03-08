from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass

from ..entity import MeshSolarEntity
from .helpers import build_unique_id, display_suffix, environment_label, normalized


class MonetarySensor(MeshSolarEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry_id, environment, name_suffix: str, unique_suffix: str, keys: tuple[str, ...]):
        super().__init__(coordinator)
        self._environment = normalized(environment)
        self._keys = keys
        self._attr_name = f"Mesh Solar {name_suffix}{display_suffix(self._environment)}"
        self._attr_unique_id = build_unique_id(self._environment, entry_id, unique_suffix)

    def _extract_value(self):
        if not self.coordinator.data:
            return None
        for key in self._keys:
            if key in self.coordinator.data:
                return self.coordinator.data.get(key)
        return None

    @property
    def native_value(self):
        value = self._extract_value()
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            try:
                return float(str(value).strip())
            except (TypeError, ValueError):
                return None

    @property
    def native_unit_of_measurement(self):
        currency = getattr(self.coordinator, "currency", None)
        if currency:
            return currency
        return None

    @property
    def extra_state_attributes(self):
        attrs = {
            "environment": environment_label(self._environment),
        }
        currency = getattr(self.coordinator, "currency", None)
        if currency:
            attrs["currency"] = currency
        return attrs
