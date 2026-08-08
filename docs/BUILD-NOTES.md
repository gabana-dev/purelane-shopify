# Build notes

What I'd flag about the original file, what I changed and why, and what I'd do with more
time. Written to be read in five minutes.

---

## What I'd flag about the prototype

I read the file before writing any code. Seven things would have caused problems in
production, and one thing was done well.

**1. It defines `:root` twice, and the second block wins.** The first token block is a dark
palette (`--ink:#17102b`, light text). A second `:root` further down overrides it with a
light palette (`--ink:#f4f0fb`, `--paper:#241a3d`). The page therefore renders *light*.
Anyone porting the tokens from the top of the file ships the wrong colour scheme across
every section at once. Both blocks are merged in cascade order in `assets/purelane.css`.

**2. Duplicate DOM ids — the markup is invalid.** `cg`, `wf` and `wf2` each appear twice,
and the SVG gradient ids (`gTAPl`, `gKITb`, …) repeat every time a card is duplicated.
Duplicate gradient ids mean a card's fill can resolve to a different card's gradient.

**3. No real images anywhere.** Zero `<img>` tags. All 68 product visuals are inline SVG or
CSS backgrounds on `<span role="img">`, with the dimensions carried by per-product classes
(`.p-tap`, `.p-kitchen`). Fine for a prototype, impossible for a store.

**4. The breakpoint logic is incoherent.** 30 media queries across 12 distinct widths,
mixing desktop-first `max-width` with mobile-first `min-width` — including `760px` used in
both directions.

**5. Add to cart is decorative.** `<button class="btn">Add to cart</button>` sits outside
any form. It looks like commerce and does nothing.

**6. All behaviour is bound once, globally, at load.** One `querySelectorAll` pass wires
every animation on the page — fatal in the theme editor (see below).

**7. The hero is not a product carousel.** This one I got wrong first and had to correct.
Its three slides are bundle *tiers* — one bottle at "Single bottle ₹200 / 33% off", two at
"Any 2 products ₹349 / Save ₹249", three at "Any 3 ₹499 / Save ₹398". The `.hs2` / `.hs3`
rules with staggered heights and z-order exist precisely to stack two or three bottles.
I built it as "rotate through featured products", realised the error when comparing against
the prototype in a browser, and rebuilt it.

**Done well, and kept:** the prototype checks `prefers-reduced-motion` before animating.
That is more than most production themes do. Kept, and extended to everything I added.

## What I changed, and why

| Change | Reason |
|---|---|
| One `product-card` snippet for shop / combos / tiers | The brief notes several sections render similar cards. Three copies drift apart the first time one is edited |
| Ratings, review counts, badges → metafields | No native Shopify field. Using the **standard** `reviews.rating` keys means a real review app populates them on day one |
| Savings and discount % computed from `compare_at_price` | Typed values drift. A merchant running a sale should not have to remember to edit the homepage |
| Reviews → `review` metaobject | No native testimonial object. Marketing adds one in admin with no deploy |
| Behaviour rewritten as per-section controllers with teardown | See "theme editor" below |
| 62 KB of CSS → 32 KB, scoped under `.pl` | We render five of twelve sections. Scoping stops collisions with Dawn in both directions |
| Repeated inline SVG → one icon snippet | The same 24×24 leaf appeared 55 times |
| Fixed aspect ratios on every media box | The prototype's images had no intrinsic dimensions — a CLS problem once images are real |
| Hero owns its background | The mint gradient came from a page-wide fixed "scene" layer shared by all sections (see below) |

### The theme editor, specifically

This is the requirement I'd expect most submissions to miss.

Shopify's editor re-renders **one section** over AJAX when a merchant edits it. Any handler
bound at page load then points at DOM nodes that no longer exist: reveals stop firing, the
hero freezes, and the old section's `setInterval` keeps running forever. Edit a section ten
times and you have ten timers mutating detached nodes.

`assets/purelane.js` treats every behaviour as a controller that owns one section element
and knows how to destroy itself, keyed by section id:

