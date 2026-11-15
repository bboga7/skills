# Motion

Machine-made pages tend to animate *everything a little*: every card fades up, every button
bounces, a gradient loops forever. Hand-made motion does *one thing well*, at the moment it matters.

All motion here is plain CSS, with an optional ten-line script. Ready-made pieces are in
`assets/motion.css`. Copy only the parts you use.

---

## 1. Ask three questions before adding any animation

1. **What should the reader notice?** A change of state, a relationship, an order, a direction.
2. **When?** On load, on scroll into view, on hover or focus, on navigation.
3. **Would the page be worse without it?** If not, leave it out.

If you cannot answer the first question in one short sentence, do not add the animation.

---

## 2. Principles

- **One signature moment.** Choose a single memorable motion for the page (the headline assembling,
  a line being drawn, a page turning) and keep everything else quiet.
- **Motion follows the idea.** Paper slides and settles. Ink spreads. Machines snap. Water eases.
  Pick easing and duration that match the page's idea from `references/visual.md`.
- **Short and quick.** Most UI transitions: 120–250 ms. Entrances: 400–700 ms. Nothing important should wait for an animation.
- **Animate cheap properties.** `transform` and `opacity` (and `clip-path` for reveals). Avoid animating `width`, `height`, `top`, `left` or `margin`.
- **No infinite loops** on content. A loop is acceptable only for a real loading state.
- **Stagger with intent.** If items enter one after another, the order should mean something (reading order, time order).
- **Respect the reader.** Everything turns off under `prefers-reduced-motion: reduce`. This is required, not optional.

### Easing set

Defined as custom properties in `assets/motion.css`:

| Name | Value | Feels like |
|---|---|---|
| `--ease-settle` | `cubic-bezier(.2, .7, .1, 1)` | paper landing, calm entrance |
| `--ease-snap` | `cubic-bezier(.5, 0, .1, 1)` | precise, mechanical |
| `--ease-swing` | `cubic-bezier(.3, 1.4, .5, 1)` | playful, slight overshoot (use rarely) |

---

## 3. Patterns in `assets/motion.css`

| Class | What it does | Use for |
|---|---|---|
| `.nk-reveal` | Fades and lifts an element as it scrolls into view. Set `style="--i: 2"` to delay by order. | section entrances |
| `.nk-mask` | Reveals a headline line by line from behind a mask. Wrap each line in `<span>`. | the signature headline |
| `.nk-draw` | Draws an inline SVG path as if by hand. | underlines, signatures, simple illustrations |
| `.nk-link` | Underline that thickens and lifts on hover and focus. Stays visible at rest. | text links |
| `.nk-press` | Small press-down response on buttons. | buttons |
| `.nk-tilt` | Slight resting rotation that straightens on hover. | cards, photos, notes |

### Scroll reveals

`.nk-reveal` uses CSS scroll-driven animation where the browser supports it, so no script is needed.
Where it is not supported, the element simply appears. If you need the effect in every browser,
add this small script once, before `</body>`:

```html
<script>
  if (!CSS.supports("animation-timeline: view()")) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    }, { rootMargin: "0px 0px -10% 0px" });
    document.querySelectorAll(".nk-reveal").forEach((el) => { el.classList.add("nk-js"); io.observe(el); });
  }
</script>
```

---

## 4. Page transitions

For multi-page sites, cross-document view transitions give a smooth change between pages with CSS only:

```css
@view-transition { navigation: auto; }
::view-transition-old(root) { animation: 220ms var(--ease-snap) both nk-out; }
::view-transition-new(root) { animation: 420ms var(--ease-settle) both nk-in; }
```

Give a shared element the same name on both pages to make it travel between them:

```css
.site-title { view-transition-name: site-title; }
```

Browsers without support simply load the next page normally. These rules are included in `assets/motion.css`.

---

## 5. What to avoid

- Every section fading up the same way.
- Buttons that bounce, pulse or glow continuously.
- Looping gradient backgrounds and floating blobs.
- Parallax on body text.
- Scroll-jacking (taking control of the scroll speed or direction).
- Cursor followers and custom cursors on content pages.
- Typing effects that make the reader wait to read the headline.

---

## 6. Before you leave this step

- You can name the signature moment in one sentence.
- No more than one or two animation types on the page besides hover and focus feedback.
- `prefers-reduced-motion` turns all of it off.
- The page is fully readable with animations disabled.
