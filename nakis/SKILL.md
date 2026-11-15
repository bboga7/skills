---
name: nakis
description: Makes web pages look and read hand-made instead of machine-generated. Use when building, redesigning or reviewing a landing page, portfolio, personal site, product page or any marketing page; when the user asks for original copy, a distinctive visual identity, tasteful animations or page transitions; or when they say a page looks "AI-generated", "generic", "templated" or "soulless". Covers copy (English and Turkish), color, typography, layout, motion, and a local audit script that scores the result. Not meant for app dashboards or admin screens.
license: MIT
---

# Nakis

*Nakış* is hand embroidery: every stitch placed on purpose, never printed from a stock pattern.
A page made with this skill should feel the same. Someone made decisions here.

Generic pages are not ugly. They are made of defaults: the first font that comes to mind,
the most common gradient, three equal cards, a headline that could sell anything.
This skill replaces each default with a decision, in words, visuals and motion, and then checks the result.

## Ground rules

- **Local only.** No external fonts, CDNs, stock images, icon packs, analytics or network calls.
  Use system font stacks, inline SVG, plain CSS and as little script as possible.
- **No borrowed identity.** Never name, quote or imitate real brands, people or products,
  unless the user provides them as their own content.
- **Never invent facts.** A fact is anything the reader could hold the owner to: numbers, clients,
  testimonials, awards, prices, dates, guarantees, what a customer gets, how the work is done,
  who it is for. Facts come only from the brief or the user. When something is missing:
  - if the page works without it, **leave it out**;
  - if the page cannot work without it, ask the user, or use a visible placeholder like `[course date]`;
  - never put a placeholder in the first screen, and never build a whole section out of placeholders.
  Small, reasonable inferences (for example "visit us on Saturday" when the brief only gives Saturday hours)
  are allowed, but list each one in your report so the user can confirm it.
- **Don't write about the page itself.** No lines about the fonts, the code, "built by hand",
  "no tracking" or how the page was made, unless the user asks for them. Readers came for the subject.
- **Accessible by default.** Readable contrast, visible focus states, semantic HTML, reduced-motion support.
- **Quality, not disguise.** The goal is a better page. Do not describe the result as
  "undetectable" or as a way to hide that a tool was used.

## Workflow

Follow the steps in order. Each step has a reference file. Read it when you reach that step, not before.

### 1. Read the brief

Before writing any code, work out four things:

1. **What** the page is (portfolio, product launch, personal site, event...).
2. **Who** reads it, and what they already know.
3. **The one action** a reader should take.
4. **Three tone words** (for example: calm, precise, warm).

If the request is too vague to decide these, ask **one** question. Otherwise state your reading in one line and continue:

> Reading this as: a portfolio for hiring managers, tone calm / precise / warm, main action "get in touch".

Then gather **concrete material**: real project names, numbers, places, dates, tools, short stories.
Specific detail is the strongest signal that a person made the page. Ask for it if it is missing.

### 2. Write the copy first

Copy decides the layout, never the other way round. Read `references/copy.md`.

- Write the headline last, after the body copy shows what the page is really about.
- Prefer one concrete claim over three vague ones.
- Detect the page language and apply the matching section of `references/copy.md`.
- **Claim check.** Before moving on, go through the copy sentence by sentence. For every factual claim,
  point to the line of the brief it comes from. Delete or rewrite every claim you cannot point to.
  Specific does not mean invented: be specific with the facts you have, and plain where you have none.
- **A thin brief makes a short page.** If there are few facts, write fewer sections. Do not repeat the same
  number, phrase or call to action to fill space: each fact once in the body, the main action at most twice
  in the copy. Contact details (a phone number, an address) may appear wherever the reader needs them.
  The page always ends with a way to act: the button, the number or the address.
- **Sound like the owner talking.** Warmth comes from voice, not from invented detail: address the reader,
  use the trade's own words, vary the sentences. Do not describe interface behavior ("your phone app opens").

### 3. Set the visual identity

Read `references/visual.md`.

- Pick a single **idea** for the page (a metaphor, a material, a period, a place) and let it drive the choices.
- Generate the palette from one seed color that fits the idea:

  ```bash
  python3 scripts/palette.py "#2f5d50"            # prints CSS custom properties
  python3 scripts/palette.py "#2f5d50" --json     # machine-readable output
  ```

  The script checks text and background contrast and adjusts colors that fail.
  To keep a background you chose yourself, add `--bg "#f4ead8"`; text colors are then fitted to it.
- Choose a system font stack that fits the tone (the stacks are in `references/visual.md`).
- Break the grid at least once, on purpose.
- Textures, grids and patterns stay faint or stay out of text areas. If a texture makes body text
  harder to read, the texture goes.
- **Avoid this skill's own house look.** A serif headline with an italic, colored second half, small
  uppercase monospace labels and numbered sections is now this skill's most common output. Use that
  combination only when the page's idea truly calls for it; otherwise take type, color and layout
  somewhere else (a sans-serif page, a dark page, a single-column page, a photo-led page).
- `examples/` shows the audit, not a style. Do not reuse its idea (linen and a red thread). If the subject
  really calls for something close, change the material, the color and the signature motion.

### 4. Add motion

Read `references/motion.md`. Copy only the parts you need from `assets/motion.css`.

- Every animation must answer "what does this help the reader notice?". If nothing, remove it.
- Prefer one memorable moment over many small effects.
- Always respect `prefers-reduced-motion`.

### 5. Audit and fix

Run the audit on the finished page:

```bash
python3 scripts/audit.py path/to/index.html                # human-readable report
python3 scripts/audit.py path/to/index.html --json         # machine-readable report
python3 scripts/audit.py path/to/index.html --lang tr      # force Turkish copy rules
```

- Fix every **high** finding. Review every **medium** finding and fix it or explain why it stays.
- If the page quotes a bad phrase on purpose (for example in a before/after comparison),
  add `data-nakis-ignore` to that element so the copy checks skip it. Do not use it to hide real copy.
- Target score: **85 or higher**. Re-run the audit after fixing.
- Finish with `references/checklist.md`, which covers what a script cannot judge.

## Working inside an existing project

- Keep the project's stack, components and existing brand. Apply the principles; do not rewrite the framework.
- Run the audit on the built HTML output, not on template source files.
- If the project already loads external fonts or libraries, mention it once and leave the decision to the user.

## What to report back

Keep it short:

1. The one-line brief reading.
2. The page's idea and the 3–5 decisions that follow from it (palette, type, layout, motion).
3. The audit score before and after fixing, and any finding you deliberately kept.
4. Every placeholder the user still needs to fill, and every claim you were unsure about.
