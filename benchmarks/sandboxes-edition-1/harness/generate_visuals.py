#!/usr/bin/env python3
"""
generate_visuals.py — The Glintbase Integration Index: Sandboxes Edition 1
Generates high-resolution, minimalist editorial graphics strictly matching Anthropic's research announcement aesthetic:
- Visual 1: Master Leaderboard Benchmark Table (media_1791326076769.png)
- Visual 2: The Dual Matrix: Front-Door vs. Reality Gap Scatter (media_1791326076770.png aesthetic)
- Visual 3: Autonomous Agent Tool Turns by Challenge Stage (Line Graph strictly matching media_1791326076770.png)
- Visual 4: Integration Tax (IT) Leaderboard Bar Chart
- Visual 5: Provider × Challenge Friction Heatmap Matrix
"""

import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
from PIL import Image, ImageDraw

# Anthropic Visual Design Constants
BG_COLOR = "#FAF9F5"          # Warm off-white / light cream paper
TEXT_MAIN = "#141413"         # Deep charcoal
TEXT_MUTED = "#6B6B66"        # Subtle neutral gray
TEXT_FOOTNOTE = "#767672"     # Footnote text
BORDER_COLOR = "#8E8E8A"      # Crisp table gridline
BORDER_LIGHT = "#DCDCD7"      # Subtle separator
GRID_COLOR = "#E6E5DF"        # Ultra faint horizontal gridline

# Exact Color Palette from Anthropic Reference Images
COLOR_BLUE = "#5B9BD5"        # Sonnet / Modal blue
COLOR_BLUE_BG = "#E2ECF7"     # Winner highlight fill
COLOR_BLUE_BORDER = "#4A88CC" # Winner highlight border
COLOR_RUST = "#D76C48"        # Opus / E2B terracotta
COLOR_SAGE = "#8BA898"        # Sonnet 5 / boat muted sage green
COLOR_SLATE = "#6B7D96"       # Vercel slate blue
COLOR_TAUPE = "#BAAE9E"       # Daytona oatmeal taupe

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_DIR = r"C:\Users\USER\.gemini\antigravity\brain\5cbe0344-fbc0-4389-8025-d9d3ae4b88eb"

LOGO_PATHS = {
    'modal': r'C:/Users/USER/.gemini/antigravity/brain/5cbe0344-fbc0-4389-8025-d9d3ae4b88eb/.user_uploaded/media_1791327854470.jpg',
    'e2b': r'C:/Users/USER/.gemini/antigravity/brain/5cbe0344-fbc0-4389-8025-d9d3ae4b88eb/.user_uploaded/media_1791327854467.png',
    'boat': r'C:/Users/USER/.gemini/antigravity/brain/5cbe0344-fbc0-4389-8025-d9d3ae4b88eb/.user_uploaded/media_1791327854464.png',
    'vercel': r'C:/Users/USER/.gemini/antigravity/brain/5cbe0344-fbc0-4389-8025-d9d3ae4b88eb/.user_uploaded/media_1791327854466.png',
    'daytona': r'C:/Users/USER/.gemini/antigravity/brain/5cbe0344-fbc0-4389-8025-d9d3ae4b88eb/.user_uploaded/media_1791327854471.png'
}

