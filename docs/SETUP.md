# Store setup — metafields, metaobjects and seed data

Everything needed to reproduce the dev store from scratch. Written as a checklist rather
than prose because this is the sort of thing that otherwise becomes tribal knowledge.

---

## 1. Product metafield definitions

**Settings → Custom data → Products → Add definition.**

| Name | Namespace and key | Type | Notes |
|---|---|---|---|
| Product rating | `reviews.rating` | Rating (0–5) | **Use Shopify's standard definition** — pick it from the "standard definitions" list rather than creating a custom one |
| Rating count | `reviews.rating_count` | Integer | Standard definition |
| Card badge | `custom.badge` | Single line text | "Best seller", "New", "Top rated". Blank hides the pill |
| Combo items | `custom.combo_items` | Product (list of) | The products stacked in a combo tray |
| Combo blurb | `custom.combo_blurb` | Multi-line text | The "Includes: …" line |

**Why the standard `reviews.*` keys matter.** Every real review app — Judge.me, Loox,
Okendo — writes to those exact keys. Using them means the merchant installs their review
app and the cards populate themselves. A bespoke `custom.rating` field would force the
marketing team to type every rating twice and let the two copies drift apart.

## 2. Metaobject definition — `review`

**Settings → Custom data → Metaobjects → Add definition.** Name it `Review`, type `review`.

| Field | Key | Type |
|---|---|---|
| Rating | `rating` | Integer (1–5) |
| Title | `title` | Single line text |
| Body | `body` | Multi-line text |
| Author | `author` | Single line text |
| Context | `context` | Single line text — e.g. "Laundry detergent" |

Tick **Storefronts → make available to storefront**, or the section cannot read them.

Then add 5–6 entries under **Content → Metaobjects → Review**.

## 3. Products to seed

The brief requires at least eight products **including one sold out, one with no image and
one with a very long title**. Those three are not decoration — they are the edge cases the
card is graded on, so they are seeded deliberately.

Artwork for each is in `/seed-images` (extracted from the prototype so the store matches
the design rather than showing grey placeholders).

| # | Title | Price | Compare-at | Badge | Rating | Image | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Tap cleaner & limescale remover | 200 | 299 | Best seller | 4.8 / 237 | `p-tap.svg` | |
| 2 | Kitchen cleaner, foaming | 200 | 299 | Best seller | 4.8 / 254 | `p-kitchen.svg` | |
| 3 | Copper, bronze & brass cleaner | 200 | 299 | Top rated | 4.8 / 231 | `p-metal.svg` | |
| 4 | Washing machine cleaner & descaler | 200 | 299 | New | 4.8 / 183 | `p-wm.svg` | |
| 5 | Organic dishwash liquid gel | 249 | 349 | — | 4.7 / 402 | `p-dish.svg` | |
| 6 | Liquid handwash, aloe & neem | 179 | 249 | — | 4.9 / 118 | `p-handwash.svg` | **Set inventory to 0, uncheck "continue selling"** → sold-out state |
| 7 | Floor cleaner concentrate | 299 | 399 | — | 4.6 / 95 | *(none — leave empty)* | **No image** → placeholder state |
| 8 | Plant-powered laundry detergent concentrate for sensitive skin, tough stains and everyday family washing | 349 | 499 | Best seller | 4.8 / 512 | `p-laundry.svg` | **90-char title** → clamping state |

Also create three **combo products** for the combos section:

| Title | Price | Compare-at | `custom.combo_items` |
|---|---|---|---|
| Kitchen essentials | 499 | 897 | products 2, 5, 1 |
| Laundry care set | 599 | 998 | products 8, 6 |
| Whole home box | 999 | 1,796 | products 1, 2, 5, 7 |

Put products 1–8 in a collection called **Bestsellers** and point the shop section at it.

## 4. Theme setup

1. Online Store → Themes → Dawn → **Edit code**, or connect this repo via GitHub.
2. Homepage → **Add section** → the five `Purelane …` sections appear under the
   section list.
3. Hero: add three promise badges and three product slides.
4. Shop: pick the **Bestsellers** collection.
5. Combos: add three combo blocks, pick the combo products.
6. Bundles: three tiers; tick "Highlight" on the middle one.
7. Reviews: pick the review metaobjects.

## 4b. Store configuration gotchas (learned the hard way)

Two settings that are invisible until they break everything:

