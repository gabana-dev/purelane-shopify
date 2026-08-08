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

## 5. Verification checklist

Run before handing over. Each item maps to an acceptance criterion in the PRD.

- [ ] 375 / 768 / 1024 / 1440 match the prototype; no horizontal scroll at 375
- [ ] Sold-out product shows a disabled "Sold out" button, card height unchanged
- [ ] Imageless product shows the placeholder, grid stays aligned
- [ ] 90-character title clamps to two lines, card height unchanged
- [ ] Product with no compare-at price shows no strikethrough and no discount pill
- [ ] Add / remove / reorder / duplicate each section in the editor — layout **and
      animations** still work afterwards
- [ ] Edit a section ten times in a row, then confirm the hero still rotates at the
      configured speed (proves no stacked timers)
- [ ] Keyboard: tab through hero dots, card links, buttons and both rails; focus visible
- [ ] OS "reduce motion" on → no parallax, no autoplay, content fully visible
- [ ] Zero console errors
- [ ] Add to cart works from the shop grid and from a combo
