from typing import Optional

DOMAIN = "mesh_solar"

CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_BATTERY_CAPACITY_SENSOR = "battery_capacity_sensor"
CONF_ENVIRONMENT = "environment"
CONF_HASH = "hash"
CONF_REGISTRATION_DATA = "registration_data"
DEFAULT_ENVIRONMENT = ""
DEFAULT_ENVIRONMENT_LABEL = "Live"
SANDBOX_ENVIRONMENT = "Sandbox"
LEGACY_LIVE_ENVIRONMENT = "Live"
UPDATE_INTERVAL = 60  # seconds


def normalize_environment(value: Optional[str]) -> str:
    """Normalize environment strings to canonical values."""
    if value is None:
        return DEFAULT_ENVIRONMENT

    candidate = value.strip()
    if not candidate:
        return DEFAULT_ENVIRONMENT

    lowered = candidate.lower()

    if lowered == LEGACY_LIVE_ENVIRONMENT.lower():
        return DEFAULT_ENVIRONMENT

    if lowered == SANDBOX_ENVIRONMENT.lower():
        return SANDBOX_ENVIRONMENT

    return candidate


def display_environment(value: Optional[str]) -> str:
    """Return a user-friendly environment label."""
    normalized = normalize_environment(value)
    if normalized == DEFAULT_ENVIRONMENT:
        return DEFAULT_ENVIRONMENT_LABEL
    return normalized
