# PRD — Purelane homepage sections (Shopify / Dawn)

**Author:** Gabana Kane · **Date:** 2026-08-08 · **Status:** approved for build
**Source of truth for visuals:** `purelane-homepage.html` (the prototype).
**Source of truth for behaviour:** this document.

> Written before implementation. Precise enough that an agent can build from it and that I
> can verify the output against it. Where the prototype and this document disagree on
> *appearance*, the prototype wins. Where they disagree on *implementation*, this wins.

---

## 1. Objective

Convert five prototype sections into Shopify sections a merchant's marketing team can
operate without a developer, on stock Dawn 15.5.0, with no visual change.

**Explicit non-goal:** improving the design. The brief is unambiguous — *"This is a build,
not a redesign"* and *"Rebuilding it to look how you'd have designed it is an automatic
no."* Visual output is reproduced exactly. Engineering judgment goes underneath it.

## 2. Device scope

Verified at **375, 414, 768, 1024, 1280, 1440**. 375px is the floor. No horizontal scroll
at any width. The prototype's breakpoint set is incoherent (§8) and is normalised to a
mobile-first ladder without changing rendered output.

## 3. Design tokens (extracted from the prototype, not re-invented)

```
--ink #17102b   --deep #241a3d   --brand #4b3a8f   --brand-lt #6b55b8
--paper #ece6f7 --accent #f0a03c --accent-2 #c9761d --surface #faf7fd
--r 26px  --r-sm 16px  --maxw 1180px  --sec-y 34px
--ease cubic-bezier(.2,.7,.2,1)
Display/headings: Outfit 500–800 · Body: Inter 400–700
```

Tokens live once in `assets/purelane.css`, scoped under `.pl` so they cannot leak into
Dawn's own styles. Fonts are loaded once at theme level, not per section.

## 4. Sections to build

| # | Section | File | Prototype anchor |
|---|---|---|---|
| 01 | Hero | `sections/purelane-hero.liquid` | `section.hero` |
| 02 | Shop / product grid | `sections/purelane-shop.liquid` | `#shop` |
| 03 | Best-selling combos | `sections/purelane-combos.liquid` | `#combos` |
| 04 | Bundles | `sections/purelane-bundles.liquid` | `#bundles` |
| 05 | Reviews rail | `sections/purelane-reviews.liquid` | `#reviews` |

Shared: `snippets/purelane-product-card.liquid`, `snippets/purelane-rating.liquid`,
`snippets/purelane-price.liquid`, `assets/purelane.css`, `assets/purelane.js`.

## 5. The shared card — the spine of the build

The brief states *"Several sections render similar cards. Build accordingly."* Shop,
combos and bundles all render a product-shaped card. **One snippet, parameterised:**

```liquid
{% render 'purelane-product-card',
     product: product,
     variant: 'shop' | 'combo' | 'tier',
     show_rating: true,
     show_badge: true,
     index: forloop.index0 %}
```

**Card anatomy:** media → badge pill → title → rating + count → price / compare-at /
discount % → add-to-cart.

### Card edge cases (the store must contain each — the brief requires seeding them)

| Case | Required behaviour |
|---|---|
| **Sold out** | Button reads "Sold out", disabled, `aria-disabled`; card stays same height; no layout shift |
| **No image** | Render a styled placeholder at the exact card media aspect ratio. Never a broken image, never a collapsed card |
| **Very long title** | Clamp to 2 lines with ellipsis; card height unchanged; full title in `title` attribute for a11y |
| No compare-at price | Hide the strikethrough and the discount badge entirely — no empty elements, no "0% off" |
| No rating metafield | Hide the rating row entirely rather than printing "★ 0.0" |

## 6. Data model — real Shopify data

Products, titles, prices, availability and images come from the platform. Where no native
field exists we define metafields rather than hardcoding into Liquid.

### Product metafields

| Namespace.key | Type | Purpose |
|---|---|---|
| `reviews.rating` | `rating` (Shopify standard) | Star value on the card |
| `reviews.rating_count` | `number_integer` (standard) | "· 237 reviews" |
| `custom.badge` | `single_line_text_field` | "Best seller" / "New" / "Top rated" pill |
| `custom.combo_items` | `list.product_reference` | Products shown stacked in a combo tray |
| `custom.combo_blurb` | `multi_line_text_field` | The "Includes: …" line |

**Why standard `reviews.*`**: any real review app (Judge.me, Loox, Okendo) writes to those
keys. Using them means the merchant's actual review app populates the cards on day one
instead of us owning a bespoke field they'd have to double-enter.

**Prices and savings are computed, never typed.** "You save ₹398" and "33% off" derive from
`compare_at_price - price`. A merchant changing price in admin updates the badge with no
developer involved. Hardcoding these would fail the brief's core requirement.

### Metaobject — `review`

| Field | Type |
|---|---|
| `rating` | integer 1–5 |
| `title` | single line text |
| `body` | multi-line text |
| `author` | single line text |
| `context` | single line text ("· Laundry detergent") |

Reviews rail renders a metaobject list, so marketing adds a review without touching code.

## 7. Merchant controls (schema)

Nothing a marketing team would plausibly change is hardcoded. Every section exposes:

