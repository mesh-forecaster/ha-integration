from homeassistant.util import slugify

from ..const import DOMAIN, DEFAULT_ENVIRONMENT, display_environment, normalize_environment


def normalized(env: str) -> str:
    return normalize_environment(env)


def display_suffix(env: str) -> str:
    env_normalized = normalized(env)
    if env_normalized == DEFAULT_ENVIRONMENT:
        return ""
    return f" ({display_environment(env)})"


def build_unique_id(environment: str, entry_id: str, suffix: str) -> str:
    env_normalized = normalized(environment)
    if env_normalized == DEFAULT_ENVIRONMENT:
        return f"{DOMAIN}_{suffix}"
    env_slug = slugify(env_normalized) or entry_id
    return f"{DOMAIN}_{entry_id}_{env_slug}_{suffix}"


def extract_from_payload(payload: dict | None, keys: tuple[str, ...]):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def environment_label(env: str) -> str:
    return display_environment(normalized(env))