def generate_clean_badge(name, path, size=128):
    """Normalizes provider brand assets into clean, unified squircle badges matching Anthropic dark-mode iconography."""
    bg_dark = (16, 16, 15, 255)
    im = Image.open(path).convert('RGBA')
    s2 = size * 2
    canvas = Image.new('RGBA', (s2, s2), bg_dark)
    
    if name == 'modal':
        crop_m = im.crop((60, 160, 492, 394))
        m_arr = np.array(crop_m)
        mask = (m_arr[:, :, 0] < 20) & (m_arr[:, :, 1] < 20) & (m_arr[:, :, 2] < 20)
        m_arr[mask] = list(bg_dark)
        crop_m = Image.fromarray(m_arr)
        target_w = int(s2 * 0.72)
        crop_m.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)
        ox = (s2 - crop_m.width) // 2
        oy = (s2 - crop_m.height) // 2
        canvas.paste(crop_m, (ox, oy))
        
    elif name == 'e2b':
        im_crop = im.crop(im.getbbox())
        arr = np.array(im_crop)
        mask = (arr[:, :, 0] < 25) & (arr[:, :, 1] < 25) & (arr[:, :, 2] < 25)
        arr[mask] = list(bg_dark)
        im_crop = Image.fromarray(arr)
        target_w = int(s2 * 0.75)
        im_crop.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)
        ox = (s2 - im_crop.width) // 2
        oy = (s2 - im_crop.height) // 2
        canvas.paste(im_crop, (ox, oy), im_crop)
        
    elif name == 'daytona':
        im_crop = im.crop(im.getbbox())
        arr = np.array(im_crop)
        mask = (arr[:, :, 0] < 30) & (arr[:, :, 1] < 30) & (arr[:, :, 2] < 30)
        arr[mask] = list(bg_dark)
        im_crop = Image.fromarray(arr)
        target_w = int(s2 * 0.72)
        im_crop.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)
        ox = (s2 - im_crop.width) // 2
        oy = (s2 - im_crop.height) // 2
        canvas.paste(im_crop, (ox, oy), im_crop)
        
    elif name == 'vercel':
        crop_v = im.crop((203, 20, 820, 555))
        v_arr = np.array(crop_v)
        mask = v_arr[:, :, 3] > 50
        white_v = np.zeros_like(v_arr)
        white_v[mask] = [255, 255, 255, 255]
        glyph = Image.fromarray(white_v)
        target_w = int(s2 * 0.60)
        glyph.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)
        ox = (s2 - glyph.width) // 2
        oy = (s2 - glyph.height) // 2 + 2
        canvas.paste(glyph, (ox, oy), glyph)
        
    elif name == 'boat':
        crop_b = im.crop((11, 28, 81, 123))
        arr = np.array(crop_b)
        alpha = 255 - np.mean(arr[:, :, :3], axis=2)
        white_b = np.zeros((crop_b.height, crop_b.width, 4), dtype=np.uint8)
        mask = alpha > 40
        white_b[mask] = [255, 255, 255, 255]
        glyph = Image.fromarray(white_b)
        target_w = int(s2 * 0.68)
        glyph.thumbnail((target_w, target_w), Image.Resampling.LANCZOS)
        ox = (s2 - glyph.width) // 2
        oy = (s2 - glyph.height) // 2
        canvas.paste(glyph, (ox, oy), glyph)
        
    mask = Image.new('L', (s2, s2), 0)
    mdraw = ImageDraw.Draw(mask)
    radius = int(s2 * 0.22)
    mdraw.rounded_rectangle([0, 0, s2 - 1, s2 - 1], radius=radius, fill=255)
    
    cdraw = ImageDraw.Draw(canvas)
    cdraw.rounded_rectangle([1, 1, s2 - 2, s2 - 2], radius=radius, outline=(65, 65, 63, 255), width=3)
    
    res = Image.new('RGBA', (s2, s2), (0, 0, 0, 0))
    res.paste(canvas, (0, 0), mask)
    return res.resize((size, size), Image.Resampling.LANCZOS)

BADGES = {k: generate_clean_badge(k, v) for k, v in LOGO_PATHS.items()}

def copy_to_artifact(filename):
    src = os.path.join(OUTPUT_DIR, filename)
    dst = os.path.join(ARTIFACT_DIR, filename)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Synced {filename} to artifact directory.")

