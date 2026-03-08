from ..const import DEFAULT_ENVIRONMENT, DOMAIN
from .helpers import normalized
from .monetary import MonetarySensor
from .diagnostic import ForecastDetailSensor
from .bms_state import BatteryManagementSystemStateSensor


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    environment = normalized(getattr(coordinator, "environment", DEFAULT_ENVIRONMENT))

    async_add_entities(
        [
            MonetarySensor(
                coordinator,
                config_entry.entry_id,
                environment,
                name_suffix="Total Cost",
                unique_suffix="total_cost",
                keys=("TotalCost", "totalCost", "total_cost"),
            ),
            MonetarySensor(
                coordinator,
                config_entry.entry_id,
                environment,
                name_suffix="Charging Cost",
                unique_suffix="charging_cost",
                keys=("ChargingCost", "chargingCost", "charging_cost"),
            ),
            MonetarySensor(
                coordinator,
                config_entry.entry_id,
                environment,
                name_suffix="Saving",
                unique_suffix="saving",
                keys=("Saving", "saving", "savings"),
            ),
            ForecastDetailSensor(
                coordinator,
                config_entry.entry_id,
                environment,
            ),
            BatteryManagementSystemStateSensor(
                coordinator,
                config_entry.entry_id,
                environment,
            ),
        ]
    )
