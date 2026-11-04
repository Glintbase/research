#!/usr/bin/env python3
"""SOAR Edition 2 analysis (PREREGISTRATION.md §6-§9).

    python harness/compute_stats.py collect --experiment <agentsim experiment dir>:haiku [--experiment <dir>:sonnet ...]
    python harness/compute_stats.py analyse [--data-dir data]
    python harness/compute_stats.py mock --out <dir>        # synthetic data for testing only (synthetic: true)

`collect` reads AgentSim result.json files (glintbase.agentsim.result/v1) and writes data/runs.csv with
one row per episode and no transcript, answer or key content. `analyse` reads data/runs.csv,
data/predictors_frozen.csv and, when present, data/key_verdicts.csv (task_id, verdict), and writes
data/stats/results.json plus data/stats/summary.md. Every number in the report comes from these files.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
from scipy import stats

STUDY = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SEED = 20261105
N_BOOT = 10_000
FAMILIES = {"auth_header": "soar_auth_header", "first_request": "soar_first_request", "error_rate_limit": "soar_error_rate_limit"}
SUCCESS = {"success", "correct_refusal"}
PRIMARY_RT = "runtime_measured"
PRIMARY_DISC = "discoverability_measured"
SECONDARY = ["runtime_published", "discoverability_published", "ars_overall"]
RUN_COLS = ["run_id", "experiment", "arm", "model", "task_id", "family", "platform_id", "harness", "browser_arm", "repeat",
            "status", "outcome", "judge_verdict", "tool_calls", "cost_usd", "seconds_active", "synthetic"]


# ---------------------------------------------------------------- collect

def collect(experiments: list[str], out: str) -> None:
    rows = []
    for spec in experiments:
        path, arm = (spec.rsplit(":", 1) if spec.endswith((":haiku", ":sonnet")) else (spec, "haiku"))
        exp = os.path.basename(os.path.normpath(path))
        for f in sorted(glob.glob(os.path.join(path, "*", "*", "r*", "result.json"))):
            with open(f, encoding="utf8") as fh:
                r = json.load(fh)
            task_id = r["task"]["id"]
            fam, _, platform = task_id.partition(".")
            if fam not in FAMILIES:
                continue
            g = r.get("grade") or {}
            m = r.get("metrics") or {}
            harness_dir = os.path.basename(os.path.dirname(os.path.dirname(f)))
            rows.append({
                "run_id": r.get("runId"), "experiment": exp, "arm": arm, "model": r.get("model"),
                "task_id": task_id, "family": FAMILIES[fam], "platform_id": platform,
                "harness": (r.get("harness") or {}).get("id"), "browser_arm": r.get("arm", "fetch"),
                "repeat": os.path.basename(os.path.dirname(f)).lstrip("r"),
                "status": r.get("status"), "outcome": g.get("outcome"),
                "judge_verdict": (g.get("judge") or {}).get("verdict", ""),
                "tool_calls": (m.get("agent") or {}).get("toolCalls", ""),
                "cost_usd": (m.get("model") or {}).get("costUsdEstimate", ""),
                "seconds_active": (m.get("timing") or {}).get("secondsActive", ""),
                "synthetic": "false",
            })
            assert harness_dir.split("@")[0] == rows[-1]["harness"], f"harness mismatch in {f}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=RUN_COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"collected {len(rows)} runs from {len(experiments)} experiment(s) -> {out}")


# ---------------------------------------------------------------- helpers

def read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def spearman(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return float("nan")
    return float(stats.spearmanr(x, y).statistic)


def boot_idx(n: int, strata=None) -> np.ndarray:
    """N_BOOT x n resample indices (fixed seed); stratified resampling keeps each stratum's size."""
    rng = np.random.default_rng(SEED)
    if strata is None:
        return rng.integers(0, n, size=(N_BOOT, n))
    strata = np.asarray(strata)
    out = np.empty((N_BOOT, n), dtype=int)
    for s in np.unique(strata):
        pos = np.flatnonzero(strata == s)
        out[:, pos] = pos[rng.integers(0, len(pos), size=(N_BOOT, len(pos)))]
    return out


