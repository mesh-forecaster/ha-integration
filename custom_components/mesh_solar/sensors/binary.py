from homeassistant.components.binary_sensor import BinarySensorEntity

from ..const import DEFAULT_ENVIRONMENT, DOMAIN
from ..entity import MeshSolarEntity
from .helpers import build_unique_id, display_suffix, environment_label, normalized


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    environment = normalized(getattr(coordinator, "environment", DEFAULT_ENVIRONMENT))

    async_add_entities(
        [
            ImportSensor(coordinator, config_entry.entry_id, environment),
            ExportSensor(coordinator, config_entry.entry_id, environment),
        ]
    )


class ImportSensor(MeshSolarEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry_id, environment):
        super().__init__(coordinator)
        self._environment = normalized(environment)
        self._attr_name = f"Mesh Solar Import{display_suffix(self._environment)}"
        self._attr_unique_id = build_unique_id(self._environment, entry_id, "import")

    @property
    def is_on(self):
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("shouldImport", False))

    @property
    def extra_state_attributes(self):
        return {
            "environment": environment_label(self._environment),
        }


class ExportSensor(MeshSolarEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry_id, environment):
        super().__init__(coordinator)
        self._environment = normalized(environment)
        self._attr_name = f"Mesh Solar Export{display_suffix(self._environment)}"
        self._attr_unique_id = build_unique_id(self._environment, entry_id, "export")

    @property
    def is_on(self):
        if not self.coordinator.data:
            return False
        return not bool(self.coordinator.data.get("shouldImport", False))

    @property
    def extra_state_attributes(self):
        return {
            "environment": environment_label(self._environment),
        }
