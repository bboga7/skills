# Visual identity

A generic page is a stack of first choices. A hand-made page has **one idea** and a few
decisions that follow from it. This file shows how to get there with nothing but CSS,
the fonts already on the reader's device, and inline SVG.

---

## 1. Start with an idea, not a style

Before touching colors, write one sentence:

> This page looks like **[a material / a place / an object / a period]** because **[reason from the brief]**.

Examples:

- A bicycle repair shop → *looks like the workshop chalkboard*: dark slate, chalk white, one safety-orange accent, hand-ruled lines.
- A night-shift nurse's blog → *looks like a hospital corridor at 3 a.m.*: dark, quiet, one green accent, monospace times.
- A developer's personal site → *looks like a well-kept notebook*: grid paper lines, margin notes, a single red pen color.

Every later decision should be explainable by this sentence. If a choice cannot be explained by it, it is probably a default.

---

## 2. Color

### Generate the palette from one seed

```bash
python3 scripts/palette.py "#7a4b2a"                 # light palette as CSS custom properties
python3 scripts/palette.py "#7a4b2a" --mode dark     # dark palette
python3 scripts/palette.py "#7a4b2a" --json          # machine-readable
python3 scripts/palette.py "#7a4b2a" --bg "#f4ead8"     # keep your own background, fit the rest to it
python3 scripts/palette.py --check "#555555" "#ffffff"   # contrast of any two colors
```

The script returns a small set of roles: `--bg`, `--surface`, `--ink`, `--muted`, `--line`,
`--line-strong`, `--accent`, `--accent-ink`. It raises or lowers lightness until text passes a
contrast ratio of 4.5:1 and `--line-strong` passes 3:1, so the palette is readable before you start.
`--line` is decorative and intentionally soft.

### Rules

1. **Pick the seed from the idea**, never from habit. Paper, rust, moss, ink, brick, sea-glass, chalk.
2. **Tint the neutrals.** Pure grey (`#888`, `#f5f5f5`) is a default. The script mixes a little of the seed into every neutral.
3. **One accent, used rarely.** If the accent appears in more than about a tenth of the screen, it stops being an accent.
4. **Avoid the common default range:** saturated violet-to-blue gradients, especially behind a centered headline.
   The audit flags them. If the idea really calls for violet, use it flat and muted.
5. **Off-white and off-black.** Backgrounds a touch warmer or cooler than white; text a touch softer than black.
6. **Keep the count low.** Six to eight colors in total, including neutrals, is plenty.

---

## 3. Typography

This skill uses **no font files and no font services**. Character comes from *how* type is set,
not from which font is loaded. Use only the generic CSS font keywords. They resolve to fonts that
are already installed on the reader's device:

| Stack | Feels | Good for |
|---|---|---|
| `font-family: ui-serif, serif;` | bookish, calm, editorial | essays, studios, craft |
| `font-family: system-ui, sans-serif;` | neutral, native, quick | products, tools, docs |
| `font-family: ui-rounded, system-ui, sans-serif;` | soft, friendly | kids, food, community |
| `font-family: ui-monospace, monospace;` | technical, precise, honest | developers, data, logs |

Be honest about what this means: the exact font differs between devices, and the `ui-` keywords
are not understood by every browser. Where they are not, the browser uses the second keyword
(`serif`, `sans-serif`, `monospace`), so the page still works but may look plainer. Check the page in
more than one browser when you can, and design so that scale, weight, spacing and layout carry the character
even when the fallback font appears.

Combine at most two stacks: for example serif headlines with monospace details,
or system sans body with serif pull quotes.

### Where the character really comes from

- **Scale contrast.** A headline 4–6 times the body size, not 2 times. Use `clamp()` so it scales:
  `font-size: clamp(2.75rem, 7vw, 6rem);`
- **Weight and width.** Very light huge headlines, or very heavy small labels. Try `font-weight: 300` or `850`.
- **Spacing.** Tight letter-spacing on large headlines (`-0.03em`), wide tracking on small uppercase labels (`0.12em`).
- **Line length.** Body text between 55 and 75 characters: `max-width: 65ch;`
- **Details:** `font-variant-numeric: tabular-nums oldstyle-nums;`, `font-feature-settings`, `hanging-punctuation: first;`,
  `text-wrap: balance;` for headings and `text-wrap: pretty;` for paragraphs.
- **Sentence case** headings. Title Case On Every Word reads like a template.

---

## 4. Layout

### Break the default rhythm

The most common machine layout is: centered hero → three equal cards → centered quote → centered call to action.
Change at least two of these:

- **Asymmetry.** Put the headline on the left two-thirds and something small on the right.
  `grid-template-columns: 2fr 1fr;` or a 12-column grid with content starting at column 2 or 3.
- **Unequal items.** Instead of three equal cards: one large, two small. Or a list. Or a single paragraph.
- **Real alignment.** Left-aligned body text. Center only short, single lines.
- **Overlap once.** A heading that crosses into an image area, a number that sits in the margin.
- **Whitespace as a decision.** Large, uneven gaps between sections show hierarchy. Equal gaps everywhere flatten it.
- **Edges and rules.** Thin lines, margin notes, numbered sections and visible structure feel made by a person.

### Details that look generic

- The same large border radius on every box. Use a small radius, or none, or vary it with intent.
- Glass panels (blurred translucent cards) everywhere.
- Drop shadows on every card. Prefer borders or tone changes.
- Decorative blobs and floating gradient orbs.
- Icon above every heading.

---

## 5. Images and graphics without external files

- **Inline SVG** for marks, dividers, small illustrations, patterns and charts. Draw simple shapes that relate to the idea.
  Hand-tuned paths with slight irregularity look hand-made.
- **CSS patterns** with `repeating-linear-gradient` for paper lines, grids and textures.
- **Noise / grain** with an inline SVG `feTurbulence` filter at low opacity, to break flat digital color.
  Treat it as decoration: some browsers may not draw it, and the page must look finished without it.
- **Photos only from the user.** If none are given, design a page that does not need them.
  Never insert stock image links. Use a labeled placeholder box if a photo is essential.

Inline grain example:

```html
<svg width="0" height="0" aria-hidden="true">
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="2" stitchTiles="stitch"/></filter>
</svg>
<style>
  .grain::after { content: ""; position: fixed; inset: 0; pointer-events: none;
    filter: url(#grain); opacity: .06; }
</style>
```

---

## 6. Accessibility checks that belong to this step

- Text contrast at least 4.5:1, large text and UI lines at least 3:1. The palette script handles the base colors; re-check anything you add.
- Visible focus style on every link and button: `:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }`
  Never remove outlines without a replacement.
- Never use color alone to carry meaning.
- `<html lang="...">`, one `<h1>`, headings in order, `alt` text on every image.
