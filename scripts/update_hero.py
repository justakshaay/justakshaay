#!/usr/bin/env python3
"""
Update assets/hero-card.svg:
- Luminous Traveling Border Light Beam (perimeter trace at 6s linear loop)
- Diagonal Glassmorphic Sheen Sweep (sweeps across glass panel every 5s)
- Visible Breathing Avatar Halo (pulses 0.35 -> 0.85 every 3.5s)
- Ambient shifting aurora wash in background
- Zero floating radar dots or circles
- Preserve Base64 avatar and all profile text/pills
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
HERO_PATH = REPO_DIR / "assets" / "hero-card.svg"

def main():
    orig = HERO_PATH.read_text(encoding="utf-8")
    m = re.search(r'(<image[^>]+>)', orig)
    assert m, "Avatar image tag not found!"
    image_tag = m.group(1)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 250" width="100%" height="100%">
  <defs>
    <!-- Aura Double-Frame Glow Gradients -->
    <linearGradient id="heroOuterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#14b8a6" stop-opacity="0.45" />
      <stop offset="28%" stop-color="#0d9488" stop-opacity="0.30" />
      <stop offset="70%" stop-color="#082f49" stop-opacity="0.22" />
      <stop offset="100%" stop-color="#071a19" />
    </linearGradient>

    <radialGradient id="heroAuraRadial" cx="80%" cy="20%" r="65%">
      <stop offset="0%" stop-color="#2dd4bf" stop-opacity="0.30" />
      <stop offset="45%" stop-color="#0d9488" stop-opacity="0.12" />
      <stop offset="85%" stop-color="#071a19" stop-opacity="0.02" />
      <stop offset="100%" stop-color="#071a19" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="heroAuraBottom" cx="15%" cy="85%" r="55%">
      <stop offset="0%" stop-color="#0d9488" stop-opacity="0.25" />
      <stop offset="60%" stop-color="#071a19" stop-opacity="0.05" />
      <stop offset="100%" stop-color="#071a19" stop-opacity="0" />
    </radialGradient>

    <!-- Clip Path for Inner Panel (cleanly bounds sheen and aurora) -->
    <clipPath id="innerPanelClip">
      <rect x="14" y="14" width="892" height="222" rx="12" />
    </clipPath>

    <!-- Soft Aurora Ambient Glow Blobs -->
    <radialGradient id="auroraBlob1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#14b8a6" stop-opacity="0.22" />
      <stop offset="45%" stop-color="#0d9488" stop-opacity="0.10" />
      <stop offset="100%" stop-color="#061414" stop-opacity="0" />
    </radialGradient>

    <radialGradient id="auroraBlob2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.20" />
      <stop offset="50%" stop-color="#082f49" stop-opacity="0.08" />
      <stop offset="100%" stop-color="#061414" stop-opacity="0" />
    </radialGradient>

    <!-- Diagonal Glassmorphic Sheen Gradient -->
    <linearGradient id="sheenGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#5eead4" stop-opacity="0" />
      <stop offset="30%" stop-color="#5eead4" stop-opacity="0.03" />
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.14" />
      <stop offset="70%" stop-color="#5eead4" stop-opacity="0.03" />
      <stop offset="100%" stop-color="#5eead4" stop-opacity="0" />
    </linearGradient>

    <!-- Border Light Beam Glow Filter -->
    <filter id="beamGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <!-- Avatar Halo Gradient -->
    <radialGradient id="avatarHalo" cx="50%" cy="50%" r="50%">
      <stop offset="40%" stop-color="#2dd4bf" stop-opacity="0.45" />
      <stop offset="75%" stop-color="#14b8a6" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#061414" stop-opacity="0" />
    </radialGradient>

    <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#5eead4" />
      <stop offset="100%" stop-color="#2dd4bf" />
    </linearGradient>

    <!-- Clip Path for Avatar -->
    <clipPath id="avatarClip">
      <circle cx="120" cy="125" r="54" />
    </clipPath>
  </defs>

  <style>
    @keyframes ambientBreath {{
      0%, 100% {{ opacity: 0.65; }}
      50%      {{ opacity: 0.90; }}
    }}
    @keyframes borderTrace {{
      0%   {{ stroke-dashoffset: 0; }}
      100% {{ stroke-dashoffset: -2020; }}
    }}
    @keyframes sheenSweep {{
      0% {{
        transform: translate(-380px, -20px) skewX(-25deg);
      }}
      55%, 100% {{
        transform: translate(1150px, -20px) skewX(-25deg);
      }}
    }}
    @keyframes avatarPulse {{
      0%, 100% {{
        opacity: 0.35;
        transform: scale(0.96);
      }}
      50% {{
        opacity: 0.85;
        transform: scale(1.06);
      }}
    }}
    @keyframes blobDrift1 {{
      0%, 100% {{
        transform: translate(0px, 0px) scale(1);
        opacity: 0.16;
      }}
      50% {{
        transform: translate(35px, 15px) scale(1.08);
        opacity: 0.22;
      }}
    }}
    @keyframes blobDrift2 {{
      0%, 100% {{
        transform: translate(0px, 0px) scale(1);
        opacity: 0.14;
      }}
      50% {{
        transform: translate(-30px, -18px) scale(1.10);
        opacity: 0.20;
      }}
    }}
    .ambient-glow {{
      animation: ambientBreath 8s ease-in-out infinite;
    }}
    .border-beam {{
      stroke-dasharray: 220 1800;
      animation: borderTrace 6s linear infinite;
    }}
    .sheen-rect {{
      animation: sheenSweep 5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    }}
    .avatar-glow {{
      animation: avatarPulse 3.5s ease-in-out infinite;
      transform-origin: 120px 125px;
    }}
    .blob-1 {{
      animation: blobDrift1 8s ease-in-out infinite;
      transform-origin: 280px 40px;
    }}
    .blob-2 {{
      animation: blobDrift2 8s ease-in-out infinite;
      transform-origin: 720px 210px;
    }}
  </style>

  <!-- Base Canvas -->
  <rect x="0" y="0" width="920" height="250" rx="18" fill="#071a19" />

  <!-- Outer Frame: Aura Glow and Gradient Border with slow 8s ambient breath -->
  <rect x="1" y="1" width="918" height="248" rx="18" fill="url(#heroOuterGrad)" stroke="#2dd4bf" stroke-width="1.5" stroke-opacity="0.35" />
  <rect class="ambient-glow" x="1" y="1" width="918" height="248" rx="18" fill="url(#heroAuraRadial)" />
  <rect x="1" y="1" width="918" height="248" rx="18" fill="url(#heroAuraBottom)" />

  <!-- Inner Recessed Panel (14px inset, 90% dark fill, 20% teal border) -->
  <rect x="14" y="14" width="892" height="222" rx="12" fill="#061414" fill-opacity="0.90" stroke="#2dd4bf" stroke-width="1" stroke-opacity="0.20" />

  <!-- Ambient Shifting Aurora Glow Blobs and Diagonal Sheen Sweep (Clipped cleanly to inner panel) -->
  <g clip-path="url(#innerPanelClip)">
    <circle cx="280" cy="40" r="260" fill="url(#auroraBlob1)" class="blob-1" />
    <circle cx="720" cy="210" r="280" fill="url(#auroraBlob2)" class="blob-2" />
    <!-- Diagonal Glassmorphic Sheen Sweep -->
    <rect class="sheen-rect" x="0" y="-30" width="220" height="320" fill="url(#sheenGrad)" />
  </g>

  <!-- Luminous Traveling Border Light Beam (Glides continuously around perimeter) -->
  <rect class="border-beam" x="14" y="14" width="892" height="222" rx="12"
        fill="none" stroke="#5eead4" stroke-width="2" filter="url(#beamGlow)" />

  <!-- Avatar Soft Halo and Crisp Solid Ring (Pulsing Avatar Halo) -->
  <circle cx="120" cy="125" r="74" fill="url(#avatarHalo)" class="avatar-glow" />
  <circle cx="120" cy="125" r="56" fill="#071a19" stroke="url(#ringGrad)" stroke-width="2.5" />

  <!-- Embedded Base64 Avatar Image -->
  {image_tag}

  <!-- Text Details -->
  <text x="206" y="72" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="14.5" font-weight="600" fill="#2dd4bf" letter-spacing="0.3px">@justakshaay</text>

  <text x="206" y="110" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="33" font-weight="800" fill="#ffffff" letter-spacing="-0.5px">Akshay Kumar</text>

  <text x="206" y="137" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" font-weight="600" fill="#99f6e4" opacity="0.95">Software Developer | AI/ML Engineer</text>

  <text x="206" y="164" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13.5" font-style="italic" fill="#94a3b8">Ideas into systems. Systems into reality.</text>

  <!-- 5 Outlined Dark-Teal Pills -->
  <g transform="translate(206, 186)">
    <!-- Pill 1: AI/ML -->
    <rect x="0" y="0" width="68" height="26" rx="13" fill="#041918" stroke="#14b8a6" stroke-width="1" stroke-opacity="0.8" />
    <text x="34" y="17" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="11.5" font-weight="600" fill="#99f6e4">AI/ML</text>

    <!-- Pill 2: Full-Stack -->
    <rect x="78" y="0" width="92" height="26" rx="13" fill="#041918" stroke="#14b8a6" stroke-width="1" stroke-opacity="0.8" />
    <text x="124" y="17" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="11.5" font-weight="600" fill="#99f6e4">Full-Stack</text>

    <!-- Pill 3: Python -->
    <rect x="180" y="0" width="76" height="26" rx="13" fill="#041918" stroke="#14b8a6" stroke-width="1" stroke-opacity="0.8" />
    <text x="218" y="17" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="11.5" font-weight="600" fill="#99f6e4">Python</text>

    <!-- Pill 4: TypeScript -->
    <rect x="266" y="0" width="98" height="26" rx="13" fill="#041918" stroke="#14b8a6" stroke-width="1" stroke-opacity="0.8" />
    <text x="315" y="17" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="11.5" font-weight="600" fill="#99f6e4">TypeScript</text>

    <!-- Pill 5: C++ -->
    <rect x="374" y="0" width="58" height="26" rx="13" fill="#041918" stroke="#14b8a6" stroke-width="1" stroke-opacity="0.8" />
    <text x="403" y="17" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace" font-size="11.5" font-weight="600" fill="#99f6e4">C++</text>
  </g>
</svg>"""

    ET.fromstring(svg_content)
    print("XML Validation: PASS")

    HERO_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Updated: {HERO_PATH}")

if __name__ == "__main__":
    main()
