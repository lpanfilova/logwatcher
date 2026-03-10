"""
OpenAI integration (Windows-safe + widely supported).

This version uses Chat Completions:
  client.chat.completions.create(...)

Why:
- errors shows installed OpenAI SDK does not have client.responses
- Chat Completions is supported across more versions/environments
"""

import os
import json

from typing import Dict, Any, List
from openai import OpenAI
from openai import RateLimitError, AuthenticationError, APIConnectionError, APIStatusError
from schemas import LogEvent
from pathlib import Path

MODEL = "gpt-4o-mini"

def load_openai_key() -> str | None:
    """
    Load the OpenAI API key.

    Priority:
    1. OPENAI_API_KEY.txt file
    2. Environment variable OPENAI_API_KEY
    """
    key_file = Path("OPENAI_API_KEY.txt")

    if key_file.exists():
        key = key_file.read_text().strip()
        if key:
            print("[AI] Loaded OpenAI key from OPENAI_API_KEY.txt")
            return key

    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        print("[AI] Loaded OpenAI key from environment variable")
        return env_key

    print("[AI] No OpenAI API key found")
    return None


OPENAI_API_KEY = load_openai_key()

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def _chat(prompt: str, system: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content.strip()

    except (RateLimitError, AuthenticationError, APIConnectionError, APIStatusError) as e:
        # Graceful fallback message so your API doesn't 500 during demos
        return (
            "AI call failed (likely billing/quota). "
            "The server is working, but OpenAI rejected the request.\n\n"
            f"Details: {type(e).__name__}: {e}"
        )


def build_filter_from_question(question: str) -> Dict[str, Any]:
    """
    Convert a natural-language question into a structured filter dict.
    Returns a dict with allowed keys only. If parsing fails, returns a safe default.
    """
    system = """
You are a log query assistant.
Return ONLY valid JSON (no markdown) for a filter object with these allowed keys:

- "since_minutes": number
- "event": string (exact match, e.g. "db_connection_failed", "db_query_slow", "http_request", "user_login")
- "level_min": number (e.g. 40 means warnings/errors)
- "route_contains": string
- "userId": number
- "durationMs_min": number
- "latencyMs_min": number

If the user asks for "errors", set level_min to 50 or pick event "db_connection_failed".
If they ask for "slow queries", set event "db_query_slow" and maybe durationMs_min.
If they ask for "requests", set event "http_request".
Always default to since_minutes = 10 if not specified.
"""

    text = _chat(question, system=system)

    # Defensive parsing
    try:
        filt = json.loads(text)
        if "since_minutes" not in filt:
            filt["since_minutes"] = 10
        return filt
    except Exception:
        return {"since_minutes": 10, "level_min": 40}


def explain_results(question: str, filt: Dict[str, Any], matched: List[LogEvent]) -> str:
    """
    Answers the user's question using ONLY matched logs.
    """
    max_lines = 200
    lines = [e.model_dump() for e in matched[:max_lines]]

    payload = {
        "question": question,
        "filter_used": filt,
        "matched_count": len(matched),
        "matched_logs": lines,
        "rules": [
            "If matched_logs are empty, say you found no evidence in the requested window.",
            "Do NOT claim events that do not appear in matched_logs.",
            "Summarize patterns and suggest next debugging steps.",
        ],
    }

    system = "You are an SRE assistant. Follow the rules in the payload strictly."

    return _chat(json.dumps(payload), system=system)
