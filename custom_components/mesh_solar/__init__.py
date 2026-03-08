from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .config_data import merged_config_data, validate_config_data
from .const import (
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    CONF_URL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import MeshSolarCoordinator
from .models import MeshSolarConfigData

_LOGGER = logging.getLogger(__name__)
_LOCAL_DOCS_READY_KEY = f"{DOMAIN}_local_docs_ready"
_LOCAL_DOCS_SOURCE = "local_docs/index.html"
_LOCAL_DOCS_TARGET = ("www", "mesh_solar", "index.html")
_ENTRY_KEYS = (
    CONF_URL,
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
)


def _copy_local_docs_file(source_path: Path, target_path: Path) -> None:
    """Copy the bundled documentation page into Home Assistant's www folder."""
    if not source_path.exists():
        _LOGGER.warning(
            "Local docs source file missing at %s. Skipping docs publish.",
            source_path,
        )
        return

    desired_text = source_path.read_text(encoding="utf-8")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        target_text = target_path.read_text(encoding="utf-8")
        if target_text == desired_text:
            return

    target_path.write_text(desired_text, encoding="utf-8")


async def _ensure_local_docs(hass: HomeAssistant) -> None:
    """Publish the bundled local documentation page."""
    source_path = Path(__file__).resolve().parent / _LOCAL_DOCS_SOURCE
    target_path = Path(hass.config.path(*_LOCAL_DOCS_TARGET))
    try:
        await hass.async_add_executor_job(
            _copy_local_docs_file, source_path, target_path
        )
    except OSError as err:
        _LOGGER.warning("Unable to publish local documentation file: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mesh Solar from a config entry."""
    if not hass.data.get(_LOCAL_DOCS_READY_KEY):
        await _ensure_local_docs(hass)
        hass.data[_LOCAL_DOCS_READY_KEY] = True

    config_data = merged_config_data(entry)
    _sync_entry_data(hass=hass, entry=entry, config_data=config_data)

    validation_errors = validate_config_data(config_data)
    if validation_errors:
        invalid_fields = ", ".join(sorted(validation_errors))
        message = (
            f"Invalid configuration for entry {entry.entry_id}: {invalid_fields}. "
            "Reconfigure the integration."
        )
        _LOGGER.error(message)
        raise ConfigEntryNotReady(message)

    coordinator = MeshSolarCoordinator(
        hass=hass,
        entry=entry,
        url=config_data[CONF_URL],
        api_key=config_data[CONF_API_KEY],
        battery_capacity_sensor=config_data[CONF_BATTERY_CAPACITY_SENSOR],
        environment=config_data[CONF_ENVIRONMENT],
        initial_hash=config_data[CONF_HASH],
        initial_registration=config_data[CONF_REGISTRATION_DATA],
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady as err:
        _LOGGER.warning(
            "Initial refresh failed for entry %s; loading integration anyway so "
            "registration data can still be cleared. Error: %s",
            entry.entry_id,
            err,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Mesh Solar config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    _LOGGER.debug("Mesh Solar unloaded for entry %s", entry.entry_id)
    return unload_ok


def _sync_entry_data(
    *,
    hass: HomeAssistant,
    entry: ConfigEntry,
    config_data: MeshSolarConfigData,
) -> None:
    """Keep normalized values in entry.data and remove duplicate options."""
    updated_data = dict(entry.data)
    needs_entry_update = False

    for key in _ENTRY_KEYS:
        value = config_data[key]
        if updated_data.get(key) != value:
            updated_data[key] = value
            needs_entry_update = True

    if not needs_entry_update and not any(key in entry.options for key in _ENTRY_KEYS):
        return

    updated_options = dict(entry.options)
    for key in _ENTRY_KEYS:
        updated_options.pop(key, None)

    hass.config_entries.async_update_entry(
        entry, data=updated_data, options=updated_options
    )
