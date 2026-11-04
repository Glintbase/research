"""Validation draws and scoring for E1 and E3 (seed 20261104, 30 items each).

  python validate_draw.py draw e1|e3
  node validate_check.mjs e1|e3 <study>/data/validation_draw.json <study>/data/validation_check.json
  python validate_draw.py score e1|e3      -> <study>/data/validation.csv

E1: stratified by class, every `conflict` site up to 10 first. E3: stratified by outcome over
(site, file) pairs, `valid` non-sitemap/non-llms files up to 10 first.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent.parent
STUDY = {"e1": BENCH / "content-signal-census", "e3": BENCH / "front-door-files-census"}
SEED, N = 20261104, 30
PATHS = {"ai_catalog": "/.well-known/ai-catalog.json", "ard": "/.well-known/ard.json", "api_catalog": "/.well-known/api-catalog",
         "poppy": "/.well-known/poppy.json", "agent_card": "/.well-known/agent-card.json",
         "sig_directory": "/.well-known/http-message-signatures-directory", "llms_txt": "/llms.txt", "sitemap": "/sitemap.xml"}


def rows(study):
    return [json.loads(l) for l in (STUDY[study] / "data" / "sites.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]


def stratified(items, key, first, cap_first):
    rng = random.Random(SEED)
    pri = [i for i in items if first(i)]
    rng.shuffle(pri)
    picked = pri[:cap_first]
    strata = defaultdict(list)
    for i in items:
        if i not in picked:
            strata[key(i)].append(i)
    for v in strata.values():
        rng.shuffle(v)
    order = sorted(strata, key=lambda k: -len(strata[k]))
    while len(picked) < N and any(strata.values()):
        for k in order:
            if strata[k] and len(picked) < N:
                picked.append(strata[k].pop())
    return picked


def draw(study):
    rs = [r for r in rows(study) if r.get("reachable")]
    if study == "e1":
        p = stratified(rs, lambda r: r["class"], lambda r: r["class"] == "conflict", 10)
        out = [{"site": r["site"], "harness_class": r["class"], "harness_md_served": r["md_served"],
                "harness_has_docs_headers": any(k.startswith("docs") or k == "md_twin" for k in r["header_signals"])} for r in p]
    else:
        items = [{"site": r["site"], "file": f, "path": PATHS[f], "harness_outcome": v["outcome"]}
                 for r in rs for f, v in r["files"].items() if v["outcome"] not in ("self_excluded", "not_requested")]
        p = stratified(items, lambda i: i["harness_outcome"],
                       lambda i: i["harness_outcome"] == "valid" and i["file"] not in ("sitemap", "llms_txt"), 10)
        out = p
    (STUDY[study] / "data" / "validation_draw.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(len(out), "drawn")


def score(study):
    res = json.loads((STUDY[study] / "data" / "validation_check.json").read_text(encoding="utf8"))
    out, agree = [], 0
    for r in res:
        c = r["check"]
        if study == "e1":
            a = c["class"] == r["harness_class"]
            row = {"site": r["site"], "harness": r["harness_class"], "check": c["class"], "agree": a,
                   "harness_has_docs_headers": r["harness_has_docs_headers"], "check_headers": json.dumps(c["headers"]),
                   "check_robots_policy": json.dumps(c["robots_policy"])}
        else:
            a = c["verdict"] == r["harness_outcome"]
            row = {"site": r["site"], "file": r["file"], "harness": r["harness_outcome"], "check": c["verdict"], "agree": a,
                   "check_status": c.get("status"), "check_ctype": c.get("ctype"), "check_control_status": c.get("control_status")}
        row["reviewer_note"] = ""
        agree += a
        out.append(row)
    with open(STUDY[study] / "data" / "validation.csv", "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"{study}: agreement {agree}/{len(out)}")
    for row in out:
        if not row["agree"]:
            print("  disagree:", row)


if __name__ == "__main__":
    cmd, study = sys.argv[1], sys.argv[2]
    draw(study) if cmd == "draw" else score(study)
