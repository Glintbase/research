"""Shared constants for The Silent Wall."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = STUDY_DIR / "data"
SAMPLE_CSV = DATA_DIR / "sample" / "domains.csv"
ROBOTS_DIR = DATA_DIR / "robots"
EDGE_DIR = DATA_DIR / "edge"

HARNESS_VERSION = "1.0.0"
AGENT_TOKEN = "GlintbaseResearch"
AGENT_UA = "GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)"

# Vendor-documented agent tokens (verified 2026-10-12; sources in PREREGISTRATION.md).
TOKENS = {
    "GPTBot": ("OpenAI", "training"),
    "OAI-SearchBot": ("OpenAI", "search"),
    "ChatGPT-User": ("OpenAI", "user"),
    "ClaudeBot": ("Anthropic", "training"),
    "Claude-SearchBot": ("Anthropic", "search"),
    "Claude-User": ("Anthropic", "user"),
    "PerplexityBot": ("Perplexity", "search"),
    "Perplexity-User": ("Perplexity", "user"),
    "Google-Extended": ("Google", "training"),
    "Googlebot": ("Google", "search-control"),
    "Applebot-Extended": ("Apple", "training"),
    "CCBot": ("Common Crawl", "training"),
    "Meta-ExternalAgent": ("Meta", "training"),
    "Bytespider": ("ByteDance", "training"),
}

TIMEOUT_S = 20.0
PAUSE_BETWEEN_IDENTITIES_S = 30.0
PAUSE_BETWEEN_REQUESTS_S = 1.0
MAX_PAGES = 4  # homepage + up to 3


def chromium_executable() -> str | None:
    hits = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*\chrome-win64\chrome.exe"))
    return sorted(hits)[-1] if hits else None


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
