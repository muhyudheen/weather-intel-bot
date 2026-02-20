import os
import json
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# ── LLM config (AI Pipe – OpenAI-compatible) ──────────────────────────────────
LLM_URL   = "https://aipipe.org/openai/v1/chat/completions"
LLM_MODEL = "gpt-4o-mini"
API_KEY   = os.environ.get("OPENAI_API_KEY")

# ── Open-Meteo client (cached + retry) ────────────────────────────────────────
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# ── helpers ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


def call_llm(messages: list) -> str:
    """Send messages to the LLM and return the assistant reply as a string."""
    resp = requests.post(
        LLM_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": LLM_MODEL, "messages": messages},
    )
    return resp.json()["choices"][0]["message"]["content"]


def fetch_weather(latitude: float, longitude: float) -> dict:
    """Call Open-Meteo and return a flat dict of current conditions."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code",
        ],
    }
    responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
    r = responses[0]
    cur = r.Current()
    return {
        "latitude":             r.Latitude(),
        "longitude":            r.Longitude(),
        "temperature_2m":       cur.Variables(0).Value(),
        "relative_humidity_2m": cur.Variables(1).Value(),
        "wind_speed_10m":       cur.Variables(2).Value(),
        "weather_code":         cur.Variables(3).Value(),
    }


# ── endpoint ──────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(request: ChatRequest):
    # Step 1 – detect weather intent & extract coordinates from LLM
    intent_raw = call_llm([
        {
            "role": "system",
            "content": (
                "You are a weather intent detector. "
                "Given a user message, decide if it is a weather-related query. "
                "If yes, identify the city and resolve its latitude and longitude as numeric values — "
                "do NOT use any geocoding API, use your own knowledge. "
                "Reply ONLY with a valid JSON object, no markdown, no extra text. "
                'Format when weather: {"is_weather": true, "city": "CityName", "latitude": 12.34, "longitude": 56.78} '
                'Format when not weather: {"is_weather": false}'
            ),
        },
        {"role": "user", "content": request.message},
    ])

    intent = json.loads(intent_raw)

    if not intent.get("is_weather"):
        return {"response": "I can only help with weather-related queries. Try asking about the weather somewhere!"}

    # Step 2 – fetch live weather from Open-Meteo
    weather = fetch_weather(intent["latitude"], intent["longitude"])

    # Step 3 – synthesize a natural reply
    answer = call_llm([
        {
            "role": "system",
            "content": (
                "You are a friendly weather assistant. "
                "The user asked a weather question. You have fetched live data from Open-Meteo. "
                "Synthesize the raw JSON into a natural, conversational response. "
                "Include temperature, humidity, and wind speed in a readable way."
            ),
        },
        {"role": "user", "content": request.message},
        {
            "role": "user",
            "content": f"Live weather data for {intent['city']}: {json.dumps(weather)}",
        },
    ])

    return {"response": answer}


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
