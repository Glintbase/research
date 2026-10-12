"""Classify raw probe records into the pre-registered outcome categories.

Input:  data/raw/round_<name>/*.json   (not published: contains body snippets)
Output: data/round_<name>.jsonl         (published: derived fields only)

Primary status (exactly one per endpoint), checked in this order:
  excluded           opted out or resolves to a private address
  unreachable        every request failed below HTTP (DNS, connect, TLS, timeout)
  auth_compliant     401 with a Bearer WWW-Authenticate challenge AND valid RFC 9728 metadata
  auth_noncompliant  401 (or 403 + WWW-Authenticate) without that
  ok                 handshake (server/discover or initialize result) AND tools/list returned tools[]
  handshake_only     handshake succeeded but tools/list did not
  modern_rejected    modern server (modern error code) that rejected our requests
  legacy_sse         deprecated HTTP+SSE transport detected via `endpoint` event (not probed further)
  jsonrpc_error      speaks JSON-RPC but rejected initialize (both versions)
  payment_required   HTTP 402 on the protocol requests (paid or disabled deployment)
  server_error       5xx or 429 on the protocol requests
  not_mcp            anything else (HTML, 404, non-JSON-RPC body, ...)

Usage: python classify.py --round 1
"""

from __future__ import annotations

import argparse
import json

from common import DATA_DIR, RAW_DIR, host_of, write_jsonl

NETWORK_ERRORS = {"dns_error", "connect_error", "tls_error", "timeout", "redirect_to_private_address"}
PROTOCOL_STEPS = ("discover", "initialize", "initialize_retry", "sse_get")


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def classify(rec: dict) -> dict:
    out = {
        "url": rec["url"],
        "host": host_of(rec["url"]),
        "frame_url": rec.get("frame_url"),
        "transport": rec.get("transport"),
        "round": rec.get("round"),
        "probed_at": rec.get("probed_at"),
    }
    if rec.get("excluded"):
        out["primary_status"] = "excluded"
        out["excluded_reason"] = rec["excluded"]
        return out

    steps: dict = rec.get("steps", {})
    obs: dict = rec.get("obs", {})
    proto = [steps[k] for k in PROTOCOL_STEPS if k in steps]
    first = steps.get("discover", {})

    out["discover_status"] = first.get("status")
    out["discover_error"] = first.get("error")
    out["initialize_status"] = (steps.get("initialize_retry") or steps.get("initialize") or {}).get("status")
    out["era"] = obs.get("era")
    out["redirected"] = any(s.get("redirects") for s in steps.values())

    hs = obs.get("handshake") or {}
    out["protocol_version"] = hs.get("protocol_version")
    out["supported_versions"] = hs.get("supported_versions")
    sv = hs.get("supported_versions") or []
    out["dual_era"] = obs.get("era") == "modern" and any(v != "2026-07-28" for v in sv)
    out["capabilities"] = hs.get("capabilities")
    out["server_name"] = hs.get("server_name")
    out["session_issued"] = obs.get("session_issued")
    hs_step = steps.get("discover") if obs.get("era") == "modern" else (steps.get("initialize_retry") or steps.get("initialize"))
    out["handshake_latency_ms"] = hs_step.get("latency_ms") if hs_step and hs else None

    tools = obs.get("tools")
    if tools:
        n = tools["tool_count"]
        out.update(
            tool_count=n,
            tools_paginated=tools["has_next_cursor"],
            pct_tools_strict_schema=pct(tools["strict_schema"], n),
            pct_tools_readonly_declared=pct(tools["readonly_declared"], n),
            pct_tools_destructive_declared=pct(tools["destructive_declared"], n),
            pct_tools_described=pct(tools["has_description"], n),
        )

    canary = steps.get("canary")
    if canary and "status" in canary:
        rpc = canary.get("rpc", {})
        out["canary_http_status"] = canary.get("status")
        out["error_in_channel"] = bool(rpc.get("error_code") is not None or rpc.get("is_error_result"))
        out["canary_error_code"] = rpc.get("error_code")

    auth_path = "prm_valid" in obs
    if auth_path:
        www = obs.get("www_authenticate") or ""
        out["www_authenticate_bearer"] = www.lower().startswith("bearer")
        out["prm_valid"] = obs.get("prm_valid")
        out["auth_after_handshake"] = bool(hs)

    # --- primary status -------------------------------------------------------
    if proto and all(s.get("error") in NETWORK_ERRORS and "status" not in s for s in proto):
        status = "unreachable"
        out["network_error"] = proto[0].get("error")
    elif auth_path:
        status = "auth_compliant" if (out["www_authenticate_bearer"] and out["prm_valid"]) else "auth_noncompliant"
    elif hs and tools is not None:
        status = "ok"
    elif hs:
        status = "handshake_only"
    elif obs.get("era") == "modern":
        status = "modern_rejected"
        out["modern_error_code"] = first.get("rpc", {}).get("error_code")
    elif obs.get("era") == "legacy_sse":
        status = "legacy_sse"
    elif any(s.get("rpc", {}).get("jsonrpc") for s in proto):
        status = "jsonrpc_error"
        last = steps.get("initialize_retry") or steps.get("initialize") or {}
        out["jsonrpc_error_code"] = last.get("rpc", {}).get("error_code")
    elif any(s.get("status") == 402 for s in proto):
        status = "payment_required"
    elif any((s.get("status") or 0) >= 500 or s.get("status") == 429 for s in proto):
        status = "server_error"
    else:
        status = "not_mcp"
    out["primary_status"] = status
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    a = ap.parse_args()
    src = RAW_DIR / f"round_{a.round}"
    rows = []
    for p in sorted(src.glob("*.json")):
        if p.name.startswith("_"):
            continue
        rows.append(classify(json.loads(p.read_text(encoding="utf8"))))
    rows.sort(key=lambda r: r["url"])
    dest = DATA_DIR / f"round_{a.round}.jsonl"
    write_jsonl(dest, rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["primary_status"]] = counts.get(r["primary_status"], 0) + 1
    print(f"{len(rows)} endpoints -> {dest.name}")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:20s} {v}")


if __name__ == "__main__":
    main()
