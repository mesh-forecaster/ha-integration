from homeassistant.helpers.update_coordinator import CoordinatorEntity


class MeshSolarEntity(CoordinatorEntity):
    """Base class for all Mesh Solar entities."""

    @property
    def available(self) -> bool:
        """Return if the coordinator is available."""
        return self.coordinator.last_update_success
