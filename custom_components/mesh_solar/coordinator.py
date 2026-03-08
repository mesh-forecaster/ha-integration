import logging
from datetime import timedelta
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    CONF_HASH,
    CONF_REGISTRATION_DATA,
    normalize_environment,
)
from .coordinator_helpers import extract_first, normalize_forecast, normalize_periods

_LOGGER = logging.getLogger(__name__)


class MeshSolarCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        url,
        api_key,
        battery_capacity_sensor,
        environment,
        initial_hash: Optional[str] = None,
        initial_registration: Optional[str] = None,
    ):
        self._hass = hass
        self._entry = entry
        self._url = url
        self._api_key = api_key
        self._battery_capacity_sensor = battery_capacity_sensor
        self._session = async_get_clientsession(hass)
        self._last_hash = (initial_hash or "").strip()
        self._registration_data = (initial_registration or "").strip()
        self.environment = normalize_environment(environment)
        self._currency = ""
        self._forecast_periods = []
        self._forecast: dict = {}
        self._target_capacity: Optional[float] = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def registration_data(self) -> str:
        return self._registration_data


    @property
    def currency(self) -> str:
        return self._currency

    @property
    def forecast_periods(self) -> list[dict]:
        return self._forecast_periods

    @property
    def forecast(self) -> dict:
        return self._forecast

    @property
    def target_capacity(self) -> Optional[float]:
        return self._target_capacity

    async def _async_update_data(self):
        try:
            headers = {"X-API-KEY": f"{self._api_key}"}

            battery_state = self._hass.states.get(self._battery_capacity_sensor)
            battery_capacity = battery_state.state if battery_state else ""

            _LOGGER.info(
                "Got entity value for %s: %s",
                self._battery_capacity_sensor,
                battery_capacity,
            )

            request_url = self._build_request_url(str(battery_capacity or ""))
            _LOGGER.info("URL to be used: %s", request_url)

            async with async_timeout.timeout(10):
                async with self._session.get(
                    request_url, headers=headers
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API returned {response.status}")

                    data = await response.json()
                    _LOGGER.info(repr(data))

                    state_changed = False

                    forecast_info = normalize_forecast(data)

                    returned_hash = extract_first(
                        data,
                        ("hash", "Hash", "forecastHash"),
                    )
                    if returned_hash in (None, ""):
                        returned_hash = forecast_info.get("hash")
                    if returned_hash is not None:
                        returned_hash = str(returned_hash)
                        if returned_hash != self._last_hash:
                            self._last_hash = returned_hash
                            state_changed = True
                            _LOGGER.debug("Stored new forecast hash: %s", returned_hash)

                    returned_registration = extract_first(
                        data,
                        ("registrationData", "RegistrationData", "registration_data"),
                    )
                    if returned_registration in (None, ""):
                        returned_registration = forecast_info.get("registration_data")
                    if returned_registration is not None:
                        returned_registration = str(returned_registration)
                        if returned_registration != self._registration_data:
                            self._registration_data = returned_registration
                            state_changed = True
                            _LOGGER.debug(
                                "Stored new registration data: %s",
                                returned_registration,
                            )
                    currency = extract_first(
                        data,
                        ("currency", "Currency", "currencyCode", "CurrencyCode"),
                    )
                    if currency is not None:
                        currency = str(currency)
                        if currency != self._currency:
                            self._currency = currency

                    target_capacity = extract_first(
                        data,
                        ("TargetCapacity", "targetCapacity", "target_capacity"),
                    )
                    if target_capacity in (None, ""):
                        target_capacity = forecast_info.get("target_capacity")
                    if target_capacity == "":
                        self._target_capacity = None
                    elif target_capacity is not None:
                        new_target: Optional[float]
                        try:
                            new_target = float(target_capacity)
                        except (TypeError, ValueError):
                            new_target = None
                        if new_target is None and isinstance(target_capacity, (int, float)):
                            new_target = float(target_capacity)
                        if new_target is not None:
                            self._target_capacity = new_target


                    if state_changed:
                        self._persist_state()

                    self._forecast = forecast_info or {}
                    periods = forecast_info.get("periods") if forecast_info else None
                    if not periods:
                        periods = normalize_periods(data)
                    self._forecast_periods = periods or []

                    return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {repr(err)}")

    def _build_request_url(self, battery_capacity: str) -> str:
        parsed = urlparse(self._url)
        query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_params["currentBatteryCapacity"] = battery_capacity
        query_params["hash"] = self._last_hash or ""
        query_params["registrationData"] = self._registration_data or ""
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))



    def _persist_state(self) -> None:
        entry_data = dict(self._entry.data)
        updated = False
        if entry_data.get(CONF_HASH, "") != self._last_hash:
            entry_data[CONF_HASH] = self._last_hash
            updated = True
        if entry_data.get(CONF_REGISTRATION_DATA, "") != self._registration_data:
            entry_data[CONF_REGISTRATION_DATA] = self._registration_data
            updated = True
        if updated:
            self._hass.config_entries.async_update_entry(self._entry, data=entry_data)

    async def async_clear_registration_data(self) -> None:
        if self._registration_data:
            _LOGGER.info(
                "Clearing registration data for entry %s", self._entry.entry_id
            )
        else:
            _LOGGER.info(
                "Registration data already empty for entry %s", self._entry.entry_id
            )

        self._registration_data = ""
        self._persist_state()
        try:
            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.warning(
                "Registration data was cleared for entry %s, but refresh failed: %r",
                self._entry.entry_id,
                err,
            )