# ==============================================================================
# VISUAL 1: Master Leaderboard Benchmark Table (matching media_1791326076769.png)
# ==============================================================================
def create_table_visual():
    fig = plt.figure(figsize=(11.5, 13.2), facecolor=BG_COLOR, dpi=300)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG_COLOR)
    ax.axis("off")
    
    # Title & Subtitle (Clean Serif Header)
    ax.text(0.5, 0.948, "The Glintbase Integration Index", 
            ha="center", va="center", fontsize=30, weight="bold", 
            family="serif", color=TEXT_MAIN)
    ax.text(0.5, 0.920, "Sandboxes Edition 1 · Empirical Autonomous AI Coding Benchmark", 
            ha="center", va="center", fontsize=13, weight="normal", 
            family="sans-serif", color=TEXT_MUTED)
    
    # Layout Coordinates
    col_widths = [0.29, 0.135, 0.135, 0.135, 0.135, 0.135]
    col_starts = [0.055]
    for w in col_widths[:-1]:
        col_starts.append(col_starts[-1] + w)
        
    y_start = 0.835
    row_height = 0.052
    
    headers = [
        ("", "", None),
        ("Modal Labs", "Rank #1", "modal"),
        ("E2B", "Rank #2", "e2b"),
        ("boat.dev", "Rank #3", "boat"),
        ("Vercel", "Rank #4", "vercel"),
        ("Daytona", "Rank #5", "daytona")
    ]
    
    rows = [
        ("Integration Tax (IT)", "Composite multiplier", "1.03x", "1.17x", "1.21x", "1.37x", "1.43x", True),
        ("Pass Rate", "6/6 SWE challenges", "100.0%", "100.0%", "100.0%", "100.0%", "100.0%", False),
        ("Median Token Burn", "Prompt + Completion", "2,010", "1,865¹", "2,580", "2,235", "2,260", False),
        ("Total Tokens Burned", "Sum across 6 trials", "12,380", "10,910", "26,598²", "13,820", "16,520", False),
        ("Median Agent Steps", "Autonomous tool turns", "3.0", "3.5", "3.0", "5.0", "5.0", False),
        ("Median Wall Time", "End-to-end command latency", "19.5s³", "29.2s", "25.0s", "21.6s", "27.4s", False),
        ("Human Stops (Hs)", "Out-of-band interventions", "1⁴", "0 (None)", "1⁵", "1⁶", "0 (None)", False),
        ("Stumbles & Retries", "In-band autonomous loops", "0", "0", "1 (402)", "0", "1 (401)", False),
        ("Front-Door ARS Score", "119 automated checks", "36 / 100⁷", "75 / 100", "82 / 100⁸", "69 / 100", "48 / 100", False),
        ("Teardown Integrity", "Dangling cloud microVMs", "0 leaks", "0 leaks", "0 leaks", "0 leaks", "0 leaks", False)
    ]
    
    # 1. Winner Column Continuous Box (Modal Labs)
    modal_left = col_starts[1]
    modal_width = col_widths[1]
    table_top = y_start + 0.065
    table_bottom = y_start - (len(rows) * row_height)
    table_left = col_starts[0]
    table_right = col_starts[-1] + col_widths[-1]
    
    # Soft ice-blue background fill for Modal Labs column
    rect_winner = patches.Rectangle((modal_left, table_bottom), modal_width, table_top - table_bottom,
                                    facecolor=COLOR_BLUE_BG, edgecolor=COLOR_BLUE_BORDER, linewidth=2.2, zorder=1)
    ax.add_patch(rect_winner)
    
    # 2. Draw Table Grid Lines (Clean 1px grey lines matching Anthropic reference)
    # Outer frame
    ax.plot([table_left, table_right], [table_top, table_top], color=BORDER_COLOR, lw=1.2, zorder=2)
    ax.plot([table_left, table_right], [y_start, y_start], color=BORDER_COLOR, lw=1.2, zorder=2)
    ax.plot([table_left, table_right], [table_bottom, table_bottom], color=BORDER_COLOR, lw=1.2, zorder=2)
    
    # Outer verticals
    ax.plot([table_left, table_left], [table_top, table_bottom], color=BORDER_COLOR, lw=1.2, zorder=2)
    ax.plot([table_right, table_right], [table_top, table_bottom], color=BORDER_COLOR, lw=1.2, zorder=2)
    
    # Column dividers
    for i in range(1, len(col_starts)):
        cs = col_starts[i]
        # Skip modal borders since they are handled by the blue rectangle
        if i not in [1, 2]:
            ax.plot([cs, cs], [table_top, table_bottom], color=BORDER_COLOR, lw=0.9, zorder=2)
            
    # Horizontal row dividers
    curr_y = y_start
    for r_idx in range(len(rows) - 1):
        curr_y -= row_height
        ax.plot([table_left, table_right], [curr_y, curr_y], color=BORDER_COLOR, lw=0.8, zorder=2)
        
    # 3. Header Text & Embedded Brand Badges
    for i, (h_title, h_sub, key) in enumerate(headers):
        if i == 0:
            continue
        x_center = col_starts[i] + col_widths[i] / 2
        is_winner = (i == 1)
        
        # Embed Logo Badge
        if key in BADGES:
            oi = OffsetImage(BADGES[key], zoom=0.20)
            ab = AnnotationBbox(oi, (x_center, y_start + 0.043), frameon=False, zorder=4)
            ax.add_artist(ab)
            
        ax.text(x_center, y_start + 0.018, h_title, ha="center", va="center",
                fontsize=12.5, weight="bold", family="sans-serif", color=TEXT_MAIN, zorder=3)
        ax.text(x_center, y_start + 0.003, h_sub, ha="center", va="center",
                fontsize=10.0, weight="normal", family="sans-serif",
                color=COLOR_BLUE_BORDER if is_winner else TEXT_MUTED, zorder=3)
        
    # 4. Row Text
    curr_y = y_start
    for r_idx, (m_title, m_sub, v_modal, v_e2b, v_boat, v_vercel, v_daytona, is_hero) in enumerate(rows):
        curr_y -= row_height
        y_mid = curr_y + row_height / 2
        
        # Left metric title
        ax.text(table_left + 0.015, y_mid + 0.006, m_title,
                ha="left", va="center", fontsize=11.5, weight="bold",
                family="sans-serif", color=TEXT_MAIN, zorder=3)
        ax.text(table_left + 0.015, y_mid - 0.009, m_sub,
                ha="left", va="center", fontsize=9.5, weight="normal",
                family="sans-serif", color=TEXT_MUTED, zorder=3)
        
        vals = [v_modal, v_e2b, v_boat, v_vercel, v_daytona]
        for c_idx, val in enumerate(vals):
            col_pos = c_idx + 1
            x_mid = col_starts[col_pos] + col_widths[col_pos] / 2
            is_winner_col = (col_pos == 1)
            
            # Winner in column or hero gets bold, non-winners standard
            font_wt = "bold" if (is_winner_col or is_hero or "0 leaks" in val) else "normal"
            f_size = 12 if is_hero else 11
            
            ax.text(x_mid, y_mid, val, ha="center", va="center",
                    fontsize=f_size, weight=font_wt,
                    family="sans-serif", color=TEXT_MAIN, zorder=3)
            
    # 5. Footnotes Block (matching Anthropic reference image)
    foot_y = table_bottom - 0.026
    ax.text(table_left, foot_y, "Evaluation protocol: 30 empirical integration trials executed across 5 providers (n=1 preliminary pilot cohort, October 2026).",
            fontsize=8.5, family="sans-serif", color=TEXT_FOOTNOTE)
    
    notes = [
        "¹ E2B achieved the lowest token consumption across all 30 trials (1,865 median tokens) due to clean SDK type declarations.",
        "² boat.dev's total tokens reflect an in-trial retry loop triggered by an HTTP 402 card gate during Trial 2 (Install & Run).",
        "³ Modal achieved the fastest execution wall time (19.5s) via native container caching and zero-config TLS ingress tunneling.",
        "⁴ Modal required 1 human stop to resolve a credential mismatch between Webhook keys (wk-...) and API tokens (ak-...).",
        "⁵ boat.dev halted autonomously in Trial 2 until a credit card was added to the web console billing dashboard.",
        "⁶ Vercel Sandbox required manual human inspection to retrieve the mandatory project ID and team ID triad.",
        "⁷ Modal scored 36/100 on front-door ARS 3.0 scans due to the absence of public REST/OpenAPI endpoints on its web homepage.",
        "⁸ boat.dev scored 82/100 on ARS 3.0 (32/35 base usability + 16 bonus points across MCP and RFC 8414/9728 protocols; 84/102 active denominator)."
    ]
    
    for i, note in enumerate(notes):
        ax.text(table_left, foot_y - 0.014 * (i + 1), note,
                fontsize=8.0, family="sans-serif", color=TEXT_FOOTNOTE)
        
    out_file = os.path.join(OUTPUT_DIR, "visual1_master_leaderboard_table.png")
    fig.savefig(out_file, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    copy_to_artifact("visual1_master_leaderboard_table.png")
    print(f"Generated Visual 1: {out_file}")

# ==============================================================================
# VISUAL 2: The Dual Matrix: Front Door vs. Runtime Reality (Scatter Plot)
# ==============================================================================
def create_scatter_matrix_visual():
    fig, ax = plt.subplots(figsize=(11, 8.5), facecolor=BG_COLOR, dpi=300)
    ax.set_facecolor(BG_COLOR)
    
    # Title & Subtitle (Clean Sans-Serif Header matching reference linegraph)
    fig.text(0.5, 0.945, "The Dual Matrix: Front Door vs. Runtime Reality",
             ha="center", va="center", fontsize=24, weight="bold",
             family="sans-serif", color=TEXT_MAIN)
    fig.text(0.5, 0.910, "Machine Discoverability (ARS 3.0) vs. Empirical Integration Tax (IT)",
             ha="center", va="center", fontsize=12.5, style="italic",
             family="serif", color=TEXT_MUTED)
    
    # Legend at Top (Matching Image 2 style with circular dots)
    legend_items = [
        ("Modal Labs (#1)", COLOR_BLUE),
        ("E2B (#2)", COLOR_RUST),
        ("boat.dev (#3)", COLOR_SAGE),
        ("Vercel (#4)", COLOR_SLATE),
        ("Daytona (#5)", COLOR_TAUPE)
    ]
    
    legend_x_starts = np.linspace(0.18, 0.82, len(legend_items))
    for x_pos, (label, col) in zip(legend_x_starts, legend_items):
        # Draw dot with thin dark border
        fig.text(x_pos - 0.012, 0.865, "●", color=col, fontsize=14, ha="right", va="center")
        fig.text(x_pos, 0.865, label, color=TEXT_MAIN, fontsize=10.5, weight="bold", ha="left", va="center", family="sans-serif")
        
    # Configure Spines and Minimalist Axes (Anthropic Style: Left and Bottom only)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["left"].set_linewidth(1.3)
    ax.spines["bottom"].set_color("#333333")
    ax.spines["bottom"].set_linewidth(1.3)
    
    ax.set_xlim(28, 92)
    ax.set_ylim(0.96, 1.54)
    
    ax.set_xticks([30, 40, 50, 60, 70, 80, 90])
    ax.set_yticks([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    
    ax.tick_params(colors=TEXT_MAIN, labelsize=11)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=1.0)
    
    ax.set_xlabel("Front-Door ARS 3.0 Score (Higher = More Machine-Discoverable)", 
                  fontsize=11.5, weight="bold", family="sans-serif", color=TEXT_MAIN, labelpad=12)
    ax.set_ylabel("Integration Tax (IT, Lower = Less Agent Friction)", 
                  fontsize=11.5, weight="bold", family="sans-serif", color=TEXT_MAIN, labelpad=12)
    
    # Ideal quadrant shading (Bottom Right: High Discoverability + Low Integration Tax)
    ideal_box = patches.Rectangle((60, 0.96), 32, 0.28, facecolor="#EAF5EA", alpha=0.45, zorder=1)
    ax.add_patch(ideal_box)
    ax.text(89, 0.985, "IDEAL ZONE\n(High Discovery + Low Tax)", ha="right", va="bottom",
            fontsize=9.0, weight="bold", color="#3E754B", family="sans-serif", alpha=0.75)
    
    # Minimalist Trendline
    ars_pts = [36, 75, 82, 69, 48]
    tax_pts = [1.03, 1.17, 1.21, 1.37, 1.43]
    z = np.polyfit(ars_pts, tax_pts, 1)
    p = np.poly1d(z)
    x_trend = np.linspace(32, 88, 40)
    ax.plot(x_trend, p(x_trend), color="#CBCAC4", linestyle="--", linewidth=1.2, zorder=2)
    ax.text(88, p(88) + 0.015, "Linear Trend", color=TEXT_MUTED, fontsize=8.5, ha="right")
    
    # Data Points & Direct Minimalist Typography (NO clunky speech bubbles!)
    # Format: (name, ars, tax, color, label_text, sub_text, text_x_offset, text_y_offset, ha, va)
    points = [
        ("Modal", 36, 1.03, COLOR_BLUE, "Modal Labs (1.03x)", "The Paradox: Grade D front door, dominant #1 at runtime", 1.8, 0.025, "left", "bottom"),
        ("E2B", 75, 1.17, COLOR_RUST, "E2B (1.17x)", "The Balanced Baseline: 0 human stops, lowest tokens", 1.8, -0.025, "left", "top"),
        ("boat", 82, 1.21, COLOR_SAGE, "boat (by ASCII) (1.21x)", "The Inversion: Top front door (82/100), card gate stumble", 1.8, 0.022, "left", "bottom"),
        ("Vercel", 69, 1.37, COLOR_SLATE, "Vercel Sandbox (1.37x)", "Triple-Credential Setup Tax (Token + Project + Team)", 1.8, 0.020, "left", "bottom"),
        ("Daytona", 48, 1.43, COLOR_TAUPE, "Daytona (1.43x)", "Unauthenticated Proxy Barrier (Requires signed preview URLs)", 1.8, 0.022, "left", "bottom")
    ]
    
    for name, ars, tax, col, l_title, l_sub, ox, oy, ha, va in points:
        # Anthropic style marker: Large dot with solid fill and #222222 edge
        ax.scatter(ars, tax, color=col, s=200, edgecolor="#222222", linewidth=1.3, zorder=5)
        
        # Clean typography direct annotation
        ax.text(ars + ox, tax + oy, l_title, fontsize=10.5, weight="bold", color=TEXT_MAIN,
                family="sans-serif", ha=ha, va=va, zorder=6)
        sub_y_shift = -0.022 if va == "bottom" else -0.020
        ax.text(ars + ox, tax + oy + sub_y_shift, l_sub, fontsize=8.5, weight="normal", color=TEXT_MUTED,
                family="sans-serif", ha=ha, va=va, zorder=6)
        
    # Subplot positioning for perfect margins
    fig.subplots_adjust(bottom=0.14, top=0.83, left=0.08, right=0.92)
    
    # Footnote
    fig.text(0.08, 0.025, "Source: Glintbase Integration Index: Sandboxes Edition 1 (October 2026). Preliminary pilot cohort (n=1 deterministic).",
             fontsize=8.5, family="sans-serif", color=TEXT_FOOTNOTE)
    
    out_file = os.path.join(OUTPUT_DIR, "visual2_frontdoor_vs_reality_scatter.png")
    fig.savefig(out_file, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    copy_to_artifact("visual2_frontdoor_vs_reality_scatter.png")
    print(f"Generated Visual 2: {out_file}")

# ==============================================================================
# VISUAL 3: Autonomous Agent Tool Turns by Challenge Stage (Direct Line Graph)
# Strictly matching media_1791326076770.png
# ==============================================================================
def create_challenge_linegraph_visual():
    fig, ax = plt.subplots(figsize=(11, 8.5), facecolor=BG_COLOR, dpi=300)
    ax.set_facecolor(BG_COLOR)
    
    # Title & Subtitle (Exact styling from media_1791326076770.png)
    fig.text(0.5, 0.945, "Autonomous agent tool turns across challenge stages",
             ha="center", va="center", fontsize=24, weight="bold",
             family="sans-serif", color=TEXT_MAIN)
    fig.text(0.5, 0.910, "Glintbase Sandboxes Edition 1 · SWE Complexity Spectrum",
             ha="center", va="center", fontsize=12.5, style="italic",
             family="serif", color=TEXT_MUTED)
    
    # Legend at Top with colored circles and dark rims
    series_meta = [
        ("Modal Labs", COLOR_BLUE, [3, 3, 3, 4, 4, 3]),
        ("E2B", COLOR_RUST, [3, 4, 3, 4, 3, 4]),
        ("boat.dev", COLOR_SAGE, [3, 6, 3, 4, 3, 3]),
        ("Vercel", COLOR_SLATE, [3, 6, 5, 8, 5, 4]),
        ("Daytona", COLOR_TAUPE, [4, 5, 4, 9, 5, 10])
    ]
    
    legend_x_starts = np.linspace(0.18, 0.82, len(series_meta))
    for x_pos, (label, col, _) in zip(legend_x_starts, series_meta):
        fig.text(x_pos - 0.012, 0.865, "●", color=col, fontsize=14, ha="right", va="center")
        fig.text(x_pos, 0.865, label, color=TEXT_MAIN, fontsize=10.5, weight="bold", ha="left", va="center", family="sans-serif")
        
    # Configure Spines and Minimalist Axes (Anthropic Style: Left and Bottom only)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["left"].set_linewidth(1.3)
    ax.spines["bottom"].set_color("#333333")
    ax.spines["bottom"].set_linewidth(1.3)
    
    # X and Y coordinates
    x_indices = np.arange(1, 7)
    x_labels = [
        "1. Hello\nLifecycle",
        "2. Install &\nDependencies",
        "3. State\nPersistence",
        "4. Serve It\n(Ingress)",
        "5. Break It\n(Recovery)",
        "6. Real Job\n(SWE Pytest)"
    ]
    
    ax.set_xlim(0.6, 6.4)
    ax.set_ylim(0, 12)
    ax.set_xticks(x_indices)
    ax.set_xticklabels(x_labels, fontsize=10.5, family="sans-serif", weight="bold", color=TEXT_MAIN)
    ax.set_yticks([0, 2, 4, 6, 8, 10, 12])
    ax.tick_params(colors=TEXT_MAIN, labelsize=11)
    
    ax.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=1.0)
    
    ax.set_ylabel("Agent Tool Turns / Steps (Lower = Less Friction)", 
                  fontsize=11.5, weight="bold", family="sans-serif", color=TEXT_MAIN, labelpad=12)
    ax.set_xlabel("Challenge Progression (Increasing Real-World Complexity)", 
                  fontsize=11.5, weight="bold", family="sans-serif", color=TEXT_MAIN, labelpad=14)
    
    # Plot Lines and Markers
    for name, col, steps in series_meta:
        # Plot continuous trajectory line
        ax.plot(x_indices, steps, color=col, linewidth=2.0, alpha=0.9, zorder=3)
        # Plot circular dots with dark crisp outline (#222222)
        ax.scatter(x_indices, steps, color=col, s=150, edgecolor="#222222", linewidth=1.2, zorder=5)
        
    # Add Direct Point Annotations (Anthropic Style: Clean direct sans-serif labels)
    # boat card gate on T2
    ax.text(2.0, 6.45, "Card Gate [402]", fontsize=9.0, weight="bold", color="#A32418", ha="center", family="sans-serif")
    # Daytona signed URL on T4
    ax.text(4.0, 9.45, "Signed URL Trap [401]", fontsize=9.0, weight="bold", color="#A32418", ha="center", family="sans-serif")
    # Vercel ingress on T4
    ax.text(4.0, 7.35, "SSL Route Setup", fontsize=8.5, weight="bold", color=COLOR_SLATE, ha="center", family="sans-serif")
    # Daytona SWE clone on T6
    ax.text(6.0, 10.45, "10 Steps (Git + Pytest)", fontsize=9.0, weight="bold", color=TEXT_MAIN, ha="center", family="sans-serif")
    # Modal stability callout on T6
    # Subplot positioning for perfect margins
    fig.subplots_adjust(bottom=0.15, top=0.83, left=0.09, right=0.92)
    
    # Footnote
    fig.text(0.09, 0.025, "Glintbase Sandboxes Edition 1: 30 empirical trials. Gemini 3.8 Flash model harness. Zero cloud leaks across all runs.",
             fontsize=8.5, family="sans-serif", color=TEXT_FOOTNOTE)
    
    out_file = os.path.join(OUTPUT_DIR, "visual3_challenge_progression_linegraph.png")
    fig.savefig(out_file, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    copy_to_artifact("visual3_challenge_progression_linegraph.png")
    print(f"Generated Visual 3 (Line Graph): {out_file}")

# ==============================================================================
# VISUAL 4: Integration Tax (IT) Leaderboard Bar Chart
# ==============================================================================
def create_tax_leaderboard_bar_visual():
    fig, ax = plt.subplots(figsize=(10.5, 7.0), facecolor=BG_COLOR, dpi=300)
    ax.set_facecolor(BG_COLOR)
    
    # Title & Subtitle (Anthropic Serif Header)
    fig.text(0.5, 0.948, "Integration Tax (IT) Leaderboard",
             ha="center", va="center", fontsize=24, weight="bold",
             family="serif", color=TEXT_MAIN)
    fig.text(0.5, 0.910, "Compounded Autonomous Agent Overhead Relative to Baseline (1.00x = Ideal)",
             ha="center", va="center", fontsize=12, weight="normal",
             family="sans-serif", color=TEXT_MUTED)
    
    platforms = [
        ("Modal Labs", 1.03, COLOR_BLUE, "Rank #1 · Fastest execution (19.5s), 3.0 steps", "modal"),
        ("E2B", 1.17, COLOR_RUST, "Rank #2 · Lowest tokens (1,865 med), 0 human stops", "e2b"),
        ("boat.dev", 1.21, COLOR_SAGE, "Rank #3 · Easy ingress, 1 stumble on card gate", "boat"),
        ("Vercel", 1.37, COLOR_SLATE, "Rank #4 · 3-key prerequisite, 5.0 median steps", "vercel"),
        ("Daytona", 1.43, COLOR_TAUPE, "Rank #5 · Signed preview URL requirement, 5.0 steps", "daytona")
    ]
    
    platforms.reverse()
    names = [p[0] for p in platforms]
    scores = [p[1] for p in platforms]
    colors = [p[2] for p in platforms]
    subtitles = [p[3] for p in platforms]
    keys = [p[4] for p in platforms]
    
    y_pos = np.arange(len(platforms))
    
    # Minimalist Axes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BORDER_LIGHT)
    ax.spines["bottom"].set_color("#333333")
    ax.spines["bottom"].set_linewidth(1.3)
    
    ax.set_xlim(0.8, 1.6)
    ax.set_ylim(-0.7, 4.5)
    ax.set_xticks([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6])
    ax.set_xticklabels(["1.00x\n(Baseline)", "1.10x", "1.20x", "1.30x", "1.40x", "1.50x", "1.60x"])
    
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.9)
    ax.tick_params(axis="x", colors=TEXT_MAIN, labelsize=10.5)
    ax.tick_params(axis="y", left=False)
    
    # Horizontal Bars with thin dark crisp border
    bars = ax.barh(y_pos, scores, height=0.48, color=colors, edgecolor="#222222", linewidth=1.2, zorder=3)
    
    # Adjust margins for clean left badges
    fig.subplots_adjust(left=0.25, right=0.92, bottom=0.15, top=0.86)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels([]) # Hide default text labels to render custom badge + title layout
    
    for idx, (score, sub, key, name) in enumerate(zip(scores, subtitles, keys, names)):
        # Embed Logo Badge
        if key in BADGES:
            oi = OffsetImage(BADGES[key], zoom=0.21)
            ab = AnnotationBbox(oi, (0.8, idx), xybox=(-125, 0), xycoords='data', boxcoords='offset points', frameon=False, clip_on=False, zorder=5)
            ax.add_artist(ab)
            
        ax.annotate(name, xy=(0.8, idx), xytext=(-98, 0), xycoords='data', textcoords='offset points',
                    ha='left', va='center', fontsize=12.5, weight='bold', color=TEXT_MAIN, family='sans-serif', clip_on=False)
                    
        ax.text(score + 0.015, idx, f"{score:.2f}x", ha="left", va="center",
                fontsize=12.5, weight="bold", color=TEXT_MAIN, family="sans-serif")
        ax.text(1.005, idx - 0.31, sub, ha="left", va="top",
                fontsize=8.5, color=TEXT_MUTED, family="sans-serif")
        
    fig.text(0.12, 0.03, "Evaluated on 30 deterministic trials across 5 providers. Antigravity Agent Harness (Gemini 3.8 Flash). October 2026.",
             fontsize=8.5, family="sans-serif", color=TEXT_FOOTNOTE)
    
    out_file = os.path.join(OUTPUT_DIR, "visual4_integration_tax_leaderboard.png")
    fig.savefig(out_file, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    copy_to_artifact("visual4_integration_tax_leaderboard.png")
    print(f"Generated Visual 4: {out_file}")

# ==============================================================================
# VISUAL 5: Provider × Challenge Friction Heatmap Matrix
# ==============================================================================
def create_heatmap_visual():
    fig = plt.figure(figsize=(11.8, 8.0), facecolor=BG_COLOR, dpi=300)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG_COLOR)
    ax.axis("off")
    
    # Title & Subtitle (Serif Header)
    ax.text(0.5, 0.940, "Friction Matrix: Provider × Challenge Heatmap", 
            ha="center", va="center", fontsize=24, weight="bold", 
            family="serif", color=TEXT_MAIN)
    ax.text(0.5, 0.898, "Tool Turns & Wall Latency per Trial · Highlighted by Human Stops [Hs] and Stumbles [!]", 
            ha="center", va="center", fontsize=12, weight="normal", 
            family="sans-serif", color=TEXT_MUTED)
    
    col_names = ["1. Hello\nLifecycle", "2. Install &\nDependencies", "3. State\nPersistence", "4. Serve It\n(Ingress)", "5. Break It\n(Recovery)", "6. Real Job\n(SWE Test)"]
    row_info = [
        ("Modal Labs", "modal"),
        ("E2B", "e2b"),
        ("boat.dev", "boat"),
        ("Vercel", "vercel"),
        ("Daytona", "daytona")
    ]
    
    # Matrix data: (steps, time_s, has_human_stop, has_stumble)
    matrix = [
        [(3, 16.5, False, False), (3, 18.0, False, False), (3, 17.5, False, False), (4, 24.5, False, False), (4, 21.0, False, False), (3, 26.0, False, False)],
        [(3, 12.4, False, False), (4, 23.5, False, False), (3, 14.2, False, False), (4, 45.0, False, False), (3, 35.0, False, False), (4, 40.0, False, False)],
        [(3, 16.0, False, False), (6, 42.0, True, True), (3, 24.0, False, False), (4, 28.0, False, False), (3, 18.0, False, False), (3, 26.0, False, False)],
        [(3, 15.2, True, False), (6, 28.5, False, False), (5, 22.1, False, False), (8, 36.5, False, False), (5, 21.0, False, False), (4, 18.5, False, False)],
        [(4, 19.5, False, False), (5, 32.4, False, False), (4, 21.0, False, False), (9, 45.0, False, True), (5, 22.4, False, False), (10, 48.0, False, False)]
    ]
    
    start_x = 0.175
    start_y = 0.78
    cell_w = 0.126
    cell_h = 0.105
    
    # Column Headers
    for c_idx, c_name in enumerate(col_names):
        cx = start_x + c_idx * cell_w + cell_w / 2
        ax.text(cx, start_y + 0.038, c_name, ha="center", va="center",
                fontsize=11, weight="bold", color=TEXT_MAIN, family="sans-serif")
        
    # Rows & Cells
    for r_idx, (r_name, r_key) in enumerate(row_info):
        cy = start_y - (r_idx + 1) * cell_h
        y_mid = cy + cell_h / 2
        
        # Row Header: Logo Badge + Provider Name
        if r_key in BADGES:
            oi = OffsetImage(BADGES[r_key], zoom=0.20)
            ab = AnnotationBbox(oi, (0.042, y_mid), frameon=False, zorder=4)
            ax.add_artist(ab)
            
        ax.text(0.066, y_mid, r_name, ha="left", va="center",
                fontsize=12, weight="bold", color=TEXT_MAIN, family="sans-serif")
        
        for c_idx in range(len(col_names)):
            steps, t_sec, is_hs, is_stumble = matrix[r_idx][c_idx]
            cx = start_x + c_idx * cell_w
            
            # Pastel tones matching Anthropic subtlety
            if is_hs or is_stumble or steps >= 8:
                bg = "#FCEAE8" # Subtle pastel coral/red
                border = "#E4AAA3"
            elif steps >= 5 or t_sec >= 35:
                bg = "#FFF6E5" # Subtle pastel amber
                border = "#EBD8AC"
            else:
                bg = "#EFF5EE" # Subtle pastel sage
                border = "#C6DEC5"
                
            rect = patches.FancyBboxPatch((cx + 0.005, cy + 0.005), cell_w - 0.01, cell_h - 0.01,
                                          boxstyle="round,pad=0.006,rounding_size=0.012",
                                          facecolor=bg, edgecolor=border, linewidth=1.1, zorder=2)
            ax.add_patch(rect)
            
            main_text = f"{steps} steps"
            sub_text = f"{t_sec:.1f}s"
            
            tag = ""
            if is_hs and is_stumble:
                tag = " [Hs+!]"
            elif is_hs:
                tag = " [Hs]"
            elif is_stumble:
                tag = " [!]"
                
            ax.text(cx + cell_w / 2, cy + cell_h * 0.62, main_text + tag,
                    ha="center", va="center", fontsize=10.5, weight="bold",
                    color="#A32418" if (is_hs or steps>=8) else TEXT_MAIN, family="sans-serif", zorder=3)
            ax.text(cx + cell_w / 2, cy + cell_h * 0.32, sub_text,
                    ha="center", va="center", fontsize=9.0, weight="normal",
                    color=TEXT_MUTED, family="sans-serif", zorder=3)
            
    # Legend at bottom
    leg_y = 0.12
    ax.text(start_x, leg_y, "Legend:  ■ Smooth (3–4 steps)   ■ Moderate (5–6 steps)   ■ High Friction (8+ steps)   [Hs] = Human Stop   [!] = Stumble / 401/402 retry",
            fontsize=9.0, family="sans-serif", color=TEXT_MUTED)
    ax.text(start_x, leg_y - 0.035, "Evaluation dataset: Glintbase Integration Index (October 2026). Antigravity Harness on Gemini 3.8 Flash.",
            fontsize=8.5, family="sans-serif", color=TEXT_FOOTNOTE)
    
    out_file = os.path.join(OUTPUT_DIR, "visual5_provider_challenge_heatmap.png")
    fig.savefig(out_file, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)
    copy_to_artifact("visual5_provider_challenge_heatmap.png")
    print(f"Generated Visual 5: {out_file}")

if __name__ == "__main__":
    print("Generating visual assets with Anthropic minimalist research aesthetic...")
    create_table_visual()
    create_scatter_matrix_visual()
    create_challenge_linegraph_visual()
    create_tax_leaderboard_bar_visual()
    create_heatmap_visual()
    print("All visuals generated and synced successfully!")