- **Hero** — heading (3 lines), highlighted word, lede, 2 CTAs (label + link), 3 promise
  badges (blocks: icon, label), slides (blocks: product reference), autoplay on/off,
  autoplay interval, parallax on/off.
- **Shop** — kicker, heading, product source (collection picker), product limit, columns
  desktop/mobile, show rating, show badges.
- **Combos** — kicker, heading, lede, combo blocks (product reference + flag text).
- **Bundles** — kicker, heading, lede, tier blocks (tag, product reference, qty label,
  feature list, CTA label/link, "most popular" flag).
- **Reviews** — kicker, aggregate rating, aggregate text, review source (metaobject list),
  scroll speed.

All section colours, paddings and top/bottom spacing exposed as settings where Dawn
convention expects them, so sections can be reused on other templates.

## 8. Production defects in the prototype — fix and document

The brief invites this: *"where the underlying HTML or CSS is wrong for production …fix it
and tell us what you changed."* Each fix is visually neutral.

| Defect | Evidence | Fix |
|---|---|---|
| Duplicate DOM ids | `cg`, `wf`, `wf2` appear twice; SVG gradient ids repeat per card | Scope ids per section via `section.id`; gradient ids suffixed |
| No real images | 0 `<img>` tags; 68 inline SVG / CSS `role="img"` spans | Real `<img>` with `srcset`, `width`/`height`, `loading`, `decoding` |
| Incoherent breakpoints | 30 media queries, 12 widths, `max-` and `min-width` mixed, `760` in both directions | Single mobile-first ladder: 640 / 768 / 1024 / 1180 |
| Render-blocking fonts | Google Fonts `@import` in `<head>` | `preconnect` + `font-display: swap`, loaded once at theme level |
| Non-functional add-to-cart | `<button>` outside any form | Real product form posting to `/cart/add` |
| 40 inline styles, 4 `!important` | inline `style=` attributes | Moved to stylesheet classes |
| Layout shift risk | media with no intrinsic dimensions | Fixed aspect ratios on all media boxes |

**Kept deliberately:** the prototype's `prefers-reduced-motion` handling is correct. It is
preserved and extended to every animation we add.

## 9. Theme-editor survival (the requirement most likely to be missed)

The prototype initialises with a single `querySelectorAll` at load. Shopify's theme editor
re-renders individual sections over AJAX, so any handler bound at load is dead the moment a
merchant edits a section — the brief requires that *"adding, removing, reordering and
reconfiguring should never break anything, including the animations."*

**Design:** every behaviour is a self-contained initialiser scoped to a section root, with
teardown, registered against Shopify's section lifecycle:

```
shopify:section:load     → init that section only
shopify:section:unload   → disconnect observers, clear timers, remove listeners
shopify:section:select   → pause autoplay while the merchant is editing
shopify:section:deselect → resume
```

No global state. Observers and intervals are stored per-section and disposed on unload, so
repeated edits cannot leak timers or stack duplicate observers.

## 10. Performance

- No per-section `<script>` or `<style>` tags; one CSS and one JS asset, deferred.
- Hero image: `loading="eager"`, `fetchpriority="high"`; all other media lazy.
- Explicit `width`/`height` on every image → CLS ≈ 0.
- Scroll/pointer work batched in one `requestAnimationFrame`, listeners `passive`.
- Parallax and pointer tracking bound only ≥1024px and only when motion is allowed.
- Inline SVG decorative icons carry `aria-hidden="true"` and are not duplicated per card.

Target: LCP < 2.5 s, CLS < 0.1, INP < 200 ms on a mid-tier mobile.

## 11. Accessibility

- Card media has meaningful `alt` from the product; decorative SVG is `aria-hidden`.
- Carousels: real `<button>` controls, `aria-label`, visible focus rings, arrow-key
  support, autoplay pauses on hover **and** on focus-within.
- Rating exposed as text to screen readers, not stars alone.
- All interactive targets ≥44 px; contrast checked against the prototype palette.
- `prefers-reduced-motion: reduce` disables parallax, autoplay and reveals — content
  renders in its final state, never hidden.

## 12. Acceptance criteria

A section is **done** only when all of these hold:

1. Visually indistinguishable from the prototype at 375 / 768 / 1024 / 1440.
2. Every merchant-editable string/image/link is a schema setting or Shopify data.
3. Renders correctly with a sold-out product, an imageless product and a 90-character title.
4. Add / remove / reorder / duplicate in the theme editor leaves layout **and animations**
   working; no duplicate timers after ten consecutive edits.
5. Zero console errors; no horizontal scroll at 375px.
6. Keyboard-operable end to end; visible focus; reduced-motion respected.
7. No hardcoded price, rating, badge or product name anywhere in Liquid.
8. Section renders without error when its data source is empty or unset.

## 13. Out of scope (stated, not silently dropped)

Everything in the prototype outside the five sections (ingredients, how-it-works, proof,
range, categories, footer, the scene-crossfade background system). The global scroll-driven
scene crossfade is deliberately **not** ported: it couples every section to a page-level
background stage, which would break section independence in the theme editor. Documented as
a trade-off in the build notes rather than half-implemented.
