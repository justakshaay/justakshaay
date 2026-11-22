#!/usr/bin/env python3
"""
Generate assets/chess-board.svg
Aura glassmorphic chess board with Italian Game opening animation.
Pure SVG CSS – no JavaScript, no SMIL, no external resources.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
OUT_PATH   = REPO_DIR / "assets" / "chess-board.svg"

# ─── Layout ───────────────────────────────────────────────────────────────────
W, H = 480, 480
SQ   = 50       # chess square size (px)
BX   = 42       # board left edge x  (28px from inner panel left for rank labels)
BY   = 26       # board top edge y   (12px from inner panel top)

def sq_cx(f): return BX + f * SQ + SQ // 2       # center x of file f (0=a..7=h)
def sq_cy(r): return BY + (7 - r) * SQ + SQ // 2 # center y of rank r (0=rank1 bottom)

# ─── Piece SVG paths (all centered at origin 0,0) ────────────────────────────
# Design principle: recognizable Staunton-inspired silhouettes at 50px square.
PP = {
    # PAWN: round head, narrow neck, wide base
    "P": ("M 0,-17 C -5,-17 -6,-12 -4,-9 "
          "C -7,-8 -9,-5 -9,-1 L -12,-1 L -12,2 L 12,2 "
          "L 12,-1 L 9,-1 C 9,-5 7,-8 4,-9 "
          "C 6,-12 5,-17 0,-17 Z"),

    # ROOK: flat base, rectangular body, three crenellations
    "R": ("M -12,2 L 12,2 L 12,-2 L 9,-2 L 9,-12 "
          "L 12,-12 L 12,-17 L 7,-17 L 7,-14 L 2,-14 "
          "L 2,-17 L -2,-17 L -2,-14 L -7,-14 L -7,-17 "
          "L -12,-17 L -12,-12 L -9,-12 L -9,-2 L -12,-2 Z"),

    # KNIGHT: horse-head silhouette with curved neck and ear
    "N": ("M -12,2 L 12,2 L 12,-2 L 9,-2 L 9,-4 "
          "C 12,-6 13,-10 11,-14 C 10,-17 7,-20 4,-21 "
          "C 5,-22 6,-24 4,-25 C 2,-26 0,-25 -1,-23 "
          "C -2,-21 -4,-20 -6,-19 C -10,-18 -12,-14 -12,-9 "
          "L -12,-2 Z"),

    # BISHOP: mitre tip, tall tapered body, wide base
    "B": ("M 0,-23 C -1,-26 1,-26 0,-23 "
          "C -3,-20 -5,-16 -5,-11 C -7,-9 -9,-6 -9,-2 "
          "L -12,-2 L -12,2 L 12,2 L 12,-2 L 9,-2 "
          "C 9,-6 7,-9 5,-11 C 5,-16 3,-20 0,-23 Z"),

    # QUEEN: crown with 5 points (3 visible), tapered body
    "Q": ("M -13,2 L 13,2 L 13,-2 L 10,-2 "
          "C 10,-6 8,-10 6,-12 L 9,-19 L 6,-22 L 3,-16 "
          "L 0,-21 L -3,-16 L -6,-22 L -9,-19 L -6,-12 "
          "C -8,-10 -10,-6 -10,-2 L -13,-2 Z"),

    # KING: cross on top, wide body
    "K": ("M -13,2 L 13,2 L 13,-2 L 10,-2 "
          "C 10,-7 8,-11 5,-14 L -5,-14 "
          "C -8,-11 -10,-7 -10,-2 L -13,-2 Z "
          "M -2,-14 L -2,-20 L -5,-20 L -5,-23 "
          "L -2,-23 L -2,-28 L 2,-28 L 2,-23 "
          "L 5,-23 L 5,-20 L 2,-20 L 2,-14 Z"),
}

# ─── Standard chess starting position ─────────────────────────────────────────
# (piece, file 0=a..7=h, rank 0=rank1(bottom)..7=rank8(top), side 'w'/'b')
START = [
    # White back rank (rank 1)
    ('R',0,0,'w'), ('N',1,0,'w'), ('B',2,0,'w'), ('Q',3,0,'w'),
    ('K',4,0,'w'), ('B',5,0,'w'), ('N',6,0,'w'), ('R',7,0,'w'),
    # White pawns (rank 2)
    ('P',0,1,'w'), ('P',1,1,'w'), ('P',2,1,'w'), ('P',3,1,'w'),
    ('P',4,1,'w'), ('P',5,1,'w'), ('P',6,1,'w'), ('P',7,1,'w'),
    # Black pawns (rank 7)
    ('P',0,6,'b'), ('P',1,6,'b'), ('P',2,6,'b'), ('P',3,6,'b'),
    ('P',4,6,'b'), ('P',5,6,'b'), ('P',6,6,'b'), ('P',7,6,'b'),
    # Black back rank (rank 8)
    ('R',0,7,'b'), ('N',1,7,'b'), ('B',2,7,'b'), ('Q',3,7,'b'),
    ('K',4,7,'b'), ('B',5,7,'b'), ('N',6,7,'b'), ('R',7,7,'b'),
]

# ─── Italian Game moves ───────────────────────────────────────────────────────
# 20-second loop:  each move = 10%  |  60-80% = hold  |  80-100% = smooth return
# (from_file, from_rank, delta_x_px, delta_y_px, css_id)
MOVES = [
    (4, 1,    0, -100, "a-wp"),  # 1. e2→e4  white pawn
    (4, 6,    0, +100, "a-bp"),  # 1. e7→e5  black pawn
    (6, 0,  -50, -100, "a-wn"),  # 2. g1→f3  white knight
    (1, 7,  +50, +100, "a-bn"),  # 2. b8→c6  black knight
    (5, 0, -150, -150, "a-wb"),  # 3. f1→c4  white bishop
    (5, 7, -150, +150, "a-bb"),  # 3. f8→c5  black bishop
]

ANIM_MAP = {(f, r): aid for f, r, dx, dy, aid in MOVES}


# ─── Build CSS animation block ────────────────────────────────────────────────
def build_css():
    ease = "cubic-bezier(0.4,0,0.2,1)"
    lines = [
        "@keyframes glowPulse { 0%,100% { opacity:0.55; } 50% { opacity:0.9; } }",
        ".gp { animation: glowPulse 3.5s ease-in-out infinite; }",
    ]
    for i, (f_, r_, dx, dy, aid) in enumerate(MOVES):
        sp   = i * 10        # start-percent for this move
        ep   = sp + 10       # end-percent (move complete)
        name = "mv" + aid.replace("-", "")

        kf = "@keyframes " + name + " {"
        # Phase 1: hold at start position (0% .. sp%)
        if sp > 0:
            kf += " 0% { transform:translate(0px,0px); }"
            kf += " " + str(sp) + "% { transform:translate(0px,0px);"
            kf += " animation-timing-function:" + ease + "; }"
        else:
            kf += " 0% { transform:translate(0px,0px);"
            kf += " animation-timing-function:" + ease + "; }"
        # Phase 2: glide to target (sp% .. ep%)
        kf += " " + str(ep) + "% { transform:translate(" + str(dx) + "px," + str(dy) + "px); }"
        # Phase 3: hold at target (ep% .. 80%)
        kf += " 80% { transform:translate(" + str(dx) + "px," + str(dy) + "px);"
        kf += " animation-timing-function:" + ease + "; }"
        # Phase 4: glide back to start (80% .. 100%)
        kf += " 100% { transform:translate(0px,0px); } }"

        lines.append(kf)
        lines.append("#" + aid + " { animation:" + name + " 20s linear infinite; }")

    return "\n".join(lines)


def main():
    # ── Board squares (64 cells) ──
    squares = []
    for f in range(8):
        for r in range(8):
            x   = BX + f * SQ
            y   = BY + (7 - r) * SQ
            clr = "#165a5c" if (f + r) % 2 == 1 else "#0c3b3d"
            squares.append(f'<rect x="{x}" y="{y}" width="{SQ}" height="{SQ}" fill="{clr}"/>')

    # ── Coordinate labels ──
    font_attrs = ('font-family="\'Courier New\',Courier,monospace" '
                  'font-size="11" fill="#5eead4" text-anchor="middle"')
    labels = []
    for r in range(8):
        lx = BX - 15
        ly = BY + (7 - r) * SQ + SQ // 2 + 4   # +4 for text baseline
        labels.append(f'<text x="{lx}" y="{ly}" {font_attrs}>{r + 1}</text>')
    for f in range(8):
        lx = BX + f * SQ + SQ // 2
        ly = BY + 8 * SQ + 18
        labels.append(f'<text x="{lx}" y="{ly}" {font_attrs}>{chr(ord("a") + f)}</text>')

    # ── Chess pieces ──
    # Each piece: outer <g> positions at starting square via SVG 'transform' attribute;
    # inner <g> (with optional CSS id) receives the CSS translate animation.
    # Using nested groups avoids CSS/attribute transform conflicts.
    pieces = []
    for piece, file, rank, side in START:
        x, y = sq_cx(file), sq_cy(rank)
        aid  = ANIM_MAP.get((file, rank))
        fill   = "#ecfeff" if side == 'w' else "#99f6e4"
        stroke = "#0891b2" if side == 'w' else "#134e4a"
        gfilt  = "wGlow"  if side == 'w' else "bGlow"
        inner_id = f' id="{aid}"' if aid else ''
        pieces.append(
            f'<g transform="translate({x},{y})">'
            f'<g{inner_id} filter="url(#{gfilt})">'
            f'<path d="{PP[piece]}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="1.2" stroke-linejoin="round"/>'
            f'</g></g>'
        )

    # ── CSS ──
    css = build_css()

    # ── Assemble blocks ──
    sq_str = "\n    ".join(squares)
    lb_str = "\n    ".join(labels)
    pc_str = "\n    ".join(pieces)
    BW = 8 * SQ  # board width/height = 400

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
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
        '      <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur"/>\n'
        '      <feFlood flood-color="#22d3ee" flood-opacity="0.65" result="color"/>\n'
        '      <feComposite in="color" in2="blur" operator="in" result="glow"/>\n'
        '      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>\n'
        '    </filter>\n'
        '    <!-- Black piece glow: teal halo -->\n'
        '    <filter id="bGlow" x="-50%" y="-50%" width="200%" height="200%">\n'
        '      <feGaussianBlur in="SourceAlpha" stdDeviation="2.5" result="blur"/>\n'
        '      <feFlood flood-color="#14b8a6" flood-opacity="0.55" result="color"/>\n'
        '      <feComposite in="color" in2="blur" operator="in" result="glow"/>\n'
        '      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>\n'
        '    </filter>\n'
        '  </defs>\n'
        '\n'
        f'  <style>{css}</style>\n'
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
        '  <!-- ── Chess Board ── -->\n'
        '  <g id="board">\n'
        f'    {sq_str}\n'
        '  </g>\n'
        '\n'
        '  <!-- Board border -->\n'
        f'  <rect x="{BX}" y="{BY}" width="{BW}" height="{BW}"\n'
        '        fill="none" stroke="#2dd4bf" stroke-width="0.6" stroke-opacity="0.3"/>\n'
        '\n'
        '  <!-- ── Coordinate Labels ── -->\n'
        '  <g id="coords">\n'
        f'    {lb_str}\n'
        '  </g>\n'
        '\n'
        '  <!-- ── Chess Pieces (Italian Game opening animation) ── -->\n'
        '  <g id="pieces">\n'
        f'    {pc_str}\n'
        '  </g>\n'
        '</svg>'
    )

    # ── Validate XML ──
    try:
        ET.fromstring(svg)
        print("XML validation: PASS")
    except ET.ParseError as e:
        print(f"XML validation FAILED: {e}")
        # Print the problematic area
        lines = svg.split('\n')
        for ln, l in enumerate(lines, 1):
            if any(c in l for c in ['<', '&', '>']):
                pass
        raise

    # ── Write ──
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Written: {OUT_PATH}")
    print(f"Size:    {OUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
