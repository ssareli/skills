#!/usr/bin/env python3
"""Weather data fetcher using Open-Meteo API with NWS severe weather alerts.

Location Input:
    Uses the Open-Meteo Geocoding API (https://open-meteo.com/en/docs/geocoding-api)
    to convert location names to GPS coordinates.
    
    Supported formats:
        - City names: "Austin", "New York", "London"
        - City with state/region: "Austin, TX", "New York, NY"
        - City with country code: "London, GB", "Paris, FR"
        - Postal codes: "78701", "10001"
        - GPS coordinates: "40.7128,-74.0060"
    
    NOT supported:
        - Full street addresses (e.g., "123 Main Street, Austin, TX")
        - Landmarks or building names

Usage:
    python get_weather.py "New York, NY"
    python get_weather.py "40.7128,-74.0060"
    python get_weather.py "London, GB" --units celsius
    python get_weather.py "Paris" --no-emoji
    python get_weather.py "Austin, TX" --alerts-only
    python get_weather.py "78701"
    python get_weather.py "Austin, TX" --verbose
"""

import sys
import json
import argparse
import requests
from typing import Dict, Tuple, Optional, List


def geocode(address: str) -> Dict:
    """Convert city name, postal code, or region to coordinates using Open-Meteo Geocoding API.
    
    Note: This API performs name-based search. Full street addresses are NOT supported
    and will either fail or return unexpected results.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": address, "count": 1, "language": "en", "format": "json"}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data.get("results"):
        raise ValueError(f"Location not found: {address}")
    
    location = data["results"][0]
    return {
        "lat": location["latitude"],
        "lon": location["longitude"],
        "name": location["name"],
        "country": location.get("country", ""),
        "admin1": location.get("admin1", ""),
        "country_code": location.get("country_code", "")
    }


def get_weather_emoji(weather_code: int, is_night: bool = False) -> Tuple[str, str]:
    """Get weather description and emoji for WMO weather code."""
    weather_map = {
        0: ("Clear sky", "☀️", "🌙"),
        1: ("Mainly clear", "🌤️", "🌙"),
        2: ("Partly cloudy", "⛅", "☁️"),
        3: ("Overcast", "☁️", "☁️"),
        45: ("Foggy", "🌫️", "🌫️"),
        48: ("Foggy", "🌫️", "🌫️"),
        51: ("Light drizzle", "🌦️", "🌧️"),
        53: ("Moderate drizzle", "🌦️", "🌧️"),
        55: ("Dense drizzle", "🌧️", "🌧️"),
        56: ("Freezing drizzle", "🌧️", "🌧️"),
        57: ("Freezing drizzle", "🌧️", "🌧️"),
        61: ("Slight rain", "🌦️", "🌧️"),
        63: ("Moderate rain", "🌧️", "🌧️"),
        65: ("Heavy rain", "🌧️", "🌧️"),
        66: ("Freezing rain", "🌧️", "🌧️"),
        67: ("Freezing rain", "🌧️", "🌧️"),
        71: ("Slight snow", "🌨️", "🌨️"),
        73: ("Moderate snow", "❄️", "❄️"),
        75: ("Heavy snow", "❄️", "❄️"),
        77: ("Snow grains", "❄️", "❄️"),
        80: ("Slight showers", "🌦️", "🌧️"),
        81: ("Moderate showers", "🌧️", "🌧️"),
        82: ("Violent showers", "⛈️", "⛈️"),
        85: ("Slight snow showers", "🌨️", "🌨️"),
        86: ("Heavy snow showers", "❄️", "❄️"),
        95: ("Thunderstorm", "⛈️", "⛈️"),
        96: ("Thunderstorm with hail", "⛈️", "⛈️"),
        99: ("Thunderstorm with hail", "⛈️", "⛈️")
    }
    
    if weather_code not in weather_map:
        return ("Unknown", "❓")
    
    desc, day_emoji, night_emoji = weather_map[weather_code]
    emoji = night_emoji if is_night else day_emoji
    return desc, emoji


def get_alert_emoji(severity: str, certainty: str) -> str:
    """Get emoji based on alert severity and certainty."""
    if severity == "Extreme":
        return "🚨"
    elif severity == "Severe":
        return "⚠️"
    elif severity == "Moderate":
        return "🔶"
    elif severity == "Minor":
        return "🔷"
    return "ℹ️"


def fetch_nws_alerts(lat: float, lon: float) -> List[Dict]:
    """
    Fetch active weather alerts from NWS API for a given location.
    
    Note: NWS API only covers US territories. Returns empty list for non-US locations.
    """
    url = f"https://api.weather.gov/alerts/active"
    params = {"point": f"{lat},{lon}"}
    headers = {
        "User-Agent": "(weather-fetcher-skill, contact@example.com)",
        "Accept": "application/geo+json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # NWS returns 404 for locations outside US coverage
        if response.status_code == 404:
            return []
        
        response.raise_for_status()
        data = response.json()
        
        alerts = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            
            alert = {
                "id": props.get("id", ""),
                "event": props.get("event", "Unknown"),
                "headline": props.get("headline", ""),
                "severity": props.get("severity", "Unknown"),
                "certainty": props.get("certainty", "Unknown"),
                "urgency": props.get("urgency", "Unknown"),
                "status": props.get("status", ""),
                "message_type": props.get("messageType", ""),
                "category": props.get("category", ""),
                "effective": props.get("effective", ""),
                "expires": props.get("expires", ""),
                "onset": props.get("onset", ""),
                "ends": props.get("ends", ""),
                "sender": props.get("senderName", ""),
                "description": props.get("description", ""),
                "instruction": props.get("instruction", ""),
                "area_desc": props.get("areaDesc", ""),
                "emoji": get_alert_emoji(props.get("severity", ""), props.get("certainty", ""))
            }
            alerts.append(alert)
        
        # Sort by severity (Extreme > Severe > Moderate > Minor > Unknown)
        severity_order = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 5))
        
        return alerts
        
    except requests.exceptions.RequestException:
        # Return empty list on any network error - don't fail the whole request
        return []


def fetch_weather_data(lat: float, lon: float, units: str = "fahrenheit") -> Dict:
    """Fetch weather data from Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,weather_code,is_day",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "temperature_unit": units,
        "wind_speed_unit": "mph" if units == "fahrenheit" else "kmh",
        "precipitation_unit": "inch" if units == "fahrenheit" else "mm",
        "timezone": "auto"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def wind_direction_label(degrees: float) -> str:
    """Convert wind direction degrees to compass label."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return directions[idx]


def build_forecast_summary(daily: Dict, include_emoji: bool = True) -> List[Dict]:
    """Build a compact multi-day forecast summary from daily data."""
    days = []
    for i in range(len(daily.get("time", []))):
        desc, emoji = get_weather_emoji(daily["weather_code"][i])
        day = {
            "date": daily["time"][i],
            "high": round(daily["temperature_2m_max"][i]),
            "low": round(daily["temperature_2m_min"][i]),
            "description": desc,
            "sunrise": daily["sunrise"][i],
            "sunset": daily["sunset"][i],
        }
        if include_emoji:
            day["emoji"] = emoji
        days.append(day)
    return days


def get_weather(location: str, units: str = "fahrenheit", include_emoji: bool = True,
                include_alerts: bool = True, verbose: bool = False) -> Dict:
    """
    Fetch weather for any location.
    
    Args:
        location: City name, postal code, or "latitude,longitude"
                  NOTE: Full street addresses are NOT supported
        units: "fahrenheit" or "celsius"
        include_emoji: Include weather emoticons in response
        include_alerts: Include NWS severe weather alerts (US only)
        verbose: Include raw hourly and daily data arrays
    
    Returns:
        Dictionary with location info, weather data, and alerts
    """
    # Check if input is coordinates
    if ',' in location:
        try:
            lat, lon = map(float, location.split(','))
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}", "country_code": ""}
        except ValueError:
            # Not valid coordinates, treat as address
            location_info = geocode(location)
    else:
        # Geocode address
        location_info = geocode(location)
    
    # Fetch weather
    weather_data = fetch_weather_data(location_info["lat"], location_info["lon"], units)
    
    # Extract current weather
    current = weather_data["current"]
    daily = weather_data["daily"]
    desc, emoji = get_weather_emoji(current["weather_code"])
    
    # Get today's high/low from daily data
    today_high = round(daily["temperature_2m_max"][0])
    today_low = round(daily["temperature_2m_min"][0])
    today_sunrise = daily["sunrise"][0]
    today_sunset = daily["sunset"][0]
    
    # Wind direction
    wind_deg = current.get("wind_direction_10m")
    wind_dir = wind_direction_label(wind_deg) if wind_deg is not None else None
    
    unit_label = "F" if units == "fahrenheit" else "C"
    speed_label = "mph" if units == "fahrenheit" else "km/h"
    precip_label = "in" if units == "fahrenheit" else "mm"
    
    result = {
        "location": location_info,
        "units": unit_label,
        "temp": round(current["temperature_2m"]),
        "feels_like": round(current["apparent_temperature"]),
        "high": today_high,
        "low": today_low,
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "wind_speed_unit": speed_label,
        "wind_direction": wind_dir,
        "wind_direction_degrees": wind_deg,
        "precipitation": current["precipitation"],
        "precipitation_unit": precip_label,
        "description": desc,
        "sunrise": today_sunrise,
        "sunset": today_sunset,
        "forecast": build_forecast_summary(daily, include_emoji),
    }
    
    if include_emoji:
        result["emoji"] = emoji
    
    # Include raw hourly/daily only in verbose mode
    if verbose:
        result["hourly"] = weather_data["hourly"]
        result["daily_raw"] = daily
    
    # Fetch alerts (NWS API - US only)
    if include_alerts:
        alerts = fetch_nws_alerts(location_info["lat"], location_info["lon"])
        result["alerts"] = alerts
        result["alerts_count"] = len(alerts)
        result["has_alerts"] = len(alerts) > 0
        
        # Add summary of most severe alert if any exist
        if alerts:
            most_severe = alerts[0]  # Already sorted by severity
            result["alerts_summary"] = {
                "most_severe_event": most_severe["event"],
                "most_severe_severity": most_severe["severity"],
                "most_severe_headline": most_severe["headline"]
            }
    
    return result


def get_alerts_only(location: str) -> Dict:
    """
    Fetch only weather alerts for a location (no forecast data).
    
    Args:
        location: City name, postal code, or "latitude,longitude"
                  NOTE: Full street addresses are NOT supported
    
    Returns:
        Dictionary with location info and alerts only
    """
    # Check if input is coordinates
    if ',' in location:
        try:
            lat, lon = map(float, location.split(','))
            location_info = {"lat": lat, "lon": lon, "name": f"{lat}, {lon}", "country_code": ""}
        except ValueError:
            location_info = geocode(location)
    else:
        location_info = geocode(location)
    
    alerts = fetch_nws_alerts(location_info["lat"], location_info["lon"])
    
    result = {
        "location": location_info,
        "alerts": alerts,
        "alerts_count": len(alerts),
        "has_alerts": len(alerts) > 0
    }
    
    if alerts:
        most_severe = alerts[0]
        result["alerts_summary"] = {
            "most_severe_event": most_severe["event"],
            "most_severe_severity": most_severe["severity"],
            "most_severe_headline": most_severe["headline"]
        }
    
    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch weather data and alerts for any location",
        epilog="Note: Full street addresses are NOT supported. Use city names, postal codes, or GPS coordinates."
    )
    parser.add_argument("location", help="City name, postal code, or 'latitude,longitude'")
    parser.add_argument("--units", choices=["fahrenheit", "celsius"], default="fahrenheit",
                        help="Temperature units (default: fahrenheit)")
    parser.add_argument("--no-emoji", action="store_true", help="Exclude emoji from output")
    parser.add_argument("--no-alerts", action="store_true", help="Exclude weather alerts")
    parser.add_argument("--alerts-only", action="store_true", 
                        help="Fetch only alerts (no forecast data)")
    parser.add_argument("--verbose", action="store_true",
                        help="Include raw hourly and daily data arrays (large output)")
    
    args = parser.parse_args()
    
    try:
        if args.alerts_only:
            result = get_alerts_only(args.location)
        else:
            result = get_weather(
                args.location, 
                args.units, 
                not args.no_emoji,
                not args.no_alerts,
                args.verbose
            )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except ValueError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Weather fetch failed: {str(e)}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()