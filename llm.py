import os
import requests

LLM_URL   = "https://aipipe.org/openai/v1/chat/completions"
LLM_MODEL = "gpt-4o-mini"
API_KEY   = os.environ.get("OPENAI_API_KEY")


def call_llm(messages: list, json_mode: bool = False) -> str:
    """Call the AI Pipe LLM and return the assistant reply string."""
    payload = {"model": LLM_MODEL, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(
        LLM_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
