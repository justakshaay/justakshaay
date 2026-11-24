#!/usr/bin/env python3
"""
Generate:
1. assets/contribution-snake.svg (serpentine contribution grid)
2. assets/streak-stats.svg (Aura-styled Streak Stats card with IST timezone)
3. Update live profile stats (repos, contributions, followers) in README.md

Uses GraphQL API when GITHUB_TOKEN is set, falls back to public REST/HTML scraping.
Zero pip installs - stdlib only.
"""
import os
import json
import re
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR      = Path(__file__).parent
REPO_DIR        = SCRIPT_DIR.parent
OUT_SNAKE_PATH  = REPO_DIR / "assets" / "contribution-snake.svg"
OUT_STREAK_PATH = REPO_DIR / "assets" / "streak-stats.svg"
README_PATH     = REPO_DIR / "README.md"

# ─── Timezone (Asia/Kolkata = UTC+5:30) ───────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

# ─── Aura Palette ─────────────────────────────────────────────────────────────
LEVEL_COLORS = ["#11282c", "#0e7490", "#14b8a6", "#2dd4bf", "#5eead4"]

# ─── Fetch contribution & profile stats via GraphQL ───────────────────────────
def fetch_via_graphql(token):
    query = ('{ user(login: "justakshaay") {'
             ' repositories(privacy: PUBLIC) { totalCount }'
             ' followers { totalCount }'
             ' contributionsCollection {'
             ' contributionCalendar { totalContributions weeks {'
             ' contributionDays { contributionCount date } } } } } }')
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 snake-generator/1.0",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    user = data["data"]["user"]
    repos = user.get("repositories", {}).get("totalCount", 9)
    followers = user.get("followers", {}).get("totalCount", 3)
    cal = user["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    weeks = cal["weeks"]
    days_grid = []
    all_days = []
    for week in weeks:
        col = []
        for d in week["contributionDays"]:
            c = d["contributionCount"]
            col.append(c)
            all_days.append({"date": d["date"], "count": c})
        while len(col) < 7:
            col.append(0)
        days_grid.append(col)
    return total, days_grid, all_days, repos, followers

# ─── Fallback: REST API for repos & followers ─────────────────────────────────
def fetch_user_meta_fallback():
    url = "https://api.github.com/users/justakshaay"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 snake-generator/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        repos = data.get("public_repos", 9)
        followers = data.get("followers", 3)
        return repos, followers
    except Exception as e:
        print(f"User meta REST fallback failed: {e}")
        return 9, 3

# ─── Fallback: scrape GitHub contributions HTML ───────────────────────────────
def fetch_via_html():
    url = "https://github.com/users/justakshaay/contributions"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 snake-generator/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"HTML fallback failed: {e}")
        return 0, [[0]*7 for _ in range(52)], []

    rects = re.findall(
        r'<td[^>]+data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"[^>]*/?>',
        html
    )
    if not rects:
        rects = re.findall(
            r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d)"',
            html
        )

    m = re.search(r'([0-9,]+)\s+contributions\s+in', html, re.I)
    if m:
        total_active = int(m.group(1).replace(',', ''))
    else:
        total_active = sum(1 for _, lvl in rects if int(lvl) > 0)

    all_days = [{"date": d, "count": int(lvl)} for d, lvl in rects]

    days_grid = []
    col = []
    for _date, lvl in rects:
        col.append(int(lvl))
        if len(col) == 7:
            days_grid.append(col)
            col = []
    if col:
        days_grid.append(col + [0] * (7 - len(col)))

    while len(days_grid) < 52:
        days_grid.append([0] * 7)

    return total_active, days_grid, all_days

# ─── Streak Calculation in Asia/Kolkata (IST) ─────────────────────────────────
def format_date_short(d_str):
    if not d_str:
        return ""
    try:
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        return dt.strftime("%b %d")
    except Exception:
        return d_str

