"""Classify Edition 1.1 raw records: Edition 1's classifier (unchanged) plus the metadata fields.

Usage: python classify_e11.py --round 1     -> data/round_1.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
sys.path.insert(0, str(STUDY_DIR.parent / "production-mcp-reliability-crisis" / "harness"))

import classify as ed1_classify  # noqa: E402  (Edition 1 classifier, unchanged)
from common import write_jsonl  # noqa: E402

SKILLS_EXT = "io.modelcontextprotocol/skills"


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def classify(rec: dict) -> dict:
    out = ed1_classify.classify({k: v for k, v in rec.items() if k not in ("meta", "meta_steps")})
    meta = rec.get("meta")
    if not meta:
        return out
    ext = meta.get("extensions")
    out["extensions"] = ext
    out["declares_skills"] = bool(ext and SKILLS_EXT in ext)
    sk = meta.get("skills")
    if sk:
        out["skills_list_status"] = sk.get("status")
        out["skills_list_ok"] = bool(sk.get("result") and sk.get("skill_count") is not None)
        out["skill_count"] = sk.get("skill_count")
    card = meta.get("server_card") or {}
    if "skipped" in card:
        out["server_card_skipped"] = card["skipped"]
    else:
        out["server_card_status"] = card.get("status")
        out["server_card_error"] = card.get("error")
        out["server_card_content_type"] = (card.get("content_type") or "").split(";")[0] or None
        out["server_card_json"] = bool(card.get("status") == 200 and card.get("json_object"))
        out["server_card_valid_v1"] = bool(out["server_card_json"] and card.get("valid_v1"))
    t = meta.get("tools")
    if t and t.get("tool_count"):
        n = t["tool_count"]
        sizes = t.get("input_schema_bytes") or []
        out.update(
            pct_tools_annotated=pct(t["annotated"], n),
            pct_tools_output_schema=pct(t["has_output_schema"], n),
            pct_tools_title=pct(t["has_title"], n),
            schema_bytes_median=statistics.median(sizes) if sizes else None,
            schema_bytes_max=max(sizes) if sizes else None,
            schema_bytes_total=sum(sizes) if sizes else None,
            schema_bytes_per_tool=sizes,
        )
    out["requests_sent"] = meta.get("total_requests")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    a = ap.parse_args()
    src = STUDY_DIR / "data" / "raw" / f"round_{a.round}"
    rows = [classify(json.loads(p.read_text(encoding="utf8"))) for p in sorted(src.glob("*.json"))
            if not p.name.startswith("_")]
    rows.sort(key=lambda r: r["url"])
    dest = STUDY_DIR / "data" / f"round_{a.round}.jsonl"
    write_jsonl(dest, rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["primary_status"]] = counts.get(r["primary_status"], 0) + 1
    print(f"{len(rows)} endpoints -> {dest.name}; max requests {max((r.get('requests_sent') or 0) for r in rows)}")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:20s} {v}")


if __name__ == "__main__":
    main()
