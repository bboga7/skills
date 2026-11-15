#!/usr/bin/env python3
"""
nakis / palette.py

Builds a small, readable color palette from one seed color.
Neutrals are tinted with the seed; text colors are adjusted until they pass contrast.
Standard library only. No network access.

Usage:
    python3 palette.py "#7a4b2a"                 # light palette as CSS custom properties
    python3 palette.py "#7a4b2a" --mode dark     # dark palette
    python3 palette.py "#7a4b2a" --json          # JSON output
    python3 palette.py "#7a4b2a" --bg "#f4ead8"  # keep your own background
    python3 palette.py --check "#555555" "#ffffff"   # contrast between two colors

License: MIT
"""

from __future__ import annotations

import argparse
import colorsys
import json
import re
import sys

TEXT_MIN = 4.5   # normal text
LARGE_MIN = 3.0  # large text, icons and UI borders


def parse_hex(value: str):
    value = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", value):
        raise ValueError(f"not a hex color: #{value}")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def hls(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return (r * 255, g * 255, b * 255)


def luminance(rgb) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def fit(h, l, s, against, minimum, direction):
    """Move lightness in `direction` (-1 darker, +1 lighter) until contrast >= minimum."""
    color = hls(h, l, s)
    steps = 0
    while contrast(color, against) < minimum and 0.0 < l < 1.0 and steps < 200:
        l += 0.01 * direction
        color = hls(h, l, s)
        steps += 1
    return color


def is_default_violet(rgb) -> bool:
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return 230 <= h * 360 <= 300 and s > 0.35 and 0.25 < l < 0.85


def build(seed_hex: str, mode: str = "light", bg_hex: str | None = None) -> dict:
    seed = parse_hex(seed_hex)
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in seed))
    tint = min(s, 1.0)
    requested_mode = mode
    if bg_hex:
        # A background chosen by the user decides the mode: dark backgrounds get light text.
        mode = "dark" if luminance(parse_hex(bg_hex)) < 0.18 else "light"

    if mode == "dark":
        bg = hls(h, 0.10, tint * 0.22)
        surface = hls(h, 0.14, tint * 0.22)
        ink = fit(h, 0.90, tint * 0.15, bg, 7.0, +1)
        muted = fit(h, 0.62, tint * 0.15, bg, TEXT_MIN, +1)
        line = hls(h, 0.24, tint * 0.18)
        line_strong = fit(h, 0.36, tint * 0.18, bg, LARGE_MIN, +1)
        accent = fit(h, max(l, 0.55), s, bg, TEXT_MIN, +1)
    else:
        bg = hls(h, 0.965, tint * 0.30)
        surface = hls(h, 0.925, tint * 0.30)
        ink = fit(h, 0.15, tint * 0.30, bg, 7.0, -1)
        muted = fit(h, 0.42, tint * 0.20, bg, TEXT_MIN, -1)
        line = hls(h, 0.85, tint * 0.18)
        line_strong = fit(h, 0.62, tint * 0.15, bg, LARGE_MIN, -1)
        accent = fit(h, min(l, 0.45), s, bg, TEXT_MIN, -1)

    if bg_hex:
        bg = parse_hex(bg_hex)
        bh, bl, bs = colorsys.rgb_to_hls(*(c / 255 for c in bg))
        step = 0.04 if mode == "dark" else -0.04
        surface = hls(bh, bl + step, bs)
        line = hls(bh, bl + step * 3, bs * 0.8)
        d = +1 if mode == "dark" else -1
        ink = fit(h, 0.90 if mode == "dark" else 0.15, tint * 0.25, bg, 7.0, d)
        muted = fit(h, 0.62 if mode == "dark" else 0.42, tint * 0.18, bg, TEXT_MIN, d)
        line_strong = fit(bh, 0.36 if mode == "dark" else 0.62, bs * 0.6, bg, LARGE_MIN, d)
        accent = fit(h, max(l, 0.55) if mode == "dark" else min(l, 0.45), s, bg, TEXT_MIN, d)

    # Text must also read on --surface, not only on --bg: fit against the harder of the two.
    d = +1 if mode == "dark" else -1
    for _ in range(100):
        worst = min(contrast(muted, bg), contrast(muted, surface))
        if worst >= TEXT_MIN:
            break
        mh, ml, ms = colorsys.rgb_to_hls(*(c / 255 for c in muted))
        muted = hls(mh, ml + 0.01 * d, ms)
    for _ in range(100):
        worst = min(contrast(accent, bg), contrast(accent, surface))
        if worst >= TEXT_MIN:
            break
        ah, al, as_ = colorsys.rgb_to_hls(*(c / 255 for c in accent))
        accent = hls(ah, al + 0.01 * d, as_)

    white, black = (255, 255, 255), (0, 0, 0)
    on_accent = white if contrast(white, accent) >= contrast(ink, accent) else ink
    if contrast(on_accent, accent) < TEXT_MIN:
        on_accent = white if contrast(white, accent) > contrast(black, accent) else black

    roles = {
        "bg": (bg, "page background"),
        "surface": (surface, "raised areas, code blocks, cards"),
        "ink": (ink, "main text"),
        "muted": (muted, "secondary text"),
        "line": (line, "decorative rules and dividers"),
        "line-strong": (line_strong, "input borders and UI lines that must be seen"),
        "accent": (accent, "links, one key action, highlights; use rarely"),
        "accent-ink": (on_accent, "text placed on the accent color"),
    }
    checks = {
        "ink on bg": contrast(ink, bg),
        "muted on bg": contrast(muted, bg),
        "muted on surface": contrast(muted, surface),
        "accent on bg": contrast(accent, bg),
        "accent on surface": contrast(accent, surface),
        "accent-ink on accent": contrast(on_accent, accent),
        "line-strong on bg": contrast(line_strong, bg),
    }
    notes = []
    if bg_hex and mode != requested_mode:
        notes.append(f"The background you gave is {'dark' if mode == 'dark' else 'light'}, "
                     f"so the palette was built in {mode} mode.")
    if is_default_violet(seed):
        notes.append("This seed sits in the most common default range (saturated violet-blue). "
                     "Make sure it comes from the page's idea, and use it flat, not as a gradient.")
    if s < 0.08:
        notes.append("The seed is almost grey, so the palette will be neutral. That is fine for a quiet page.")
    return {
        "seed": to_hex(seed),
        "mode": mode,
        "colors": {name: {"value": to_hex(c), "use": use} for name, (c, use) in roles.items()},
        "contrast": {k: round(v, 2) for k, v in checks.items()},
        "notes": notes,
    }


