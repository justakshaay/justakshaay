#!/usr/bin/env python3
"""
Generate assets/chess-board.svg
Aura glassmorphic chess board with fluid 60fps CSS transform ping-pong animations.
Strict coordinate math, zero collision with grid lines, nested groups for CSS transforms.
Pure SVG CSS – no JavaScript, no external dependencies.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
OUT_PATH   = REPO_DIR / "assets" / "chess-board.svg"

# ─── Strict Grid Layout ───────────────────────────────────────────────────────
W, H     = 480, 480
BOARD_X  = 48
BOARD_Y  = 48
S        = 48       # Square size (px), 8 * 48 = 384x384 board
HALF_S   = S // 2   # 24px

def sq_center(col, row):
    """col 0..7 (a..h), row 0..7 (8..1)"""
    return BOARD_X + col * S + HALF_S, BOARD_Y + row * S + HALF_S

# ─── Staunton Piece Definitions (Strictly inside 24x26 box centered at (0,0)) ─
# Bounding box of every piece is within X in [-11, 11] and Y in [-14, 12],
# leaving at least 10px of breathing room from the 48x48 square borders on all 4 sides.
PIECE_PATHS = {
    # PAWN: base y=12, body, collar, head y=-11
    "P": "M -9,12 L 9,12 C 7,12 7,9 5,9 C 4,9 4,4 5,2 C 7,1 8,-1 8,-4 C 8,-8 4,-11 0,-11 C -4,-11 -8,-8 -8,-4 C -8,-1 -7,1 -5,2 C -4,4 -4,9 -5,9 C -7,9 -7,12 -9,12 Z",

    # ROOK: base y=12, tower, battlements top y=-12
    "R": "M -10,12 L 10,12 C 8,12 8,9 6,9 L 6,-4 L 9,-4 L 9,-12 L 5,-12 L 5,-8 L 2,-8 L 2,-12 L -2,-12 L -2,-8 L -5,-8 L -5,-12 L -9,-12 L -9,-4 L -6,-4 L -6,9 C -8,9 -8,12 -10,12 Z",

    # KNIGHT: horse head, snout, ears top y=-13, mane, base y=12
    "N": "M -10,12 L 10,12 C 8,12 8,9 6,9 C 6,7 8,5 9,1 C 10,-3 9,-7 7,-10 C 6,-12 4,-13 2,-13 C 0,-13 0,-11 -2,-9 C -3,-9 -6,-7 -9,-5 C -11,-3 -10,0 -8,1 C -6,2 -5,4 -5,9 C -7,9 -7,12 -10,12 Z",

    # BISHOP: base y=12, curved body, mitre with top finial ball at y=-14
    "B": "M -10,12 L 10,12 C 8,12 8,9 5,9 C 4,7 5,3 6,0 C 7,-4 7,-8 4,-11 C 3,-12 1,-12 1,-14 C 1,-15 0,-15 0,-14 C 0,-12 -2,-12 -3,-11 C -6,-8 -6,-4 -5,0 C -4,3 -3,7 -4,9 C -7,9 -7,12 -10,12 Z",

    # QUEEN: base y=12, flared gown, 5-point crown with center peak at y=-13
    "Q": "M -11,12 L 11,12 C 9,12 8,9 5,9 L 9,-2 L 9,-10 L 5,-6 L 0,-13 L -5,-6 L -9,-10 L -9,-2 L -5,9 C -8,9 -9,12 -11,12 Z",

    # KING: base y=12, robe, crown, cross on top (cross bar y=-11, tip y=-14)
    "K": "M -11,12 L 11,12 C 9,12 8,9 6,9 C 7,6 8,1 7,-3 C 6,-6 4,-7 2,-8 L 2,-10 L 4,-10 L 4,-12 L 2,-12 L 2,-14 L -2,-14 L -2,-12 L -4,-12 L -4,-10 L -2,-10 L -2,-8 C -4,-7 -6,-6 -7,-3 C -8,1 -7,6 -6,9 C -8,9 -9,12 -11,12 Z"
}

# ─── Standard Chess Board Layout ──────────────────────────────────────────────
# (piece, col 0..7 for a..h, row 0..7 for 8..1, side 'w'/'b')
START_PIECES = [
    # Rank 8 (row 0) - Black back rank
    ('R', 0, 0, 'b'), ('N', 1, 0, 'b'), ('B', 2, 0, 'b'), ('Q', 3, 0, 'b'),
    ('K', 4, 0, 'b'), ('B', 5, 0, 'b'), ('N', 6, 0, 'b'), ('R', 7, 0, 'b'),
    # Rank 7 (row 1) - Black pawns
    ('P', 0, 1, 'b'), ('P', 1, 1, 'b'), ('P', 2, 1, 'b'), ('P', 3, 1, 'b'),
    ('P', 4, 1, 'b'), ('P', 5, 1, 'b'), ('P', 6, 1, 'b'), ('P', 7, 1, 'b'),
    # Rank 2 (row 6) - White pawns
    ('P', 0, 6, 'w'), ('P', 1, 6, 'w'), ('P', 2, 6, 'w'), ('P', 3, 6, 'w'),
    ('P', 4, 6, 'w'), ('P', 5, 6, 'w'), ('P', 6, 6, 'w'), ('P', 7, 6, 'w'),
    # Rank 1 (row 7) - White back rank
    ('R', 0, 7, 'w'), ('N', 1, 7, 'w'), ('B', 2, 7, 'w'), ('Q', 3, 7, 'w'),
    ('K', 4, 7, 'w'), ('B', 5, 7, 'w'), ('N', 6, 7, 'w'), ('R', 7, 7, 'w'),
]

# ─── Animated Moves (Italian Game: e4, e5, Nf3, Nc6, Bc4, Bc5) ───────────────
# (col, row, dx, dy, css_class, delay)
# Square size S = 48
ANIMATED_MOVES = [
    (4, 6,    0,  -96, "move-e2-e4", "0s"),      # 1. White Pawn e2 -> e4 (row 6 -> row 4: dy = -2*48)
    (4, 1,    0,   96, "move-e7-e5", "-1.4s"),   # 1. Black Pawn e7 -> e5 (row 1 -> row 3: dy = +2*48)
    (6, 7,  -48,  -96, "move-g1-f3", "-2.8s"),   # 2. White Knight g1 -> f3 (col 6->5: dx=-48, row 7->5: dy=-96)
    (1, 0,   48,   96, "move-b8-c6", "-4.2s"),   # 2. Black Knight b8 -> c6 (col 1->2: dx=48, row 0->2: dy=96)
    (5, 7, -144, -144, "move-f1-c4", "-5.6s"),   # 3. White Bishop f1 -> c4 (col 5->2: dx=-144, row 7->4: dy=-144)
    (5, 0, -144,  144, "move-f8-c5", "-7.0s"),   # 3. Black Bishop f8 -> c5 (col 5->2: dx=-144, row 0->3: dy=144)
]

ANIM_MAP = {(col, row): (dx, dy, cls, delay) for col, row, dx, dy, cls, delay in ANIMATED_MOVES}

def build_css():
    lines = [
        "@keyframes glowPulse { 0%,100% { opacity:0.55; } 50% { opacity:0.9; } }",
        ".gp { animation: glowPulse 3.5s ease-in-out infinite; }",
    ]
    ease = "cubic-bezier(0.42, 0, 0.58, 1)"
    for _col, _row, dx, dy, cls, delay in ANIMATED_MOVES:
        kf_name = "kf-" + cls.replace("move-", "")
        kf = (
            f"    @keyframes {kf_name} {{\n"
            f"      0%   {{ transform: translate(0px, 0px); }}\n"
            f"      40%  {{ transform: translate({dx}px, {dy}px); }}\n"
            f"      55%  {{ transform: translate({dx}px, {dy}px); }}\n"
            f"      90%  {{ transform: translate(0px, 0px); }}\n"
            f"      100% {{ transform: translate(0px, 0px); }}\n"
            f"    }}\n"
            f"    .{cls} {{\n"
            f"      animation: {kf_name} 10s {ease} infinite;\n"
            f"      animation-delay: {delay};\n"
            f"    }}"
        )
        lines.append(kf)
    return "\n".join(lines)

def main():
    # ── Board Squares (64 cells) ──
    squares = []
    for row in range(8):
        for col in range(8):
            x = BOARD_X + col * S
            y = BOARD_Y + row * S
            # FIDE standard: h1 is light, a1 is dark
            clr = "#165a5c" if (col + row) % 2 == 0 else "#0c3b3d"
            squares.append(f'<rect x="{x}" y="{y}" width="{S}" height="{S}" fill="{clr}"/>')

    # ── Coordinate Labels ──
    font_attrs = ('font-family="\'Courier New\',Courier,monospace" '
                  'font-size="11" fill="#5eead4" text-anchor="middle"')
    labels = []
    # Rank labels on left (8 down to 1)
    for row in range(8):
        lx = BOARD_X - 16
        ly = BOARD_Y + row * S + HALF_S + 4
        labels.append(f'<text x="{lx}" y="{ly}" {font_attrs}>{8 - row}</text>')
    # File labels on bottom (a through h)
    for col in range(8):
        lx = BOARD_X + col * S + HALF_S
        ly = BOARD_Y + 8 * S + 20
        labels.append(f'<text x="{lx}" y="{ly}" {font_attrs}>{chr(ord("a") + col)}</text>')

    # ── Piece Definitions in <defs> ──
    defs_pieces = []
    for p_name, d_str in PIECE_PATHS.items():
        defs_pieces.append(f'<path id="p-{p_name}" d="{d_str}"/>')
    defs_str = "\n    ".join(defs_pieces)

    # ── Pieces Layout (Nested <g> for animated pieces to prevent CSS override) ──
    static_pieces = []
    animated_pieces = []

    for piece, col, row, side in START_PIECES:
        cx, cy = sq_center(col, row)
        fill   = "#ecfeff" if side == 'w' else "#99f6e4"
        stroke = "#0891b2" if side == 'w' else "#134e4a"
        gfilt  = "wGlow"  if side == 'w' else "bGlow"

        if (col, row) in ANIM_MAP:
            _dx, _dy, cls, _delay = ANIM_MAP[(col, row)]
            # CRITICAL: Outer <g> sets static coordinate transform="translate(cx, cy)".
            # Inner <g> receives ONLY relative CSS @keyframes translation via class.
            piece_elem = (
                f'<g transform="translate({cx},{cy})">\n'
                f'      <g class="{cls}" filter="url(#{gfilt})">\n'
                f'        <use href="#p-{piece}" xlink:href="#p-{piece}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-linejoin="round"/>\n'
                f'      </g>\n'
                f'    </g>'
            )
            animated_pieces.append(piece_elem)
        else:
            piece_elem = (
                f'<g transform="translate({cx},{cy})" filter="url(#{gfilt})">\n'
                f'      <use href="#p-{piece}" xlink:href="#p-{piece}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-linejoin="round"/>\n'
                f'    </g>'
            )
            static_pieces.append(piece_elem)

    # Animated pieces placed AFTER static pieces in DOM for clean stacking/z-order
    all_pieces_str = "\n    ".join(static_pieces + animated_pieces)
    sq_str = "\n    ".join(squares)
    lb_str = "\n    ".join(labels)
    css_str = build_css()
    BW = 8 * S  # 384px

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n'
        f'     viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
        '  <defs>\n'
        '    <radialGradient id="outerGlow" cx="50%" cy="50%" r="60%">\n'
        '      <stop offset="0%"   stop-color="#14b8a6" stop-opacity="0.55"/>\n'
        '      <stop offset="35%"  stop-color="#0d9488" stop-opacity="0.35"/>\n'
        '      <stop offset="70%"  stop-color="#082f49" stop-opacity="0.20"/>\n'
        '      <stop offset="100%" stop-color="#071a19" stop-opacity="0.08"/>\n'
        '    </radialGradient>\n'
        '    <linearGradient id="innerGrad" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%"   stop-color="#0a1f1e" stop-opacity="0.95"/>\n'
        '      <stop offset="100%" stop-color="#061414" stop-opacity="0.88"/>\n'
        '    </linearGradient>\n'
        '    <!-- White piece glow: cyan halo -->\n'
        '    <filter id="wGlow" x="-50%" y="-50%" width="200%" height="200%">\n'
        '      <feGaussianBlur in="SourceAlpha" stdDeviation="2.5" result="blur"/>\n'
        '      <feFlood flood-color="#22d3ee" flood-opacity="0.60" result="color"/>\n'
        '      <feComposite in="color" in2="blur" operator="in" result="glow"/>\n'
        '      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>\n'
        '    </filter>\n'
        '    <!-- Black piece glow: teal halo -->\n'
        '    <filter id="bGlow" x="-50%" y="-50%" width="200%" height="200%">\n'
        '      <feGaussianBlur in="SourceAlpha" stdDeviation="2.0" result="blur"/>\n'
        '      <feFlood flood-color="#14b8a6" flood-opacity="0.50" result="color"/>\n'
        '      <feComposite in="color" in2="blur" operator="in" result="glow"/>\n'
        '      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>\n'
        '    </filter>\n'
        f'    {defs_str}\n'
        '  </defs>\n'
        '\n'
        f'  <style>\n{css_str}\n  </style>\n'
        '\n'
        '  <!-- ── Aura Double-Frame ── -->\n'
        f'  <rect width="{W}" height="{H}" fill="#071a19" rx="20"/>\n'
        f'  <rect width="{W}" height="{H}" rx="20" fill="url(#outerGlow)" class="gp"/>\n'
        f'  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20"\n'
        '        fill="none" stroke="#2dd4bf" stroke-width="1.2" stroke-opacity="0.35"/>\n'
        f'  <rect x="14" y="14" width="{W-28}" height="{H-28}" rx="14" fill="url(#innerGrad)"/>\n'
        f'  <rect x="14.5" y="14.5" width="{W-29}" height="{H-29}" rx="14"\n'
        '        fill="none" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.22"/>\n'
        '\n'
        '  <!-- ── Chess Board (384x384, Centered) ── -->\n'
        '  <g id="board">\n'
        f'    {sq_str}\n'
        '  </g>\n'
        '\n'
        '  <!-- Board border -->\n'
        f'  <rect x="{BOARD_X}" y="{BOARD_Y}" width="{BW}" height="{BW}"\n'
        '        fill="none" stroke="#2dd4bf" stroke-width="0.8" stroke-opacity="0.35"/>\n'
        '\n'
        '  <!-- ── Coordinate Labels ── -->\n'
        '  <g id="coords">\n'
        f'    {lb_str}\n'
        '  </g>\n'
        '\n'
        '  <!-- ── Chess Pieces (Static pieces first, animated pieces in front) ── -->\n'
        '  <g id="pieces">\n'
        f'    {all_pieces_str}\n'
        '  </g>\n'
        '</svg>'
    )

    # ── Validate XML ──
    try:
        ET.fromstring(svg)
        print("XML validation: PASS")
    except ET.ParseError as e:
        print(f"XML validation FAILED: {e}")
        raise

    # ── Write output ──
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Written: {OUT_PATH}")
    print(f"Size:    {OUT_PATH.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
