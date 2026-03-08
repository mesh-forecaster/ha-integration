import logging
from pathlib import Path
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_URL,
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    DEFAULT_ENVIRONMENT,
    normalize_environment,
)
from .coordinator import MeshSolarCoordinator

_LOGGER = logging.getLogger(__name__)
_LOCAL_DOCS_READY_KEY = f"{DOMAIN}_local_docs_ready"
_LOCAL_DOCS_SOURCE = "local_docs/index.html"
_LOCAL_DOCS_TARGET = ("www", "mesh_solar", "index.html")


def _copy_local_docs_file(source_path: Path, target_path: Path) -> None:
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
    source_path = Path(__file__).resolve().parent / _LOCAL_DOCS_SOURCE
    target_path = Path(hass.config.path(*_LOCAL_DOCS_TARGET))
    try:
        await hass.async_add_executor_job(_copy_local_docs_file, source_path, target_path)
    except Exception as err:
        _LOGGER.warning("Unable to publish local documentation file: %r", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    if not hass.data.get(_LOCAL_DOCS_READY_KEY):
        await _ensure_local_docs(hass)
        hass.data[_LOCAL_DOCS_READY_KEY] = True

    url = entry.data.get(CONF_URL) or entry.options.get(CONF_URL)
    api_key = entry.data.get(CONF_API_KEY) or entry.options.get(CONF_API_KEY)
    battery_capacity_sensor = (
        entry.data.get(CONF_BATTERY_CAPACITY_SENSOR)
        or entry.options.get(CONF_BATTERY_CAPACITY_SENSOR)
    )
    environment_raw = (
        entry.data.get(CONF_ENVIRONMENT)
        or entry.options.get(CONF_ENVIRONMENT)
        or DEFAULT_ENVIRONMENT
    )
    environment = normalize_environment(environment_raw)

    stored_hash = entry.data.get(CONF_HASH, "") or ""
    registration_data = entry.data.get(CONF_REGISTRATION_DATA, "") or ""

    needs_entry_update = False
    updated_data = dict(entry.data)

    if updated_data.get(CONF_URL, "") != (url or ""):
        updated_data[CONF_URL] = url or ""
        needs_entry_update = True

    if updated_data.get(CONF_API_KEY, "") != (api_key or ""):
        updated_data[CONF_API_KEY] = api_key or ""
        needs_entry_update = True

    if updated_data.get(CONF_BATTERY_CAPACITY_SENSOR, "") != (battery_capacity_sensor or ""):
        updated_data[CONF_BATTERY_CAPACITY_SENSOR] = battery_capacity_sensor or ""
        needs_entry_update = True

    if updated_data.get(CONF_HASH, "") != stored_hash:
        updated_data[CONF_HASH] = stored_hash
        needs_entry_update = True

    if updated_data.get(CONF_REGISTRATION_DATA, "") != registration_data:
        updated_data[CONF_REGISTRATION_DATA] = registration_data
        needs_entry_update = True

    if updated_data.get(CONF_ENVIRONMENT) != environment:
        updated_data[CONF_ENVIRONMENT] = environment
        needs_entry_update = True

    if needs_entry_update:
        updated_options = dict(entry.options)
        for key in (
            CONF_URL,
            CONF_API_KEY,
            CONF_BATTERY_CAPACITY_SENSOR,
            CONF_ENVIRONMENT,
            CONF_HASH,
            CONF_REGISTRATION_DATA,
        ):
            updated_options.pop(key, None)
        hass.config_entries.async_update_entry(
            entry, data=updated_data, options=updated_options
        )

    if not url or not api_key or not battery_capacity_sensor:
        message = (
            "Missing required config for entry "
            f"{entry.entry_id} (url={bool(url)}, api_key={bool(api_key)}, "
            f"battery_capacity_sensor={bool(battery_capacity_sensor)}). "
            "Reconfigure the integration."
        )
        _LOGGER.error(message)
        raise ConfigEntryNotReady(message)

    coordinator = MeshSolarCoordinator(
        hass,
        entry,
        url,
        api_key,
        battery_capacity_sensor,
        environment,
        initial_hash=stored_hash,
        initial_registration=registration_data,
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

    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor", "button"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["binary_sensor", "sensor", "button"]
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.debug("Mesh Solar unloaded for entry %s", entry.entry_id)
    return unload_ok



