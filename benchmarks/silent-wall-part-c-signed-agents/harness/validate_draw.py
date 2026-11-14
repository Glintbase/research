"""Draw the 30 domain x arm validation items (pre-registration §7) and write a review sheet.

  python validate_draw.py --round S1     -> data/validation_draw.json (with the stored evidence per item)

Stratified by home outcome and arm, seed 20261104. The reviewer judges each item by hand from the
stored status, selected headers, challenge markers, visible-text length and title, re-opening the
homepage with an independent client where the stored evidence is ambiguous, and records the verdict in
data/validation.csv.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SEED, N = 20261104, 30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="S1")
    a = ap.parse_args()
    rows = [json.loads(l) for l in (DATA / f"edge_round_{a.round}.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]
    raw = {}
    for p in (DATA / "edge" / f"round_{a.round}").glob("*.json"):
        if not p.name.startswith("_"):
            d = json.loads(p.read_text(encoding="utf8"))
            for ident in d["identities"]:
                raw[(d["domain"], ident["identity"])] = ident["requests"][0]
    rng = random.Random(SEED)
    strata = defaultdict(list)
    for r in rows:
        strata[(r["home_outcome"], r["identity"])].append(r)
    for v in strata.values():
        rng.shuffle(v)
    keys = sorted(strata, key=lambda k: (-len(strata[k]), k))
    picked = []
    while len(picked) < N and any(strata.values()):
        for k in keys:
            if strata[k] and len(picked) < N:
                picked.append(strata[k].pop())
    out = []
    for r in picked:
        req = raw.get((r["domain"], r["identity"]), {})
        out.append({"domain": r["domain"], "arm": r["identity"], "harness_outcome": r["home_outcome"],
                    "evidence": {k: req.get(k) for k in ("url", "status", "error", "error_detail", "text_len", "markers", "title", "final_url")}
                    | {"headers": {k: v for k, v in (req.get("headers") or {}).items() if k != "cookie_names"}}})
    (DATA / f"validation_draw_{a.round}.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(len(out), "drawn")


if __name__ == "__main__":
    main()
