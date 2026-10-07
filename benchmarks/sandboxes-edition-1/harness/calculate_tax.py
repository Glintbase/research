#!/usr/bin/env python3
"""
calculate_tax.py — Glintbase Integration Tax Calculator
Processes all run_log.json files across benchmark folders and calculates:
- Pass Rate (%)
- Stumbles & Human Stops
- Integration Tax Ratio: 0.4*(Tokens/Min) + 0.4*(Steps/Min) + 0.2*(Time/Min)
- Leaked Instance Audits
"""

import os
import json
import glob
from statistics import median

def load_all_runs(base_dir="."):
    search_path = os.path.join(base_dir, "**", "run_log.json")
    files = glob.glob(search_path, recursive=True)
    
    platforms = {}
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                platform = data.get("platform", "unknown")
                if platform not in platforms:
                    platforms[platform] = []
                platforms[platform].append(data)
        except Exception as e:
            print(f"Warning: Could not read {f}: {e}")
            
    return platforms

def calculate_metrics(runs):
    total_runs = len(runs)
    if total_runs == 0:
        return None
        
    passed_runs = [r for r in runs if r.get("passed", False)]
    pass_rate = (len(passed_runs) / total_runs) * 100.0
    
    tokens = [r.get("tokens", {}).get("total_tokens", 0) for r in runs]
    steps = [r.get("steps_count", 0) for r in runs]
    times = [r.get("wall_time_seconds", 0) for r in runs]
    stumbles = [r.get("stumbles_count", 0) for r in runs]
    human_stops = [r.get("human_stops_count", 0) for r in runs]
    leaks = [r.get("leaked_sandboxes", 0) for r in runs]
    
    return {
        "total_runs": total_runs,
        "pass_rate": pass_rate,
        "median_tokens": median(tokens) if tokens else 0,
        "median_steps": median(steps) if steps else 0,
        "median_time": median(times) if times else 0,
        "total_stumbles": sum(stumbles),
        "total_human_stops": sum(human_stops),
        "total_leaked_instances": sum(leaks),
        "runs": runs
    }

def main():
    print("=" * 70)
    print("  GLINTBASE INTEGRATION TAX & BENCHMARK INDEX CALCULATOR")
    print("=" * 70)
    
    platforms = load_all_runs()
    if not platforms:
        print("\nNo run_log.json files found. Run the trials first!")
        return

    summary = {}
    for p, runs in platforms.items():
        metrics = calculate_metrics(runs)
        if metrics:
            summary[p] = metrics

    if not summary:
        print("No valid trial records found.")
        return

    # Find minimums for normalization
    min_tokens = min([m["median_tokens"] for m in summary.values() if m["median_tokens"] > 0] or [1])
    min_steps = min([m["median_steps"] for m in summary.values() if m["median_steps"] > 0] or [1])
    min_time = min([m["median_time"] for m in summary.values() if m["median_time"] > 0] or [1])

    # Calculate Integration Tax
    # Formula: 0.40 * (Tokens/Min) + 0.40 * (Steps/Min) + 0.20 * (Time/Min)
    for p, m in summary.items():
        token_ratio = (m["median_tokens"] / min_tokens) if min_tokens > 0 else 1.0
        step_ratio = (m["median_steps"] / min_steps) if min_steps > 0 else 1.0
        time_ratio = (m["median_time"] / min_time) if min_time > 0 else 1.0
        
        # Penalize if pass rate is under 100%
        penalty = 1.0
        if m["pass_rate"] < 100:
            penalty += (100.0 - m["pass_rate"]) / 50.0 # up to 3x penalty for 0% pass rate
            
        tax = (0.40 * token_ratio + 0.40 * step_ratio + 0.20 * time_ratio) * penalty
        m["integration_tax"] = round(tax, 2)

    # Print Table
    print(f"\n{'Platform':<15} | {'Pass Rate':<10} | {'Tax (IT)':<10} | {'Med Tokens':<12} | {'Med Steps':<10} | {'Med Time':<10} | {'Leaks'}")
    print("-" * 85)
    for p, m in sorted(summary.items(), key=lambda x: x[1]["integration_tax"]):
        print(f"{p.upper():<15} | {m['pass_rate']:>8.1f}% | {m['integration_tax']:>8.2f}x | {m['median_tokens']:>12,.0f} | {m['median_steps']:>10} | {m['median_time']:>8.1f}s | {m['total_leaked_instances']}")

    output_file = "integration_tax_summary.json"
    with open(output_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
    print(f"\nDetailed summary saved to {output_file}\n")

if __name__ == "__main__":
    main()
