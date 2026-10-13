"""Publication figures for The Silent Wall report.

Every value is read from data/summary.json (round 1 = headline round). Writes PNGs to
reports/figures/. Usage: python figures.py
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from common import DATA_DIR, STUDY_DIR  # noqa: E402

OUT = STUDY_DIR / "reports" / "figures"

# Reference palette (dataviz skill). Slots 1–3 validated all-pairs, light mode.
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#c3c2b7"
IDENT_COLOR = {"agent": BLUE, "script": ORANGE, "browser": AQUA}
IDENT_LABEL = {"agent": "Declared agent (GlintbaseResearch)", "script": "Unlabelled script", "browser": "Headless browser"}
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2, "axes.edgecolor": AXIS,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})
SOURCE = "Source: Glintbase Research, The Silent Wall (2026). 150 domains (Tranco 4672X, 30 per sector), round 1; round 2 replicates it."


def style(ax, xmax, xlabel):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.set_xlim(0, xmax)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)


def header(fig, title, subtitle):
    fig.text(0.012, 0.975, title, fontsize=14, fontweight="bold", va="top", color=INK)
    fig.text(0.012, 0.915, subtitle, fontsize=10, va="top", color=INK2)
    fig.text(0.012, 0.02, SOURCE, fontsize=7.5, color=MUTED)


def fig_identities(s):
    """One measure across three clients: the story is 'no difference', so one colour."""
    idents = ["agent", "script", "browser"]
    props = [s["rq2_challenged_or_blocked_home"][i] for i in idents]
    y = [2, 1, 0]
    fig, ax = plt.subplots(figsize=(9, 3.9))
    fig.subplots_adjust(left=0.30, right=0.95, top=0.74, bottom=0.2)
    ax.barh(y, [p["pct"] for p in props], height=0.55, color=BLUE, zorder=2)
    for yi, p in zip(y, props):
        lo, hi = p["ci95"]
        ax.plot([lo, hi], [yi, yi], color=INK, linewidth=1, zorder=3)
        for x in (lo, hi):
            ax.plot([x, x], [yi - 0.1, yi + 0.1], color=INK, linewidth=1, zorder=3)
        ax.text(hi + 0.6, yi, f"{p['pct']:.1f}%  ({p['k']}/{p['n']})", va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([IDENT_LABEL[i] for i in idents])
    style(ax, 40, "Homepages challenged or blocked (%), whiskers: 95% CI")
    pr = s["rq2_paired"]
    header(fig, "Declaring itself an AI agent didn't cost access",
           f"Same public pages, same connection, three clients · paired McNemar p = {pr['agent_vs_browser']['mcnemar_exact_p']:.2f} (agent vs browser), "
           f"{pr['agent_vs_script']['mcnemar_exact_p']:.2f} (agent vs script)")
    fig.savefig(OUT / "sw_fig1_identities.png", dpi=200)
    plt.close(fig)


def fig_robots(s):
    """Disallow-at-/ rate per vendor token, coloured by purpose (3 categories + gray control)."""
    purpose_color = {"training": BLUE, "search": ORANGE, "user": AQUA, "search-control": GRAY}
    purpose_label = {"training": "AI training", "search": "AI search", "user": "User-initiated agent",
                     "search-control": "Googlebot (control)"}
    toks = s["rq1_tokens"]
    order = ["training", "search", "user", "search-control"]
    items = sorted(toks.items(), key=lambda kv: (order.index(kv[1]["purpose"]), -kv[1]["root_disallowed"]["pct"]))
    y = list(range(len(items)))[::-1]
    fig, ax = plt.subplots(figsize=(9, 6.6))
    fig.subplots_adjust(left=0.24, right=0.95, top=0.83, bottom=0.11)
    vals = [v["root_disallowed"]["pct"] for _, v in items]
    ax.barh(y, vals, height=0.62, color=[purpose_color[v["purpose"]] for _, v in items], zorder=2)
    for yi, val, (_, v) in zip(y, vals, items):
        ax.text(val + 0.4, yi, f"{val:.1f}%", va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{t}  ({v['vendor']})" for t, v in items])
    n = items[0][1]["root_disallowed"]["n"]
    style(ax, 25, f"Sites whose robots.txt disallows the token at / (%), of {n} sites with a fetchable robots.txt")
    ax.legend(handles=[Patch(color=purpose_color[p], label=purpose_label[p]) for p in order],
              loc="lower right", frameon=False, fontsize=9)
    any_ = s["rq1_any_token_disallowed_by_purpose"]
    header(fig, "robots.txt targets AI training, not AI agents in general",
           f"Any training crawler disallowed: {any_['training']['pct']:.1f}% of sites · any AI search crawler: "
           f"{any_['search']['pct']:.1f}% · any user-initiated agent: {any_['user']['pct']:.1f}%")
    fig.savefig(OUT / "sw_fig2_robots.png", dpi=200)
    plt.close(fig)


def grouped(ax, groups, data, labels, xmax):
    """Grouped horizontal bars: one group per category, one bar per identity (fixed colour order)."""
    idents = ["agent", "script", "browser"]
    h = 0.24
    base = list(range(len(groups)))[::-1]
    for k, ident in enumerate(idents):
        ys = [b + (1 - k) * (h + 0.03) for b in base]
        vals = [data[g][ident]["pct"] for g in groups]
        ax.barh(ys, vals, height=h, color=IDENT_COLOR[ident], zorder=2)
        for yv, v in zip(ys, vals):
            ax.text(v + 0.6, yv, f"{v:.0f}%", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(base)
    ax.set_yticklabels(labels)
    style(ax, xmax, "Homepages challenged or blocked (%)")


def fig_breakdown(s):
    sec = s["rq4_by_sector"]
    sec_order = sorted(sec, key=lambda g: -max(sec[g][i]["pct"] for i in ("agent", "script", "browser")))
    sec_names = {"ecommerce": "E-commerce", "media": "Media", "saas": "SaaS / B2B", "finance": "Finance", "devtools": "Developer tools"}
    ven = {k: v for k, v in s["rq4_by_vendor"].items() if v["agent"]["n"] >= 7}  # skip tiny cells (DataDome n=3)
    ven_order = sorted(ven, key=lambda g: -max(ven[g][i]["pct"] for i in ("agent", "script", "browser")))
    ven_names = {"akamai": "Akamai", "cloudflare": "Cloudflare", "cloudfront": "CloudFront", "fastly": "Fastly",
                 "vercel": "Vercel", "other/unknown": "Other / unknown"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.6), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.78, bottom=0.17, wspace=0.42)
    grouped(a1, sec_order, sec, [f"{sec_names[g]}\nn = {sec[g]['agent']['n']}" for g in sec_order], 55)
    grouped(a2, ven_order, ven, [f"{ven_names.get(g, g)}\nn = {ven[g]['agent']['n']}" for g in ven_order], 55)
    a1.set_title("By sector", loc="left", fontsize=11, color=INK, fontweight="bold")
    a2.set_title("By edge vendor (inferred; n ≥ 7)", loc="left", fontsize=11, color=INK, fontweight="bold")
    fig.legend(handles=[Patch(color=IDENT_COLOR[i], label=IDENT_LABEL[i]) for i in ("agent", "script", "browser")],
               loc="upper left", bbox_to_anchor=(0.012, 0.875), ncol=3, frameon=False, fontsize=9)
    fig.text(0.012, 0.975, "Who blocks depends on the site and its defences, not the client's label",
             fontsize=14, fontweight="bold", va="top", color=INK)
    fig.text(0.012, 0.02, SOURCE + " Small cells; descriptive only.", fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "sw_fig3_breakdown.png", dpi=200)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = json.loads((DATA_DIR / "summary.json").read_text(encoding="utf8"))["round_1"]
    fig_identities(s)
    fig_robots(s)
    fig_breakdown(s)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
