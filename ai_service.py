import os
import json
import re
import httpx
from typing import List, Dict, Any

# Helper to extract raw JSON from LLM responses that may contain markdown code fences
def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    url = "https://inference.do-ai.run/v1/chat/completions"
    api_key = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
    model = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Expected OpenAI‑compatible response structure
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            raw_json = _extract_json(content)
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError:
                # Return whatever text we got if it wasn't JSON
                return {"note": "Failed to parse JSON from AI response", "raw": raw_json}
    except Exception as e:
        # Fallback – never let the error propagate to route handlers
        return {"note": f"AI service temporarily unavailable: {str(e)}"}

async def call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    """Public wrapper used by route handlers.
    Returns a dict – callers should safely access keys.
    """
    return await _call_inference(messages, max_tokens)
