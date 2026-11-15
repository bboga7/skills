#!/usr/bin/env python3
"""
nakis / audit.py

Scores a web page for common machine-made patterns in copy, visuals and motion,
plus a few accessibility basics. Standard library only. No network access.

Usage:
    python3 audit.py page.html
    python3 audit.py page.html --json
    python3 audit.py page.html --lang tr
    python3 audit.py page.html --min-score 85     # exit code 1 if below

Text inside an element with the attribute data-nakis-ignore is skipped by the copy checks.
Use it only for text that quotes a bad example on purpose.

License: MIT
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import re
import statistics
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERNS_FILE = HERE / "patterns.json"

WEIGHTS = {"high": 12, "medium": 5, "low": 2}
AREAS = ("copy", "visual", "motion", "access")
AREA_TITLES = {
    "copy": "Copy",
    "visual": "Visual",
    "motion": "Motion",
    "access": "Accessibility & technical",
}

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
HIDDEN_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "head", "title"}
GENERIC_FONT_KEYWORDS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "math",
    "emoji", "fangsong", "inherit", "initial", "unset", "revert", "revert-layer",
}
NAMED_COLORS = {
    "white": (255, 255, 255), "black": (0, 0, 0), "transparent": None,
    "red": (255, 0, 0), "green": (0, 128, 0), "blue": (0, 0, 255),
    "gray": (128, 128, 128), "grey": (128, 128, 128), "purple": (128, 0, 128),
    "violet": (238, 130, 238), "indigo": (75, 0, 130), "orange": (255, 165, 0),
    "yellow": (255, 255, 0), "navy": (0, 0, 128), "teal": (0, 128, 128),
    "silver": (192, 192, 192), "maroon": (128, 0, 0), "olive": (128, 128, 0),
}
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U00002B50\U00002B55\U0000231A-\U0000231B\U000023E9-\U000023FA]"
)
EXTERNAL_RE = re.compile(r"^(https?:)?//", re.I)


# ---------------------------------------------------------------- DOM

class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text_parts")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []
        self.parent = parent
        self.text_parts = []

    def iter(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.iter()

    def text(self, skip=HIDDEN_TEXT_TAGS):
        out = []
        for child in self.children:
            if isinstance(child, str):
                out.append(child)
            elif child.tag not in skip and "data-nakis-ignore" not in child.attrs:
                out.append(child.text(skip))
        return " ".join(" ".join(out).split())

    def elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def classes(self):
        return tuple(sorted(self.attrs.get("class", "").split()))


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.current = self.root
        self.styles = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag == "style":
            self._in_style = True
        if tag not in VOID_TAGS:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        node = self.current
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self.current = node.parent

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        self.current.children.append(data)


# ---------------------------------------------------------------- helpers

def tr_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()


def load_patterns():
    with PATTERNS_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def detect_language(root: Node, text: str) -> str:
    for node in root.iter():
        if node.tag == "html":
            lang = node.attrs.get("lang", "").lower()
            if lang.startswith("tr"):
                return "tr"
            if lang.startswith("en"):
                return "en"
    letters = sum(ch.isalpha() for ch in text) or 1
    turkish = sum(ch in "çğışöüÇĞİŞÖÜ" for ch in text)
    return "tr" if turkish / letters > 0.01 else "en"


def strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_rules(css: str):
    """Yield (selector, declarations dict, raw block) for innermost rule blocks."""
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector = match.group(1).strip()
        body = match.group(2)
        decls = {}
        for part in body.split(";"):
            if ":" in part:
                prop, value = part.split(":", 1)
                decls[prop.strip().lower()] = value.strip()
        yield selector, decls, body


def parse_color(value: str, variables: dict, depth: int = 0):
    """Return (r, g, b) or None for a CSS color value. Ignores alpha."""
    if value is None or depth > 8:
        return None
    value = value.strip().lower().replace("!important", "").strip()
    var = re.fullmatch(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)", value)
    if var:
        name, fallback = var.group(1), var.group(2)
        if name in variables:
            return parse_color(variables[name], variables, depth + 1)
        return parse_color(fallback, variables, depth + 1) if fallback else None
    if value in NAMED_COLORS:
        return NAMED_COLORS[value]
    hexm = re.fullmatch(r"#([0-9a-f]{3,8})", value)
    if hexm:
        h = hexm.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        elif len(h) in (6, 8):
            h = h[:6]
        else:
            return None
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    rgbm = re.fullmatch(r"rgba?\(\s*([\d.]+)%?[\s,]+([\d.]+)%?[\s,]+([\d.]+)%?.*\)", value)
    if rgbm:
        return tuple(max(0, min(255, round(float(x)))) for x in rgbm.groups())
    hslm = re.fullmatch(r"hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%.*\)", value)
    if hslm:
        h, s, l = (float(x) for x in hslm.groups())
        r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
        return (round(r * 255), round(g * 255), round(b * 255))
    return None


def first_color_in(value: str, variables: dict):
    if value is None or "gradient(" in value or "url(" in value:
        return None
    for token in re.findall(r"var\([^)]*\)|#[0-9a-fA-F]{3,8}\b|(?:rgb|hsl)a?\([^)]*\)|[a-zA-Z]+", value):
        color = parse_color(token, variables)
        if color is not None:
            return color
    return None


def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def is_default_violet(rgb) -> bool:
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    hue = h * 360
    return 230 <= hue <= 300 and s > 0.35 and 0.25 < l < 0.85


# ---------------------------------------------------------------- audit

class Report:
    def __init__(self):
        self.findings = []
        self.placeholders = []

    def add(self, area, severity, rule, message, examples=None, count=1, penalty=None):
        self.findings.append({
            "area": area,
            "severity": severity,
            "rule": rule,
            "message": message,
            "count": count,
            "examples": list(examples or [])[:5],
            "penalty": WEIGHTS[severity] if penalty is None else penalty,
        })

    @property
    def score(self):
        return max(0, 100 - sum(f["penalty"] for f in self.findings))


def collect_css(builder: TreeBuilder, root: Node, base_dir: Path | None, report: Report):
    chunks = list(builder.styles)
    external = []
    for node in root.iter():
        if node.tag == "link" and "stylesheet" in node.attrs.get("rel", "").lower():
            href = node.attrs.get("href", "")
            if EXTERNAL_RE.match(href):
                continue
            if base_dir is not None and href:
                path = (base_dir / href).resolve()
                if path.is_file():
                    chunks.append(path.read_text(encoding="utf-8", errors="replace"))
                else:
                    external.append(href)
        style_attr = node.attrs.get("style")
        if style_attr:
            chunks.append("x{" + style_attr + "}")
    if external:
        report.add("access", "low", "missing-stylesheet",
                   "Linked local stylesheet not found; it was not audited.", external)
    return strip_css_comments("\n".join(chunks))


def check_external(root: Node, css: str, report: Report):
    found = []
    for node in root.iter():
        for attr in ("href", "src", "srcset", "data", "poster"):
            value = node.attrs.get(attr)
            if not value:
                continue
            if node.tag == "a" and attr == "href":
                continue
            if node.tag == "link" and node.attrs.get("rel", "").lower() in ("canonical", "alternate", "me", "author"):
                continue
            for part in value.split(","):
                url = part.strip().split(" ")[0]
                if EXTERNAL_RE.match(url):
                    found.append(f"<{node.tag} {attr}> {url}")
    for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", css):
        if EXTERNAL_RE.match(url.strip()):
            found.append(f"css url() {url.strip()}")
    for url in re.findall(r"@import\s+(?:url\()?\s*['\"]?([^'\";)]+)", css):
        if EXTERNAL_RE.match(url.strip()):
            found.append(f"css @import {url.strip()}")
    if found:
        report.add("access", "high", "external-resource",
                   "Page loads files from other servers. Keep fonts, styles, scripts and images local or inline.",
                   found, count=len(found))


def check_copy(root: Node, text: str, lang: str, patterns: dict, report: Report):
    low = tr_lower(text) if lang == "tr" else text.lower()
    words = re.findall(r"\w+", low)
    if len(words) < 15:
        report.add("copy", "low", "too-little-copy",
                   "Very little text on the page; copy checks are limited.", penalty=0)
        return

    if re.search(r"lorem ipsum|dolor sit amet", low):
        report.add("copy", "high", "lorem-ipsum", "Filler text (lorem ipsum) is still on the page.")

    lang_patterns = patterns.get(lang, {})
    category_rules = {
        "stock_phrases": ("medium", "Stock phrases that could sit on any page.", 3, 15),
        "inflated_verbs": ("low", "Inflated verbs. Say what actually happens.", 2, 8),
        "empty_adjectives": ("low", "Empty adjectives. Replace with a fact or a number.", 2, 8),
        "translation_smell": ("low", "Translation smell: passive voice, '-mektedir', noun + 'sağlamak/sunmak'.", 2, 8),
        "mirror_sentences": ("medium", "Mirror sentences ('not just X, but Y').", 4, 8),
    }
    for category, (severity, message, per_hit, cap) in category_rules.items():
        hits = []
        for pattern in lang_patterns.get(category, []):
            for m in re.finditer(pattern, low):
                hits.append(m.group(0))
        if hits:
            penalty = min(cap, per_hit * len(hits))
            report.add("copy", severity, category.replace("_", "-"), message,
                       sorted(set(hits), key=hits.index), count=len(hits), penalty=penalty)

    # Generic calls to action
    ctas = set(lang_patterns.get("generic_cta", []))
    generic = []
    for node in root.iter():
        is_button = node.tag == "button" or node.attrs.get("role") == "button"
        cls = node.attrs.get("class", "").lower()
        is_button = is_button or (node.tag == "a" and re.search(r"\b(btn|button|cta)\b", cls))
        label = node.text()
        if node.tag == "input" and node.attrs.get("type", "").lower() in ("submit", "button"):
            is_button, label = True, node.attrs.get("value", "submit")
        if not is_button:
            continue
        norm = re.sub(r"[^\w\s']", "", tr_lower(label) if lang == "tr" else label.lower()).strip()
        if norm and any(norm == c or norm.startswith(c) for c in ctas):
            generic.append(label.strip())
    if generic:
        report.add("copy", "medium", "generic-cta",
                   "Buttons that do not say what happens next.", generic, count=len(generic),
                   penalty=min(10, 4 * len(generic)))

    # Emoji used as decoration in headings, list items and buttons
    deco = []
    for node in root.iter():
        if node.tag in ("h1", "h2", "h3", "h4", "li", "button", "summary"):
            if EMOJI_RE.search(node.text()):
                deco.append(node.text()[:60])
    if deco:
        report.add("copy", "medium" if len(deco) > 2 else "low", "decorative-emoji",
                   "Emoji used as decoration in headings, lists or buttons.", deco, count=len(deco))

    # Rule of three
    threes = []
    for node in root.iter():
        kids = node.elements()
        if node.tag in ("ul", "ol"):
            items = [k for k in kids if k.tag == "li"]
            if len(items) == 3:
                threes.append(f"<{node.tag}> with 3 items")
        elif len(kids) == 3 and node.tag not in ("head", "html", "body", "tr", "thead", "tbody"):
            signature = {(k.tag, k.classes()) for k in kids}
            if len(signature) == 1 and kids[0].classes():
                threes.append(f"3 x <{kids[0].tag} class='{' '.join(kids[0].classes())}'>")
    if len(threes) >= 2:
        report.add("copy", "medium", "rule-of-three",
                   "The page keeps grouping things in threes. Use two, four, or one.",
                   threes, count=len(threes))

    # Headings
    headings = [n for n in root.iter() if n.tag in ("h1", "h2", "h3")]
    if lang == "en":
        title_case = []
        for h in headings:
            ws = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", h.text()) if len(w) > 3]
            if len(ws) >= 3 and all(w[0].isupper() for w in ws):
                title_case.append(h.text())
        if len(title_case) >= 2:
            report.add("copy", "low", "title-case", "Title Case On Every Heading reads like a template.",
                       title_case, count=len(title_case))
    colon = [h.text() for h in headings if re.match(r"^[^:]{2,28}:\s+\S", h.text())]
    if len(colon) >= 2:
        report.add("copy", "low", "colon-headings", "Several 'Label: slogan' headings.", colon, count=len(colon))

    first_lines = [n.text() for n in root.iter() if n.tag in ("h1", "h2", "p") and n.text()][:2]
    if first_lines and first_lines[0].endswith("?"):
        report.add("copy", "low", "question-opener", "The page opens with a question. Start with the answer.",
                   first_lines[:1])

    # Dash overload
    dashes = text.count("—") + len(re.findall(r"\s–\s", text))
    if dashes >= 3 and dashes / max(1, len(words)) * 100 > 1.5:
        report.add("copy", "low", "dash-overload", "Long dashes in many sentences. Use periods and commas.",
                   count=dashes)

    # Uniform sentence length
    paragraphs = " ".join(n.text() for n in root.iter() if n.tag == "p")
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", paragraphs) if len(s.split()) >= 3]
    if len(sentences) >= 8:
        lengths = [len(s.split()) for s in sentences]
        if statistics.pstdev(lengths) < 3.5:
            report.add("copy", "low", "flat-rhythm",
                       "Sentences all have about the same length. Mix short and long.",
                       [f"average {statistics.mean(lengths):.1f} words, spread {statistics.pstdev(lengths):.1f}"])

    # Repetition: the same sentence, or the same number, again and again
    blocks = [n.text() for n in root.iter() if n.tag in ("p", "li", "h1", "h2", "h3", "a", "button", "dd", "td")]
    norm = Counter(re.sub(r"\W+", " ", tr_lower(b) if lang == "tr" else b.lower()).strip()
                   for b in blocks if len(b.split()) >= 3)
    repeated = [f"{t[:50]} (x{n})" for t, n in norm.items() if n >= 3]
    if repeated:
        report.add("copy", "medium", "repeated-lines",
                   "The same line appears three or more times. Say it once; a thin brief makes a short page.",
                   repeated, count=len(repeated))
    # Phone numbers and similar digit groups are contact details, not repeated facts
    no_phones = re.sub(r"\+?\d[\d ()\-]{6,}\d", " ", text)
    numbers = Counter(re.findall(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])", no_phones))
    loud = [f"{num} (x{n})" for num, n in numbers.items() if n >= 4 and len(num) >= 2]
    if loud:
        report.add("copy", "low", "repeated-numbers",
                   "The same number appears four or more times. State each fact once.", loud, count=len(loud))

    # Question headings anywhere on the page
    questions = [h.text() for h in headings if h.text().endswith("?")]
    if len(questions) >= 2:
        report.add("copy", "low", "question-headings", "Several headings are questions. State the answer instead.",
                   questions, count=len(questions))

    # Placeholders: fine while drafting, not fine to publish
    placeholder_re = r"\[[^\[\]]{2,40}\]"
    report.placeholders = sorted(set(re.findall(placeholder_re, text)))
    if report.placeholders:
        first = next((n for n in root.iter() if n.tag in ("header", "h1")), None)
        hero = first.text() if first is not None else ""
        if re.search(placeholder_re, hero):
            report.add("copy", "high", "placeholder-in-hero",
                       "A placeholder sits in the first screen. Fill it or remove that line.",
                       re.findall(placeholder_re, hero))
        report.add("copy", "medium", "placeholders-left",
                   "Placeholders still on the page. Fill them, or remove optional lines, before publishing.",
                   report.placeholders, count=len(report.placeholders))


def check_visual(root: Node, css: str, variables: dict, report: Report):
    # Fonts
    declared = {f.strip("'\" ").lower() for f in re.findall(
        r"@font-face\s*\{[^}]*font-family\s*:\s*([^;}]+)", css)}
    named = set()
    for value in re.findall(r"font-family\s*:\s*([^;}]+)", css):
        for name in value.split(","):
            name = name.strip().strip("'\"").lower()
            if name.startswith("var("):
                continue
            if name and name not in GENERIC_FONT_KEYWORDS and name not in declared:
                named.add(name)
    if named:
        report.add("visual", "low", "named-fonts",
                   "Named font families that are not bundled. They depend on what each device has installed. "
                   "Prefer generic stacks (ui-serif, system-ui, ui-rounded, ui-monospace).",
                   sorted(named), count=len(named))

    # Gradients
    violet, gradient_count = [], 0
    for grad in re.findall(r"(?:linear|radial|conic)-gradient\(((?:[^()]|\([^()]*\))*)\)", css):
        gradient_count += 1
        colors = []
        for token in re.findall(r"var\([^)]*\)|#[0-9a-fA-F]{3,8}\b|(?:rgb|hsl)a?\([^)]*\)", grad):
            c = parse_color(token, variables)
            if c is not None:
                colors.append(c)
        if sum(is_default_violet(c) for c in colors) >= 2:
            violet.append(grad[:70])
    if violet:
        report.add("visual", "medium", "default-gradient",
                   "Saturated violet-blue gradient, the most common machine default.", violet, count=len(violet))
    if re.search(r"background-clip\s*:\s*text", css):
        report.add("visual", "low", "gradient-text", "Gradient-filled text.")

    glass = len(re.findall(r"backdrop-filter\s*:\s*[^;]*blur", css))
    if glass >= 2:
        report.add("visual", "low", "glass-everywhere", "Blurred glass panels used repeatedly.", count=glass)

    radii = Counter(v.strip() for v in re.findall(r"border-radius\s*:\s*([^;}]+)", css))
    if radii:
        value, n = radii.most_common(1)[0]
        px = re.match(r"([\d.]+)(px|rem)", value)
        size = float(px.group(1)) * (16 if px and px.group(2) == "rem" else 1) if px else 0
        if n >= 5 and size >= 12:
            report.add("visual", "low", "same-radius",
                       f"The same large corner radius ({value}) on many boxes.", count=n)

    shadows = len([v for v in re.findall(r"box-shadow\s*:\s*([^;}]+)", css) if v.strip() != "none"])
    if shadows >= 6:
        report.add("visual", "low", "shadow-everywhere", "Drop shadows on many elements.", count=shadows)

    centered = len(re.findall(r"text-align\s*:\s*center", css))
    if centered >= 6:
        report.add("visual", "low", "centered-everything", "Most text is centered. Left-align body copy.",
                   count=centered)

    colors = set()
    for token in re.findall(r"#[0-9a-fA-F]{3,8}\b|(?:rgb|hsl)a?\([^)]*\)", css):
        c = parse_color(token, variables)
        if c:
            colors.add(c)
    if len(colors) > 14:
        report.add("visual", "low", "too-many-colors", f"{len(colors)} different colors in the styles.",
                   count=len(colors))


def check_contrast(css: str, variables: dict, report: Report):
    failing = []
    base_fg = base_bg = None
    for selector, decls, _ in css_rules(css):
        fg = parse_color(decls.get("color"), variables) if "color" in decls else None
        bg_value = decls.get("background-color") or decls.get("background")
        bg = first_color_in(bg_value, variables) if bg_value else None
        sel = selector.split("\n")[-1].strip()
        if sel in ("html", "body", ":root", "html, body", "body, html"):
            base_fg = fg or base_fg
            base_bg = bg or base_bg
        if fg and bg:
            ratio = contrast(fg, bg)
            if ratio < 4.5:
                failing.append((sel, ratio))
    if base_fg and base_bg:
        ratio = contrast(base_fg, base_bg)
        if ratio < 4.5 and not any(s in ("html", "body") for s, _ in failing):
            failing.append(("page text", ratio))
    if failing:
        worst = min(r for _, r in failing)
        report.add("access", "high" if worst < 3 else "medium", "low-contrast",
                   "Text and background contrast below 4.5:1.",
                   [f"{s[:40]} ({r:.2f}:1)" for s, r in failing], count=len(failing))


def check_motion(css: str, report: Report):
    animations = re.findall(r"(?<![-\w])animation(?:-name)?\s*:\s*([^;}]+)", css)
    transitions = re.findall(r"(?<![-\w])transition\s*:\s*([^;}]+)", css)
    has_motion = bool(animations or transitions or "@keyframes" in css)
    if not has_motion:
        return
    if "prefers-reduced-motion" not in css:
        report.add("motion", "high", "no-reduced-motion",
                   "Animations exist but nothing respects prefers-reduced-motion.")
    infinite = [a for a in animations if "infinite" in a]
    if infinite:
        report.add("motion", "medium", "infinite-animation", "Animations that loop forever.",
                   infinite, count=len(infinite))
    if any(re.match(r"\s*all\b", t) for t in transitions):
        report.add("motion", "low", "transition-all", "'transition: all' animates more than intended.")
    layout_props = []
    for body in re.findall(r"@keyframes\s+[\w-]+\s*\{((?:[^{}]|\{[^{}]*\})*)\}", css):
        for prop in re.findall(r"(?<![-\w])(width|height|top|left|right|bottom|margin[\w-]*)\s*:", body):
            layout_props.append(prop)
    if layout_props:
        report.add("motion", "low", "layout-animation",
                   "Keyframes animate layout properties. Use transform and opacity.",
                   sorted(set(layout_props)))
    real = [a for a in animations if a.strip() not in ("none", "none !important")]
    if len(real) > 10:
        report.add("motion", "low", "too-much-motion", f"{len(real)} animation declarations. Pick one signature moment.",
                   count=len(real))


def check_draw_paths(root: Node, report: Report):
    missing = [n.attrs.get("d", "")[:30] for n in root.iter()
               if "nk-draw" in n.attrs.get("class", "").split() and "pathlength" not in n.attrs]
    if missing:
        report.add("motion", "medium", "draw-without-pathlength",
                   'Elements using .nk-draw need pathLength="1", or the line will not draw.', missing,
                   count=len(missing))


def check_access(root: Node, css: str, report: Report):
    html = next((n for n in root.iter() if n.tag == "html"), None)
    if html is None or not html.attrs.get("lang"):
        report.add("access", "medium", "missing-lang", "<html> has no lang attribute.")
    if not any(n.tag == "meta" and n.attrs.get("name", "").lower() == "viewport" for n in root.iter()):
        report.add("access", "medium", "missing-viewport", "No viewport meta tag; the page will not scale on phones.")
    no_alt = [n.attrs.get("src", "?") for n in root.iter() if n.tag == "img" and "alt" not in n.attrs]
    if no_alt:
        report.add("access", "medium", "img-alt", "Images without alt text.", no_alt, count=len(no_alt))
    h1 = sum(1 for n in root.iter() if n.tag == "h1")
    if h1 != 1:
        report.add("access", "low", "h1-count", f"The page has {h1} <h1> elements; use exactly one.")
    interactive = any(n.tag in ("a", "button", "input", "select", "textarea") for n in root.iter())
    removes_outline = re.search(r"outline\s*:\s*(none|0)\b", css)
    has_focus = re.search(r":focus(-visible|-within)?\b", css)
    if removes_outline and not has_focus:
        report.add("access", "high", "focus-removed", "Focus outlines are removed with no replacement.")
    elif interactive and not has_focus:
        report.add("access", "medium", "no-focus-style", "No custom :focus-visible style for links and buttons.")


def css_variables(css: str) -> dict:
    variables = {}
    for _, decls, _ in css_rules(css):
        for prop, value in decls.items():
            if prop.startswith("--") and prop not in variables:
                variables[prop] = value
    return variables


def audit(html: str, base_dir: Path | None = None, lang: str = "auto") -> dict:
    builder = TreeBuilder()
    builder.feed(html)
    builder.close()
    root = builder.root
    report = Report()

    css = collect_css(builder, root, base_dir, report)
    variables = css_variables(css)
    body = next((n for n in root.iter() if n.tag == "body"), root)
    text = body.text()
    if lang == "auto":
        lang = detect_language(root, text)

    check_external(root, css, report)
    check_copy(root, text, lang, load_patterns(), report)
    check_visual(root, css, variables, report)
    check_contrast(css, variables, report)
    check_motion(css, report)
    check_draw_paths(root, report)
    check_access(root, css, report)

    order = {"high": 0, "medium": 1, "low": 2}
    report.findings.sort(key=lambda f: (AREAS.index(f["area"]), order[f["severity"]]))
    return {
        "score": report.score,
        "language": lang,
        "findings": report.findings,
        "placeholders": report.placeholders,
        "counts": dict(Counter(f["severity"] for f in report.findings)),
    }


# ---------------------------------------------------------------- output

def verdict(score: int) -> str:
    if score >= 85:
        return "hand-made"
    if score >= 65:
        return "partly templated"
    return "templated"


def render_text(result: dict, path: str) -> str:
    score = result["score"]
    bar = "#" * round(score / 5) + "." * (20 - round(score / 5))
    lines = [
        f"nakis audit  {path}",
        f"score {score}/100  [{bar}]  {verdict(score)}   language: {result['language']}",
        "",
    ]
    if not result["findings"]:
        lines.append("No findings. Finish with references/checklist.md.")
    for area in AREAS:
        items = [f for f in result["findings"] if f["area"] == area]
        if not items:
            continue
        lines.append(AREA_TITLES[area])
        for f in items:
            count = f" x{f['count']}" if f["count"] > 1 else ""
            lines.append(f"  [{f['severity'].upper():6}] {f['rule']}{count}: {f['message']}")
            for ex in f["examples"]:
                lines.append(f"           - {ex}")
        lines.append("")
    if result["placeholders"]:
        lines.append("Placeholders still to fill:")
        lines.extend(f"  {p}" for p in result["placeholders"])
        lines.append("")
    lines.append("Fix every HIGH, review every MEDIUM, then re-run. Target: 85+.")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audit a web page for machine-made patterns.")
    parser.add_argument("path", help="HTML file to audit")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--lang", choices=("auto", "en", "tr"), default="auto", help="copy language")
    parser.add_argument("--min-score", type=int, default=None, help="exit with code 1 below this score")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    html = path.read_text(encoding="utf-8", errors="replace")
    result = audit(html, base_dir=path.parent, lang=args.lang)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result, str(path)))

    if args.min_score is not None and result["score"] < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