def compute_streaks(daily_data, now_dt=None):
    if now_dt is None:
        now_dt = datetime.now(IST)
    today = now_dt.date()
    yesterday = today - timedelta(days=1)

    day_map = {d['date']: d['count'] for d in daily_data}

    # 1. Current streak
    curr_streak = 0
    curr_start = None
    curr_end = None

    if day_map.get(str(today), 0) > 0:
        curr_streak = 1
        curr_start = today
        curr_end = today
        check_d = today - timedelta(days=1)
        while day_map.get(str(check_d), 0) > 0:
            curr_streak += 1
            curr_start = check_d
            check_d -= timedelta(days=1)
    elif day_map.get(str(yesterday), 0) > 0:
        curr_streak = 1
        curr_start = yesterday
        curr_end = yesterday
        check_d = yesterday - timedelta(days=1)
        while day_map.get(str(check_d), 0) > 0:
            curr_streak += 1
            curr_start = check_d
            check_d -= timedelta(days=1)

    # 2. Longest streak
    all_dates = sorted(day_map.keys())
    longest_streak = 0
    longest_start = None
    longest_end = None

    temp_streak = 0
    temp_start = None

    for d_str in all_dates:
        cnt = day_map[d_str]
        if cnt > 0:
            if temp_streak == 0:
                temp_start = d_str
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
                longest_start = temp_start
                longest_end = d_str
        else:
            temp_streak = 0

    if curr_streak > longest_streak:
        longest_streak = curr_streak
        longest_start = str(curr_start)
        longest_end = str(curr_end)

    curr_range_str = f"{format_date_short(str(curr_start))} – {format_date_short(str(curr_end))}" if curr_streak > 0 else "No streak"
    long_range_str = f"{format_date_short(str(longest_start))} – {format_date_short(str(longest_end))}" if longest_streak > 0 else "None"
    total_range_str = "Past 365 Days"
    if all_dates:
        total_range_str = f"{format_date_short(all_dates[0])} – Present"

    return {
        'current_streak': curr_streak,
        'current_range': curr_range_str,
        'longest_streak': longest_streak,
        'longest_range': long_range_str,
        'total_range': total_range_str
    }

# ─── Update Profile Stats in README.md ─────────────────────────────────────────
def update_readme_stats(repos, total_contribs, followers):
    if not README_PATH.exists():
        return
    text = README_PATH.read_text(encoding="utf-8")
    pattern = r"<!-- PROFILE_STATS:START -->.*?<!-- PROFILE_STATS:END -->"
    replacement = (
        "<!-- PROFILE_STATS:START -->\n"
        "      <p>\n"
        f"        <strong>{repos}</strong> public repos<br />\n"
        f"        <strong>{total_contribs}</strong> contributions<br />\n"
        f"        <strong>{followers}</strong> followers\n"
        "      </p>\n"
        "      <!-- PROFILE_STATS:END -->"
    )
    new_text, n = re.subn(pattern, replacement, text, flags=re.DOTALL)
    if n > 0:
        README_PATH.write_text(new_text, encoding="utf-8")
        print(f"Updated README profile stats: {repos} repos, {total_contribs} contributions, {followers} followers")
    else:
        print("Warning: PROFILE_STATS markers not found in README.md")

# ─── Build serpentine snake path ──────────────────────────────────────────────
def build_snake_path(cols, cell_size, gap, grid_x, grid_y):
    pts = []
    num_cols = min(len(cols), 52)
    num_rows = 7
    step = cell_size + gap

    for c in range(num_cols):
        cx = grid_x + c * step + cell_size / 2
        if c % 2 == 0:
            for r in range(num_rows):
                cy = grid_y + r * step + cell_size / 2
                pts.append((cx, cy))
        else:
            for r in range(num_rows - 1, -1, -1):
                cy = grid_y + r * step + cell_size / 2
                pts.append((cx, cy))

    if not pts:
        return "M 0 0"

    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
    for x, y in pts[1:]:
        d += f" L {x:.1f} {y:.1f}"
    return d

