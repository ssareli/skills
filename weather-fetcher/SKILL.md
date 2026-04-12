---
name: weather-fetcher
description: Fetch weather data and severe weather alerts for any location using city names, postal codes, or GPS coordinates. Returns current conditions, hourly forecasts, daily forecasts, weather emoticons, and NWS severe weather alerts (US only). Use when users request weather information, need to check for weather warnings/watches/advisories, or building weather features.
---

# Weather Fetcher

Fetch comprehensive weather data and severe weather alerts by calling `scripts/get_weather.py`.

## Location Input

The script uses the [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api) to convert location names to GPS coordinates.

**Supported location formats:**
- City names: `"Austin"`, `"New York"`, `"London"`
- City with state/region: `"Austin, TX"`, `"New York, NY"`
- City with country code: `"London, GB"`, `"Paris, FR"`
- Postal codes: `"78701"`, `"10001"`
- GPS coordinates: `"40.7128,-74.0060"`

**NOT supported:**
- Full street addresses (e.g., `"123 Main Street, Austin, TX"`)
- Landmarks or building names (e.g., `"Empire State Building"`)

The geocoding API performs a name-based search, so street-level addresses will either fail or return unexpected results.

## Usage

```bash
python scripts/get_weather.py "New York, NY"
python scripts/get_weather.py "40.7128,-74.0060"
python scripts/get_weather.py "London, GB" --units celsius
python scripts/get_weather.py "Paris" --no-emoji
python scripts/get_weather.py "Austin, TX" --alerts-only
python scripts/get_weather.py "Miami, FL" --no-alerts
python scripts/get_weather.py "78701"
```

## Output Format

```json
{
  "location": {"name": "Austin", "lat": 30.27, "lon": -97.74, "country_code": "US"},
  "temp": 75,
  "feels_like": 78,
  "humidity": 65,
  "wind_speed": 8.5,
  "precipitation": 0,
  "description": "Partly cloudy",
  "emoji": "⛅",
  "hourly": {...},
  "daily": {...},
  "alerts": [
    {
      "event": "Severe Thunderstorm Warning",
      "headline": "Severe Thunderstorm Warning issued...",
      "severity": "Severe",
      "certainty": "Observed",
      "urgency": "Immediate",
      "description": "...",
      "instruction": "...",
      "effective": "2025-01-14T15:00:00-06:00",
      "expires": "2025-01-14T18:00:00-06:00",
      "emoji": "⚠️"
    }
  ],
  "alerts_count": 1,
  "has_alerts": true,
  "alerts_summary": {
    "most_severe_event": "Severe Thunderstorm Warning",
    "most_severe_severity": "Severe",
    "most_severe_headline": "..."
  }
}
```

## Parsing Results

### Weather Data
- `temp` - Current temperature
- `feels_like` - Apparent temperature
- `description` - Weather condition text
- `emoji` - Weather emoticon (if included)
- `hourly.time[i]` / `hourly.temperature_2m[i]` - Hourly forecast
- `daily.time[i]` / `daily.temperature_2m_max[i]` - Daily forecast

### Alerts Data (US Only)
- `has_alerts` - Boolean: true if any active alerts
- `alerts_count` - Number of active alerts
- `alerts[i].event` - Alert type (e.g., "Tornado Warning", "Winter Storm Watch")
- `alerts[i].severity` - Extreme, Severe, Moderate, Minor, Unknown
- `alerts[i].urgency` - Immediate, Expected, Future, Unknown
- `alerts[i].certainty` - Observed, Likely, Possible, Unlikely, Unknown
- `alerts[i].headline` - Short summary
- `alerts[i].description` - Full alert text
- `alerts[i].instruction` - Recommended actions
- `alerts[i].effective` / `alerts[i].expires` - Alert validity period
- `alerts[i].emoji` - Severity indicator (🚨⚠️🔶🔷ℹ️)
- `alerts_summary` - Quick access to most severe alert info

## Options

- `--units celsius` - Use Celsius instead of Fahrenheit
- `--no-emoji` - Exclude emoji from output
- `--no-alerts` - Skip fetching weather alerts
- `--alerts-only` - Fetch only alerts (no forecast data)

## Alert Types

Common NWS alert events include:
- **Warnings** (🚨⚠️): Tornado, Severe Thunderstorm, Flash Flood, Hurricane, Blizzard
- **Watches** (🔶): Tornado Watch, Severe Thunderstorm Watch, Winter Storm Watch
- **Advisories** (🔷): Wind Advisory, Heat Advisory, Dense Fog Advisory, Freeze Advisory
- **Statements** (ℹ️): Special Weather Statement, Hazardous Weather Outlook

## Limitations

- **Location input**: Only city names, postal codes, and GPS coordinates are supported. Full street addresses are NOT supported.
- **Alerts are US-only**: NWS API covers US territories only. Non-US locations return empty alerts array.
- **Network errors**: Alert fetch failures don't break weather requests - alerts will be empty.

## Error Handling

Errors output JSON to stderr with exit code 1:
```json
{"error": "Location not found: XYZ"}
```

## Weather Codes

The script maps WMO codes to descriptions and emoji:
- 0: Clear (☀️/🌙)
- 1-3: Cloudy (🌤️/⛅/☁️)
- 45-48: Fog (🌫️)
- 51-67: Rain (🌦️/🌧️)
- 71-77: Snow (🌨️/❄️)
- 80-82: Showers (🌦️/🌧️)
- 95-99: Thunderstorm (⛈️)