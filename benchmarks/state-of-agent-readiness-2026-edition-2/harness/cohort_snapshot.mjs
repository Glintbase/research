#!/usr/bin/env node
/**
 * SOAR Edition 2 cohort rule (PREREGISTRATION.md §2).
 *
 *   node harness/cohort_snapshot.mjs snapshot   # GitHub stars for every candidate owner, dated
 *   node harness/cohort_snapshot.mjs correct    # re-query owner handles fixed under replacement rule 1
 *   node harness/cohort_snapshot.mjs select     # ranking.csv: top 15 per category selected, rest reserve
 *   node harness/cohort_snapshot.mjs build      # cohort.csv after logged replacements, with docs roots
 *
 * Stars = the most-starred public, non-fork repository owned by the candidate's official GitHub
 * account, from the GitHub search API (`user:<owner> fork:false`, sorted by stars).
 * Unauthenticated search allows 10 requests a minute, so requests are paced at one per 7 s.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const STUDY = join(dirname(fileURLToPath(import.meta.url)), "..");
const COHORT = join(STUDY, "data", "cohort");
const SNAP = join(COHORT, "github_stars_snapshot.json");
const PER_CATEGORY = 15;
const UA = "GlintbaseResearch/1.0 (+https://glintbase.dev/research/bot; research@glintbase.dev)";

export function readCsv(path) {
  const [head, ...rows] = readFileSync(path, "utf8").replace(/^﻿/, "").trim().split(/\r?\n/);
  const cols = head.split(",");
  return rows.map((r) => {
    const cells = parseLine(r);
    return Object.fromEntries(cols.map((c, i) => [c, cells[i] ?? ""]));
  });
}

function parseLine(line) {
  const out = [];
  let cur = "";
  let q = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (q) {
      if (ch === '"' && line[i + 1] === '"') (cur += '"'), i++;
      else if (ch === '"') q = false;
      else cur += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") out.push(cur), (cur = "");
    else cur += ch;
  }
  out.push(cur);
  return out;
}

export const csvCell = (v) => (/[",\r\n]/.test(String(v ?? "")) ? `"${String(v).replace(/"/g, '""')}"` : String(v ?? ""));

async function topRepo(owner) {
  const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(`user:${owner} fork:false`)}&sort=stars&order=desc&per_page=1`;
  for (let attempt = 0; attempt < 5; attempt++) {
    const res = await fetch(url, { headers: { "user-agent": UA, accept: "application/vnd.github+json" } });
    if (res.status === 403 || res.status === 429) {
      const reset = Number(res.headers.get("x-ratelimit-reset") ?? 0) * 1000;
      const wait = Math.max(10_000, reset - Date.now() + 2000);
      console.log(`  rate limited, waiting ${Math.round(wait / 1000)} s`);
      await new Promise((r) => setTimeout(r, wait));
      continue;
    }
    const body = await res.json().catch(() => null);
    const item = body?.items?.[0] ?? null;
    return {
      http_status: res.status,
      total_count: body?.total_count ?? null,
      repo: item?.full_name ?? null,
      owner_login: item?.owner?.login ?? null,
      stars: item?.stargazers_count ?? null,
      archived: item?.archived ?? null,
      error: res.ok ? null : JSON.stringify(body).slice(0, 200),
    };
  }
  return { http_status: null, total_count: null, repo: null, owner_login: null, stars: null, archived: null, error: "rate limit retries exhausted" };
}

async function snapshot() {
  const pool = readCsv(join(COHORT, "candidate_pool.csv"));
  const prev = existsSync(SNAP) ? JSON.parse(readFileSync(SNAP, "utf8")) : null;
  const done = new Map((prev?.rows ?? []).filter((r) => r.http_status === 200).map((r) => [r.platform_id, r]));
  const rows = [];
  for (const c of pool) {
    if (done.has(c.platform_id) && done.get(c.platform_id).github_owner === c.github_owner) {
      rows.push(done.get(c.platform_id));
      continue;
    }
    const r = await topRepo(c.github_owner);
    rows.push({ platform_id: c.platform_id, category: c.category, github_owner: c.github_owner, fetched_at: new Date().toISOString(), ...r });
    console.log(`${c.category.padEnd(18)} ${c.platform_id.padEnd(14)} ${String(r.stars).padStart(7)}  ${r.repo ?? r.error}`);
    writeFileSync(SNAP, JSON.stringify({ source: "GitHub REST search API, unauthenticated", query: "user:<owner> fork:false sort:stars", rows }, null, 2));
    await new Promise((res) => setTimeout(res, 7000));
  }
  const meta = { source: "GitHub REST search API, unauthenticated", query: "user:<owner> fork:false sort:stars", started_at: rows[0]?.fetched_at, finished_at: new Date().toISOString(), rows };
  writeFileSync(SNAP, JSON.stringify(meta, null, 2));
  console.log(`snapshot: ${rows.length} candidates -> ${SNAP}`);
}

/**
 * Replacement rule 1: a declared owner handle that does not exist or does not match is corrected once,
 * from data/cohort/owner_corrections.csv, and the corrected handle is looked up by the same query.
 */
