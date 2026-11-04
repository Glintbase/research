"""Per-minute connectivity log, run alongside every round (as in The Silent Wall).

Usage: python connectivity.py <logfile>   (runs until killed)
"""

import sys
import time
from datetime import datetime, timezone

import httpx

URLS = ["https://www.gstatic.com/generate_204", "https://cloudflare.com/cdn-cgi/trace"]

with open(sys.argv[1], "a", encoding="utf8") as log:
    while True:
        ok = []
        for u in URLS:
            try:
                ok.append(httpx.get(u, timeout=10).status_code < 500)
            except Exception:
                ok.append(False)
        log.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {'ok' if any(ok) else 'FAIL'} {ok}\n")
        log.flush()
        time.sleep(60)
