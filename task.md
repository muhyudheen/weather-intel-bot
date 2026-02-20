# Weather Intel Bot - Development Instructions

## Goal
Build a chatbot that detects weather-related queries, dynamically calls the Open-Meteo API to fetch real-time data, and synthesizes it into an intelligent conversational response.

## Workflow Steps
1. **User Input:** Accept a user message via a FastAPI endpoint.
2. **Detect Intent & Extract Coordinates:** - Send the user input to the LLM.
   - The LLM must determine if the intent is weather-related.
   - If it is a weather query, the LLM must identify the target city and natively determine its `latitude` and `longitude` as numeric values. Do NOT implement a separate geocoding step or use a geocoding API.
3. **API Call:**
   - Pass the extracted `latitude` and `longitude` payload to the Open-Meteo API (no API key required).
   - Fetch the current weather data (temperature, humidity, etc.).
4. **Format Final Answer:**
   - Pass the structured JSON response from Open-Meteo back to the LLM.
   - Have the LLM synthesize this raw data into a natural, conversational, human-like response for the user.

## Technical Constraints
- **Architecture:** Write the entire application in a single script named `main.py`.
- **Framework:** Use FastAPI.
- **Simplicity:** Keep the project highly basic. Do not implement complex error handling, grace handling, or edge-case management right now. Stick strictly to the primary workflow.
- **LLM Setup:** Rely on the provided AI Pipe base URL and token for LLM calls.