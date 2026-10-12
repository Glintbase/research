#!/usr/bin/env python3
"""
measure_transcripts.py - derive harness-measured metrics from the published transcripts.

Why this exists (Correction 2026-10-12): the tokens, steps and wall time in each
run_log.json (and therefore in data/benchmark_master.* and the Integration Tax) were
written by the agent itself at the end of each trial. They were not measured by the
harness. This script counts what can be counted reliably from transcripts/*/*/transcript.jsonl
and writes it next to the self-reported values so readers can compare.

What is measured:
  planner_turns      number of MODEL / PLANNER_RESPONSE records (one per model turn)
  tool_calls         total entries in tool_calls across those records
  run_command_calls  tool calls named run_command
  user_turns         number of USER_EXPLICIT records (human messages in the trial)
  session_seconds    last created_at minus first created_at (whole agent session,
                     including waits on background tasks; 1-second resolution)

What is NOT measured: tokens. The transcripts contain no token usage fields, so no
measured token count is possible from the published data.

Note that session_seconds is the duration of the whole agent session. It is not the
"end-to-end command latency of python solution.py" defined in METHODOLOGY.md section 5.6,
so the two columns are not expected to agree.

Usage (from benchmarks/sandboxes-edition-1):
    python harness/measure_transcripts.py
"""

import csv
import glob
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTS = os.path.join(ROOT, "transcripts")
SOLUTIONS = os.path.join(ROOT, "harness", "solutions")
OUT = os.path.join(ROOT, "data", "measured_metrics.csv")


def parse_ts(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def measure(path):
    planner_turns = tool_calls = run_cmd = user_turns = 0
    stamps = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("created_at"):
                stamps.append(parse_ts(rec["created_at"]))
            if rec.get("source") == "USER_EXPLICIT":
                user_turns += 1
            if rec.get("source") == "MODEL" and rec.get("type") == "PLANNER_RESPONSE":
                planner_turns += 1
                calls = rec.get("tool_calls") or []
                tool_calls += len(calls)
                run_cmd += sum(1 for c in calls if isinstance(c, dict) and c.get("name") == "run_command")
    seconds = (max(stamps) - min(stamps)).total_seconds() if stamps else None
    return planner_turns, tool_calls, run_cmd, user_turns, seconds


def self_reported(provider, trial):
    path = os.path.join(SOLUTIONS, provider, trial, "run_log.json")
    if not os.path.exists(path):
        return None, None, None
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return d.get("tokens", {}).get("total_tokens"), d.get("steps_count"), d.get("wall_time_seconds")


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(TRANSCRIPTS, "*", "*", "transcript.jsonl"))):
        parts = os.path.normpath(path).split(os.sep)
        provider, trial = parts[-3], parts[-2]
        planner, tools, runs, users, secs = measure(path)
        tok, steps, wall = self_reported(provider, trial)
        rows.append({
            "provider": provider,
            "trial_id": trial,
            "measured_planner_turns": planner,
            "measured_tool_calls": tools,
            "measured_run_command_calls": runs,
            "measured_user_turns": users,
            "measured_session_seconds": secs,
            "self_reported_total_tokens": tok,
            "self_reported_steps": steps,
            "self_reported_wall_time_seconds": wall,
        })

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'provider':<8} {'trial':<18} {'turns':>5} {'tools':>5} {'self_steps':>10} {'session_s':>9} {'self_wall_s':>11}")
    for r in rows:
        print(f"{r['provider']:<8} {r['trial_id']:<18} {r['measured_planner_turns']:>5} {r['measured_tool_calls']:>5} "
              f"{r['self_reported_steps']:>10} {r['measured_session_seconds']:>9.0f} {r['self_reported_wall_time_seconds']:>11}")
    print(f"\nWrote {len(rows)} rows to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
