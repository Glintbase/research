// Independent re-check for the E1 and E3 validation gates. Written separately from the Python
// crawler: Node fetch, one site at a time, >= 1 s between requests, same honest identity.
//
//   node validate_check.mjs e1 <draw.json> <out.json>   draw rows: {site, harness_class, ...}
//   node validate_check.mjs e3 <draw.json> <out.json>   draw rows: {site, file, path, harness_outcome, ...}
//
// E1: fetch robots.txt, the homepage as HTML and with Accept: text/markdown; parse Content-Signal
//     in robots (the * group, else lines before any group) and in each response header; classify.
// E3: fetch the file and a fresh control path; judge by hand-written rules mirroring the prereg.

import { readFileSync, writeFileSync } from 'fs';

const UA = 'GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function get(url, accept) {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 20000);
  try {
    const res = await fetch(url, { headers: { 'User-Agent': UA, Accept: accept }, redirect: 'follow', signal: ctl.signal });
    const buf = Buffer.from(await res.arrayBuffer());
    return { status: res.status, url: res.url, ctype: (res.headers.get('content-type') || '').toLowerCase(),
      signal: res.headers.get('content-signal'), body: buf.subarray(0, 300000).toString('utf8'), len: buf.length };
  } catch (e) {
    return { error: String(e.cause?.code || e.name) };
  } finally {
    clearTimeout(t);
  }
}

function parseSignal(v) {
  const out = {};
  for (const part of (v || '').split(/[,|]/)) {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim().toLowerCase()] = part.slice(i + 1).trim().toLowerCase().replace(/"/g, '');
  }
  return out;
}

function robotsPolicy(text) {
  // Content-Signal attached to the * group, else to lines before the first User-agent.
  let agents = [], inAgents = false, star = null, global = {}, any = false, seenGroup = false;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split('#')[0].trim();
    const m = /^([A-Za-z-]+)\s*:\s*(.*)$/.exec(line);
    if (!m) continue;
    const field = m[1].toLowerCase();
    if (field === 'user-agent') {
      if (!inAgents) { agents = []; inAgents = true; seenGroup = true; }
      agents.push(m[2].trim().toLowerCase());
      continue;
    }
    inAgents = false;
    if (field === 'content-signal') {
      any = true;
      const sig = parseSignal(m[2]);
      if (!seenGroup) Object.assign(global, sig);
      else if (agents.includes('*')) star = Object.assign(star || {}, sig);
    }
  }
  return { any, policy: star || global };
}

async function e1(row) {
  const base = `https://${row.site}`;
  const robots = await get(`${base}/robots.txt`, 'text/plain, */*;q=0.1');
  await sleep(1000);
  const html = await get(`${base}/`, 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8');
  await sleep(1000);
  const md = html.url ? await get(html.url, 'text/markdown') : { error: 'no homepage' };
  const rtext = robots.status === 200 && !robots.ctype.includes('html') && !/^\s*<(!doctype|html)/i.test(robots.body) ? robots.body : '';
  const r = robotsPolicy(rtext);
  const headers = {};
  if (html.signal) headers.html = parseSignal(html.signal);
  if (md.signal) headers.md = parseSignal(md.signal);
  const hasH = Object.keys(headers).length > 0;
  let conflict = false;
  const hv = Object.values(headers);
  for (const h of hv) for (const [k, v] of Object.entries(h)) if (k in r.policy && r.policy[k] !== v) conflict = true;
  if (hv.length === 2) for (const k of Object.keys(hv[0])) if (k in hv[1] && hv[0][k] !== hv[1][k]) conflict = true;
  const cls = !r.any && !hasH ? 'none' : r.any && !hasH ? 'robots_only' : !r.any ? (conflict ? 'conflict' : 'header_only') : conflict ? 'conflict' : 'agree';
  const mdServed = md.status >= 200 && md.status < 300 && /^text\/(x-)?markdown/.test(md.ctype || '');
  return { reachable: html.status !== undefined, robots_policy: r.policy, robots_any: r.any, headers, md_served: mdServed, class: cls,
    note: html.error ? `homepage ${html.error}` : '' };
}

const HTMLISH = /^\s*(<!doctype html|<html|<head|<body|<script)/i;
function validFile(file, body) {
  const j = (() => { try { return JSON.parse(body.replace(/^﻿/, '')); } catch { return null; } })();
  const obj = j && typeof j === 'object' && !Array.isArray(j);
  switch (file) {
    case 'ai_catalog': return obj && Array.isArray(j.entries) && j.entries.every((e) => e && typeof e.type === 'string' && (typeof e.url === 'string' || (e.data && typeof e.data === 'object')));
    case 'ard': return !!obj;
    case 'api_catalog': return obj && Array.isArray(j.linkset);
    case 'poppy': return obj && /^\d+\.\d+$/.test(j.protocol_version || '') && !!j.organization?.name?.trim?.() && !!j.organization?.domain?.trim?.();
    case 'agent_card': return obj && !!j.name?.trim?.() && !!j.description?.trim?.() && Array.isArray(j.skills);
    case 'sig_directory': return obj && Array.isArray(j.keys) && j.keys.length > 0 && j.keys.every((k) => k && k.kty);
    case 'llms_txt': return !HTMLISH.test(body) && (body.split(/\r?\n/).find((l) => l.trim()) || '').startsWith('# ');
    case 'sitemap': return /^\s*((<\?[^>]*\?>|<!--[\s\S]*?-->)\s*)*<(urlset|sitemapindex)/.test(body.replace(/^﻿/, '').slice(0, 5000));
  }
  return false;
}

async function e3(row) {
  const base = `https://${row.site}`;
  const f = await get(base + row.path, '*/*');
  await sleep(1000);
  const ctlPath = ['llms_txt', 'sitemap'].includes(row.file) ? `/glintbase-validate-${Math.random().toString(16).slice(2, 10)}.txt` : `/.well-known/glintbase-validate-${Math.random().toString(16).slice(2, 10)}`;
  const c = await get(base + ctlPath, '*/*');
  let verdict;
  if (f.error) verdict = 'error';
  else if (f.status !== 200) verdict = 'absent';
  else if (f.ctype.includes('html') || HTMLISH.test(f.body)) verdict = 'soft_404';
  else if (c.status === 200 && c.body === f.body) verdict = 'soft_404';
  else {
    const ok = f.len > 300000 && row.file === 'sitemap' ? f.ctype.includes('xml') : f.len > 300000 && row.file === 'llms_txt' ? /^text\/(plain|markdown)/.test(f.ctype) : validFile(row.file, f.body);
    verdict = ok ? 'valid' : (c.status === 200 && c.ctype.split(';')[0] === f.ctype.split(';')[0] ? 'soft_404' : 'invalid');
  }
  return { verdict, status: f.status, ctype: f.ctype, control_status: c.status, note: f.error || '' };
}

const [, , mode, drawPath, outPath] = process.argv;
const draw = JSON.parse(readFileSync(drawPath, 'utf8'));
const out = [];
for (const row of draw) {
  const check = mode === 'e1' ? await e1(row) : await e3(row);
  out.push({ ...row, check });
  console.log(row.site, row.file || '', mode === 'e1' ? `${row.harness_class} vs ${check.class}` : `${row.harness_outcome} vs ${check.verdict}`);
  await sleep(1000);
}
writeFileSync(outPath, JSON.stringify(out, null, 2));
