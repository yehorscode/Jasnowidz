import json
import re
import time
from random import random

from openrouter import OpenRouter
from openrouter.components import ChatChoice
from openrouter.errors import TooManyRequestsResponseError

from utils.config import increment_ratelimit
from utils.logmanager import error, warn

AI_MODEL = "deepseek/deepseek-v4-flash"


def _extract_status_code(e: Exception) -> int | None:
    """Pull a numeric HTTP status out of the exception, whatever shape it comes in."""
    status = getattr(e, "status_code", None) or getattr(e, "status", None)
    if status:
        return int(status)
    match = re.search(r"Status (\d{3})", str(e))
    return int(match.group(1)) if match else None


def _looks_transient(e: Exception) -> bool:
    """Catch network-level flakiness that isn't a clean status code."""
    transient_markers = (
        "timeout",
        "timed out",
        "connection",
        "temporarily unavailable",
    )
    msg = str(e).lower()
    return any(marker in msg for marker in transient_markers)


def clean_json_response(response_text: str) -> str:
    response_text = re.sub(r"```(?:json)?\s*\n?", "", response_text)
    response_text = response_text.strip()
    return response_text


def parse_event_duration(duration_str: str, router: OpenRouter):
    """Needs AI_MODEL const defined at top of file to function"""
    max_retries = 20
    base_delay = 2.0
    max_delay = 60.0
    response_text = None
    duration_str = duration_str.strip() if duration_str else "brak daty"
    if duration_str == "brak daty":
        return None, None
    for attempt in range(1, max_retries + 1):
        try:
            response = router.chat.send(
                model=AI_MODEL,
                max_tokens=500,
                messages=[
                    {
                        "content": 'Extract event date range from HTML. Return ONLY valid JSON with start_date and end_date in ISO format (YYYY-MM-DDTHH:MM:SSZ). Return None for start_date or end_date when no date present/you can\'t find it. If both values can\'t be determined return: {"start_date":null, "end_date":null}. Do not return responses wrapped with formatting. Example of proper response: {"start_date":"2026-09-08T00:00:00Z","end_date":"2026-09-13T23:59:59Z"}.',
                        "role": "system",
                    },
                    {
                        "content": f"Extract data from this duration string: {duration_str}",
                        "role": "user",
                    },
                ],
            )
            increment_ratelimit()
            choices: ChatChoice = response.choices[0]
            response_text = choices.message.content.strip()
            response_text = clean_json_response(response_text)
            parsed = json.loads(response_text)
            print(f"PARSE FUNC: {parsed.get('start_date')}, {parsed.get('end_date')}")
            return parsed.get("start_date"), parsed.get("end_date")

        except json.JSONDecodeError as e:
            error(f"JSON parse error: {e} | {response_text}")
            return None, None

        except Exception as e:
            status = _extract_status_code(e)
            is_retryable = status == 429 or status is None and _looks_transient(e)

            if not is_retryable or attempt == max_retries:
                error(f"Giving up on '{duration_str}' after {attempt} attempt(s): {e}")
                return None, None

            wait = min(base_delay * (2 ** (attempt - 1)), max_delay)
            wait += random.uniform(0, wait * 0.5)
            warn(
                f"Retryable error ({e}) on attempt {attempt}/{max_retries}, "
                f"sleeping {wait:.1f}s before retry"
            )
            time.sleep(wait)

    return None, None
