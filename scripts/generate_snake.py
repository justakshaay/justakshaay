#!/usr/bin/env python3
"""
Generate assets/contribution-snake.svg with real GitHub contribution data.
Uses GraphQL API when GITHUB_TOKEN is set, falls back to HTML scraping.
Zero pip installs - stdlib only.
"""
import os
import json
import re
import xml.etree.ElementTree as ET
import urllib.request
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
OUT_PATH   = REPO_DIR / "assets" / "contribution-snake.svg"

# ─── Aura Palette ─────────────────────────────────────────────────────────────
LEVEL_COLORS = ["#11282c", "#0e7490", "#14b8a6", "#2dd4bf", "#5eead4"]

# ─── Fetch contribution data via GraphQL ──────────────────────────────────────
def fetch_via_graphql(token):
    query = ('{ user(login: "justakshaay") { contributionsCollection {'
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
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    days = []
    for week in cal["weeks"]:
        col = [d["contributionCount"] for d in week["contributionDays"]]
        # pad to 7 rows
        while len(col) < 7:
            col.append(0)
        days.append(col)
    return total, days  # days[col_idx][row_idx], up to 53 cols x 7 rows

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
        return 0, [[0]*7 for _ in range(52)]

    # Match data-date and data-level attributes in any order
    rects = re.findall(
        r'<td[^>]+data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"[^>]*/?>',
        html
    )
    if not rects:
        # Try alternate attribute order
        rects = re.findall(
            r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d)"',
            html
        )

    # Extract total contribution count from heading (e.g. "86 contributions in the last year")
    m = re.search(r'([0-9,]+)\s+contributions\s+in', html, re.I)
    if m:
        total_active = int(m.group(1).replace(',', ''))
    else:
        total_active = sum(1 for _, lvl in rects if int(lvl) > 0)

    # Build columns of 7 days each
    days = []
    col = []
    for _date, lvl in rects:
        col.append(int(lvl))
        if len(col) == 7:
            days.append(col)
            col = []
    if col:
        days.append(col + [0] * (7 - len(col)))

    # Ensure at least 52 columns
    while len(days) < 52:
        days.append([0] * 7)

    return total_active, days

# ─── Build serpentine snake path ──────────────────────────────────────────────
def build_snake_path(cols, cell_size, gap, grid_x, grid_y):
    """
    Build an SVG path that snakes column-by-column through the contribution grid.
    Even columns go top→bottom, odd columns go bottom→top.
    Returns path d attribute string.
    """
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

# ─── Build the full SVG string ────────────────────────────────────────────────
def build_svg(total, days):
    W, H = 960, 270
    # Layout constants
    CELL     = 11
    GAP      = 3.5
    STEP     = CELL + GAP
    COLS     = min(len(days), 52)
    GRID_W   = COLS * STEP - GAP
    GRID_H   = 7 * STEP - GAP
    OUTER_RX = 18
    INNER_INS = 14
    INNER_RX  = 12

    # Center grid in inner panel
    inner_x = INNER_INS
    inner_y = INNER_INS
    inner_w = W - 2 * INNER_INS
    inner_h = H - 2 * INNER_INS

    HEADER_H = 60
    grid_x = inner_x + (inner_w - GRID_W) / 2
    grid_y = inner_y + HEADER_H + (inner_h - HEADER_H - GRID_H) / 2

    # Snake path
    snake_path = build_snake_path(days, CELL, GAP, grid_x, grid_y)

    # Build contribution grid cells
    grid_cells = []
    for c in range(COLS):
        col = days[c]
        for r in range(len(col)):
            lvl = min(col[r], 4)
            cx = grid_x + c * STEP
            cy = grid_y + r * STEP
            # Fade mask: cells near left edge get lower opacity
            fade = min(1.0, 0.3 + 0.7 * (c / max(COLS - 1, 1)))
            color = LEVEL_COLORS[lvl]
            grid_cells.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{color}" opacity="{fade:.2f}"/>'
            )

    grid_cells_str = "\n    ".join(grid_cells)

    # Snake animation total distance (approximate)
    total_pts = COLS * 7
    # We'll use 28s for a full loop

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
    @keyframes trail5 {{
      0%   {{ opacity: 0.85; }}
      100% {{ opacity: 0.0; }}
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

  <!-- LIVE label -->
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
  <!-- Dot 5 (farthest) -->
  <circle r="2.0" fill="#5eead4" opacity="0.20">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.70s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <!-- Dot 4 -->
  <circle r="2.5" fill="#5eead4" opacity="0.35">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.56s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <!-- Dot 3 -->
  <circle r="3.0" fill="#2dd4bf" opacity="0.50">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.42s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <!-- Dot 2 -->
  <circle r="3.8" fill="#2dd4bf" opacity="0.68">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.28s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>
  <!-- Dot 1 (closest to head) -->
  <circle r="4.5" fill="#99f6e4" opacity="0.85">
    <animateMotion dur="28s" repeatCount="indefinite" begin="-0.14s" rotate="auto">
      <mpath xlink:href="#snakePath"/>
    </animateMotion>
  </circle>

  <!-- Snake head group -->
  <g filter="url(#headGlow)">
    <!-- Head body: glowing rounded rect -->
    <rect x="-7" y="-5" width="14" height="10" rx="4"
          fill="#99f6e4" opacity="0.95">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </rect>
    <!-- Left eye -->
    <circle cx="-2" cy="-2" r="1.6" fill="#071a19">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </circle>
    <!-- Right eye -->
    <circle cx="2" cy="-2" r="1.6" fill="#071a19">
      <animateMotion dur="28s" repeatCount="indefinite" rotate="auto">
        <mpath xlink:href="#snakePath"/>
      </animateMotion>
    </circle>
  </g>
</svg>'''
    return svg

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    total = 0
    days  = []

    if token:
        print("Fetching via GraphQL API...")
        try:
            total, days = fetch_via_graphql(token)
            print(f"GraphQL: {total} total contributions, {len(days)} weeks")
        except Exception as e:
            print(f"GraphQL failed ({e}), falling back to HTML scrape...")
            total, days = fetch_via_html()
    else:
        print("No GITHUB_TOKEN — falling back to HTML scrape...")
        total, days = fetch_via_html()

    print(f"Total contributions: {total}, grid columns: {len(days)}")

    svg_str = build_svg(total, days)

    # Validate XML before writing
    try:
        ET.fromstring(svg_str)
        print("XML validation: PASS")
    except ET.ParseError as e:
        print(f"XML validation FAILED: {e}")
        raise

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg_str, encoding="utf-8")
    print(f"Written: {OUT_PATH}")

if __name__ == "__main__":
    main()
