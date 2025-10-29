# app/secure_http.py
import time

import httpx

TIMEOUT = httpx.Timeout(5.0, read=5.0, connect=3.0)
MAX_RETRIES = 3


def safe_get(url: str) -> httpx.Response:
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(0.5 * (attempt + 1))
