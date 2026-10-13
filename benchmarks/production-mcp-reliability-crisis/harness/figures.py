"""Publication figures for the Remote MCP Server Reliability report.

Every value is read from data/summary.json or data/round_2.jsonl (the headline round).
Writes PNGs to reports/figures/. Usage: python figures.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import DATA_DIR, STUDY_DIR, read_jsonl  # noqa: E402

OUT = STUDY_DIR / "reports" / "figures"

# Reference palette (dataviz skill): light surface, ink, chrome, categorical slot 1.
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, GRAY = "#2a78d6", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.edgecolor": AXIS,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})
SOURCE = "Source: Glintbase Research, Remote MCP Server Reliability (2026). n = 3,000 endpoints sampled from the official MCP Registry, round 2."


def style(ax, xmax=100, xlabel="Share of endpoints (%)"):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.set_xlim(0, xmax)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)


def header(fig, title, subtitle):
    fig.text(0.012, 0.975, title, fontsize=14, fontweight="bold", va="top", color=INK)
    fig.text(0.012, 0.915, subtitle, fontsize=10, va="top", color=INK2)
    fig.text(0.012, 0.02, SOURCE, fontsize=7.5, color=MUTED)


def ci_bars(ax, labels, props, colors=None, label_fmt="{pct:.1f}%"):
    """Horizontal bars with Wilson 95% CI whiskers and a direct value label."""
    y = list(range(len(labels)))[::-1]
    pcts = [p["pct"] for p in props]
    ax.barh(y, pcts, height=0.62, color=colors or BLUE, zorder=2)
    for yi, p in zip(y, props):
        lo, hi = p["ci95"]
        ax.plot([lo, hi], [yi, yi], color=INK, linewidth=1, zorder=3)
        for x in (lo, hi):
            ax.plot([x, x], [yi - 0.12, yi + 0.12], color=INK, linewidth=1, zorder=3)
        ax.text(hi + 1.2, yi, label_fmt.format(**p), va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)


def fig_status(s):
    order = [("ok", "Works anonymously\n(handshake + tool list)"), ("auth_compliant", "Requires auth,\nfollowable challenge"),
             ("auth_noncompliant", "Requires auth,\nno followable challenge"), ("unreachable", "Unreachable"),
             ("not_mcp", "Not an MCP endpoint"), ("payment_required", "Payment required (402)"),
             ("server_error", "Server error (5xx/429)"), ("jsonrpc_error", "Rejects handshake"),
             ("legacy_sse", "Deprecated SSE transport"), ("handshake_only", "Handshake only")]
    props = [s["rq1_primary_status"][k] for k, _ in order]
    fig, ax = plt.subplots(figsize=(9, 6.2))
    fig.subplots_adjust(left=0.27, right=0.95, top=0.82, bottom=0.12)
    ci_bars(ax, [l for _, l in order], props)
    style(ax, xmax=70)
    header(fig, "Most listed MCP endpoints work — nearly a third need credentials",
           "Outcome of a protocol-only probe of 3,000 remote endpoints (bars: share; whiskers: 95% CI)")
    fig.savefig(OUT / "mcp_fig1_outcomes.png", dpi=200)
    plt.close(fig)


def fig_protocol(s, rows):
    hs = [r for r in rows if r.get("protocol_version") or r.get("supported_versions")]
    n = len(hs)
    modern = sum(r.get("era") == "modern" for r in hs)
    legacy = Counter(r.get("protocol_version") for r in hs if r.get("era") == "legacy")
    items = [("2026-07-28 (modern)", modern)] + [(v, legacy.get(v, 0)) for v in ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")]
    other = n - sum(c for _, c in items)
    items.append(("other / non-conformant", other))
    labels = [l for l, _ in items]
    vals = [100 * c / n for _, c in items]
    y = list(range(len(items)))[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    fig.subplots_adjust(left=0.24, right=0.95, top=0.78, bottom=0.15)
    ax.barh(y, vals, height=0.62, color=[BLUE] + [GRAY] * (len(items) - 1), zorder=2)
    for yi, v, (_, c) in zip(y, vals, items):
        ax.text(v + 0.8, yi, f"{v:.1f}%  ({c:,})", va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    style(ax, xmax=55, xlabel=f"Share of endpoints that completed a handshake (n = {n:,})")
    header(fig, "Fewer than 1 in 7 servers speaks the new 2026-07-28 protocol",
           "Protocol revision negotiated by servers that completed a handshake, 11 weeks after the revision shipped")
    fig.savefig(OUT / "mcp_fig2_protocol.png", dpi=200)
    plt.close(fig)


def fig_basics(s):
    items = [
        ("Reachable", s["rq1_reachable"], "all endpoints"),
        ("Answers as an MCP server", s["rq1_speaks_mcp"], "all endpoints"),
        ("Auth challenge an agent can follow", s["rq3_compliant_among_auth"], "auth-gated endpoints"),
        ("Every tool strictly typed", s["rq4_all_tools_strict_schema"], "endpoints listing tools"),
        ("Errors reported in-channel", s["rq5_error_in_channel"], "endpoints answering the canary call"),
        ("Declares readOnlyHint on any tool", s["rq4_any_readonly_annotation"], "endpoints listing tools"),
        ("Declares destructiveHint on any tool", s["rq4_any_destructive_annotation"], "endpoints listing tools"),
    ]
    labels = [f"{name}\n{base}, n = {p['n']:,}" for name, p, base in items]
    fig, ax = plt.subplots(figsize=(9, 6.0))
    fig.subplots_adjust(left=0.33, right=0.95, top=0.82, bottom=0.12)
    ci_bars(ax, labels, [p for _, p, _ in items])
    style(ax, xmax=110, xlabel="Share (%) of the stated base")
    ax.set_xticks(range(0, 101, 20))
    ax.tick_params(axis="y", labelsize=9)
    header(fig, "The protocol basics: discovery is strong, safety hints are patchy",
           "Share of endpoints meeting each basic an agent relies on (whiskers: 95% CI); each row has its own base")
    fig.savefig(OUT / "mcp_fig3_basics.png", dpi=200)
    plt.close(fig)


def fig_errors(rows):
    can = [r for r in rows if r.get("canary_http_status") is not None]
    n = len(can)
    inch = sum(bool(r.get("error_in_channel")) for r in can)
    rest = Counter(str(r.get("canary_http_status")) for r in can if not r.get("error_in_channel"))
    items = [("JSON-RPC error or isError: true", inch, BLUE),
             ("HTTP 200 with no error signal", rest.pop("200", 0), GRAY),
             ("Bare HTTP 404", rest.pop("404", 0), GRAY),
             ("Auth required to call", rest.pop("401", 0), GRAY),
             ("Rate-limited (429)", rest.pop("429", 0), GRAY)]
    items.append(("Other", sum(rest.values()), GRAY))
    y = list(range(len(items)))[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(left=0.29, right=0.95, top=0.78, bottom=0.16)
    vals = [100 * c / n for _, c, _ in items]
    ax.barh(y, vals, height=0.62, color=[c for *_, c in items], zorder=2)
    for yi, v, (_, c, _) in zip(y, vals, items):
        ax.text(v + 0.8, yi, f"{v:.1f}%  ({c:,})", va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([l for l, *_ in items])
    style(ax, xmax=90, xlabel=f"Share of endpoints that answered the call (n = {n:,})")
    header(fig, "A quarter of servers don't report errors in a way agents can act on",
           "Response to a call to a tool that does not exist (highlighted: correct in-channel error)")
    fig.savefig(OUT / "mcp_fig4_errors.png", dpi=200)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = json.loads((DATA_DIR / "summary.json").read_text(encoding="utf8"))
    s = summary["round_1"]  # compute_stats labels the headline round "round_1" (here: round 2)
    rows = read_jsonl(DATA_DIR / "round_2.jsonl")
    fig_status(s)
    fig_protocol(s, rows)
    fig_basics(s)
    fig_errors(rows)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
