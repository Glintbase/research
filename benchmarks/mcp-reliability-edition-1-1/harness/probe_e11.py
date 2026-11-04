"""Edition 1.1 probe: the Edition 1 harness, unchanged, plus metadata-only additions.

The Edition 1 procedure (../../production-mcp-reliability-crisis/harness/probe.py) is imported and
run as-is, so its requests, pacing, identity and step records are identical. After it finishes an
endpoint, this wrapper:

  - reads extra fields from responses Edition 1 already received (no new requests):
      * extensions declared in `capabilities.extensions` of the server/discover or initialize result
      * the share of listed tools carrying a non-empty `annotations` object
      * per-tool JSON size of `inputSchema` (bytes, compact UTF-8), and `outputSchema` presence
  - sends at most two new requests, only while the endpoint's total stays at or below 8:
      a. `skills/list`, only if `io.modelcontextprotocol/skills` is declared and the handshake succeeded
      b. `GET <mcp-url>/server-card` (Accept: application/mcp-server-card+json, application/json;q=0.9)

New requests are kept apart from Edition 1's (`rec["meta_steps"]`), so Edition 1's classifier sees
exactly the same input as in Edition 1. No tool is ever called (the only tools/call is Edition 1's
non-existent canary).

Usage:
  python probe_e11.py --sample ../../production-mcp-reliability-crisis/data/frame/sample.csv --round 1
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
ED1_HARNESS = STUDY_DIR.parent / "production-mcp-reliability-crisis" / "harness"
sys.path.insert(0, str(ED1_HARNESS))

import probe as ed1  # noqa: E402  (Edition 1 harness, unchanged)
from common import HARNESS_VERSION as ED1_VERSION  # noqa: E402

E11_VERSION = "1.1.0"
MAX_REQUESTS = 8
SKILLS_EXT = "io.modelcontextprotocol/skills"
CARD_ACCEPT = "application/mcp-server-card+json, application/json;q=0.9"
RAW_DIR = STUDY_DIR / "data" / "raw"


def handshake_result(steps: dict, obs: dict) -> dict:
    if obs.get("era") == "modern":
        s = steps.get("discover")
    else:
        s = steps.get("initialize_retry") or steps.get("initialize")
    res = ((s or {}).get("json") or {}).get("result")
    return res if isinstance(res, dict) else {}


def extensions_declared(res: dict) -> list[str] | None:
    caps = res.get("capabilities")
    if not isinstance(caps, dict):
        return None
    ext = caps.get("extensions")
    if not isinstance(ext, dict):
        return []
    return sorted(str(k) for k in ext.keys())


def tool_metadata(steps: dict) -> dict | None:
    res = ((steps.get("tools_list") or {}).get("json") or {}).get("result")
    if not isinstance(res, dict) or not isinstance(res.get("tools"), list):
        return None
    tools = [t for t in res["tools"] if isinstance(t, dict)]
    sizes = [len(json.dumps(t.get("inputSchema"), separators=(",", ":"), ensure_ascii=False).encode())
             for t in tools if isinstance(t.get("inputSchema"), dict)]
    return {
        "tool_count": len(tools),
        "annotated": sum(isinstance(t.get("annotations"), dict) and bool(t["annotations"]) for t in tools),
        "has_output_schema": sum(isinstance(t.get("outputSchema"), dict) for t in tools),
        "has_title": sum(bool(t.get("title")) for t in tools),
        "input_schema_bytes": sizes,
    }


def card_summary(step: dict) -> dict:
    j = step.get("json")
    out = {"status": step.get("status"), "error": step.get("error"),
           "content_type": step.get("content_type"), "json_object": isinstance(j, dict)}
    if isinstance(j, dict):
        problems = []
        if not (isinstance(j.get("$schema"), str) and "server-card" in j["$schema"].lower()):
            problems.append("$schema")
        for f in ("name", "version", "description"):
            if not (isinstance(j.get(f), str) and j[f].strip()):
                problems.append(f)
        out["problems"] = problems
        out["valid_v1"] = not problems
    return out


async def probe_endpoint_e11(client, url: str) -> dict:
    result = await ED1_PROBE(client, url)
    steps, obs = result["steps"], result["obs"]
    meta: dict = {"core_requests": len(steps)}
    meta_steps: dict = {}

    res = handshake_result(steps, obs)
    meta["extensions"] = extensions_declared(res) if res else None
    meta["tools"] = tool_metadata(steps)

    budget = MAX_REQUESTS - len(steps)
    hs_ok = bool(res)
    if hs_ok and meta["extensions"] and SKILLS_EXT in meta["extensions"] and budget > 0:
        if obs.get("era") == "modern":
            headers = ed1.modern_headers("skills/list")
            body = {"jsonrpc": "2.0", "id": 4, "method": "skills/list", "params": {"_meta": ed1.modern_meta()}}
        else:
            hs = obs.get("handshake") or {}
            sess = (steps.get("initialize_retry") or steps.get("initialize") or {}).get("headers", {}).get("mcp-session-id")
            headers = ed1.legacy_headers(hs.get("protocol_version"), sess)
            body = {"jsonrpc": "2.0", "id": 4, "method": "skills/list", "params": {}}
        s = await ed1.http_call(client, "POST", url, headers=headers, body=body, rpc_id=4)
        meta_steps["skills_list"] = s
        r = (s.get("json") or {}).get("result")
        meta["skills"] = {
            "status": s.get("status"),
            "result": isinstance(r, dict),
            "skill_count": len(r["skills"]) if isinstance(r, dict) and isinstance(r.get("skills"), list) else None,
            "error_code": s.get("rpc", {}).get("error_code"),
        }
        budget -= 1

    all_network_failed = steps and all(ed1.network_failed(s) or s.get("error") == "timeout" for s in steps.values())
    if budget > 0 and not all_network_failed:
        card_url = url.rstrip("/") + "/server-card"
        s = await ed1.http_call(client, "GET", card_url, headers={"Accept": CARD_ACCEPT})
        meta_steps["server_card"] = s
        meta["server_card"] = card_summary(s)
        budget -= 1
    else:
        meta["server_card"] = {"skipped": "budget" if budget <= 0 else "unreachable"}

    meta["total_requests"] = len(steps) + len(meta_steps)
    result["meta"] = meta
    result["meta_steps"] = meta_steps
    return result


ED1_PROBE = ed1.probe_endpoint
_ed1_strip = ed1.strip_for_output


def strip_for_output(result: dict) -> dict:
    _ed1_strip(result)
    for s in result.get("meta_steps", {}).values():
        s.pop("json", None)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--round", required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--allow-private", action="store_true", help="tests only")
    a = ap.parse_args()
    with open(a.sample, encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    if a.limit:
        rows = rows[: a.limit]
    # Route Edition 1's runner through the wrapper; everything else in it is unchanged.
    ed1.probe_endpoint = probe_endpoint_e11
    ed1.strip_for_output = strip_for_output
    ed1.RAW_DIR = RAW_DIR
    ed1.HARNESS_VERSION = f"{E11_VERSION} (core {ED1_VERSION})"
    asyncio.run(ed1.run(rows, a.round, a.concurrency, a.allow_private))


if __name__ == "__main__":
    main()
