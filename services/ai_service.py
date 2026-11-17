"""
HardwareIQ - Optional Gemini AI Integration Service
Provides optional natural-language synthesis using Google Gemini API.
If GEMINI_API_KEY is absent, invalid, or network is unavailable, seamlessly
falls back to the offline deterministic local tool router.
Compatible with Python 3.8+.
"""

import json
import os
from typing import Any, Dict, Optional
import requests
from dotenv import load_dotenv

from services.tool_router import route_question

# Load environment variables from .env or .env.example if present
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv(".env.example")

# Primary model and resilient fallback models
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-3-flash-preview"]


def get_gemini_api_key() -> Optional[str]:
    """Retrieves the Gemini API key from environment variables."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key else None


def is_ai_available() -> bool:
    """Returns True if a Gemini API key is configured."""
    return get_gemini_api_key() is not None


def call_gemini_api(prompt: str, context_json: str, api_key: str, timeout: float = 8.0) -> Optional[str]:
    """
    Calls the Gemini REST API using requests.
    Strictly instructs the model to rely only on the provided hardware data.
    Attempts the primary GEMINI_MODEL first, falling back to GEMINI_FALLBACK_MODELS if experiencing high demand.
    """
    headers = {"Content-Type": "application/json"}

    system_instruction = (
        "You are HardwareIQ, a strict and factual Linux Hardware Q&A Assistant. "
        "You must answer user queries based EXCLUSIVELY on the actual detected hardware data "
        "provided below in JSON format. Never invent, extrapolate, or hallucinate missing specs. "
        "If a specific detail is not present in the detected hardware data, explicitly state that "
        "it is not reported or unavailable. For virtual display adapters (like VirtualBox or VMware), "
        "never misrepresent them as dedicated GPUs."
    )

    full_prompt = (
        f"{system_instruction}\n\n"
        f"--- DETECTED HARDWARE DATA (GROUND TRUTH) ---\n"
        f"{context_json}\n\n"
        f"--- USER QUESTION ---\n"
        f"{prompt}\n\n"
        f"Provide a helpful, precise, markdown-formatted answer:"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
        }
    }

    models_to_try = [GEMINI_MODEL]
    for fb in GEMINI_FALLBACK_MODELS:
        if fb not in models_to_try:
            models_to_try.append(fb)

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            continue

    return None


def ask_assistant(query: str, prefer_ai: bool = True) -> Dict[str, Any]:
    """
    Answers a hardware question.
    Uses Gemini if configured, enabled, and reachable; otherwise uses
    the deterministic offline local engine.
    """
    # Always query local hardware tools first to establish grounded truth
    local_result = route_question(query)

    api_key = get_gemini_api_key()
    if prefer_ai and api_key and local_result.get("status") == "success":
        context_str = json.dumps(local_result.get("structured_data", {}), indent=2)
        ai_response = call_gemini_api(query, context_str, api_key)
        if ai_response:
            return {
                "intent": local_result["intent"],
                "tool_used": local_result["tool_used"],
                "answer": ai_response,
                "structured_data": local_result.get("structured_data", {}),
                "source": "gemini_grounded",
                "status": "success"
            }

    # Default to robust offline local answer
    local_result["source"] = "local_deterministic"
    return local_result
