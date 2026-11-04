// Independent re-check for the Edition 1.1 validation gate (pre-registration §7).
// Written separately from the Python harness: Node fetch, one endpoint at a time, following the
// MCP 2026-07-28 backward-compatibility procedure by hand. Metadata only; the only tools/call is
// the non-existent canary tool. No real tool is called.
//
// Usage: node validate_check.mjs <draw.json> <out.json>
//   draw.json: [{"url": "...", ...}]

import { readFileSync, writeFileSync } from 'fs';

const UA = 'GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)';
const CLIENT = { name: 'GlintbaseResearch', version: 'validate-1.1' };
const META = {
  'io.modelcontextprotocol/protocolVersion': '2026-07-28',
  'io.modelcontextprotocol/clientInfo': CLIENT,
  'io.modelcontextprotocol/clientCapabilities': {},
};

async function call(url, { method = 'POST', headers = {}, body } = {}) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 12000);
  try {
    const res = await fetch(url, {
      method,
      headers: { 'User-Agent': UA, ...headers },
      body: body ? JSON.stringify(body) : undefined,
      signal: ctl.signal,
      redirect: 'follow',
    });
    const ctype = res.headers.get('content-type') || '';
    let text = '';
    const reader = res.body?.getReader();
    if (reader) {
      const dec = new TextDecoder();
      while (text.length < 300000) {
        const { done, value } = await reader.read();
        if (done) break;
        text += dec.decode(value, { stream: true });
        if (ctype.includes('event-stream') && /\n\n/.test(text) && /"(result|error)"/.test(text)) break;
      }
      reader.cancel().catch(() => {});
    }
    let json = null;
    if (ctype.includes('event-stream')) {
      for (const block of text.split(/\r?\n\r?\n/)) {
        const data = block.split(/\r?\n/).filter((l) => l.startsWith('data:')).map((l) => l.slice(5).trim()).join('\n');
        try {
          const o = JSON.parse(data);
          if (o && (o.result || o.error)) { json = o; break; }
        } catch {}
      }
    } else {
      try { json = JSON.parse(text); } catch {}
    }
    return { status: res.status, ctype, json, www: res.headers.get('www-authenticate'), session: res.headers.get('mcp-session-id') };
  } catch (e) {
    return { error: String(e.cause?.code || e.name || e) };
  } finally {
    clearTimeout(t);
  }
}

async function check(url) {
  const out = { url };
  const d = await call(url, {
    headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', 'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'server/discover' },
    body: { jsonrpc: '2.0', id: 1, method: 'server/discover', params: { _meta: META } },
  });
  out.discover = { status: d.status, error: d.error, code: d.json?.error?.code, result: !!d.json?.result };
  let caps = null;
  let era = null;
  let session = null;
  let version = null;
  if (d.error) { out.verdict = 'unreachable'; }
  else if (d.status === 401 || (d.status === 403 && d.www)) { out.verdict = 'auth'; out.www = d.www; }
  else if (d.json?.result?.supportedVersions || [-32020, -32021].includes(d.json?.error?.code)) {
    era = 'modern';
    caps = d.json?.result?.capabilities || null;
  } else {
    const i = await call(url, {
      headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' },
      body: { jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: CLIENT } },
    });
    out.initialize = { status: i.status, error: i.error, result: !!i.json?.result, code: i.json?.error?.code };
    if (i.status === 401 || (i.status === 403 && i.www)) { out.verdict = 'auth'; out.www = i.www; }
    else if (i.json?.result) {
      era = 'legacy';
      caps = i.json.result.capabilities || null;
      session = i.session;
      version = i.json.result.protocolVersion;
    } else if (i.json?.jsonrpc) out.verdict = 'jsonrpc_error';
    else if (i.status === 402) out.verdict = 'payment_required';
    else if (i.status >= 500 || i.status === 429) out.verdict = 'server_error';
    else if (i.error) out.verdict = 'unreachable';
    else out.verdict = 'not_mcp_or_sse';
  }
  if (era === 'modern' && !d.json?.result) {
    // a -32020/-32021 rejection with no DiscoverResult: no handshake happened
    out.era = era;
    out.verdict = 'modern_rejected';
    era = null;
  }
  if (era) {
    out.era = era;
    out.extensions = caps && typeof caps.extensions === 'object' ? Object.keys(caps.extensions) : [];
    const h = era === 'modern'
      ? { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', 'MCP-Protocol-Version': '2026-07-28', 'Mcp-Method': 'tools/list' }
      : { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', ...(session ? { 'Mcp-Session-Id': session } : {}), ...(['2025-06-18', '2025-11-25'].includes(version) ? { 'MCP-Protocol-Version': version } : {}) };
    if (era === 'legacy') await call(url, { headers: h, body: { jsonrpc: '2.0', method: 'notifications/initialized' } });
    const tl = await call(url, { headers: h, body: { jsonrpc: '2.0', id: 2, method: 'tools/list', params: era === 'modern' ? { _meta: META } : {} } });
    out.tools_list = { status: tl.status, tools: Array.isArray(tl.json?.result?.tools) ? tl.json.result.tools.length : null };
    if (tl.status === 401) out.verdict = 'auth';
    else out.verdict = out.tools_list.tools !== null ? 'ok' : 'handshake_only';
  }
  if (!d.error) {
    const c = await call(url.replace(/\/+$/, '') + '/server-card', { method: 'GET', headers: { Accept: 'application/mcp-server-card+json, application/json;q=0.9' } });
    const j = c.json;
    out.server_card = {
      status: c.status,
      json: !!j && typeof j === 'object' && !Array.isArray(j) && c.status === 200,
      valid_v1: c.status === 200 && !!j && typeof j.$schema === 'string' && /server-card/i.test(j.$schema) && ['name', 'version', 'description'].every((k) => typeof j[k] === 'string' && j[k].trim()),
    };
  }
  return out;
}

const [, , drawPath, outPath] = process.argv;
const draw = JSON.parse(readFileSync(drawPath, 'utf8'));
const results = [];
for (const row of draw) {
  results.push({ ...row, check: await check(row.url) });
  console.log(row.url, results.at(-1).check.verdict);
  await new Promise((r) => setTimeout(r, 1000));
}
writeFileSync(outPath, JSON.stringify(results, null, 2));
