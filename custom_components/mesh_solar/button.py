from homeassistant.components.button import ButtonEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    DEFAULT_ENVIRONMENT,
    display_environment,
    normalize_environment,
)
from .entity import MeshSolarEntity


def _normalized(env: str) -> str:
    return normalize_environment(env)


def _display_suffix(env: str) -> str:
    normalized = _normalized(env)
    if normalized == DEFAULT_ENVIRONMENT:
        return ""
    return f" ({display_environment(env)})"


def _build_unique_id(environment: str, entry_id: str) -> str:
    normalized = _normalized(environment)
    if normalized == DEFAULT_ENVIRONMENT:
        return f"{DOMAIN}_clear_registration"
    env_slug = slugify(normalized) or entry_id
    return f"{DOMAIN}_{entry_id}_{env_slug}_clear_registration"


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    environment = _normalized(getattr(coordinator, "environment", DEFAULT_ENVIRONMENT))

    async_add_entities(
        [
            ClearRegistrationButton(coordinator, config_entry.entry_id, environment),
        ]
    )


class ClearRegistrationButton(MeshSolarEntity, ButtonEntity):
    def __init__(self, coordinator, entry_id, environment):
        super().__init__(coordinator)
        self._environment = _normalized(environment)
        self._attr_name = f"Mesh Solar Clear Registration{_display_suffix(self._environment)}"
        self._attr_unique_id = _build_unique_id(self._environment, entry_id)

    async def async_press(self) -> None:
        await self.coordinator.async_clear_registration_data()

    @property
    def available(self) -> bool:
        """Keep this button callable even when coordinator updates are failing."""
        return True

    @property
    def extra_state_attributes(self):
        return {"environment": display_environment(self._environment)}
