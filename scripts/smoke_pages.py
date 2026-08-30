"""Post-deploy HTTP smoke check for the published SRTI snapshot."""

from __future__ import annotations

import json
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def fetch(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "MonarchCastleSRTIHealth/1.0"})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read(), response.headers.get_content_type()


def check(base_url: str) -> None:
    base_url = base_url.rstrip("/") + "/"
    page, page_type = fetch(base_url)
    markup = page.decode("utf-8")
    if page_type != "text/html" or "SRTI / PUBLIC OSINT MONITOR" not in markup:
        raise RuntimeError("root page identity check failed")

    snapshot_bytes, _ = fetch(base_url + "data/srti_latest.json")
    snapshot = json.loads(snapshot_bytes)
    if snapshot.get("schema_version") != 2 or not snapshot.get("quality_gate", {}).get("passed"):
        raise RuntimeError("published snapshot contract check failed")
    if snapshot.get("fetched_at") not in markup:
        raise RuntimeError("page and published snapshot timestamps disagree")

    logo, logo_type = fetch(base_url + "assets/mc-mark.png")
    if logo_type != "image/png" or not logo.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("brand asset check failed")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/smoke_pages.py <pages-url>")
    last_error = None
    for attempt in range(1, 6):
        try:
            check(sys.argv[1])
            print(f"[OK] Published SRTI health check passed on attempt {attempt}")
            return
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError, URLError) as error:
            last_error = error
            if attempt < 5:
                time.sleep(5)
    raise SystemExit(f"published health check failed: {last_error}")


if __name__ == "__main__":
    main()
