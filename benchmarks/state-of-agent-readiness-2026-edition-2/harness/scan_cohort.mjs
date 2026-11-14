#!/usr/bin/env node
/**
 * Frozen ARS scans for the SOAR E2 cohort (PREREGISTRATION.md §3).
 *
 *   node harness/scan_cohort.mjs scan --round 1 [--only id,id] [--cli <path to glintbase bin>]
 *   node harness/scan_cohort.mjs extract          # data/predictors_frozen.csv from round-1 scans
 *
 * Each scan runs `glintbase audit <homepage> --json --offline --profile deep` with the public CLI
 * (@glintbase/cli 3.5.0 + @glintbase/scanner-core 3.5.1 = ars-3.3.1). Stdout is saved verbatim as
 * data/raw_scans/<platform_id>__r<round>__<UTC timestamp>.json; data/raw_scans/manifest.jsonl records
 * the command, CLI version, timing, exit code and SHA-256 of every file.
 */
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { csvCell, readCsv } from "./cohort_snapshot.mjs";

const STUDY = join(dirname(fileURLToPath(import.meta.url)), "..");
const RAW = join(STUDY, "data", "raw_scans");
const MANIFEST = join(RAW, "manifest.jsonl");
const EXPECTED_VERSION = "ars-3.3.1";
const argv = process.argv.slice(2);
const arg = (n, d) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 ? argv[i + 1] : d;
};

export function cohort() {
  return readCsv(join(STUDY, "data", "cohort", "cohort.csv"));
}

export function manifest() {
  return existsSync(MANIFEST) ? readFileSync(MANIFEST, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)) : [];
}

function runCli(cli, url) {
  return new Promise((resolve) => {
    const started = new Date();
    const p = spawn(cli, ["audit", url, "--json", "--offline", "--profile", "deep"], { shell: process.platform === "win32" });
    let out = "";
    let err = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    const timer = setTimeout(() => p.kill(), 300_000);
    p.on("close", (code) => {
      clearTimeout(timer);
      resolve({ started, ended: new Date(), code, out, err: err.slice(-2000) });
    });
  });
}

async function scan() {
  const round = Number(arg("round", "1"));
  const cli = arg("cli", process.env.GLINTBASE_CLI ?? "glintbase");
  const only = arg("only")?.split(",");
  const v = spawnSync(cli, ["-V"], { encoding: "utf8", shell: process.platform === "win32" }).stdout.trim();
  if (!v.includes(EXPECTED_VERSION)) throw new Error(`CLI reports "${v}", expected ${EXPECTED_VERSION}`);
  mkdirSync(RAW, { recursive: true });
  const done = new Set(manifest().filter((m) => m.round === round && m.ok).map((m) => m.platform_id));
  // --reserves scans the named ranked reserves (contingency for replacement rule 4) without adding them to the cohort.
  const pool = argv.includes("--reserves") ? readCsv(join(STUDY, "data", "cohort", "ranking.csv")) : cohort();
  const todo = pool.filter((c) => (!only || only.includes(c.platform_id)) && !done.has(c.platform_id));
  console.log(`round ${round}: ${todo.length} to scan with ${v}`);
  let next = 0;
  await Promise.all(
    Array.from({ length: Number(arg("concurrency", "3")) }, async () => {
      while (next < todo.length) {
        const c = todo[next++];
        const r = await runCli(cli, c.homepage);
        const ts = r.started.toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
        const file = `${c.platform_id}__r${round}__${ts}.json`;
        let parsed = null;
        try {
          parsed = JSON.parse(r.out);
        } catch {}
        writeFileSync(join(RAW, file), r.out);
        const ok = !!parsed && parsed.score_version === EXPECTED_VERSION && parsed.evidence?.targetReachable !== false && !parsed.evidence?.homepageBlocked;
        const rec = {
          platform_id: c.platform_id,
          round,
          url: c.homepage,
          file,
          sha256: createHash("sha256").update(r.out).digest("hex"),
          started_at: r.started.toISOString(),
          ended_at: r.ended.toISOString(),
          exit_code: r.code,
          cli: v,
          command: `glintbase audit ${c.homepage} --json --offline --profile deep`,
          score_version: parsed?.score_version ?? null,
          score: parsed?.score ?? null,
          target_reachable: parsed?.evidence?.targetReachable ?? null,
          homepage_blocked: parsed?.evidence?.homepageBlocked ?? null,
          ok,
          stderr_tail: r.err ? r.err.slice(-300) : null,
        };
        appendFileSync(MANIFEST, JSON.stringify(rec) + "\n");
        console.log(`${c.platform_id.padEnd(14)} r${round} ${ok ? "ok " : "BAD"} score=${rec.score} ${((r.ended - r.started) / 1000).toFixed(0)}s`);
      }
    }),
  );
}

/** Live-only discoverability (PREREGISTRATION.md §3): same rule as scanner-core's runtimeMeasured. */
export function measuredPillar(report, layers) {
  const checks = layers.flatMap((l) => report.layers?.[l]?.checks ?? []).filter((c) => !c.isBonus && (c.measurement === "live" || c.measurement === "content") && ["pass", "warn", "fail"].includes(c.status));
  const possible = checks.reduce((s, c) => s + c.maxPoints, 0);
  const earned = checks.filter((c) => c.status === "pass").reduce((s, c) => s + c.maxPoints, 0);
  return { score: possible > 0 ? Math.round((earned / possible) * 100) : 0, n: checks.length };
}

function extract() {
  const m = manifest();
  const rows = [];
  for (const c of cohort()) {
    const byRound = (r) => m.filter((x) => x.platform_id === c.platform_id && x.round === r && x.ok).sort((a, b) => a.started_at.localeCompare(b.started_at))[0];
    const row = { platform_id: c.platform_id, category: c.category };
    for (const r of [1, 2]) {
      const rec = byRound(r);
      const j = rec ? JSON.parse(readFileSync(join(RAW, rec.file), "utf8")) : null;
      const disc = j ? measuredPillar(j, ["discovery", "access"]) : null;
      const pre = r === 1 ? "" : "r2_";
      Object.assign(row, {
        [`${pre}scan_file`]: rec?.file ?? "",
        [`${pre}scanned_at`]: rec?.started_at ?? "",
        [`${pre}ars_overall`]: j?.score ?? "",
        [`${pre}runtime_measured`]: j?.pillars?.runtimeMeasured?.score ?? "",
        [`${pre}runtime_measured_checks`]: j?.pillars?.runtimeMeasured?.checksCounted ?? "",
        [`${pre}discoverability_measured`]: disc?.score ?? "",
        [`${pre}discoverability_measured_checks`]: disc?.n ?? "",
        [`${pre}runtime_published`]: j?.pillars?.runtimeErgonomics?.score ?? "",
        [`${pre}discoverability_published`]: j?.pillars?.discoverability?.score ?? "",
        [`${pre}archetype`]: j?.archetype?.canonicalArchetype ?? "",
      });
    }
    rows.push(row);
  }
  const cols = Object.keys(rows[0]);
  writeFileSync(join(STUDY, "data", "predictors_frozen.csv"), [cols.join(","), ...rows.map((r) => cols.map((k) => csvCell(r[k])).join(","))].join("\n") + "\n");
  console.log(`predictors for ${rows.filter((r) => r.scan_file).length}/${rows.length} platforms (round 2 for ${rows.filter((r) => r.r2_scan_file).length})`);
}

if (argv[0] === "scan") await scan();
else if (argv[0] === "extract") extract();
else if (argv[0] !== undefined) {
  console.error("usage: scan_cohort.mjs scan --round N | extract");
  process.exit(1);
}