# ─── Build Snake Trail SVG ────────────────────────────────────────────────────
def build_snake_svg(total, days):
    W, H = 960, 270
    CELL     = 11
    GAP      = 3.5
    STEP     = CELL + GAP
    COLS     = min(len(days), 52)
    GRID_W   = COLS * STEP - GAP
    GRID_H   = 7 * STEP - GAP
    OUTER_RX = 18
    INNER_INS = 14
    INNER_RX  = 12

    inner_x = INNER_INS
    inner_y = INNER_INS
    inner_w = W - 2 * INNER_INS
    inner_h = H - 2 * INNER_INS

    HEADER_H = 60
    grid_x = inner_x + (inner_w - GRID_W) / 2
    grid_y = inner_y + HEADER_H + (inner_h - HEADER_H - GRID_H) / 2

    snake_path = build_snake_path(days, CELL, GAP, grid_x, grid_y)

    grid_cells = []
    for c in range(COLS):
        col = days[c]
        for r in range(len(col)):
            lvl = min(col[r], 4)
            cx = grid_x + c * STEP
            cy = grid_y + r * STEP
            fade = min(1.0, 0.3 + 0.7 * (c / max(COLS - 1, 1)))
            color = LEVEL_COLORS[lvl]
            grid_cells.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{color}" opacity="{fade:.2f}"/>'
            )

    grid_cells_str = "\n    ".join(grid_cells)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <!-- Outer glow gradient -->
    <radialGradient id="outerGlow" cx="50%" cy="50%" r="60%" fx="20%" fy="30%">
      <stop offset="0%"   stop-color="#14b8a6" stop-opacity="0.55"/>
      <stop offset="35%"  stop-color="#0d9488" stop-opacity="0.35"/>
      <stop offset="70%"  stop-color="#082f49" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#071a19" stop-opacity="0.08"/>
    </radialGradient>
    <!-- Inner panel gradient -->
    <linearGradient id="innerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#0a1f1e" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#061414" stop-opacity="0.88"/>
    </linearGradient>
    <!-- Snake head glow filter -->
    <filter id="headGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <!-- LIVE dot pulse filter -->
    <filter id="dotGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.5"/>
    </filter>
    <!-- Snake motion path -->
    <path id="snakePath" d="{snake_path}" fill="none"/>
  </defs>

  <style>
    @keyframes glowPulse {{
      0%, 100% {{ opacity: 0.55; }}
      50%       {{ opacity: 0.85; }}
    }}
    @keyframes livePulse {{
      0%, 100% {{ opacity: 1; r: 4; }}
      50%       {{ opacity: 0.4; r: 5.5; }}
    }}
    .glow-pulse {{ animation: glowPulse 3.5s ease-in-out infinite; }}
    .live-dot   {{ animation: livePulse 1.4s ease-in-out infinite; }}
  </style>

  <!-- Canvas -->
  <rect width="{W}" height="{H}" fill="#071a19" rx="{OUTER_RX}"/>

  <!-- Outer glow overlay -->
  <rect width="{W}" height="{H}" rx="{OUTER_RX}"
        fill="url(#outerGlow)" class="glow-pulse"/>

  <!-- Outer border -->
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{OUTER_RX}"
        fill="none" stroke="#2dd4bf" stroke-width="1.2" stroke-opacity="0.35"/>

  <!-- Inner recessed panel -->
  <rect x="{INNER_INS}" y="{INNER_INS}"
        width="{W - 2*INNER_INS}" height="{H - 2*INNER_INS}"
        rx="{INNER_RX}" fill="url(#innerGrad)"/>
  <rect x="{INNER_INS+0.5}" y="{INNER_INS+0.5}"
        width="{W - 2*INNER_INS - 1}" height="{H - 2*INNER_INS - 1}"
        rx="{INNER_RX}" fill="none" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.20"/>

  <!-- Header: SNAKE TRAIL label -->
  <text x="{INNER_INS + 14}" y="{INNER_INS + 22}"
        font-family="'JetBrains Mono','Fira Code','Courier New',monospace"
        font-size="9" font-weight="600" fill="#2dd4bf"
        letter-spacing="3">SNAKE TRAIL</text>

  <!-- Header: Contributions count -->
  <text x="{INNER_INS + 14}" y="{INNER_INS + 44}"
        font-family="'JetBrains Mono','Fira Code','Courier New',monospace"
        font-size="15" font-weight="700" fill="#f8fafc"
        letter-spacing="0.3">{total} contributions, one continuous run</text>

  <!-- LIVE label (shifted 8px left of dot) -->
  <text x="{W - INNER_INS - 58}" y="{INNER_INS + 22}"
        font-family="'JetBrains Mono','Fira Code','Courier New',monospace"
        font-size="9" font-weight="600" fill="#99f6e4"
        letter-spacing="3">LIVE</text>

  <!-- LIVE pulsing dot -->
  <circle cx="{W - INNER_INS - 18}" cy="{INNER_INS + 18}"
          r="4" fill="#2dd4bf" class="live-dot"/>
  <circle cx="{W - INNER_INS - 18}" cy="{INNER_INS + 18}"
          r="7" fill="#2dd4bf" opacity="0.18" filter="url(#dotGlow)"/>

  <!-- Contribution grid cells -->
  <g id="grid">
    {grid_cells_str}
  </g>

  <!-- Snake trailing dots (behind head) -->
  <circle r="2.0" fill="#5eead4" opacity="0.20">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.70s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <circle r="2.5" fill="#5eead4" opacity="0.35">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.56s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <circle r="3.0" fill="#2dd4bf" opacity="0.50">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.42s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <circle r="3.8" fill="#2dd4bf" opacity="0.68">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.28s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <circle r="4.5" fill="#99f6e4" opacity="0.85">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.14s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>

  <!-- Snake head group -->
  <g filter="url(#headGlow)">
    <rect x="-7" y="-5" width="14" height="10" rx="4"
          fill="#99f6e4" opacity="0.95">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </rect>
    <circle cx="-2" cy="-2" r="1.6" fill="#071a19">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </circle>
    <circle cx="2" cy="-2" r="1.6" fill="#071a19">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </circle>
  </g>
