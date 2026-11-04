"""Fixture tests for the Edition 1.1 metadata additions.

Checks that (1) Edition 1's step records and classification are untouched by the wrapper,
(2) skills/list is sent only when the skills extension is declared, (3) the server-card fetch
and tool metadata are recorded, and (4) no endpoint exceeds 8 requests.

Usage: python test_probe_e11.py   (needs aiohttp)
"""

from __future__ import annotations

import asyncio
import json
import sys

import httpx
from aiohttp import web

import probe_e11 as e11
from probe_e11 import ed1

sys.path.insert(0, str(e11.ED1_HARNESS))
import classify as ed1_classify  # noqa: E402

TOOLS = [
    {"name": "a", "description": "A", "annotations": {"readOnlyHint": True},
     "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}}},
    {"name": "b", "description": "B", "inputSchema": {"type": "object"}, "outputSchema": {"type": "object"}},
]
CARD = {"$schema": "https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json",
        "name": "fx", "version": "1", "description": "fixture"}
calls: dict[str, list[str]] = {}


def res(rid, r):
    return web.json_response({"jsonrpc": "2.0", "id": rid, "result": r})


def make_modern(with_skills: bool):
    async def h(request: web.Request):
        body = await request.json()
        calls.setdefault(request.path, []).append(body["method"])
        rid, m = body.get("id"), body["method"]
        caps = {"tools": {}, "resources": {}}
        if with_skills:
            caps["extensions"] = {"io.modelcontextprotocol/skills": {}}
        if m == "server/discover":
            return res(rid, {"resultType": "complete", "supportedVersions": ["2026-07-28"], "capabilities": caps})
        if m == "tools/list":
            return res(rid, {"resultType": "complete", "tools": TOOLS})
        if m == "skills/list":
            return res(rid, {"resultType": "complete", "skills": [{"uri": "skill://x/SKILL.md", "frontmatter": {"name": "x"}}]})
        return web.json_response({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "Unknown tool"}})
    return h


async def legacy(request: web.Request):
    body = await request.json()
    calls.setdefault(request.path, []).append(body.get("method"))
    rid, m = body.get("id"), body.get("method")
    if m == "server/discover":
        return web.json_response({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "nf"}}, status=404)
    if m == "initialize":
        return res(rid, {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "l"}})
    if m == "notifications/initialized":
        return web.Response(status=202)
    if m == "tools/list":
        return res(rid, {"tools": TOOLS})
    return web.json_response({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "Unknown tool"}})


async def card(request):
    return web.json_response(CARD, content_type="application/mcp-server-card+json")


async def main() -> int:
    app = web.Application()
    app.router.add_post("/skills", make_modern(True))
    app.router.add_post("/modern", make_modern(False))
    app.router.add_get("/modern/server-card", card)
    app.router.add_post("/legacy", legacy)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 18765)
    await site.start()
    base = "http://127.0.0.1:18765"
    failures = 0
    ed1.ALLOW_INSECURE_METADATA = True
    async with httpx.AsyncClient(follow_redirects=True, max_redirects=3) as client:
        for path in ("skills", "modern", "legacy"):
            r_core = await ed1.probe_endpoint(client, f"{base}/{path}")
            calls.clear()
            r = await e11.probe_endpoint_e11(client, f"{base}/{path}")
            meta = r["meta"]
            c_core = ed1_classify.classify({"url": f"{base}/{path}", **e11.strip_for_output(r_core)})
            c_e11 = ed1_classify.classify({"url": f"{base}/{path}", **e11.strip_for_output(r)})
            checks = {
                "classification unchanged": c_core["primary_status"] == c_e11["primary_status"] == "ok",
                "<=8 requests": meta["total_requests"] <= 8,
                "skills/list only if declared": ("skills/list" in calls.get(f"/{path}", [])) == (path == "skills"),
                "skills counted": (meta.get("skills") or {}).get("skill_count") == (1 if path == "skills" else None),
                "annotation share": meta["tools"]["annotated"] == 1 and meta["tools"]["has_output_schema"] == 1,
                "server card": (meta["server_card"].get("valid_v1") is True) == (path == "modern"),
            }
            for k, ok in checks.items():
                print(f"{'PASS' if ok else 'FAIL'} {path:7s} {k}")
                failures += not ok
            print("      ", json.dumps(meta)[:300])
    await runner.cleanup()
    return failures


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
