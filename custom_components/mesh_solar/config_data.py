from __future__ import annotations

from typing import Final, Mapping
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    CONF_API_KEY,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    CONF_URL,
    DEFAULT_API_KEY,
    DEFAULT_BATTERY_CAPACITY_SENSOR,
    DEFAULT_ENVIRONMENT_LABEL,
    DEFAULT_FORECAST_URL,
    SANDBOX_ENVIRONMENT,
    normalize_environment,
)
from .models import MeshSolarConfigData

_MISSING: Final = object()


def default_config_data() -> MeshSolarConfigData:
    """Return default form values."""
    return MeshSolarConfigData(
        url=DEFAULT_FORECAST_URL,
        api_key=DEFAULT_API_KEY,
        battery_capacity_sensor=DEFAULT_BATTERY_CAPACITY_SENSOR,
        environment=DEFAULT_ENVIRONMENT_LABEL,
        hash="",
        registration_data="",
    )


def normalize_config_input(user_input: Mapping[str, object]) -> MeshSolarConfigData:
    """Normalize config flow input into stored entry data."""
    return MeshSolarConfigData(
        url=_strip_text(user_input.get(CONF_URL)),
        api_key=_strip_text(user_input.get(CONF_API_KEY)),
        battery_capacity_sensor=_strip_text(
            user_input.get(CONF_BATTERY_CAPACITY_SENSOR)
        ),
        environment=normalize_environment(_string_value(user_input.get(CONF_ENVIRONMENT))),
        hash=_string_value(user_input.get(CONF_HASH)),
        registration_data=_string_value(user_input.get(CONF_REGISTRATION_DATA)),
    )


def merged_config_data(entry: ConfigEntry) -> MeshSolarConfigData:
    """Merge config entry data and options into one normalized structure."""
    defaults = default_config_data()
    return normalize_config_input(
        {
            CONF_URL: _entry_value(entry, CONF_URL, defaults[CONF_URL]),
            CONF_API_KEY: _entry_value(entry, CONF_API_KEY, defaults[CONF_API_KEY]),
            CONF_BATTERY_CAPACITY_SENSOR: _entry_value(
                entry,
                CONF_BATTERY_CAPACITY_SENSOR,
                defaults[CONF_BATTERY_CAPACITY_SENSOR],
            ),
            CONF_ENVIRONMENT: _entry_value(
                entry, CONF_ENVIRONMENT, defaults[CONF_ENVIRONMENT]
            ),
            CONF_HASH: _entry_value(entry, CONF_HASH, ""),
            CONF_REGISTRATION_DATA: _entry_value(entry, CONF_REGISTRATION_DATA, ""),
        }
    )


def validate_config_data(config_data: MeshSolarConfigData) -> dict[str, str]:
    """Validate normalized config values and return field errors."""
    errors: dict[str, str] = {}

    if not config_data[CONF_URL]:
        errors[CONF_URL] = "required"
    elif not _is_valid_http_url(config_data[CONF_URL]):
        errors[CONF_URL] = "invalid_url"

    if not config_data[CONF_API_KEY]:
        errors[CONF_API_KEY] = "required"

    battery_sensor = config_data[CONF_BATTERY_CAPACITY_SENSOR]
    if not battery_sensor:
        errors[CONF_BATTERY_CAPACITY_SENSOR] = "required"
    else:
        try:
            cv.entity_id(battery_sensor)
        except vol.Invalid:
            errors[CONF_BATTERY_CAPACITY_SENSOR] = "invalid_entity_id"

    return errors


def build_config_schema(*, config_data: MeshSolarConfigData) -> vol.Schema:
    """Build the config flow schema."""
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=config_data[CONF_URL]): str,
            vol.Required(CONF_API_KEY, default=config_data[CONF_API_KEY]): str,
            vol.Required(
                CONF_BATTERY_CAPACITY_SENSOR,
                default=config_data[CONF_BATTERY_CAPACITY_SENSOR],
            ): str,
            vol.Optional(
                CONF_ENVIRONMENT,
                default=_environment_for_form(config_data[CONF_ENVIRONMENT]),
            ): vol.In([DEFAULT_ENVIRONMENT_LABEL, SANDBOX_ENVIRONMENT]),
            vol.Optional(CONF_HASH, default=config_data[CONF_HASH]): str,
            vol.Optional(
                CONF_REGISTRATION_DATA,
                default=config_data[CONF_REGISTRATION_DATA],
            ): str,
        }
    )


def _entry_value(entry: ConfigEntry, key: str, default: object) -> object:
    value = entry.data.get(key, _MISSING)
    if value is not _MISSING:
        return value

    value = entry.options.get(key, _MISSING)
    if value is not _MISSING:
        return value

    return default


def _environment_for_form(value: str) -> str:
    normalized = normalize_environment(value)
    if normalized:
        return normalized
    return DEFAULT_ENVIRONMENT_LABEL


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _strip_text(value: object) -> str:
    return _string_value(value).strip()


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)