def render_css(palette: dict) -> str:
    lines = [f"/* nakis palette: seed {palette['seed']}, {palette['mode']} mode */", ":root {"]
    width = max(len(n) for n in palette["colors"])
    for name, info in palette["colors"].items():
        lines.append(f"  --{name}:{' ' * (width - len(name))} {info['value']};  /* {info['use']} */")
    lines.append("}")
    lines.append("")
    lines.append("/* contrast */")
    for pair, ratio in palette["contrast"].items():
        need = LARGE_MIN if pair.startswith("line") else TEXT_MIN
        mark = "ok" if ratio >= need else "LOW"
        lines.append(f"/*   {pair:22} {ratio:5.2f}:1  {mark} */")
    for note in palette["notes"]:
        lines.append(f"/* note: {note} */")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a readable palette from one seed color.")
    parser.add_argument("seed", nargs="?", help="seed color, for example #7a4b2a")
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    parser.add_argument("--json", action="store_true", help="print JSON instead of CSS")
    parser.add_argument("--bg", metavar="HEX", help="use this background color and fit the other colors to it")
    parser.add_argument("--check", nargs=2, metavar=("FG", "BG"), help="print the contrast of two colors")
    args = parser.parse_args(argv)

    try:
        if args.check:
            fg, bg = (parse_hex(c) for c in args.check)
            ratio = contrast(fg, bg)
            result = {
                "foreground": to_hex(fg),
                "background": to_hex(bg),
                "ratio": round(ratio, 2),
                "normal_text": ratio >= TEXT_MIN,
                "large_text_and_ui": ratio >= LARGE_MIN,
            }
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"{result['foreground']} on {result['background']}: {result['ratio']}:1")
                print(f"  normal text (4.5:1): {'pass' if result['normal_text'] else 'FAIL'}")
                print(f"  large text / UI (3:1): {'pass' if result['large_text_and_ui'] else 'FAIL'}")
            return 0 if result["normal_text"] else 1

        if not args.seed:
            parser.error("give a seed color, or use --check FG BG")
        palette = build(args.seed, args.mode, args.bg)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    print(json.dumps(palette, indent=2) if args.json else render_css(palette))
    return 0


if __name__ == "__main__":
    sys.exit(main())
