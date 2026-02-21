import json
from llm import call_llm

INTENT_SYSTEM = """
You are a weather query intent detector. Analyse the user's message and respond ONLY with a valid JSON object — no markdown, no explanation.

Rules:
1. If the message is weather-related, set "is_weather": true and fill:
   - "city": best-matched city name (string)
   - "country": country of that city (string)
   - "latitude": numeric latitude (float, use your built-in knowledge — no geocoding API)
   - "longitude": numeric longitude (float)
   - "query_type": one of "current" | "forecast" | "general"
     • "current"  → asking about right now (e.g. "what is the weather", "is it hot")
     • "forecast" → asking about future   (e.g. "will it rain tomorrow", "this week")
     • "general"  → vague / historical    (e.g. "what is summer like in Paris")
   - "forecast_days": integer 1-7, only relevant when query_type=="forecast", else null
   - "ambiguous": true if the city name is genuinely ambiguous (e.g. "Springfield", "Paris" without country)
   - "ambiguity_note": short string explaining the ambiguity if ambiguous==true, else null

2. If the message is NOT weather-related, set only "is_weather": false.

3. Never invent coordinates. If you are unsure about a city, set "ambiguous": true and pick the most famous match.

Examples:
{"is_weather":true,"city":"Delhi","country":"India","latitude":28.6139,"longitude":77.2090,"query_type":"current","forecast_days":null,"ambiguous":false,"ambiguity_note":null}
{"is_weather":true,"city":"Paris","country":"France","latitude":48.8566,"longitude":2.3522,"query_type":"forecast","forecast_days":3,"ambiguous":true,"ambiguity_note":"Defaulted to Paris, France — there is also Paris, Texas, USA"}
{"is_weather":false}
""".strip()


def detect_intent(message: str) -> dict:
    """
    Returns a dict with at minimum {"is_weather": bool}.
    If is_weather is True, also has city, country, latitude, longitude, query_type, etc.
    """
    raw = call_llm(
        [
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user",   "content": message},
        ],
        json_mode=True,
    )
    return json.loads(raw)
