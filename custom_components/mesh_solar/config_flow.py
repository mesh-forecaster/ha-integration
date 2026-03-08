from homeassistant import config_entries
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_URL,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_ENVIRONMENT,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    DEFAULT_ENVIRONMENT_LABEL,
    SANDBOX_ENVIRONMENT,
    normalize_environment,
)

def _normalize_input(user_input: dict) -> dict:
    return {
        CONF_URL: str(user_input.get(CONF_URL, "") or "").strip(),
        CONF_API_KEY: str(user_input.get(CONF_API_KEY, "") or "").strip(),
        CONF_BATTERY_CAPACITY_SENSOR: str(
            user_input.get(CONF_BATTERY_CAPACITY_SENSOR, "") or ""
        ).strip(),
        CONF_ENVIRONMENT: normalize_environment(user_input.get(CONF_ENVIRONMENT)),
        CONF_HASH: str(user_input.get(CONF_HASH, "") or ""),
        CONF_REGISTRATION_DATA: str(user_input.get(CONF_REGISTRATION_DATA, "") or ""),
    }


def _environment_for_form(value: str) -> str:
    normalized = normalize_environment(value)
    if normalized:
        return normalized
    return DEFAULT_ENVIRONMENT_LABEL


def _build_config_schema(
    *,
    url: str,
    api_key: str,
    battery_capacity_sensor: str,
    environment: str,
    hash_value: str,
    registration_data: str,
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=url): str,
            vol.Required(CONF_API_KEY, default=api_key): str,
            vol.Required(
                CONF_BATTERY_CAPACITY_SENSOR,
                default=battery_capacity_sensor,
            ): str,
            vol.Optional(
                CONF_ENVIRONMENT,
                default=environment,
            ): vol.In([DEFAULT_ENVIRONMENT_LABEL, SANDBOX_ENVIRONMENT]),
            vol.Optional(CONF_HASH, default=hash_value): str,
            vol.Optional(CONF_REGISTRATION_DATA, default=registration_data): str,
        }
    )


class MeshSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _DEFAULT_URL = "https://meshsolar-production-faf.azurewebsites.net/api/Forecast_Get?code="
    _DEFAULT_CODE = ""
    _DEFAULT_API_KEY = ""
    _DEFAULT_BATTERY_SENSOR = "sensor.battery_capacity"

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Mesh Solar",
                data=_normalize_input(user_input),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_config_schema(
                url=f"{self._DEFAULT_URL}{self._DEFAULT_CODE}",
                api_key=self._DEFAULT_API_KEY,
                battery_capacity_sensor=self._DEFAULT_BATTERY_SENSOR,
                environment=DEFAULT_ENVIRONMENT_LABEL,
                hash_value="",
                registration_data="",
            ),
            errors={},
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return MeshSolarOptionsFlow(config_entry)


class MeshSolarOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            updated_data = dict(self._config_entry.data)
            updated_data.update(_normalize_input(user_input))

            # Remove legacy duplicated values from options so data is authoritative.
            updated_options = dict(self._config_entry.options)
            for key in (
                CONF_URL,
                CONF_API_KEY,
                CONF_BATTERY_CAPACITY_SENSOR,
                CONF_ENVIRONMENT,
                CONF_HASH,
                CONF_REGISTRATION_DATA,
            ):
                updated_options.pop(key, None)

            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data=updated_data,
                options=updated_options,
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_build_config_schema(
                url=str(
                    (
                        self._config_entry.data.get(
                            CONF_URL,
                            self._config_entry.options.get(
                                CONF_URL,
                                (
                                    f"{MeshSolarConfigFlow._DEFAULT_URL}"
                                    f"{MeshSolarConfigFlow._DEFAULT_CODE}"
                                ),
                            ),
                        )
                    )
                    or (
                        f"{MeshSolarConfigFlow._DEFAULT_URL}"
                        f"{MeshSolarConfigFlow._DEFAULT_CODE}"
                    )
                ),
                api_key=str(
                    (
                        self._config_entry.data.get(
                            CONF_API_KEY,
                            self._config_entry.options.get(
                                CONF_API_KEY, MeshSolarConfigFlow._DEFAULT_API_KEY
                            ),
                        )
                    )
                    or MeshSolarConfigFlow._DEFAULT_API_KEY
                ),
                battery_capacity_sensor=str(
                    (
                        self._config_entry.data.get(
                            CONF_BATTERY_CAPACITY_SENSOR,
                            self._config_entry.options.get(
                                CONF_BATTERY_CAPACITY_SENSOR,
                                MeshSolarConfigFlow._DEFAULT_BATTERY_SENSOR,
                            ),
                        )
                    )
                    or MeshSolarConfigFlow._DEFAULT_BATTERY_SENSOR
                ),
                environment=_environment_for_form(
                    self._config_entry.data.get(
                        CONF_ENVIRONMENT,
                        self._config_entry.options.get(
                            CONF_ENVIRONMENT,
                            DEFAULT_ENVIRONMENT_LABEL,
                        ),
                    )
                ),
                hash_value=str(
                    self._config_entry.data.get(
                        CONF_HASH,
                        self._config_entry.options.get(CONF_HASH, ""),
                    )
                    or ""
                ),
                registration_data=str(
                    self._config_entry.data.get(
                        CONF_REGISTRATION_DATA,
                        self._config_entry.options.get(CONF_REGISTRATION_DATA, ""),
                    )
                    or ""
                ),
            ),
            errors={},
        )
