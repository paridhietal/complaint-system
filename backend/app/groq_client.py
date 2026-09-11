import json
import re

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_FAST_MODEL, GROQ_REASONING_MODEL

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def call_llm(system_prompt: str, user_prompt: str, model: str, json_mode: bool = False,
             temperature: float = 0.2) -> str:
    """
    Calls a Groq chat completion. Raises RuntimeError with a clear message if no
    API key is configured, so the failure is obvious in the demo instead of a
    confusing stack trace.
    """
    if _client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env and "
            "paste a key from https://console.groq.com/keys"
        )

    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )
    return response.choices[0].message.content


def call_llm_json(system_prompt: str, user_prompt: str, model: str) -> dict:
    raw = call_llm(system_prompt, user_prompt, model, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # gemma2-9b-it occasionally wraps JSON in prose or code fences even in
        # json_object mode; fall back to a best-effort cleanup before giving up.
        cleaned = _strip_code_fences(raw)
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


FAST_MODEL = GROQ_FAST_MODEL
REASONING_MODEL = GROQ_REASONING_MODEL
