# Purelane — prototype homepage → production Shopify sections

Assignment submission for Troopod. Built on stock **Dawn 15.5.0**, committed unmodified as
the first commit so everything after it is a reviewable diff:

```
git diff 16e496f..HEAD          # every line of the work, isolated from Dawn
```

## Verified on the live store

Measured, not asserted. Method for each is in [`docs/SETUP.md`](docs/SETUP.md), including
where the method fell short.

| | |
|---|---|
| Theme-editor safety | 10 consecutive `shopify:section:load` events on the hero — carousel transition rate unchanged, 2 before and 2 after. No timer stacking. `unload` freezes it |
| Layout stability | **CLS 0**, zero layout-shift entries, across two loads |
| Card contract | One card height across all 8 products at 500 / 768 / 1024 / 1440 — including the sold-out, the imageless and the 103-character title |
| Horizontal overflow | None at any measured width. Every element past the viewport edge sits inside a clipping ancestor |
| Contrast | **0 failures** across 530 elements at WCAG AA — after fixing one the prototype shipped at 4.38:1 |
| Keyboard | 42 of 42 focusable elements take focus with a visible ring. Hero dots use roving `tabindex`; arrows move selection and focus |
| Reduced motion | No parallax, no autoplay, both marquees frozen, reveals render final-state, manual controls still work |
| Images | 24 of 24 carry `width` + `height`; 21 lazy; webfonts non-render-blocking |
| CI | Theme Check + section-schema validation, green |

**Not measured:** 375px specifically (Chrome's minimum window width on macOS is 500; the
prototype has no breakpoint between 375 and 420), and LCP — there is no throttled-mobile
Lighthouse run, so no score is claimed. Full gaps in the build notes.

**Read in this order:**

| Document | What's in it |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | The spec, written before any code — section breakdown, card contract, data model, acceptance criteria |
| [`docs/BUILD-NOTES.md`](docs/BUILD-NOTES.md) | What I'd flag in the original file, what I changed and why, what I'd do with more time, and the gaps |
| [`docs/AI-WORKFLOW.md`](docs/AI-WORKFLOW.md) | What I delegated, where the agents failed, what I'd systematise over twenty of these |
| [`docs/SETUP.md`](docs/SETUP.md) | Metafield and metaobject definitions, seed products, verification checklist |

## What was built

| Section | File |
|---|---|
| Hero | `sections/purelane-hero.liquid` |
| Shop / product grid | `sections/purelane-shop.liquid` |
| Best-selling combos | `sections/purelane-combos.liquid` |
| Bundles | `sections/purelane-bundles.liquid` |
| Reviews rail | `sections/purelane-reviews.liquid` |

Shared: `snippets/purelane-product-card.liquid` (one card for shop, combos and tiers),
`snippets/purelane-review-card.liquid`, `snippets/purelane-icon.liquid`,
`assets/purelane.css`, `assets/purelane.js`.

## The three decisions that shaped the build

**1. Behaviour is per-section and tears itself down.** Shopify's theme editor re-renders a
single section over AJAX. The prototype bound every animation once at page load, so the
first time a merchant edits a section the reveals stop firing and the old section's timers
keep running against detached nodes. Every behaviour in `assets/purelane.js` is a
controller scoped to one section with an explicit teardown, wired to
`shopify:section:load` / `unload` / `select` / `deselect`.

**2. Nothing a merchant would change is hardcoded.** Ratings and badges are metafields —
using Shopify's *standard* `reviews.rating` keys, so the merchant's own review app
populates the cards rather than forcing double entry. Savings and discount percentages are
computed from `compare_at_price`, so a price change in admin can never leave a stale
"33% off" on the homepage.

**3. One card, three sections.** The brief notes several sections render similar cards, so
there is one parameterised snippet rather than three copies that drift apart.

## Notable find in the prototype

It defines `:root` **twice**, and the second block silently overrides the first with a
light palette. The page renders light despite the dark tokens at the top of the file.
Porting the first block would have shipped the wrong colour scheme across every section.
Full list of defects in [`docs/BUILD-NOTES.md`](docs/BUILD-NOTES.md).

## Running it

See [`docs/SETUP.md`](docs/SETUP.md). Product artwork extracted from the prototype's
base64 data-URIs is in `seed-images/` so the store matches the design.

## Honest status

The five required sections are built, the store setup is documented and reproducible, and
the verification checklist in `SETUP.md` has been run on the live store — including the
keyboard and reduced-motion passes, each marked with how it was measured and where the
method fell short of the real thing. That pass found one real defect, since fixed: with
motion off, the reviews marquee froze and took every review past the fold out of reach.

What remains open is a spacing-by-spacing diff against the prototype, and 375px
specifically, which Chrome's 500px minimum window width put out of range. Details in the
gaps section of the build notes.
