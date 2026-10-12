"""Fixture-server tests for probe.py + classify.py.

Runs a local aiohttp server exposing one route per server behaviour, probes every route,
classifies the results, and checks each lands in the expected category.

Usage: python test_probe.py
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import uuid

from aiohttp import web

import classify
import probe
from common import RAW_DIR

TOOLS = [
    {"name": "get_weather", "description": "Weather", "annotations": {"readOnlyHint": True},
     "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
    {"name": "delete_note", "description": "Delete", "annotations": {"destructiveHint": True},
     "inputSchema": {"type": "object", "properties": {"id": {}}}},  # untyped property -> not strict
]


def rpc_result(req_id, result):
    return web.json_response({"jsonrpc": "2.0", "id": req_id, "result": result})


def rpc_error(req_id, code, msg, status=200):
    return web.json_response({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}, status=status)


def sse_response(payload: dict, headers=None):
    body = f"event: message\ndata: {json.dumps(payload)}\n\n"
    return web.Response(text=body, content_type="text/event-stream", headers=headers or {})


# --- modern (2026-07-28 only, stateless) ------------------------------------
async def modern(request: web.Request):
    body = await request.json()
    rid = body.get("id")
    meta = (body.get("params") or {}).get("_meta") or {}
    if request.headers.get("MCP-Protocol-Version") != "2026-07-28" or "Mcp-Method" not in request.headers:
        return rpc_error(rid, -32020, "Header mismatch: missing required headers", status=400)
    if meta.get("io.modelcontextprotocol/protocolVersion") != "2026-07-28":
        return rpc_error(rid, -32602, "missing _meta", status=400)
    m = body["method"]
    if m == "server/discover":
        return rpc_result(rid, {"resultType": "complete", "supportedVersions": ["2026-07-28"],
                                "capabilities": {"tools": {}}, "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "fx-modern", "version": "1"}}})
    if m == "tools/list":
        return rpc_result(rid, {"resultType": "complete", "tools": TOOLS})
    if m == "tools/call":
        return rpc_error(rid, -32602, "Unknown tool")
    return rpc_error(rid, -32601, "Method not found", status=404)


# --- legacy stateful (2025-11-25 style, sessions, SSE responses) ------------
SESSIONS: set[str] = set()


async def legacy_session(request: web.Request):
    body = await request.json()
    rid = body.get("id")
    m = body.get("method")
    if m == "initialize":
        sid = uuid.uuid4().hex
        SESSIONS.add(sid)
        return sse_response({"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2025-06-18", "capabilities": {"tools": {}, "prompts": {}},
            "serverInfo": {"name": "fx-legacy", "version": "1"}}}, headers={"Mcp-Session-Id": sid})
    if request.headers.get("Mcp-Session-Id") not in SESSIONS:
        return web.json_response({"jsonrpc": "2.0", "id": None,
                                  "error": {"code": -32000, "message": "Bad Request: No valid session ID provided"}}, status=400)
    if m == "notifications/initialized":
        return web.Response(status=202)
    if m == "tools/list":
        return sse_response({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}})
    if m == "tools/call":
        return sse_response({"jsonrpc": "2.0", "id": rid, "result": {"isError": True, "content": [{"type": "text", "text": "Unknown tool"}]}})
    return rpc_error(rid, -32601, "Method not found")


# --- legacy that rejects 2025-11-25 but accepts 2025-03-26 -------------------
async def legacy_old_version(request: web.Request):
    body = await request.json()
    rid = body.get("id")
    m = body.get("method")
    if m == "initialize":
        if body["params"]["protocolVersion"] != "2025-03-26":
            return rpc_error(rid, -32602, "Unsupported protocol version")
        return rpc_result(rid, {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "fx-old"}})
    if m == "notifications/initialized":
        return web.Response(status=202)
    if m == "tools/list":
        return rpc_result(rid, {"tools": TOOLS})
    if m == "tools/call":
        # HTTP-200 plain-text masquerade instead of an in-channel error
        return web.Response(text="Error: tool not found", content_type="text/plain")
    return rpc_error(rid, -32601, "Method not found")


# --- legacy stateless JSON server that answers unknown methods with 404/-32601 ----
async def legacy_404(request: web.Request):
    body = await request.json()
    rid = body.get("id")
    m = body.get("method")
    if m == "initialize":
        return rpc_result(rid, {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "fx-404"}})
    if m == "notifications/initialized":
        return web.Response(status=202)
    if m == "tools/list":
        return rpc_result(rid, {"tools": TOOLS})
    if m == "tools/call":
        return rpc_error(rid, -32602, "Unknown tool")
    return rpc_error(rid, -32601, "Method not found", status=404)


# --- stateful server refusing 2026-07-28 with UnsupportedProtocolVersion ------
async def legacy_32022(request: web.Request):
    body = await request.json()
    rid = body.get("id")
    m = body.get("method")
    if m == "server/discover":
        return web.json_response({"jsonrpc": "2.0", "id": rid, "error": {"code": -32022, "message": "Unsupported protocol version",
                                  "data": {"supported": ["2025-11-25"], "requested": "2026-07-28"}}}, status=400)
    return await legacy_404(request)


# --- deprecated HTTP+SSE ------------------------------------------------------
async def sse_only_post(request):
    return web.Response(status=405, text="Method Not Allowed")


async def sse_only_get(request):
    resp = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
    await resp.prepare(request)
    await resp.write(b"event: endpoint\ndata: /messages?sessionId=abc\n\n")
    await asyncio.sleep(30)  # keep stream open like a real server
    return resp


# --- auth ----------------------------------------------------------------------
async def auth_ok(request):
    base = f"http://{request.host}"
    return web.Response(status=401, headers={
        "WWW-Authenticate": f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource/auth-ok"'})


async def auth_ok_prm(request):
    return web.json_response({"resource": f"http://{request.host}/auth-ok",
                              "authorization_servers": ["https://auth.example.com"]})


async def auth_bad(request):
    return web.Response(status=401, text="Unauthorized")


# --- not MCP / broken ----------------------------------------------------------
async def html(request):
    return web.Response(text="<html><body>Welcome</body></html>", content_type="text/html")


async def broken(request):
    return web.Response(status=502, text="Bad Gateway")


async def paid(request):
    return web.json_response({"error": {"code": "402", "message": "Payment required"}}, status=402)


async def slow(request):
    await asyncio.sleep(60)
    return web.Response(text="late")


EXPECTED = {
    "/modern": ("ok", "modern"),
    "/legacy-session": ("ok", "legacy"),
    "/legacy-old": ("ok", "legacy"),
    "/legacy-404": ("ok", "legacy"),
    "/legacy-32022": ("ok", "legacy"),
    "/sse-only": ("legacy_sse", "legacy_sse"),
    "/auth-ok": ("auth_compliant", None),
    "/auth-bad": ("auth_noncompliant", None),
    "/html": ("not_mcp", None),
    "/broken": ("server_error", None),
    "/slow": ("unreachable", None),
    "/paid": ("payment_required", None),
}


async def main() -> int:
    app = web.Application()
    app.router.add_post("/modern", modern)
    app.router.add_post("/legacy-session", legacy_session)
    app.router.add_post("/legacy-old", legacy_old_version)
    app.router.add_post("/legacy-404", legacy_404)
    app.router.add_post("/legacy-32022", legacy_32022)
    app.router.add_post("/sse-only", sse_only_post)
    app.router.add_get("/sse-only", sse_only_get)
    app.router.add_route("*", "/auth-ok", auth_ok)
    app.router.add_get("/.well-known/oauth-protected-resource/auth-ok", auth_ok_prm)
    app.router.add_route("*", "/auth-bad", auth_bad)
    app.router.add_route("*", "/html", html)
    app.router.add_route("*", "/broken", broken)
    app.router.add_route("*", "/slow", slow)
    app.router.add_route("*", "/paid", paid)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    round_name = "test"
    shutil.rmtree(RAW_DIR / f"round_{round_name}", ignore_errors=True)
    rows = [{"url": f"http://127.0.0.1:{port}{p}", "probe_url": f"http://127.0.0.1:{port}{p}"} for p in EXPECTED]
    await probe.run(rows, round_name, concurrency=8, allow_private=True)
    await runner.cleanup()

    failures = 0
    results = {}
    for p in (RAW_DIR / f"round_{round_name}").glob("*.json"):
        if p.name.startswith("_"):
            continue
        r = classify.classify(json.loads(p.read_text(encoding="utf8")))
        results[r["url"].split(str(port), 1)[1]] = r
    for path, (want_status, want_era) in EXPECTED.items():
        r = results.get(path, {})
        got = (r.get("primary_status"), r.get("era"))
        ok = got[0] == want_status and (want_era is None or got[1] == want_era)
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'} {path:16s} expected={want_status}/{want_era} got={got[0]}/{got[1]}")

    # Feature checks
    checks = [
        ("/modern", "error_in_channel", True),
        ("/legacy-session", "error_in_channel", True),
        ("/legacy-session", "session_issued", True),
        ("/legacy-old", "error_in_channel", False),
        ("/legacy-old", "protocol_version", "2025-03-26"),
        ("/modern", "tool_count", 2),
        ("/modern", "pct_tools_strict_schema", 50.0),
        ("/modern", "pct_tools_readonly_declared", 50.0),
        ("/modern", "supported_versions", ["2026-07-28"]),
    ]
    for path, field, want in checks:
        got = results.get(path, {}).get(field)
        ok = got == want
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'} {path:16s} {field}={got!r} (expected {want!r})")

    shutil.rmtree(RAW_DIR / f"round_{round_name}", ignore_errors=True)
    print(f"\n{'ALL PASSED' if not failures else f'{failures} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