async function correct() {
  const fixes = readCsv(join(COHORT, "owner_corrections.csv"));
  const snap = JSON.parse(readFileSync(SNAP, "utf8"));
  snap.corrections ??= [];
  for (const f of fixes) {
    if (snap.corrections.some((c) => c.platform_id === f.platform_id && c.github_owner === f.corrected_owner && c.http_status === 200)) continue;
    const r = await topRepo(f.corrected_owner);
    const row = snap.rows.find((x) => x.platform_id === f.platform_id);
    snap.corrections.push({ platform_id: f.platform_id, category: row?.category, github_owner: f.corrected_owner, corrected_from: f.declared_owner, fetched_at: new Date().toISOString(), ...r });
    console.log(`${f.platform_id}: ${f.declared_owner} -> ${f.corrected_owner}: ${r.stars} ${r.repo}`);
    await new Promise((res) => setTimeout(res, 7000));
  }
  writeFileSync(SNAP, JSON.stringify(snap, null, 2));
}

function select() {
  const pool = readCsv(join(COHORT, "candidate_pool.csv"));
  const snap = JSON.parse(readFileSync(SNAP, "utf8"));
  const byId = new Map(snap.rows.map((r) => [r.platform_id, r]));
  for (const c of snap.corrections ?? []) byId.set(c.platform_id, c);
  for (const c of pool) if (byId.get(c.platform_id)?.corrected_from) c.github_owner = byId.get(c.platform_id).github_owner;
  const out = [];
  for (const cat of [...new Set(pool.map((c) => c.category))]) {
    const ranked = pool
      .filter((c) => c.category === cat)
      .map((c) => ({ ...c, s: byId.get(c.platform_id) }))
      .map((c) => ({ ...c, valid: !!c.s && c.s.http_status === 200 && c.s.stars != null && c.s.owner_login?.toLowerCase() === c.github_owner.toLowerCase() }))
      .sort((a, b) => Number(b.valid) - Number(a.valid) || (b.s?.stars ?? -1) - (a.s?.stars ?? -1) || a.platform_id.localeCompare(b.platform_id));
    ranked.forEach((c, i) =>
      out.push({
        category: cat,
        rank: i + 1,
        platform_id: c.platform_id,
        name: c.name,
        homepage: c.homepage,
        github_owner: c.github_owner,
        top_repo: c.s?.repo ?? "",
        stars: c.s?.stars ?? "",
        stars_fetched_at: c.s?.fetched_at ?? "",
        status: !c.valid ? "no_valid_owner" : i < PER_CATEGORY ? "selected" : "reserve",
      }),
    );
  }
  const cols = Object.keys(out[0]);
  writeFileSync(join(COHORT, "ranking.csv"), [cols.join(","), ...out.map((r) => cols.map((c) => csvCell(r[c])).join(","))].join("\n") + "\n");
  const sel = out.filter((r) => r.status === "selected");
  console.log(`selected ${sel.length}; per category:`, Object.fromEntries([...new Set(out.map((r) => r.category))].map((c) => [c, sel.filter((r) => r.category === c).length])));
  const bad = out.filter((r) => r.status === "no_valid_owner");
  if (bad.length) console.log("no valid owner:", bad.map((r) => r.platform_id).join(", "));
}

/**
 * cohort.csv = per category, the first 15 ranked candidates not removed in data/cohort/replacements.csv
 * (rules 2-4, logged with evidence), with the docs entry point from data/cohort/docs_roots.csv.
 */
function build() {
  const ranking = readCsv(join(COHORT, "ranking.csv"));
  const repl = existsSync(join(COHORT, "replacements.csv")) ? readCsv(join(COHORT, "replacements.csv")) : [];
  const removed = new Set(repl.map((r) => r.platform_id));
  const docs = new Map(readCsv(join(COHORT, "docs_roots.csv")).map((d) => [d.platform_id, d.docs_root]));
  const out = [];
  for (const cat of [...new Set(ranking.map((r) => r.category))]) {
    const picked = ranking.filter((r) => r.category === cat && r.status !== "no_valid_owner" && !removed.has(r.platform_id)).slice(0, PER_CATEGORY);
    for (const r of picked) out.push({ platform_id: r.platform_id, name: r.name, category: cat, rank: r.rank, stars: r.stars, homepage: r.homepage, docs_root: docs.get(r.platform_id) ?? "", replacement: r.status === "reserve" ? "yes" : "" });
  }
  const cols = Object.keys(out[0]);
  writeFileSync(join(COHORT, "cohort.csv"), [cols.join(","), ...out.map((r) => cols.map((c) => csvCell(r[c])).join(","))].join("\n") + "\n");
  console.log(`cohort: ${out.length} platforms (${out.filter((r) => r.replacement).length} replacements); missing docs_root: ${out.filter((r) => !r.docs_root).map((r) => r.platform_id).join(", ") || "none"}`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const cmd = process.argv[2];
  mkdirSync(COHORT, { recursive: true });
  if (cmd === "snapshot") await snapshot();
  else if (cmd === "correct") await correct();
  else if (cmd === "select") select();
  else if (cmd === "build") build();
  else {
    console.error("usage: cohort_snapshot.mjs snapshot|correct|select|build");
    process.exit(1);
  }
}
