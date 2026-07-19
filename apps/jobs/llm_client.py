import logging

import httpx

logger = logging.getLogger(__name__)


def generate_with_llm(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    api_base_url: str,
    model: str,
) -> str | None:
    url = f"{api_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            logger.error(f"LLM API error {resp.status_code}: {resp.text[:300]}")
            return None

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            logger.error("LLM returned no choices")
            return None

        text = choices[0].get("message", {}).get("content", "").strip()
        if not text:
            logger.error("LLM returned empty content")
            return None

        return text

    except httpx.TimeoutException:
        logger.error("LLM API timeout after 20s")
        return None
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        return None
