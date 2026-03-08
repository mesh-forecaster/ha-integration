"""Tests for constant helpers."""

import pytest

from custom_components.mesh_solar.const import (
    DEFAULT_ENVIRONMENT,
    DEFAULT_ENVIRONMENT_LABEL,
    SANDBOX_ENVIRONMENT,
    display_environment,
    normalize_environment,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (None, DEFAULT_ENVIRONMENT),
        ("", DEFAULT_ENVIRONMENT),
        ("Live", DEFAULT_ENVIRONMENT),
        ("live", DEFAULT_ENVIRONMENT),
        (SANDBOX_ENVIRONMENT, SANDBOX_ENVIRONMENT),
        ("sandbox", SANDBOX_ENVIRONMENT),
        (" Pilot ", "Pilot"),
    ],
)
def test_normalize_environment(raw_value: str | None, expected: str) -> None:
    """Environment values are normalized to stable storage values."""
    assert normalize_environment(raw_value) == expected


def test_display_environment_uses_live_label() -> None:
    """Empty storage values are presented as Live in the UI."""
    assert display_environment(DEFAULT_ENVIRONMENT) == DEFAULT_ENVIRONMENT_LABEL
    assert display_environment("Live") == DEFAULT_ENVIRONMENT_LABEL
