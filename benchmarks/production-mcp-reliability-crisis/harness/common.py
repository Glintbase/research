"""Shared constants and helpers for the Remote MCP Server Reliability study."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

STUDY_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = STUDY_DIR / "data"
FRAME_DIR = DATA_DIR / "frame"
RAW_DIR = DATA_DIR / "raw"  # per-request logs with body snippets; not published

HARNESS_VERSION = "1.0.0"
USER_AGENT = (
    "GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)"
)
CLIENT_INFO = {"name": "GlintbaseResearch", "version": HARNESS_VERSION}

MODERN_VERSION = "2026-07-28"
LEGACY_VERSION = "2025-11-25"
# Revisions that define the MCP-Protocol-Version header on post-initialize requests.
HEADER_VERSIONS = {"2025-06-18", "2025-11-25"}

# Error codes that only a modern (2026-07-28+) server emits.
MODERN_ERROR_CODES = {-32020, -32021, -32022}

CANARY_TOOL = "__glintbase_probe_nonexistent_tool__"

REQUEST_TIMEOUT_S = 10.0
SSE_FIRST_EVENT_TIMEOUT_S = 5.0
MAX_BODY_BYTES = 512 * 1024
SNIPPET_BYTES = 2048


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=STUDY_DIR, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_url(url: str) -> str | None:
    """Lower-case scheme/host, drop query/fragment and trailing slash. None if unusable."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if not parts.scheme or not parts.netloc:
        return None
    path = parts.path.rstrip("/") or ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def is_templated(url: str) -> bool:
    return "{" in url or "}" in url or "%7b" in url.lower()


def is_private_address(host: str) -> bool:
    """True if host is a literal or resolves to a loopback/private/link-local/reserved address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False  # unresolvable; probe will record it as unreachable
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        ):
            return True
    return False


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def load_optout(path: Path = STUDY_DIR / "optout.txt") -> set[str]:
    if not path.exists():
        return set()
    hosts = set()
    for line in path.read_text(encoding="utf8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            hosts.add(line)
    return hosts


def host_opted_out(host: str, optout: set[str]) -> bool:
    return any(host == h or host.endswith("." + h) for h in optout)


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf8") as f:
        return [json.loads(line) for line in f if line.strip()]