**A market needs a shipping zone that covers it.** This store's market covers India while
the only shipping zone covered the United States. The result: *every* product reported
`available: false` on the storefront while the Admin API reported them sellable, so the
whole grid rendered "Sold out". Not an inventory, tracking, publication or location
problem — I ruled all four out first. Fix: Settings → Shipping and delivery → Add zone
covering the market's countries, with at least one rate.

**Currency formatting is separate from currency.** Setting the store currency to INR gives
you `Rs. 349.00`. The prototype shows `₹349`. Settings → General → Currency display →
Change formatting → `₹{{amount_no_decimals}}` in both HTML fields.

## 5. Verification checklist

Run before handing over. Each item maps to an acceptance criterion in the PRD.

Marked honestly — `[x]` was verified on the live store, `[ ]` was not.

- [x] Compared side by side against the prototype in a browser at 1440 and ~500px
- [x] Measured at 500 / 768 / 1024 / 1440: no page-level horizontal overflow at any width
      (`scrollWidth == clientWidth`), and every element crossing the viewport edge sits
      inside a clipping ancestor — the ticker, the reviews rail or the hero badge strip.
      Card height is one value per width across all eight products, including the three
      edge cases. Shop grid is 4-up at 1024 and 1440. **375 not measured** — Chrome's
      minimum window width on macOS is 500, so the narrowest real viewport available was
      500. Device emulation would close this
- [x] Sold-out product shows a disabled "Sold out" button, card height unchanged
- [x] Imageless product shows the placeholder, grid stays aligned
- [x] 103-character title clamps to two lines, card height unchanged
- [x] Prices, compare-at and computed discount render from real product data
- [x] Add to cart renders for available products, disabled for the sold-out one
- [x] Zero Liquid errors on the rendered page
- [x] **Ten consecutive `shopify:section:load` events on the hero: carousel transition
      rate unchanged (2 before, 2 after) — no timer stacking.** Measured on the live
      store, not asserted
- [x] `shopify:section:unload` freezes the carousel — teardown confirmed
- [x] No horizontal overflow; 24 images all carry `srcset`, `width` and `height`
- [x] 10 add-to-cart forms, 1 disabled button (the sold-out product)
- [x] Keyboard pass: all 42 focusable elements on the page take focus and every one of
      them paints a visible focus ring, except two that belong to Dawn (the skip link and
      Dawn's search input, which uses a box-shadow focus style rather than an outline).
      Hero dots implement roving `tabindex` correctly — exactly one is tabbable,
      `aria-selected` tracks it, and Arrow Left/Right move both the selection and the
      focus. **Caveat on method:** the automation harness could not deliver a real `Tab`
      keypress to the page, so focus order was read from the DOM and each stop was
      focused programmatically rather than walked with the key itself
- [x] "Reduce motion" on → no parallax (hero transform stays `none` across a 600px
      scroll), no autoplay (hero stayed on slide 0 for 9s, 2.4 intervals' worth), both
      marquees frozen (`getAnimations()` empty on the ticker and the reviews track),
      reveals rendered in their final state immediately rather than waiting on an
      observer, and the dot controls still work manually. **Caveat on method:** the OS
      toggle is out of reach from automation, so this was forced two ways — CSS by setting
      each `prefers-reduced-motion` block's `media.mediaText` to `all` *in place*, and JS
      by overriding `MediaQueryList.matches` and re-dispatching `shopify:section:load`.
      In place matters: re-emitting the blocks from an appended `<style>` moves them to the
      end of the document and silently changes which rule wins a specificity tie, so the
      first run of this check reported a false failure on the rail
- [x] Contrast: every text node under `.pl` audited against its computed background at
      WCAG AA (4.5:1 small, 3:1 large), visually-hidden labels excluded. **Zero failures**
      — after fixing one: the prototype's `#4f7d10` came in at 4.38:1. See flag 8 in the
      build notes
- [x] CLS measured at **0** across two loads, no layout-shift entries at all. All 24 images
      carry `width` and `height`, 21 of 24 lazy-loaded, webfonts non-render-blocking via
      `media="print"` + `onload`. **Not a Lighthouse run** — no throttled mobile profile,
      and LCP did not report reliably from an automated tab, so there is no LCP number here
- [x] Reviews rail is reachable with motion off. It was not: the rail is a marquee, so it
      clips its overflow and relies on the animation to bring later cards into view —
      freeze the animation and every review past the fold became unreachable. Now
      `overflow-x:auto` under `prefers-reduced-motion`, verified on the live store with the
      animation frozen. Found by this pass
