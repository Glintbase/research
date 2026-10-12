"""Dual-era MCP endpoint probe (metadata and protocol only).

Per endpoint, at most 8 requests, following the client-side backward-compatibility
procedure in MCP 2026-07-28 (basic/transports/streamable-http#backward-compatibility):

  1. server/discover            modern (2026-07-28) request with per-request _meta + headers
  -- if the server is modern --
  2. tools/list                 modern
  3. tools/call (canary)        modern; non-existent tool, checks in-channel errors
  -- otherwise, legacy (initialize-based, 2025-11-25 and earlier) --
  2. initialize                 protocolVersion 2025-11-25 (server may negotiate down);
                                retried once with 2025-03-26 if rejected with a JSON-RPC error
  3. notifications/initialized  with Mcp-Session-Id if issued
  4. tools/list
  5. tools/call (canary)
  -- if initialize fails without a JSON-RPC answer --
  6. GET (Accept: text/event-stream), wait for the HTTP+SSE `endpoint` event (detect only)
  -- if any step answered 401 --
  7-8. GET protected-resource metadata (RFC 9728)

No real tool is ever called. No security payloads are sent.

Usage:
  python probe.py --sample ../data/frame/sample.csv --round 1
  python probe.py --urls https://example.com/mcp --round pilot
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

import httpx

from common import (
    CANARY_TOOL,
    CLIENT_INFO,
    HARNESS_VERSION,
    HEADER_VERSIONS,
    LEGACY_VERSION,
    MAX_BODY_BYTES,
    MODERN_ERROR_CODES,
    MODERN_VERSION,
    RAW_DIR,
    REQUEST_TIMEOUT_S,
    SNIPPET_BYTES,
    SSE_FIRST_EVENT_TIMEOUT_S,
    USER_AGENT,
    git_sha,
    host_of,
    host_opted_out,
    is_private_address,
    load_optout,
)

KEEP_HEADERS = {
    "content-type",
    "www-authenticate",
    "mcp-session-id",
    "mcp-protocol-version",
    "server",
    "location",
    "retry-after",
    "cf-ray",
    "x-powered-by",
    "via",
}


class PrivateAddressError(Exception):
    pass


# Test-only: lets fixture servers on http://127.0.0.1 serve protected-resource metadata.
ALLOW_INSECURE_METADATA = False


# ---------------------------------------------------------------------------
# Low-level HTTP with bounded, incremental reading (SSE streams may stay open)
# ---------------------------------------------------------------------------

def parse_sse_messages(text: str) -> list[dict]:
    """Return JSON objects carried in SSE `data:` fields (one object per event)."""
    out = []
    for block in re.split(r"\r?\n\r?\n", text):
        data_lines = [l[5:].lstrip() for l in re.split(r"\r?\n", block) if l.startswith("data:")]
        if not data_lines:
            continue
        try:
            obj = json.loads("\n".join(data_lines))
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def pick_response(messages: list[dict], rpc_id) -> dict | None:
    for m in messages:
        if m.get("id") == rpc_id and ("result" in m or "error" in m):
            return m
    for m in messages:
        if "result" in m or "error" in m:
            return m
    return None


async def http_call(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict,
    body: dict | None = None,
    rpc_id=None,
    sse_detect: bool = False,
) -> dict:
    """Perform one request. Returns a step record (never raises)."""
    rec: dict = {"http_method": method, "url": url, "started_at": time.time()}
    t0 = time.perf_counter()
    buf = bytearray()

    async def run():
        req_headers = {"User-Agent": USER_AGENT, **headers}
        content = json.dumps(body).encode() if body is not None else None
        async with client.stream(method, url, headers=req_headers, content=content) as resp:
            rec["status"] = resp.status_code
            rec["final_url"] = str(resp.url)
            rec["redirects"] = len(resp.history)
            rec["headers"] = {k.lower(): v for k, v in resp.headers.items() if k.lower() in KEEP_HEADERS}
            ctype = resp.headers.get("content-type", "").lower()
            rec["content_type"] = ctype
            is_sse = "text/event-stream" in ctype
            rec["sse"] = is_sse
            async for chunk in resp.aiter_bytes():
                buf.extend(chunk)
                if len(buf) >= MAX_BODY_BYTES:
                    rec["truncated"] = True
                    break
                if is_sse:
                    text = buf.decode("utf8", "replace")
                    if sse_detect and re.search(r"\r?\n\r?\n", text):
                        break  # first complete event is all we need
                    if not sse_detect and pick_response(parse_sse_messages(text), rpc_id):
                        break  # got the JSON-RPC response; don't wait for stream close

    limit = SSE_FIRST_EVENT_TIMEOUT_S if sse_detect else REQUEST_TIMEOUT_S
    try:
        await asyncio.wait_for(run(), timeout=limit)
    except asyncio.TimeoutError:
        rec["error"] = "timeout" if "status" not in rec else "body_timeout"
    except PrivateAddressError:
        rec["error"] = "redirect_to_private_address"
    except httpx.ConnectError as e:
        msg = str(e).lower()
        if "ssl" in msg or "certificate" in msg or "tls" in msg:
            rec["error"] = "tls_error"
        elif "getaddrinfo" in msg or "name or service" in msg or "nodename" in msg or "11001" in msg:
            rec["error"] = "dns_error"
        else:
            rec["error"] = "connect_error"
    except httpx.TooManyRedirects:
        rec["error"] = "too_many_redirects"
    except httpx.HTTPError as e:
        rec["error"] = f"http_error:{type(e).__name__}"
    except Exception as e:  # defensive: never let one endpoint kill the run
        rec["error"] = f"exception:{type(e).__name__}"
    rec["latency_ms"] = round((time.perf_counter() - t0) * 1000)

    text = buf.decode("utf8", "replace")
    rec["body_snippet"] = text[:SNIPPET_BYTES]
    rec["body_bytes"] = len(buf)
    parsed = None
    if rec.get("sse"):
        msgs = parse_sse_messages(text)
        rec["sse_events"] = len(msgs)
        parsed = pick_response(msgs, rpc_id) if not sse_detect else None
        if sse_detect:
            m = re.search(r"event:\s*endpoint\s*\r?\ndata:\s*(\S+)", text)
            rec["sse_endpoint_event"] = m.group(1) if m else None
    else:
        try:
            obj = json.loads(text) if text.strip() else None
            parsed = obj if isinstance(obj, dict) else None
        except ValueError:
            parsed = None
    rec["json"] = parsed
    p = parsed or {}
    res = p.get("result")
    e = p.get("error")
    rec["rpc"] = {
        "jsonrpc": p.get("jsonrpc") == "2.0",
        "has_result": isinstance(res, dict),
        "is_error_result": isinstance(res, dict) and res.get("isError") is True,
        "error_code": e.get("code") if isinstance(e, dict) else None,
        "error_message": (str(e.get("message"))[:200] if isinstance(e, dict) else None),
    }
    return rec


# ---------------------------------------------------------------------------
# MCP message builders
# ---------------------------------------------------------------------------

def modern_meta() -> dict:
    return {
        "io.modelcontextprotocol/protocolVersion": MODERN_VERSION,
        "io.modelcontextprotocol/clientInfo": CLIENT_INFO,
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def modern_headers(method: str, name: str | None = None) -> dict:
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": MODERN_VERSION,
        "Mcp-Method": method,
    }
    if name is not None:
        h["Mcp-Name"] = name
    return h


def legacy_headers(version: str | None, session: str | None) -> dict:
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if version in HEADER_VERSIONS:
        h["MCP-Protocol-Version"] = version
    if session:
        h["Mcp-Session-Id"] = session
    return h


def err_code(step: dict) -> int | None:
    j = step.get("json") or {}
    e = j.get("error")
    return e.get("code") if isinstance(e, dict) and isinstance(e.get("code"), int) else None


def has_result(step: dict) -> bool:
    j = step.get("json") or {}
    return isinstance(j.get("result"), dict)


def is_auth_challenge(step: dict) -> bool:
    s = step.get("status")
    return s == 401 or (s == 403 and "www-authenticate" in step.get("headers", {}))


def is_modern(step: dict) -> bool:
    """Is this server modern AND unwilling to talk legacy, judged from its server/discover reply?

    - A DiscoverResult (supportedVersions) means modern.
    - -32020 / -32021 are modern errors about our request; there is no legacy fallback for them.
    - -32022 (UnsupportedProtocolVersion) means "retry with a supported version": a dual-era
      client falls back to initialize, so it is NOT treated as modern-only here.
    - 404 + -32601 on server/discover means the method is not implemented. Modern servers MUST
      implement server/discover, so this identifies a legacy server (Deviation 2).
    """
    j = step.get("json") or {}
    if isinstance(j.get("result"), dict) and "supportedVersions" in j["result"]:
        return True
    return err_code(step) in (MODERN_ERROR_CODES - {-32022})


def network_failed(step: dict) -> bool:
    return step.get("error") in {"dns_error", "connect_error", "tls_error", "redirect_to_private_address"}


# ---------------------------------------------------------------------------
# Feature extraction (kept small; raw tool lists are not stored)
# ---------------------------------------------------------------------------

def schema_is_strict(schema) -> bool:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return False
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        return False
    return all(
        isinstance(p, dict) and any(k in p for k in ("type", "enum", "const", "anyOf", "oneOf", "allOf", "$ref"))
        for p in props.values()
    )


def summarize_tools(step: dict) -> dict | None:
    j = step.get("json") or {}
    res = j.get("result")
    if not isinstance(res, dict) or not isinstance(res.get("tools"), list):
        return None
    tools = [t for t in res["tools"] if isinstance(t, dict)]
    ann = [t.get("annotations") if isinstance(t.get("annotations"), dict) else {} for t in tools]
    return {
        "tool_count": len(tools),
        "has_next_cursor": bool(res.get("nextCursor")),
        "strict_schema": sum(schema_is_strict(t.get("inputSchema")) for t in tools),
        "has_input_schema": sum(isinstance(t.get("inputSchema"), dict) for t in tools),
        "readonly_declared": sum(isinstance(a.get("readOnlyHint"), bool) for a in ann),
        "readonly_true": sum(a.get("readOnlyHint") is True for a in ann),
        "destructive_declared": sum(isinstance(a.get("destructiveHint"), bool) for a in ann),
        "has_description": sum(bool(t.get("description")) for t in tools),
    }


def summarize_init(step: dict) -> dict:
    res = (step.get("json") or {}).get("result") or {}
    caps = res.get("capabilities") if isinstance(res.get("capabilities"), dict) else {}
    info = res.get("serverInfo") or (res.get("_meta") or {}).get("io.modelcontextprotocol/serverInfo") or {}
    return {
        "protocol_version": res.get("protocolVersion"),
        "supported_versions": res.get("supportedVersions"),
        "capabilities": sorted(k for k in caps.keys()),
        "server_name": info.get("name") if isinstance(info, dict) else None,
        "server_version": info.get("version") if isinstance(info, dict) else None,
    }


def parse_resource_metadata(www_auth: str | None) -> str | None:
    if not www_auth:
        return None
    m = re.search(r'resource_metadata\s*=\s*"([^"]+)"', www_auth) or re.search(
        r"resource_metadata\s*=\s*([^\s,]+)", www_auth
    )
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Per-endpoint procedure
# ---------------------------------------------------------------------------

async def probe_endpoint(client: httpx.AsyncClient, url: str) -> dict:
    steps: dict[str, dict] = {}
    obs: dict = {}

    async def auth_followup(challenge_step: dict):
        www = challenge_step.get("headers", {}).get("www-authenticate")
        obs["www_authenticate"] = www[:300] if www else None
        candidates = []
        rm = parse_resource_metadata(www)
        if rm:
            candidates.append(urljoin(url, rm))
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        path = parts.path.rstrip("/")
        if path:
            candidates.append(f"{origin}/.well-known/oauth-protected-resource{path}")
        candidates.append(f"{origin}/.well-known/oauth-protected-resource")
        seen = []
        for c in candidates:
            if c in seen or len(seen) >= 2 or not (c.startswith("https://") or ALLOW_INSECURE_METADATA):
                continue
            seen.append(c)
            s = await http_call(client, "GET", c, headers={"Accept": "application/json"})
            steps[f"prm_{len(seen)}"] = s
            j = s.get("json") or {}
            if (
                s.get("status") == 200
                and isinstance(j.get("resource"), str)
                and isinstance(j.get("authorization_servers"), list)
                and j["authorization_servers"]
            ):
                obs["prm_valid"] = True
                obs["prm_url"] = c
                return
        obs["prm_valid"] = False

    # 1. Modern discovery
    discover = await http_call(
        client, "POST", url,
        headers=modern_headers("server/discover"),
        body={"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": modern_meta()}},
        rpc_id=1,
    )
    steps["discover"] = discover
    if network_failed(discover):
        return {"steps": steps, "obs": obs}
    if is_auth_challenge(discover):
        await auth_followup(discover)
        return {"steps": steps, "obs": obs}

    if is_modern(discover):
        obs["era"] = "modern"
        if has_result(discover):
            obs["handshake"] = summarize_init(discover)
        tl = await http_call(
            client, "POST", url,
            headers=modern_headers("tools/list"),
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": modern_meta()}},
            rpc_id=2,
        )
        steps["tools_list"] = tl
        obs["tools"] = summarize_tools(tl)
        canary = await http_call(
            client, "POST", url,
            headers=modern_headers("tools/call", CANARY_TOOL),
            body={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": CANARY_TOOL, "arguments": {}, "_meta": modern_meta()}},
            rpc_id=3,
        )
        steps["canary"] = canary
        if is_auth_challenge(tl) or is_auth_challenge(canary):
            await auth_followup(tl if is_auth_challenge(tl) else canary)
        return {"steps": steps, "obs": obs}

    # 2. Legacy initialize
    if err_code(discover) == -32022:
        obs["modern_version_unsupported"] = True  # modern error steering us to an older version
    init = await http_call(
        client, "POST", url,
        headers=legacy_headers(None, None),
        body={"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": LEGACY_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}},
        rpc_id=1,
    )
    steps["initialize"] = init
    if (init.get("json") or {}).get("error") and not has_result(init):
        # Some older servers reject an unknown protocolVersion instead of negotiating down.
        init = await http_call(
            client, "POST", url,
            headers=legacy_headers(None, None),
            body={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": CLIENT_INFO}},
            rpc_id=1,
        )
        steps["initialize_retry"] = init
    if is_auth_challenge(init):
        await auth_followup(init)
        return {"steps": steps, "obs": obs}

    if has_result(init):
        obs["era"] = "legacy"
        obs["handshake"] = summarize_init(init)
        version = obs["handshake"].get("protocol_version")
        session = init.get("headers", {}).get("mcp-session-id")
        obs["session_issued"] = bool(session)
        steps["initialized"] = await http_call(
            client, "POST", url,
            headers=legacy_headers(version, session),
            body={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        tl = await http_call(
            client, "POST", url,
            headers=legacy_headers(version, session),
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            rpc_id=2,
        )
        steps["tools_list"] = tl
        obs["tools"] = summarize_tools(tl)
        canary = await http_call(
            client, "POST", url,
            headers=legacy_headers(version, session),
            body={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": CANARY_TOOL, "arguments": {}}},
            rpc_id=3,
        )
        steps["canary"] = canary
        if is_auth_challenge(tl) or is_auth_challenge(canary):
            await auth_followup(tl if is_auth_challenge(tl) else canary)
        return {"steps": steps, "obs": obs}

    # 3. Legacy HTTP+SSE transport detection (only when no JSON-RPC answer came back)
    if not (init.get("json") or {}).get("jsonrpc"):
        sse = await http_call(client, "GET", url, headers={"Accept": "text/event-stream"}, sse_detect=True)
        steps["sse_get"] = sse
        if sse.get("sse_endpoint_event"):
            obs["era"] = "legacy_sse"
        elif is_auth_challenge(sse):
            await auth_followup(sse)
    return {"steps": steps, "obs": obs}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def strip_for_output(result: dict) -> dict:
    """Drop parsed JSON bodies from step records (features are already in obs)."""
    for s in result["steps"].values():
        s.pop("json", None)
    return result


async def run(rows: list[dict], round_name: str, concurrency: int, allow_private: bool) -> None:
    global ALLOW_INSECURE_METADATA
    ALLOW_INSECURE_METADATA = allow_private
    out_dir = RAW_DIR / f"round_{round_name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    optout = load_optout()
    sem = asyncio.Semaphore(concurrency)
    host_locks: dict[str, asyncio.Lock] = {}
    private_cache: dict[str, bool] = {}
    loop = asyncio.get_running_loop()

    async def check_private(host: str) -> bool:
        if allow_private:
            return False
        if host not in private_cache:
            private_cache[host] = await loop.run_in_executor(None, is_private_address, host)
        return private_cache[host]

    async def on_request(request: httpx.Request):
        if await check_private(request.url.host):
            raise PrivateAddressError(request.url.host)

    limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(
        follow_redirects=True,
        max_redirects=3,
        timeout=httpx.Timeout(REQUEST_TIMEOUT_S),
        limits=limits,
        event_hooks={"request": [on_request]},
        http2=False,
    ) as client:
        done = 0
        total = len(rows)

        async def one(row: dict):
            nonlocal done
            url = row.get("probe_url") or row["url"]
            key = hashlib.sha256(url.encode()).hexdigest()[:16]
            out = out_dir / f"{key}.json"
            if out.exists():
                done += 1
                return
            host = host_of(url)
            lock = host_locks.setdefault(host, asyncio.Lock())
            async with lock, sem:  # wait for the host first so queued same-host work doesn't hold slots
                record = {
                    "url": url,
                    "frame_url": row.get("url", url),
                    "transport": row.get("transport", ""),
                    "round": round_name,
                    "probed_at": datetime.now(timezone.utc).isoformat(),
                    "harness_version": HARNESS_VERSION,
                }
                if host_opted_out(host, optout):
                    record["excluded"] = "opt_out"
                elif await check_private(host):
                    record["excluded"] = "private_address"
                else:
                    record.update(strip_for_output(await probe_endpoint(client, url)))
                out.write_text(json.dumps(record, ensure_ascii=False), encoding="utf8")
            done += 1
            if done % 50 == 0 or done == total:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {done}/{total}", flush=True)

        await asyncio.gather(*(one(r) for r in rows))

    meta = {
        "round": round_name,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "endpoints": len(rows),
        "concurrency": concurrency,
        "harness_version": HARNESS_VERSION,
        "harness_git_sha": git_sha(),
        "user_agent": USER_AGENT,
        "python": sys.version.split()[0],
        "httpx": httpx.__version__,
    }
    (out_dir / "_round_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf8")


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--sample", help="CSV with url/probe_url/transport columns")
    src.add_argument("--urls", nargs="+")
    ap.add_argument("--round", required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="probe only the first N rows (pilot)")
    ap.add_argument("--allow-private", action="store_true", help="tests only")
    a = ap.parse_args()
    if a.sample:
        with open(a.sample, encoding="utf8") as f:
            rows = list(csv.DictReader(f))
    else:
        rows = [{"url": u, "probe_url": u} for u in a.urls]
    if a.limit:
        rows = rows[: a.limit]
    asyncio.run(run(rows, a.round, a.concurrency, a.allow_private))


if __name__ == "__main__":
    main()
