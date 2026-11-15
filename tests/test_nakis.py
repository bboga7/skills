"""Tests for the nakis scripts. Run from the repository root:

    python3 -m unittest discover -s tests -v

Standard library only.
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "nakis"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load("audit")
palette = load("palette")

PAGE = """<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><style>{css}</style></head>
<body><h1>{h1}</h1>{body}</body></html>"""


def page(body="", css="", h1="Title", lang="en"):
    return PAGE.format(body=body, css=css, h1=h1, lang=lang)


def rules(result):
    return {f["rule"] for f in result["findings"]}


FILLER = "<p>" + " ".join(["The workshop opens at nine and closes when the last order ships."] * 3) + "</p>"


class AuditCopyTests(unittest.TestCase):
    def test_english_stock_phrases_are_found(self):
        html = page(FILLER + "<p>In today's fast-paced world, look no further. Join thousands of makers.</p>")
        self.assertIn("stock-phrases", rules(audit.audit(html)))

    def test_turkish_patterns_are_found(self):
        body = ("<p>Dijital dünyada işinizi bir sonraki seviyeye taşıyın. Raporlar sistem tarafından "
                "hazırlanmaktadır. Size hızlı destek sağlıyoruz ve yolculuğunuzda yanınızdayız. "
                "Atölyemiz her sabah dokuzda açılır ve son sipariş çıkınca kapanır.</p>")
        result = audit.audit(page(body, lang="tr"))
        self.assertEqual(result["language"], "tr")
        self.assertIn("stock-phrases", rules(result))
        self.assertIn("translation-smell", rules(result))

    def test_language_detection_without_lang_attribute(self):
        html = page("<p>Atölyemiz her sabah dokuzda açılır, öğleden sonra çay molası verir ve "
                    "son sipariş çıkınca kapanır. Ürünlerin çoğu elde dikilir.</p>", lang="")
        self.assertEqual(audit.audit(html)["language"], "tr")

    def test_generic_cta(self):
        html = page(FILLER + '<a class="btn" href="#">Get Started</a><button>Learn more</button>')
        self.assertIn("generic-cta", rules(audit.audit(html)))

    def test_specific_cta_passes(self):
        html = page(FILLER + '<a class="btn" href="#">Book a 20-minute call</a>')
        self.assertNotIn("generic-cta", rules(audit.audit(html)))

    def test_rule_of_three(self):
        cards = '<div><div class="c">a</div><div class="c">b</div><div class="c">c</div></div>'
        html = page(FILLER + cards + "<ul><li>a</li><li>b</li><li>c</li></ul>")
        self.assertIn("rule-of-three", rules(audit.audit(html)))

    def test_ignore_attribute_skips_quoted_text(self):
        html = page(FILLER + "<p data-nakis-ignore>Look no further. In today's fast-paced world.</p>")
        self.assertNotIn("stock-phrases", rules(audit.audit(html)))

    def test_placeholders_are_listed(self):
        html = page(FILLER + "<p>Founded in [year] by [founder name].</p>")
        self.assertEqual(audit.audit(html)["placeholders"], ["[founder name]", "[year]"])

    def test_placeholders_are_a_finding(self):
        result = audit.audit(page(FILLER + "<p>Founded in [year].</p>"))
        self.assertIn("placeholders-left", rules(result))
        self.assertNotIn("placeholder-in-hero", rules(result))

    def test_placeholder_in_hero(self):
        result = audit.audit(page(FILLER, h1="Next course: [course date]"))
        self.assertIn("placeholder-in-hero", rules(result))

    def test_repeated_lines_and_numbers(self):
        line = "<p>Call us to book your place today.</p>"
        nums = "<p>41 stories.</p><p>Over 41 of them.</p><p>All 41 were public.</p><p>That is 41.</p>"
        found = rules(audit.audit(page(FILLER + line * 3 + nums)))
        self.assertIn("repeated-lines", found)
        self.assertIn("repeated-numbers", found)

    def test_phone_numbers_are_not_repeated_facts(self):
        body = FILLER + "<p>Call 0212 555 00 00.</p>" * 2 + "<p>Or 0212 555 00 00 on Saturday.</p>" * 2
        self.assertNotIn("repeated-numbers", rules(audit.audit(page(body))))

    def test_contact_links_are_not_repeated_lines(self):
        link = '<p><a href="tel:+900000000000">Call 0000 000 00 00 to book</a></p>'
        self.assertNotIn("repeated-lines", rules(audit.audit(page(FILLER + link * 3))))

    def test_question_headings(self):
        html = page(FILLER + "<h2>Why us?</h2><p>x</p><h2>How does it work?</h2>")
        self.assertIn("question-headings", rules(audit.audit(html)))

    def test_draw_path_needs_pathlength(self):
        css = "@media (prefers-reduced-motion: reduce){*{animation:none}}"
        bad = page(FILLER + '<svg><path class="nk-draw" d="M0 0 L10 10"/></svg>', css)
        good = page(FILLER + '<svg><path class="nk-draw" pathLength="1" d="M0 0 L10 10"/></svg>', css)
        self.assertIn("draw-without-pathlength", rules(audit.audit(bad)))
        self.assertNotIn("draw-without-pathlength", rules(audit.audit(good)))


class AuditVisualAndMotionTests(unittest.TestCase):
    def test_violet_gradient(self):
        css = ".hero{background:linear-gradient(135deg,#6d28d9,#4f46e5)}"
        self.assertIn("default-gradient", rules(audit.audit(page(FILLER, css))))

    def test_warm_gradient_passes(self):
        css = ".hero{background:linear-gradient(135deg,#9a3412,#f8f5f4)}"
        self.assertNotIn("default-gradient", rules(audit.audit(page(FILLER, css))))

    def test_motion_without_reduced_motion(self):
        css = ".x{animation:spin 1s infinite}@keyframes spin{to{transform:rotate(1turn)}}"
        found = rules(audit.audit(page(FILLER, css)))
        self.assertIn("no-reduced-motion", found)
        self.assertIn("infinite-animation", found)

    def test_reduced_motion_respected(self):
        css = (".x{transition:transform .2s}"
               "@media (prefers-reduced-motion: reduce){.x{transition:none}}")
        self.assertNotIn("no-reduced-motion", rules(audit.audit(page(FILLER, css))))

    def test_external_resources(self):
        html = page(FILLER).replace("</head>", '<link rel="stylesheet" href="https://fonts.invalid/a.css"></head>')
        self.assertIn("external-resource", rules(audit.audit(html)))

    def test_low_contrast_with_variables(self):
        css = ":root{--fg:#999;--bg:#fff}body{color:var(--fg);background:var(--bg)}"
        self.assertIn("low-contrast", rules(audit.audit(page(FILLER, css))))

    def test_focus_removed(self):
        css = "a{outline:none}"
        self.assertIn("focus-removed", rules(audit.audit(page(FILLER + '<a href="#">x</a>', css))))


class ExampleTests(unittest.TestCase):
    def test_before_scores_low_and_after_scores_high(self):
        before = SKILL / "examples" / "before.html"
        after = SKILL / "examples" / "after.html"
        low = audit.audit(before.read_text(encoding="utf-8"), before.parent)["score"]
        high = audit.audit(after.read_text(encoding="utf-8"), after.parent)["score"]
        self.assertLess(low, 40)
        self.assertGreaterEqual(high, 85)

    def test_cli_json_and_exit_code(self):
        before = SKILL / "examples" / "before.html"
        proc = subprocess.run([sys.executable, str(SKILL / "scripts" / "audit.py"), str(before),
                               "--json", "--min-score", "85"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("score", json.loads(proc.stdout))


class PaletteTests(unittest.TestCase):
    SEEDS = ["#7a4b2a", "#6d28d9", "#2f5d50", "#888888", "#f2c94c", "#000000", "#ffffff", "#e11d48"]

    def test_all_roles_pass_contrast(self):
        for seed in self.SEEDS:
            for mode in ("light", "dark"):
                with self.subTest(seed=seed, mode=mode):
                    result = palette.build(seed, mode)
                    c = result["contrast"]
                    self.assertGreaterEqual(c["ink on bg"], 4.5)
                    self.assertGreaterEqual(c["muted on bg"], 4.5)
                    self.assertGreaterEqual(c["muted on surface"], 4.5)
                    self.assertGreaterEqual(c["accent on surface"], 4.5)
                    self.assertGreaterEqual(c["accent on bg"], 4.5)
                    self.assertGreaterEqual(c["accent-ink on accent"], 4.5)
                    self.assertGreaterEqual(c["line-strong on bg"], 3.0)

    def test_custom_background_is_kept_and_text_fits(self):
        for seed, bg in (("#7a4b2a", "#f4ead8"), ("#e07a2f", "#1d2328"), ("#2f5d50", "#fff8e7")):
            with self.subTest(seed=seed, bg=bg):
                result = palette.build(seed, "light", bg)
                self.assertEqual(result["colors"]["bg"]["value"], bg)
                for pair in ("ink on bg", "muted on bg", "accent on bg", "accent-ink on accent"):
                    self.assertGreaterEqual(result["contrast"][pair], 4.5)

    def test_violet_seed_gets_a_note(self):
        self.assertTrue(palette.build("#6d28d9")["notes"])

    def test_contrast_reference_values(self):
        self.assertAlmostEqual(palette.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(palette.contrast((119, 119, 119), (255, 255, 255)), 4.48, places=2)

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            palette.parse_hex("not-a-color")


if __name__ == "__main__":
    unittest.main()
