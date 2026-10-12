"""Validation gate: independent re-check of 30 stratified endpoints.

Draws 30 endpoints from round 1 (seed 20261012), spread across the observed
primary statuses, and re-checks each with a minimal independent client: plain
synchronous requests written from the spec, sharing no code with probe.py's
request logic. Writes data/validation.csv with both verdicts and an agreement flag.
The reviewer then inspects every disagreement by hand, plus a sample of agreements,
and records the final call in the `reviewer_verdict` column.

Independent verdict rules (simplified from the spec, deliberately coarse):
  network failure on both POSTs                 -> unreachable
  401 (or 403 + WWW-Authenticate)               -> auth (then compliant if Bearer + metadata JSON)
  402                                           -> payment_required
  discover result with supportedVersions        -> modern handshake; tools/list result -> ok
  initialize result                             -> legacy handshake; tools/list result -> ok
  JSON-RPC body without result                  -> jsonrpc_error / modern_rejected
  5xx / 429                                     -> server_error
  GET returns `event: endpoint`                 -> legacy_sse
  otherwise                                     -> not_mcp

Usage: python validate.py --round 1 [--n 30]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

from common import DATA_DIR, USER_AGENT, read_jsonl

UA = {"User-Agent": USER_AGENT}
META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "GlintbaseResearch-validate", "version": "1"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


def post(url, body, headers, timeout=12):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={**UA, "Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(256 * 1024).decode("utf8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(64 * 1024).decode("utf8", "replace")
    except Exception as e:
        return None, {}, f"ERR {type(e).__name__}"


def get(url, headers, timeout=8):
    req = urllib.request.Request(url, headers={**UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(4096).decode("utf8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception as e:
        return None, {}, f"ERR {type(e).__name__}"


def body_json(text):
    try:
        return json.loads(text)
    except ValueError:
        for m in re.finditer(r"^data:\s*(\{.*\})\s*$", text, re.M):
            try:
                return json.loads(m.group(1))
            except ValueError:
                pass
    return None


def hdr(h, name):
    for k, v in h.items():
        if k.lower() == name:
            return v
    return None


def independent_verdict(url: str) -> tuple[str, str]:
    s1, h1, b1 = post(url, {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}},
                      {"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "server/discover"})
    j1 = body_json(b1) or {}

    def auth_verdict(h):
        www = hdr(h, "www-authenticate") or ""
        m = re.search(r'resource_metadata="?([^",\s]+)', www)
        parts = urllib.parse.urlsplit(url)
        cands = ([m.group(1)] if m else []) + [
            f"{parts.scheme}://{parts.netloc}/.well-known/oauth-protected-resource{parts.path.rstrip('/')}",
            f"{parts.scheme}://{parts.netloc}/.well-known/oauth-protected-resource"]
        for c in cands[:2]:
            st, _, b = get(urllib.parse.urljoin(url, c), {"Accept": "application/json"})
            prm = body_json(b) or {}
            if st == 200 and prm.get("resource") and prm.get("authorization_servers"):
                return ("auth_compliant" if www.lower().startswith("bearer") else "auth_noncompliant"), f"PRM at {c}"
        return "auth_noncompliant", f"www-authenticate={www[:60]!r}, no valid PRM"

    if s1 == 401 or (s1 == 403 and hdr(h1, "www-authenticate")):
        return auth_verdict(h1)
    if s1 == 402:
        return "payment_required", "402 on discover"
    if isinstance(j1.get("result"), dict) and "supportedVersions" in j1["result"]:
        s2, _, b2 = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": META}},
                         {"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/list"})
        ok = isinstance((body_json(b2) or {}).get("result", {}).get("tools"), list)
        return ("ok" if ok else "handshake_only"), f"modern; tools/list status {s2}"
    code = (j1.get("error") or {}).get("code") if isinstance(j1.get("error"), dict) else None
    modern_err = code in (-32020, -32021, -32022) or (s1 == 404 and code == -32601)

    s3, h3, b3 = post(url, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                                       "clientInfo": {"name": "GlintbaseResearch-validate", "version": "1"}}}, {})
    j3 = body_json(b3) or {}
    if s3 == 401 or (s3 == 403 and hdr(h3, "www-authenticate")):
        return auth_verdict(h3)
    if isinstance(j3.get("result"), dict) and not modern_err:
        sid = hdr(h3, "mcp-session-id")
        ver = j3["result"].get("protocolVersion")
        extra = {}
        if sid:
            extra["Mcp-Session-Id"] = sid
        if ver in ("2025-06-18", "2025-11-25"):
            extra["MCP-Protocol-Version"] = ver
        post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, extra)
        s4, _, b4 = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, extra)
        ok = isinstance(((body_json(b4) or {}).get("result") or {}).get("tools"), list)
        return ("ok" if ok else "handshake_only"), f"legacy {ver}; tools/list status {s4}"
    if modern_err:
        return "modern_rejected", f"modern error {code}"
    if j1.get("jsonrpc") or j3.get("jsonrpc"):
        if s1 == 402 or s3 == 402:
            return "payment_required", "402"
        return "jsonrpc_error", f"discover {s1}, initialize {s3}"
    if s1 is None and s3 is None:
        return "unreachable", f"{b1[:40]} / {b3[:40]}"
    if 402 in (s1, s3):
        return "payment_required", "402"
    if any(s and (s >= 500 or s == 429) for s in (s1, s3)):
        return "server_error", f"discover {s1}, initialize {s3}"
    st, h, b = get(url, {"Accept": "text/event-stream"})
    if "event: endpoint" in b or re.search(r"event:\s*endpoint", b):
        return "legacy_sse", "endpoint event"
    return "not_mcp", f"discover {s1}, initialize {s3}, GET {st}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="1")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261012)
    a = ap.parse_args()
    rows = [r for r in read_jsonl(DATA_DIR / f"round_{a.round}.jsonl") if r["primary_status"] != "excluded"]
    by = defaultdict(list)
    for r in rows:
        by[r["primary_status"]].append(r)
    rng = random.Random(a.seed)
    # Stratified: at least 2 per observed status (if available), rest proportional.
    picks = []
    for st in sorted(by):
        rng.shuffle(by[st])
        picks += by[st][:2]
    rest = [r for st in sorted(by) for r in by[st][2:]]
    rng.shuffle(rest)
    picks += rest[: max(0, a.n - len(picks))]
    picks = picks[: a.n]

    out = []
    agree = 0
    for r in picks:
        verdict, note = independent_verdict(r["url"])
        same = verdict == r["primary_status"]
        agree += same
        out.append({"url": r["url"], "probe_status": r["primary_status"], "independent_status": verdict,
                    "agree": same, "independent_note": note, "reviewer_verdict": "", "reviewer_note": ""})
        print(f"{'=' if same else 'X'} {r['primary_status']:18s} {verdict:18s} {r['url'][:70]}")
    with open(DATA_DIR / "validation.csv", "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nautomatic agreement: {agree}/{len(out)} = {100 * agree / len(out):.1f}%")


if __name__ == "__main__":
    main()