def boot_rho(x, y, idx) -> np.ndarray:
    """Spearman ρ for every resample at once (average ranks per row, then row-wise Pearson)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return np.full(len(idx), np.nan)
    rx, ry = stats.rankdata(x[idx], axis=1), stats.rankdata(y[idx], axis=1)
    rx -= rx.mean(axis=1, keepdims=True)
    ry -= ry.mean(axis=1, keepdims=True)
    den = np.sqrt((rx ** 2).sum(axis=1) * (ry ** 2).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (rx * ry).sum(axis=1) / den, np.nan)


def ci(b: np.ndarray) -> list[float]:
    b = b[np.isfinite(b)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))] if len(b) else [float("nan")] * 2


def rho_summary(x, y, idx, direction: str | None = None) -> dict:
    b = boot_rho(x, y, idx)
    out = {"n": int(len(x)), "rho": spearman(x, y), "ci95": ci(b)}
    fb = b[np.isfinite(b)]
    if direction == ">" and len(fb):
        out["p_one_sided"] = float((np.sum(fb <= 0) + 1) / (len(fb) + 1))
    if direction == "<" and len(fb):
        out["p_one_sided"] = float((np.sum(fb >= 0) + 1) / (len(fb) + 1))
    return out


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (len(items) - i) * p))
        adj[k] = running
    return adj


def within_rank(values, groups) -> np.ndarray:
    """Ranks scaled to (0,1) within each group, for the category-stratified ρ."""
    values, groups = np.asarray(values, float), np.asarray(groups)
    out = np.empty(len(values))
    for g in np.unique(groups):
        pos = np.flatnonzero(groups == g)
        out[pos] = (stats.rankdata(values[pos]) - 0.5) / len(pos)
    return out


# ---------------------------------------------------------------- analyse

def platform_table(runs, preds, verdicts, arm, success_fn):
    planned_tasks = {}
    dropped = {t for t, v in verdicts.items() if v == "unanswerable"}
    arm_runs = [r for r in runs if r["arm"] == arm]
    for r in arm_runs:
        planned_tasks.setdefault(r["platform_id"], set()).add(r["task_id"])
    table, excluded = [], []
    for pid, p in preds.items():
        rs = [r for r in arm_runs if r["platform_id"] == pid and r["task_id"] not in dropped]
        tasks = planned_tasks.get(pid, set()) - dropped
        if not tasks:
            excluded.append({"platform_id": pid, "reason": "no gradable tasks" if planned_tasks.get(pid) else "no runs"})
            continue
        valid = [r for r in rs if r["status"] != "infra_error"]
        expected = len({(r["task_id"], r["harness"], r["repeat"]) for r in rs})
        if expected == 0 or len(valid) < 0.5 * expected:
            excluded.append({"platform_id": pid, "reason": f"only {len(valid)}/{expected} valid runs"})
            continue
        succ = [success_fn(r) for r in valid]
        tc = [num(r["tool_calls"]) for r in valid if success_fn(r) and num(r["tool_calls"]) is not None]
        row = {"platform_id": pid, "category": p["category"], "n_valid": len(valid), "n_success": int(sum(succ)),
               "success_rate": sum(succ) / len(valid), "median_tool_calls_success": float(np.median(tc)) if len(tc) >= 3 else None}
        for fam in FAMILIES.values():
            fv = [success_fn(r) for r in valid if r["family"] == fam]
            row[f"success_{fam}"] = sum(fv) / len(fv) if fv else None
        for k in [PRIMARY_RT, PRIMARY_DISC, *SECONDARY]:
            row[k] = num(p.get(k))
        table.append(row)
    return table, excluded


def mixed_models(runs, preds, verdicts, arm) -> dict:
    import pandas as pd
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    dropped = {t for t, v in verdicts.items() if v == "unanswerable"}
    rows = []
    for r in runs:
        p = preds.get(r["platform_id"])
        if r["arm"] != arm or r["status"] == "infra_error" or r["task_id"] in dropped or not p:
            continue
        rt, disc = num(p.get(PRIMARY_RT)), num(p.get(PRIMARY_DISC))
        if rt is None or disc is None:
            continue
        rows.append({"success": int(r["outcome"] in SUCCESS), "rt": rt, "disc": disc, "family": r["family"],
                     "platform": r["platform_id"], "harness": r["harness"]})
    df = pd.DataFrame(rows)
    if df.empty or df["success"].nunique() < 2:
        return {"error": "not enough variation in outcomes to fit"}
    for c in ["rt", "disc"]:
        sd = df[c].std(ddof=0)
        df[f"z_{c}"] = (df[c] - df[c].mean()) / sd if sd > 0 else 0.0
    out = {"n_runs": int(len(df)), "n_platforms": int(df["platform"].nunique())}
    try:
        model = BinomialBayesMixedGLM.from_formula(
            "success ~ z_rt + z_disc + C(family)", {"platform": "0 + C(platform)", "harness": "0 + C(harness)"}, df)
        fit = model.fit_vb()
        names = model.exog_names
        fe = {}
        for i, n in enumerate(names):
            m, s = float(fit.fe_mean[i]), float(fit.fe_sd[i])
            fe[n] = {"log_odds": m, "sd": s, "odds_ratio": math.exp(m), "or_95": [math.exp(m - 1.96 * s), math.exp(m + 1.96 * s)]}
        vc = {n: {"log_sd_mean": float(fit.vcp_mean[i]), "sd": math.exp(float(fit.vcp_mean[i]))} for i, n in enumerate(model.vcp_names)}
        out["bayes_mixed_glm"] = {"method": "statsmodels BinomialBayesMixedGLM, fit_vb, default priors", "fixed_effects": fe, "random_effect_sd": vc}
    except Exception as e:  # reported, never hidden
        out["bayes_mixed_glm"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        gee = smf.gee("success ~ z_rt + z_disc + C(family) + C(harness)", groups="platform", data=df,
                      family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        ci_ = gee.conf_int()
        out["gee_logit"] = {"method": "GEE logit, exchangeable, clusters = platform, robust SE",
                            "fixed_effects": {n: {"log_odds": float(gee.params[n]), "odds_ratio": math.exp(gee.params[n]),
                                                  "or_95": [math.exp(ci_.loc[n, 0]), math.exp(ci_.loc[n, 1])], "p": float(gee.pvalues[n])}
                                              for n in gee.params.index}}
    except Exception as e:
        out["gee_logit"] = {"error": f"{type(e).__name__}: {e}"}
    return out


def analyse(data_dir: str) -> dict:
    preds_rows = read_csv(os.path.join(data_dir, "predictors_frozen.csv"))
    preds = {p["platform_id"]: p for p in preds_rows if p.get("scan_file")}
    runs = read_csv(os.path.join(data_dir, "runs.csv"))
    vpath = os.path.join(data_dir, "key_verdicts.csv")
    verdicts = {v["task_id"]: v["verdict"].strip().lower() for v in read_csv(vpath)} if os.path.exists(vpath) else {}
    synthetic = any(r.get("synthetic") == "true" for r in runs)
    res = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "synthetic": synthetic,
        "keys": {"verified": bool(verdicts), "n_verdicts": len(verdicts),
                 "counts": {k: list(verdicts.values()).count(k) for k in sorted(set(verdicts.values()))}},
        "bootstrap": {"resamples": N_BOOT, "seed": SEED, "ci": "95% percentile"},
        "runs": {"total": len(runs), "by_arm": {a: sum(r["arm"] == a for r in runs) for a in sorted({r["arm"] for r in runs})},
                 "infra_error": sum(r["status"] == "infra_error" for r in runs)},
    }
    key_ok = lambda r: r["outcome"] in SUCCESS
    judge_ok = lambda r: r["judge_verdict"] == "correct" or (r["judge_verdict"] == "refusal" and r["outcome"] == "correct_refusal")

    table, excluded = platform_table(runs, preds, verdicts, "haiku", key_ok)
    res["haiku"] = {"platforms": len(table), "excluded": excluded}
    t = [r for r in table if r[PRIMARY_RT] is not None and r[PRIMARY_DISC] is not None]
    y = [r["success_rate"] for r in t]
    rt = [r[PRIMARY_RT] for r in t]
    disc = [r[PRIMARY_DISC] for r in t]
    idx = boot_idx(len(t))
    rates = np.array(y)
    res["haiku"]["outcome"] = {"mean_success_rate": float(rates.mean()) if len(rates) else None,
                               "sd": float(rates.std(ddof=1)) if len(rates) > 1 else None,
                               "share_platforms_ge_0.9": float(np.mean(rates >= 0.9)) if len(rates) else None,
                               "ceiling_flag": bool(len(rates) and np.mean(rates >= 0.9) > 0.8)}

    # H1, H2, H3
    h1 = rho_summary(rt, y, idx, ">")
    b_rt, b_disc = boot_rho(rt, y, idx), boot_rho(disc, y, idx)
    diff = b_rt - b_disc
    fd = diff[np.isfinite(diff)]
    h2 = {"n": len(t), "rho_runtime": spearman(rt, y), "rho_discoverability": spearman(disc, y),
          "diff": spearman(rt, y) - spearman(disc, y), "ci95": ci(diff),
          "p_one_sided": float((np.sum(fd <= 0) + 1) / (len(fd) + 1)) if len(fd) else None,
          "rho_between_predictors": spearman(rt, disc)}
    t3 = [r for r in t if r["median_tool_calls_success"] is not None]
    h3 = rho_summary([r[PRIMARY_RT] for r in t3], [r["median_tool_calls_success"] for r in t3], boot_idx(len(t3)), "<")
    ps = {k: v.get("p_one_sided") for k, v in {"H1": h1, "H2": h2, "H3": h3}.items() if v.get("p_one_sided") is not None}
    adj = holm(ps)
    for k, v, cond in [("H1", h1, lambda v: v["ci95"][0] > 0), ("H2", h2, lambda v: v["ci95"][0] > 0), ("H3", h3, lambda v: v["ci95"][1] < 0)]:
        v["p_holm"] = adj.get(k)
        v["supported_ci"] = bool(cond(v)) if all(map(math.isfinite, v["ci95"])) else None
        v["supported_holm_0.05"] = bool(adj[k] < 0.05) if k in adj else None
    res["hypotheses"] = {"H1": h1, "H2": h2, "H3": h3}

    # Secondary
    sec = {k: rho_summary([r[k] for r in t if r[k] is not None], [r["success_rate"] for r in t if r[k] is not None],
                          boot_idx(sum(r[k] is not None for r in t))) for k in [PRIMARY_DISC, *SECONDARY]}
    by_family = {}
    for fam in FAMILIES.values():
        tf = [r for r in t if r[f"success_{fam}"] is not None]
        by_family[fam] = {k: rho_summary([r[k] for r in tf], [r[f"success_{fam}"] for r in tf], boot_idx(len(tf))) for k in [PRIMARY_RT, PRIMARY_DISC]}
    cats = [r["category"] for r in t]
    strat = {}
    for k in [PRIMARY_RT, PRIMARY_DISC]:
        xs, ys = within_rank([r[k] for r in t], cats), within_rank(y, cats)
        sidx = boot_idx(len(t), cats)
        bs = np.array([np.corrcoef(xs[i], ys[i])[0, 1] if np.ptp(xs[i]) and np.ptp(ys[i]) else np.nan for i in sidx])
        strat[k] = {"rho_within_category": float(np.corrcoef(xs, ys)[0, 1]) if np.ptp(xs) and np.ptp(ys) else None, "ci95": ci(bs)}
    per_category = {c: {k: rho_summary([r[k] for r in t if r["category"] == c], [r["success_rate"] for r in t if r["category"] == c],
                                       boot_idx(cats.count(c))) for k in [PRIMARY_RT, PRIMARY_DISC]} for c in sorted(set(cats))}
    jt, _ = platform_table(runs, preds, verdicts, "haiku", judge_ok)
    jt = [r for r in jt if r[PRIMARY_RT] is not None]
    per_harness = {}
    for h in sorted({r["harness"] for r in runs if r["arm"] == "haiku"}):
        ht, _ = platform_table([r for r in runs if r["harness"] == h], preds, verdicts, "haiku", key_ok)
        ht = [r for r in ht if r[PRIMARY_RT] is not None]
        per_harness[h] = rho_summary([r[PRIMARY_RT] for r in ht], [r["success_rate"] for r in ht], boot_idx(len(ht)))
    res["secondary"] = {
        "other_predictors": sec,
        "by_family": by_family,
        "category_stratified": strat,
        "per_category": per_category,
        "judge_graded_outcome": rho_summary([r[PRIMARY_RT] for r in jt], [r["success_rate"] for r in jt], boot_idx(len(jt)), ">"),
        "per_harness_exploratory": per_harness,
    }

    # Sonnet arm (descriptive)
    st, sx = platform_table(runs, preds, verdicts, "sonnet", key_ok)
    st = [r for r in st if r[PRIMARY_RT] is not None]
    res["sonnet"] = {"platforms": len(st), "excluded": [e for e in sx if e["reason"] != "no runs"],
                     "rho_runtime": rho_summary([r[PRIMARY_RT] for r in st], [r["success_rate"] for r in st], boot_idx(len(st))),
                     "rho_discoverability": rho_summary([r[PRIMARY_DISC] for r in st], [r["success_rate"] for r in st], boot_idx(len(st))),
                     "mean_success_rate": float(np.mean([r["success_rate"] for r in st])) if st else None}

    # Scan re-test reliability
    rel = {}
    for k in [PRIMARY_RT, PRIMARY_DISC, *SECONDARY]:
        pairs = [(num(p.get(k)), num(p.get(f"r2_{k}"))) for p in preds.values()]
        pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
        rel[k] = {"n": len(pairs), "rho_scan1_scan2": spearman(*zip(*pairs)) if len(pairs) >= 3 else None,
                  "share_identical": float(np.mean([a == b for a, b in pairs])) if pairs else None}
    res["scan_retest"] = rel

    res["mixed_models"] = mixed_models(runs, preds, verdicts, "haiku")
    res["platform_table"] = table

    out_dir = os.path.join(data_dir, "stats")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf8") as fh:
        json.dump(res, fh, indent=2, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else o)
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf8") as fh:
        fh.write(summary_md(res))
    return res


def fmt(v, d=2):
    return "n/a" if v is None or (isinstance(v, float) and not math.isfinite(v)) else f"{v:.{d}f}"


def summary_md(res: dict) -> str:
    h = res["hypotheses"]
    lines = [
        "# SOAR Edition 2: statistics summary", "",
        f"Generated {res['generated_at']} by `harness/compute_stats.py`.", "",
    ]
    if res["synthetic"]:
        lines += ["> **SYNTHETIC DATA (`synthetic: true`). Test output only; not a result.**", ""]
    if not res["keys"]["verified"]:
        lines += ["> Keys not yet verified (no `data/key_verdicts.csv`): grades use the LLM-drafted keys. Not for publication.", ""]
    o = res["haiku"]["outcome"]
    lines += [
        f"- Haiku arm: {res['haiku']['platforms']} platforms analysed, {len(res['haiku']['excluded'])} excluded; "
        f"mean platform success rate {fmt(o['mean_success_rate'])} (SD {fmt(o['sd'])}); share ≥ 0.9: {fmt(o['share_platforms_ge_0.9'])}"
        + (" — **ceiling flag: outcome variance too low to test the hypotheses well**" if o["ceiling_flag"] else ""), "",
        "| Hypothesis | Estimate | 95% CI | p (one-sided) | p (Holm) | Supported (CI) |", "|---|---|---|---|---|---|",
        f"| H1 ρ(Runtime_measured, success) > 0 | {fmt(h['H1']['rho'])} | [{fmt(h['H1']['ci95'][0])}, {fmt(h['H1']['ci95'][1])}] | {fmt(h['H1'].get('p_one_sided'), 4)} | {fmt(h['H1'].get('p_holm'), 4)} | {h['H1']['supported_ci']} |",
        f"| H2 ρ(Runtime_m) − ρ(Discoverability_m) > 0 | {fmt(h['H2']['diff'])} | [{fmt(h['H2']['ci95'][0])}, {fmt(h['H2']['ci95'][1])}] | {fmt(h['H2'].get('p_one_sided'), 4)} | {fmt(h['H2'].get('p_holm'), 4)} | {h['H2']['supported_ci']} |",
        f"| H3 ρ(Runtime_measured, tool calls per success) < 0 | {fmt(h['H3']['rho'])} | [{fmt(h['H3']['ci95'][0])}, {fmt(h['H3']['ci95'][1])}] | {fmt(h['H3'].get('p_one_sided'), 4)} | {fmt(h['H3'].get('p_holm'), 4)} | {h['H3']['supported_ci']} |",
        "", f"ρ between the two primary predictors: {fmt(h['H2']['rho_between_predictors'])}. H3 uses {h['H3']['n']} platforms with ≥ 3 successful runs.", "",
        "## Secondary", "", "| Predictor | ρ with success | 95% CI | n |", "|---|---|---|---|",
    ]
    for k, v in res["secondary"]["other_predictors"].items():
        lines.append(f"| {k} | {fmt(v['rho'])} | [{fmt(v['ci95'][0])}, {fmt(v['ci95'][1])}] | {v['n']} |")
    j = res["secondary"]["judge_graded_outcome"]
    lines += ["", f"Judge-graded outcome, ρ(Runtime_measured): {fmt(j['rho'])} [{fmt(j['ci95'][0])}, {fmt(j['ci95'][1])}].", ""]
    mm = res["mixed_models"].get("bayes_mixed_glm", {})
    if "fixed_effects" in mm:
        lines += ["## Mixed-effects logistic regression (run level, Haiku)", "", "| Term | OR per SD | 95% interval |", "|---|---|---|"]
        for n in ["z_rt", "z_disc"]:
            fe = mm["fixed_effects"][n]
            lines.append(f"| {n} | {fmt(fe['odds_ratio'])} | [{fmt(fe['or_95'][0])}, {fmt(fe['or_95'][1])}] |")
        lines.append("")
    elif mm:
        lines += [f"Mixed model: {mm.get('error')}", ""]
    s = res["sonnet"]
    lines += [f"Sonnet arm (descriptive): {s['platforms']} platforms, ρ(Runtime_measured) {fmt(s['rho_runtime']['rho'])} "
              f"[{fmt(s['rho_runtime']['ci95'][0])}, {fmt(s['rho_runtime']['ci95'][1])}].", ""]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- mock (tests only)

def mock(out: str, effect: float = 0.4) -> None:
    """Synthetic predictors and runs with a known positive runtime effect. Labelled synthetic: true."""
    rng = np.random.default_rng(7)
    cats = ["sandboxes_compute", "llm_apis", "vector_search", "backend_infra", "agent_tooling", "payments_comms"]
    os.makedirs(out, exist_ok=True)
    preds, runs = [], []
    for i in range(90):
        pid = f"mock{i:02d}"
        rt = float(np.clip(rng.normal(55, 20), 0, 100)); disc = float(np.clip(0.5 * rt + rng.normal(35, 15), 0, 100))
        row = {"platform_id": pid, "category": cats[i // 15], "scan_file": f"{pid}.json", PRIMARY_RT: round(rt), PRIMARY_DISC: round(disc),
               "runtime_published": round(rt + rng.normal(5, 5)), "discoverability_published": round(disc + rng.normal(3, 5)), "ars_overall": round((rt + disc) / 2)}
        row.update({f"r2_{k}": v + (0 if rng.random() < 0.8 else int(rng.integers(-3, 4))) for k, v in row.items() if k in [PRIMARY_RT, PRIMARY_DISC, *SECONDARY]})
        preds.append(row)
        base = -0.2 + effect * (rt - 55) / 20
        for fam_short, fam in FAMILIES.items():
            for h in ["claude-code", "opencode", "codex"]:
                for arm, reps in [("haiku", 2)] + ([("sonnet", 1)] if i % 15 < 5 else []):
                    for rep in range(reps):
                        infra = rng.random() < 0.03
                        p = 1 / (1 + math.exp(-(base + (0.6 if arm == "sonnet" else 0) + {"claude-code": 0.3, "opencode": 0, "codex": -0.2}[h])))
                        ok = rng.random() < p
                        runs.append({"run_id": f"mock/{fam_short}.{pid}/{h}/r{rep}", "experiment": f"mock_{arm}", "arm": arm,
                                     "model": "claude-haiku-5-5" if arm == "haiku" else "claude-sonnet-5-5", "task_id": f"{fam_short}.{pid}",
                                     "family": fam, "platform_id": pid, "harness": h, "browser_arm": "fetch", "repeat": rep,
                                     "status": "infra_error" if infra else "completed", "outcome": None if infra else ("success" if ok else "fail"),
                                     "judge_verdict": "" if infra else ("correct" if ok ^ (rng.random() < 0.05) else "incorrect"),
                                     "tool_calls": int(max(1, rng.normal(14 - 0.05 * (rt - 55), 4))), "cost_usd": 0.014, "seconds_active": 50,
                                     "synthetic": "true"})
    for name, rows in [("predictors_frozen.csv", preds), ("runs.csv", runs)]:
        with open(os.path.join(out, name), "w", newline="", encoding="utf8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(out, "key_verdicts.csv"), "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["task_id", "verdict"])
        for p in preds:
            for fam_short in FAMILIES:
                w.writerow([f"{fam_short}.{p['platform_id']}", "unanswerable" if rng.random() < 0.03 else "correct"])
    print(f"mock data (synthetic: true) -> {out}: {len(preds)} platforms, {len(runs)} runs")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("--experiment", action="append", required=True, help="<dir>[:haiku|sonnet]")
    c.add_argument("--out", default=os.path.join(STUDY, "data", "runs.csv"))
    a = sub.add_parser("analyse"); a.add_argument("--data-dir", default=os.path.join(STUDY, "data"))
    m = sub.add_parser("mock"); m.add_argument("--out", required=True); m.add_argument("--effect", type=float, default=0.4)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "collect":
        collect(args.experiment, args.out)
    elif args.cmd == "mock":
        mock(args.out, args.effect)
    else:
        res = analyse(args.data_dir)
        print(summary_md(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
