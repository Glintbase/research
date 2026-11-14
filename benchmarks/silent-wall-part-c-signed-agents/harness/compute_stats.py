"""E6 statistics, using The Silent Wall's classifier unchanged. Every reported number comes from data/summary.json.

Usage: python compute_stats.py --rounds U1,U2[,S1,S2]
Writes data/edge_round_<r>.jsonl (per domain x arm) and data/summary.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
DATA = STUDY_DIR / "data"
SW_HARNESS = STUDY_DIR.parent / "the-silent-wall" / "harness"
sys.path.insert(0, str(SW_HARNESS))
_spec = importlib.util.spec_from_file_location("sw_analyze", SW_HARNESS / "analyze.py")
sw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sw)
sw.EDGE_DIR = DATA / "edge"  # read this study's rounds with The Silent Wall's build_round()

ARMS = ["unsigned", "signed", "browser"]
BAD = {"challenge", "block"}


def rates(rows, arm):
    sub = [r for r in rows if r["identity"] == arm]
    n = len(sub)
    oc = Counter(r["home_outcome"] for r in sub)
    return {"n": n, "home_outcome": {k: sw.prop(v, n) for k, v in oc.most_common()},
            "challenged_or_blocked": sw.prop(sum(r["home_outcome"] in BAD for r in sub), n),
            "worst_page_challenged_or_blocked": sw.prop(sum(r["worst_outcome"] in BAD for r in sub), n)}


def paired(rows, a, b, by_vendor=False):
    idx = defaultdict(dict)
    for r in rows:
        idx[r["domain"]][r["identity"]] = r
    keep = [d for d, v in idx.items() if a in v and b in v
            and v[a]["home_outcome"] not in ("error", "self_excluded") and v[b]["home_outcome"] not in ("error", "self_excluded")]
    excluded = sum(1 for v in idx.values() if a in v and b in v) - len(keep)

    def counts(ds):
        x = sum(idx[d][a]["home_outcome"] in BAD and idx[d][b]["home_outcome"] not in BAD for d in ds)
        y = sum(idx[d][a]["home_outcome"] not in BAD and idx[d][b]["home_outcome"] in BAD for d in ds)
        return {"n_pairs": len(ds), f"{a}_bad_only": x, f"{b}_bad_only": y,
                f"{a}_bad": sw.prop(sum(idx[d][a]["home_outcome"] in BAD for d in ds), len(ds)),
                f"{b}_bad": sw.prop(sum(idx[d][b]["home_outcome"] in BAD for d in ds), len(ds)),
                "mcnemar_exact_p": sw.mcnemar_exact(x, y)}

    out = {"comparison": f"{a} vs {b}", "excluded_error_or_self_excluded": excluded, **counts(keep)}
    if by_vendor:
        vend = Counter(idx[d][a]["vendor"] for d in keep)
        out["by_vendor"] = {v: {**counts([d for d in keep if idx[d][a]["vendor"] == v]), "small_cell": k < 30}
                            for v, k in vend.most_common()}
    return out


def stability(r1, r2, arms):
    idx = {(r["domain"], r["identity"]): r["home_outcome"] for r in r2}
    out = {}
    for arm in arms:
        pairs = [(r["home_outcome"], idx[(r["domain"], arm)]) for r in r1 if r["identity"] == arm and (r["domain"], arm) in idx]
        if not pairs:
            continue
        n = len(pairs)
        po = sum(x == y for x, y in pairs) / n
        c1, c2 = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
        pe = sum(c1[k] * c2.get(k, 0) for k in c1) / n / n
        out[arm] = {"same": sw.prop(sum(x == y for x, y in pairs), n), "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", required=True)
    a = ap.parse_args()
    rounds = [r for r in a.rounds.split(",") if r]
    S = {"rounds": {}, "silent_wall_reference": None}
    built = {}
    for rnd in rounds:
        rows = sw.build_round(rnd)
        built[rnd] = rows
        sw.write_jsonl(DATA / f"edge_round_{rnd}.jsonl", rows)
        arms = sorted({r["identity"] for r in rows}, key=ARMS.index)
        R = {"domains": len({r["domain"] for r in rows}), "arms": arms, "per_arm": {x: rates(rows, x) for x in arms},
             "vendors": dict(Counter(r["vendor"] for r in rows if r["identity"] == arms[0]))}
        if "signed" in arms:
            R["unsigned_vs_signed"] = paired(rows, "unsigned", "signed", by_vendor=True)
            R["signed_vs_browser"] = paired(rows, "signed", "browser")
        if "browser" in arms:
            R["unsigned_vs_browser"] = paired(rows, "unsigned", "browser")
        S["rounds"][rnd] = R
    pairs = [("U1", "U2"), ("S1", "S2"), ("U1", "S1")]
    S["stability"] = {f"{x}->{y}": stability(built[x], built[y], ARMS) for x, y in pairs if x in built and y in built}
    ref = STUDY_DIR.parent / "the-silent-wall" / "data" / "summary.json"
    if ref.exists():
        sw_round1 = json.loads(ref.read_text(encoding="utf8"))["round_1"]
        S["silent_wall_reference"] = {
            "file": "the-silent-wall/data/summary.json, round_1 (October 2026, published; AS36873 vantage point)",
            "challenged_or_blocked_home": sw_round1["rq2_challenged_or_blocked_home"],
            "home_outcome": {k: v for k, v in sw_round1["rq2_home_outcome"].items() if k in ("agent", "browser")},
        }
    (DATA / "summary.json").write_text(json.dumps(S, indent=2), encoding="utf8")
    for rnd, R in S["rounds"].items():
        print(rnd, {x: (v["challenged_or_blocked"]["k"], v["n"]) for x, v in R["per_arm"].items()},
              {k: {kk: R[k][kk] for kk in R[k] if kk not in ("by_vendor",)} for k in R if k.endswith(("signed", "browser")) and isinstance(R[k], dict) and "comparison" in R[k]})


if __name__ == "__main__":
    main()