- `shopify:section:load` → initialise **that section only**
- `shopify:section:unload` → disconnect observers, clear intervals, unbind listeners
- `shopify:section:select` / `deselect` → pause autoplay while the merchant is editing

Re-initialising always tears down first, so a re-render cannot stack a second observer.

### Deliberate omission: the scene system

The prototype has a page-level, scroll-driven background stage (`data-scene="1..4"`,
`.water`, `.wl-*`) that all sections drive. **I did not port it.** It requires every section
to know its position in a global sequence and to mutate a shared element outside itself,
which breaks section independence in the theme editor — reorder two sections and the
background sequence is wrong.

The visible consequence was the hero rendering on white. Rather than leave that, the hero
now owns its own gradient and overlay: identical output, no cross-section coupling.

## Three bugs worth reporting on myself

**An unterminated quote silently discarded the entire stylesheet.** When merging the two
`:root` blocks my script split declarations on `;` — which also appears inside
`data:image/svg+xml;base64,…`. All fourteen image tokens were truncated to
`url("data:image/svg+xml;`, leaving an unclosed quote. CSS parsers discard everything after
one, so 28 KB of styles were thrown away and every section rendered unstyled. The file had
balanced braces and passed my own validation; only a browser revealed it.

**My CSS keep-list silently dropped rules I hadn't anticipated.** The extraction kept only
classes I expected from the markup, so `.ptag` — the hero's price card — was never carried
over, and it rendered as unstyled text in the wrong corner. Auditing the extraction against
the original stylesheet, rather than trusting it, found that plus `.sec-pad`, `.hs1 .a` and
the reviews-rail pause-on-hover. That audit is the reusable artifact here.

**Respecting reduced motion made a section unreachable.** The reviews rail is a marquee: it
clips its overflow and relies on the animation to bring later cards into view. Honouring
`prefers-reduced-motion` freezes that animation — which meant every review past the fold
became unreachable, by keyboard or otherwise, for exactly the visitors the media query is
meant to protect. The rail is `overflow-x:auto` under reduced motion now. Worth naming
because it is the failure mode of accessibility work done rule-by-rule: each rule was
satisfied and the outcome was still worse.

## Gaps — being straight about them

- **Store availability took an hour of store configuration, not code.** Every product read
  as sold out on the storefront while the Admin API reported them sellable. Ruled out, in
  order: inventory quantity, tracking, inventory policy, publication status, and location
  fulfilment. The actual cause was that the market covered India while the only shipping
  zone covered the United States — a market with no shippable zone makes every product
  unpurchasable. Adding an India zone with a free rate fixed it.
- **The store's nav menu is Dawn's default** (Home / Catalog / Contact) rather than the
  prototype's five links, because those link to sections that were out of scope. The header
  reads the menu from Shopify Navigation, so it is a content change, not a code change.
- **Not pixel-diffed against the prototype.** Measured on the live store at 500 / 768 /
  1024 / 1440 — no page-level horizontal overflow at any width, card height one value per
  width across all eight products including the three edge cases — but that is the layout
  holding, not a spacing-by-spacing diff against the original file. 375 specifically was
  not measured: Chrome's minimum window width on macOS is 500, and I would rather say so
  than round it down on the checklist.
- Only the five required sections plus the bonus header were built; the other seven in the
  file are untouched.

## What I'd do with more time

1. **Self-host the two webfonts** as `woff2` instead of Google Fonts — the largest remaining
   third-party request.
2. **Lighthouse pass on a throttled mobile profile** and a measured CLS/LCP number rather
   than a design that should score well.
3. **Snapshot tests for the card** across its five states (normal, sold out, no image, long
   title, no compare-at) so a future edit cannot silently regress an edge case.
4. **Metafield definitions as code** (CLI/`shopify.app.toml`) rather than a documented
   checklist, so a second store provisions without hand-clicking.
5. **Resolve the scene background properly** as a theme-level element sections opt into,
   which would restore the cross-section colour transitions without the coupling.
6. **The remaining seven sections**, reusing the card and icon snippets already built.
