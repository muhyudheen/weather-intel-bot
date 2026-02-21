import openmeteo_requests
import requests_cache
from retry_requests import retry

# ── Open-Meteo client (cached + retry) ────────────────────────────────────────
_cache   = requests_cache.CachedSession(".cache", expire_after=3600)
_session = retry(_cache, retries=5, backoff_factor=0.2)
_client  = openmeteo_requests.Client(session=_session)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather-code → human-readable label
WMO_LABELS = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Heavy drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

# WMO weather-code → emoji
WMO_EMOJI = {
    0: "☀️",
    1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "❄️", 73: "❄️", 75: "❄️", 77: "🌨️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    85: "🌨️", 86: "🌨️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}

WIND_DIRECTIONS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _wind_dir(degrees: float) -> str:
    idx = round(degrees / 22.5) % 16
    return WIND_DIRECTIONS[idx]


def fetch_current(latitude: float, longitude: float) -> dict:
    """Fetch current weather conditions from Open-Meteo."""
    params = {
        "latitude":  latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",           # 0
            "apparent_temperature",     # 1
            "relative_humidity_2m",     # 2
            "precipitation",            # 3
            "weather_code",             # 4
            "wind_speed_10m",           # 5
            "wind_direction_10m",       # 6
            "uv_index",                 # 7
        ],
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    r   = _client.weather_api(OPEN_METEO_URL, params=params)[0]
    cur = r.Current()
    code = int(cur.Variables(4).Value())
    return {
        "latitude":         round(r.Latitude(), 4),
        "longitude":        round(r.Longitude(), 4),
        "timezone":         r.Timezone().decode() if r.Timezone() else "UTC",
        "temperature":      round(cur.Variables(0).Value(), 1),
        "feels_like":       round(cur.Variables(1).Value(), 1),
        "humidity":         round(cur.Variables(2).Value()),
        "precipitation_mm": round(cur.Variables(3).Value(), 1),
        "weather_code":     code,
        "condition":        WMO_LABELS.get(code, "Unknown"),
        "emoji":            WMO_EMOJI.get(code, "🌡️"),
        "wind_speed_kmh":   round(cur.Variables(5).Value(), 1),
        "wind_direction":   _wind_dir(cur.Variables(6).Value()),
        "uv_index":         round(cur.Variables(7).Value(), 1),
    }


def fetch_forecast(latitude: float, longitude: float, days: int = 7) -> dict:
    """Fetch N-day daily forecast from Open-Meteo."""
    params = {
        "latitude":  latitude,
        "longitude": longitude,
        "daily": [
            "weather_code",                  # 0
            "temperature_2m_max",            # 1
            "temperature_2m_min",            # 2
            "precipitation_sum",             # 3
            "precipitation_probability_max", # 4
            "wind_speed_10m_max",            # 5
        ],
        "forecast_days": days,
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    r     = _client.weather_api(OPEN_METEO_URL, params=params)[0]
    daily = r.Daily()
    n     = days

    codes  = [int(daily.Variables(0).ValuesAsNumpy()[i]) for i in range(n)]
    t_max  = [round(float(daily.Variables(1).ValuesAsNumpy()[i]), 1) for i in range(n)]
    t_min  = [round(float(daily.Variables(2).ValuesAsNumpy()[i]), 1) for i in range(n)]
    precip = [round(float(daily.Variables(3).ValuesAsNumpy()[i]), 1) for i in range(n)]
    rain_p = [round(float(daily.Variables(4).ValuesAsNumpy()[i]))     for i in range(n)]
    wind   = [round(float(daily.Variables(5).ValuesAsNumpy()[i]), 1)  for i in range(n)]

    days_out = []
    for i in range(n):
        days_out.append({
            "day_index":       i,
            "weather_code":    codes[i],
            "condition":       WMO_LABELS.get(codes[i], "Unknown"),
            "emoji":           WMO_EMOJI.get(codes[i], "🌡️"),
            "temp_max":        t_max[i],
            "temp_min":        t_min[i],
            "precipitation_mm":precip[i],
            "rain_probability": rain_p[i],
            "wind_speed_kmh":  wind[i],
        })
    return {"days": days_out}
