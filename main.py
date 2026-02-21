import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from llm import call_llm
from intent import detect_intent
from weather import fetch_current, fetch_forecast

app = FastAPI(title="Weather Intel Bot")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


# ── LLM synthesis prompts ─────────────────────────────────────────────────────

SYNTH_SYSTEM = """
You are a friendly, conversational weather assistant.
The user asked a weather question and you have live data from Open-Meteo.
Write a natural, warm, 2-4 sentence reply. Include the key numbers
(temperature, humidity, wind) but make it feel like a human wrote it.
Do not mention JSON, APIs, or data sources.
""".strip()

NON_WEATHER_REPLY = (
    "I'm a weather assistant — I can only help with weather-related questions! "
    "Try asking something like \"What's the weather in Tokyo?\" or "
    "\"Will it rain in Mumbai this week?\""
)


# ── helpers ───────────────────────────────────────────────────────────────────

def synthesize(user_message: str, city: str, country: str, data: dict) -> str:
    return call_llm([
        {"role": "system", "content": SYNTH_SYSTEM},
        {"role": "user",   "content": user_message},
        {"role": "user",   "content": f"Live weather data for {city}, {country}: {json.dumps(data)}"},
    ])


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    # 1. Detect intent + extract coordinates
    intent = detect_intent(req.message)

    if not intent.get("is_weather"):
        return {"response": NON_WEATHER_REPLY, "weather_data": None, "query_type": None}

    if intent.get("needs_location"):
        return {
            "response": "Sure! 🌍 Which city would you like the weather for?",
            "weather_data": None,
            "query_type": "needs_location",
        }

    city    = intent["city"]
    country = intent["country"]
    lat     = intent["latitude"]
    lon     = intent["longitude"]
    qtype   = intent.get("query_type", "current")
    note    = intent.get("ambiguity_note")   # may be None

    # 2. Fetch live weather
    if qtype == "forecast":
        days         = intent.get("forecast_days") or 7
        weather_data = fetch_forecast(lat, lon, days=days)
        weather_data["current"] = fetch_current(lat, lon)   # also grab current
    else:
        weather_data = {"current": fetch_current(lat, lon)}

    # 3. Synthesize natural language reply
    response_text = synthesize(req.message, city, country, weather_data)
    if note:
        response_text = f"_Note: {note}_\n\n{response_text}"

    return {
        "response":    response_text,
        "weather_data": weather_data,
        "city":        city,
        "country":     country,
        "query_type":  qtype,
        "ambiguous":   intent.get("ambiguous", False),
    }


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
