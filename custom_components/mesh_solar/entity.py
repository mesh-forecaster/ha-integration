from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .models import MeshSolarSnapshot

if TYPE_CHECKING:
    from .coordinator import MeshSolarCoordinator


class MeshSolarEntity(CoordinatorEntity["MeshSolarCoordinator"]):
    """Base class for all Mesh Solar entities."""

    @property
    def available(self) -> bool:
        """Return if the coordinator is available."""
        return self.coordinator.last_update_success

    @property
    def snapshot(self) -> MeshSolarSnapshot | None:
        """Return the current normalized coordinator snapshot."""
        return self.coordinator.data
