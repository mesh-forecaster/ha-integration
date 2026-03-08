# Mesh Solar (Home Assistant Custom Integration)

This integration polls a Mesh Solar forecast endpoint and exposes forecast-driven entities in Home Assistant.

When loaded, the integration publishes a local documentation page to:
- `/local/mesh_solar/index.html`

## What This Integration Does

- Calls your configured API every 60 seconds.
- Sends your current battery capacity, plus cached forecast `hash` and `registration_data`, to reduce payload churn.
- Exposes import/export mode, monetary values, forecast diagnostics, and BMS state as entities.
- Provides a `Clear Registration` button that clears cached registration data and refreshes immediately.

## Configuration Fields

These are available in `Add Integration` and in `Configure` for existing entries.

| Field | Required | Description |
|---|---|---|
| `url` | Yes | Forecast API endpoint URL. |
| `api_key` | Yes | Value sent in `X-API-KEY` request header. |
| `battery_capacity_sensor` | Yes | Entity ID whose state is sent as `currentBatteryCapacity` query value. |
| `environment` | No | `Live` or `Sandbox`. `Live` is stored internally as an empty value. |
| `hash` | No | Deterministic result of the most recent forecast, sent as the `hash` query value. Usually managed automatically. |
| `registration_data` | No | Registration data for your site, sent as `registrationData` so it is not constantly reloaded from the database. It refreshes daily or when you force refresh with the button. |

## Entities Created

### Binary Sensors

- `Mesh Solar Import`
- `Mesh Solar Export`

Behavior:
- `Import` is on when API response contains `shouldImport = true`.
- `Export` is the inverse of `Import`.

### Sensors

- `Mesh Solar Total Cost` (monetary)
- `Mesh Solar Charging Cost` (monetary)
- `Mesh Solar Saving` (monetary)
- `Mesh Solar Forecast Diagnostics` (diagnostic)
- `Mesh Solar BMS State`

Behavior:
- Monetary sensors read values from API payload keys like `TotalCost`, `ChargingCost`, `Saving`.
- Currency is taken from API (`currency`, `Currency`, etc.) when present.
- Forecast Diagnostics state is the number of forecast periods.
- BMS State is derived from top-level forecast state, otherwise current/upcoming period state.

### Button

- `Mesh Solar Clear Registration`

Behavior:
- Clears stored `registration_data` in the config entry.
- Triggers a refresh request.
- Remains available even when the coordinator is unhealthy.

## Client-Side Stored Values

The integration stores values in Home Assistant config entry storage (`.storage/core.config_entries`).

### Persisted (entry data)

| Key | How It Is Used | How It Changes |
|---|---|---|
| `url` | API endpoint used for polling. | Set by user in config/options flow. |
| `api_key` | Sent as `X-API-KEY` header. | Set by user in config/options flow. |
| `battery_capacity_sensor` | Source entity for battery capacity query value. | Set by user in config/options flow. |
| `environment` | Labels entities and keeps environment mode. | Set by user in config/options flow. |
| `hash` | Deterministic result of the most recent forecast, sent as `hash`. | Updated from API response (`hash`/variants). |
| `registration_data` | Site registration data sent as `registrationData` to avoid constant database reloads. | Refreshed daily by upstream behavior, editable in options, and force-refreshable via button. |

### Runtime-only (not persisted)

- Last raw API response (`coordinator.data`)
- Normalized forecast object and periods
- Derived `currency`
- Derived `target_capacity`
- Last update success status

## Request/Response Notes

Each poll includes:
- `currentBatteryCapacity`
- `hash`
- `registrationData`

If API returns updated hash/registration data, the integration persists them automatically.

## Operational Notes

- Update interval: 60 seconds
- Request timeout: 10 seconds
- Initial refresh failures do not block entity creation; entities still load so registration can be cleared.