</svg>'''
    return svg

# ─── Build Streak Stats SVG (Aura Styled, 495x195) ────────────────────────────
def build_streak_svg(total, current_streak, curr_range, longest_streak, long_range, total_range):
    W, H = 495, 195
    OUTER_RX = 14
    INNER_INS = 10
    INNER_RX = 10

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <!-- Outer glow gradient -->
    <radialGradient id="outerGlowStreak" cx="50%" cy="50%" r="60%" fx="20%" fy="30%">
      <stop offset="0%"   stop-color="#14b8a6" stop-opacity="0.50"/>
      <stop offset="35%"  stop-color="#0d9488" stop-opacity="0.30"/>
      <stop offset="70%"  stop-color="#082f49" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#071a19" stop-opacity="0.08"/>
    </radialGradient>
    <!-- Inner panel gradient -->
    <linearGradient id="innerGradStreak" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#0a1f1e" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#061414" stop-opacity="0.90"/>
    </linearGradient>
    <!-- Flame glow filter -->
    <filter id="flameGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <style>
    @keyframes glowPulseStreak {{
      0%, 100% {{ opacity: 0.55; }}
      50%       {{ opacity: 0.85; }}
    }}
    @keyframes flamePulse {{
      0%, 100% {{ transform: scale(1); opacity: 0.95; }}
      50%       {{ transform: scale(1.12); opacity: 1; }}
    }}
    .glow-pulse-streak {{ animation: glowPulseStreak 3.5s ease-in-out infinite; }}
    .flame-icon {{ animation: flamePulse 2s ease-in-out infinite; transform-origin: 247.5px 44px; }}
  </style>

  <!-- Canvas -->
  <rect width="{W}" height="{H}" fill="#071a19" rx="{OUTER_RX}"/>

  <!-- Outer glow overlay -->
  <rect width="{W}" height="{H}" rx="{OUTER_RX}"
        fill="url(#outerGlowStreak)" class="glow-pulse-streak"/>

  <!-- Outer border -->
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{OUTER_RX}"
        fill="none" stroke="#2dd4bf" stroke-width="1.2" stroke-opacity="0.35"/>

  <!-- Inner recessed panel -->
  <rect x="{INNER_INS}" y="{INNER_INS}"
        width="{W - 2*INNER_INS}" height="{H - 2*INNER_INS}"
        rx="{INNER_RX}" fill="url(#innerGradStreak)"/>
  <rect x="{INNER_INS+0.5}" y="{INNER_INS+0.5}"
        width="{W - 2*INNER_INS - 1}" height="{H - 2*INNER_INS - 1}"
        rx="{INNER_RX}" fill="none" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.20"/>

  <!-- Top Micro-Header -->
  <text x="247.5" y="27"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="9" font-weight="600" fill="#2dd4bf"
        letter-spacing="2.5">STREAK TELEMETRY // ASIA-KOLKATA</text>

  <!-- Column Dividers -->
  <line x1="168" y1="36" x2="168" y2="162" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.20"/>
  <line x1="327" y1="36" x2="327" y2="162" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.20"/>

  <!-- ==================== COLUMN 1: TOTAL CONTRIBUTIONS ==================== -->
  <text x="89" y="86"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="28" font-weight="700" fill="#f8fafc">{total}</text>
  <text x="89" y="116"
        text-anchor="middle"
        font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font-size="13" font-weight="600" fill="#2dd4bf">Total Contributions</text>
  <text x="89" y="142"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="10.5" fill="#94a3b8">{total_range}</text>

  <!-- ==================== COLUMN 2: CURRENT STREAK ==================== -->
  <g class="flame-icon" filter="url(#flameGlow)">
    <path d="M 247.5 35 C 249.5 38 253.5 41 253.5 45 C 253.5 49 250.5 52 247.5 53 C 244.5 52 241.5 49 241.5 45 C 241.5 41 244.5 38 246.5 36 C 246.5 38 247.5 40 248.5 42 C 249.5 43.5 249 45.5 247.5 47 C 246.5 45.5 246.5 43 247.5 35 Z"
          fill="#2dd4bf"/>
  </g>
  <text x="247.5" y="86"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="30" font-weight="800" fill="#2dd4bf">{current_streak} days</text>
  <text x="247.5" y="116"
        text-anchor="middle"
        font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font-size="13" font-weight="700" fill="#99f6e4">Current Streak</text>
  <text x="247.5" y="142"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="10.5" font-weight="600" fill="#5eead4">{curr_range}</text>

  <!-- ==================== COLUMN 3: LONGEST STREAK ==================== -->
  <text x="406" y="86"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="28" font-weight="700" fill="#f8fafc">{longest_streak} days</text>
  <text x="406" y="116"
        text-anchor="middle"
        font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font-size="13" font-weight="600" fill="#2dd4bf">Longest Streak</text>
  <text x="406" y="142"
        text-anchor="middle"
        font-family="'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
        font-size="10.5" fill="#94a3b8">{long_range}</text>
</svg>'''
    return svg

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    total = 0
    days_grid = []
    all_days = []
    repos = 9
    followers = 3

    if token:
        print("Fetching via GraphQL API...")
        try:
            total, days_grid, all_days, repos, followers = fetch_via_graphql(token)
            print(f"GraphQL: {total} total contributions, {len(days_grid)} weeks, {len(all_days)} days, {repos} repos, {followers} followers")
        except Exception as e:
            print(f"GraphQL failed ({e}), falling back to HTML & REST...")
            total, days_grid, all_days = fetch_via_html()
            repos, followers = fetch_user_meta_fallback()
    else:
        print("No GITHUB_TOKEN — falling back to HTML & REST...")
        total, days_grid, all_days = fetch_via_html()
        repos, followers = fetch_user_meta_fallback()

    print(f"Live stats: {repos} repos, {total} contributions, {followers} followers")

    # 1. Update profile stats in README.md
    update_readme_stats(repos, total, followers)

    # 2. Compute streaks in Asia/Kolkata (IST)
    streak_data = compute_streaks(all_days)
    print(f"Streak data (IST): {streak_data}")

    # 3. Generate Snake Trail SVG
    snake_svg_str = build_snake_svg(total, days_grid)
    try:
        ET.fromstring(snake_svg_str)
        print("Snake SVG XML validation: PASS")
    except ET.ParseError as e:
        print(f"Snake SVG XML validation FAILED: {e}")
        raise

    OUT_SNAKE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_SNAKE_PATH.write_text(snake_svg_str, encoding="utf-8")
    print(f"Written: {OUT_SNAKE_PATH}")

    # 4. Generate Streak Stats SVG
    streak_svg_str = build_streak_svg(
        total=total,
        current_streak=streak_data['current_streak'],
        curr_range=streak_data['current_range'],
        longest_streak=streak_data['longest_streak'],
        long_range=streak_data['longest_range'],
        total_range=streak_data['total_range']
    )
    try:
        ET.fromstring(streak_svg_str)
        print("Streak SVG XML validation: PASS")
    except ET.ParseError as e:
        print(f"Streak SVG XML validation FAILED: {e}")
        raise

    OUT_STREAK_PATH.write_text(streak_svg_str, encoding="utf-8")
    print(f"Written: {OUT_STREAK_PATH}")

if __name__ == "__main__":
    main()
