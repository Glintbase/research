"""Draw the 30-endpoint validation sample (pre-registration §7) and score agreement.

  python validate_draw.py draw  --round 1        -> data/validation_draw.json
  node validate_check.mjs ../data/validation_draw.json ../data/validation_check.json
  python validate_draw.py score --round 1        -> data/validation.csv (+ printed agreement)

Stratified by primary status, seed 20261104; every endpoint declaring skills or serving a JSON
server card is included first, up to 6.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SEED = 20261104
N = 30

# Map the checker's coarser verdicts onto primary statuses it can confirm.
VERDICT_OK = {
    "ok": {"ok"}, "handshake_only": {"handshake_only"}, "auth": {"auth_compliant", "auth_noncompliant"},
    "unreachable": {"unreachable"}, "jsonrpc_error": {"jsonrpc_error", "modern_rejected"},
    "payment_required": {"payment_required"}, "server_error": {"server_error"},
    "not_mcp_or_sse": {"not_mcp", "legacy_sse"},
}


def read(p):
    return [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()]


def draw(rnd: str):
    rows = [r for r in read(DATA / f"round_{rnd}.jsonl") if r["primary_status"] != "excluded"]
    rng = random.Random(SEED)
    special = [r for r in rows if r.get("declares_skills") or r.get("server_card_json")]
    rng.shuffle(special)
    picked = special[:6]
    strata = defaultdict(list)
    for r in rows:
        if r not in picked:
            strata[r["primary_status"]].append(r)
    for v in strata.values():
        rng.shuffle(v)
    keys = sorted(strata, key=lambda k: -len(strata[k]))
    while len(picked) < N and any(strata.values()):
        for k in keys:
            if strata[k] and len(picked) < N:
                picked.append(strata[k].pop())
    out = [{"url": r["url"], "primary_status": r["primary_status"], "declares_skills": bool(r.get("declares_skills")),
            "server_card_valid_v1": bool(r.get("server_card_valid_v1"))} for r in picked]
    (DATA / "validation_draw.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(f"{len(out)} drawn:", {k: sum(o['primary_status'] == k for o in out) for k in sorted({o['primary_status'] for o in out})})


def score():
    res = json.loads((DATA / "validation_check.json").read_text(encoding="utf8"))
    rows, agree_s, agree_c, agree_k = [], 0, 0, 0
    for r in res:
        c = r["check"]
        s_ok = r["primary_status"] in VERDICT_OK.get(c.get("verdict"), set())
        card_ok = bool((c.get("server_card") or {}).get("valid_v1")) == r["server_card_valid_v1"]
        skills_ok = ("io.modelcontextprotocol/skills" in (c.get("extensions") or [])) == r["declares_skills"]
        agree_s += s_ok
        agree_c += card_ok
        agree_k += skills_ok
        rows.append({"url": r["url"], "harness_status": r["primary_status"], "check_verdict": c.get("verdict"),
                     "status_agree": s_ok, "harness_card_valid": r["server_card_valid_v1"],
                     "check_card_valid": bool((c.get("server_card") or {}).get("valid_v1")), "card_agree": card_ok,
                     "skills_agree": skills_ok, "reviewer_note": ""})
    with open(DATA / "validation.csv", "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    print(f"status agreement {agree_s}/{n}; server card {agree_c}/{n}; skills {agree_k}/{n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draw", "score"])
    ap.add_argument("--round", default="1")
    a = ap.parse_args()
    draw(a.round) if a.cmd == "draw" else score()
