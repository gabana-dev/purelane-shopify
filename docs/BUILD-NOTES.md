# Build notes

What I'd flag about the original file, what I changed and why, and what I'd do with more
time. Written to be read in five minutes.

---

## What I'd flag about the prototype

I read the file before writing any code. Six things would have caused problems in
production, and one thing was done well.

**1. It defines `:root` twice, and the second block wins.** The first token block is a dark
palette (`--ink:#17102b`, light text). A second `:root` further down overrides it with a
light palette (`--ink:#f4f0fb`, `--paper:#241a3d`). The page therefore renders *light*.
Anyone porting the tokens from the top of the file ships the wrong colour scheme across
every section at once. Both blocks are merged in cascade order in `assets/purelane.css`.

**2. Duplicate DOM ids — the markup is invalid.** `cg`, `wf` and `wf2` each appear twice,
and the SVG gradient ids (`gTAPl`, `gKITb`, …) repeat every time a card is duplicated.
Duplicate gradient ids mean a card's fill can resolve to a different card's gradient. Ids
are now scoped per section.

**3. No real images anywhere.** Zero `<img>` tags. All 68 product visuals are either inline
SVG or CSS backgrounds on `<span role="img">`. That is fine for a prototype and impossible
for a store: product images have to come from Shopify. Replaced with real `<img>` carrying
`srcset`, `sizes`, `width`/`height`, `loading` and `decoding`.

**4. The breakpoint logic is incoherent.** 30 media queries across 12 distinct widths,
mixing desktop-first `max-width` with mobile-first `min-width` — including `760px` used in
both directions. Normalised to one mobile-first ladder (640 / 768 / 1024 / 1180) with no
change to rendered output.

**5. Add to cart is decorative.** `<button class="btn">Add to cart</button>` sits outside
any form. It looks like commerce and does nothing. Now a real product form posting to
`/cart/add`, which also means it works with Dawn's cart drawer and without JavaScript.

**6. All behaviour is bound once, globally, at load.** One `querySelectorAll` pass wires
every animation on the page. In Shopify's theme editor this is fatal — see below.

**Done well, and kept:** the prototype checks `prefers-reduced-motion` before animating.
That is more than most production themes do. I kept it and extended it to everything I
added.

## What I changed, and why

| Change | Reason |
|---|---|
| One `product-card` snippet for shop / combos / tiers | The brief notes several sections render similar cards. Three copies would drift apart the first time one is edited |
| Ratings, review counts, badges → metafields | No native Shopify field. Using the **standard** `reviews.rating` keys means a real review app populates them on day one |
| Savings and discount % computed from `compare_at_price` | Typed values drift. A merchant running a sale should not have to remember to edit the homepage |
| Behaviour rewritten as per-section controllers with teardown | See "theme editor" below |
| 62 KB of CSS → 24 KB, scoped under `.pl` | We render five of twelve sections; shipping the rest is dead weight. Scoping stops collisions with Dawn in both directions |
| Repeated inline SVG → one icon snippet | The same 24×24 leaf appeared 55 times |
| Per-card avatar SVG → a single initial | Same visual weight, a fraction of the markup |
| Fixed aspect ratios on every media box | The prototype's images had no intrinsic dimensions, which is a CLS problem the moment images are real |

### The theme editor, specifically

This is the requirement I'd expect most submissions to miss, so it's worth being explicit.

Shopify's editor re-renders **one section** over AJAX when a merchant edits it. Any handler
bound at page load is then pointing at DOM nodes that no longer exist: reveals stop firing,
the hero freezes, and — worse — the old section's `setInterval` keeps running forever. Edit
a section ten times and you have ten timers mutating detached nodes.

`assets/purelane.js` treats every behaviour as a controller that owns one section element
and knows how to destroy itself, keyed by section id:

- `shopify:section:load` → initialise **that section only**
- `shopify:section:unload` → disconnect observers, clear intervals, unbind listeners
- `shopify:section:select` / `deselect` → pause autoplay while the merchant is editing, so
  the thing they are working on holds still

Re-initialising always tears down first, so a re-render cannot stack a second observer.

### Deliberate omission: the scene system

The prototype has a page-level, scroll-driven background stage (`data-scene="1..4"`,
`.water`, `.wl-*`) that all sections drive. **I did not port it.** It requires every section
to know its position in a global sequence and to mutate a shared element outside itself —
which breaks section independence in the theme editor. Reorder two sections and the
background sequence is wrong; delete one and it stops advancing.

Porting it properly means a theme-level background block that sections signal into, which
is a larger design decision than this assignment should make unilaterally. I left it out
and said so rather than half-implementing it.

## Gaps — being straight about them

- **The dev store was not live when I wrote this**, so the sections have not yet been
  visually diffed against the prototype on a real storefront. The build follows the
  measured tokens and ported CSS exactly, but "pixel-accurate" is a claim I can only make
  after running the verification checklist in `SETUP.md` against the live store.
- Only the five required sections were built. The other seven in the file are untouched.
- Combos and bundles render from blocks a merchant configures; I have not built an
  automatic "cheapest matching combo" resolver, which a real store would eventually want.

## What I'd do with more time

1. **Run the full verification checklist** against the live store at 375/768/1024/1440 and
   diff against the prototype screenshot by screenshot.
2. **Lighthouse pass on a throttled mobile profile**, and move the two Google fonts to
   self-hosted `woff2` with `font-display: swap` — currently the largest remaining
   render-blocking request.
3. **A theme-check / linting step in CI** so section schema errors fail before deploy.
4. **Resolve the scene background properly** as a theme-level element sections opt into.
5. **A snapshot test for the card** across its five states (normal, sold out, no image,
   long title, no compare-at) so a future edit cannot silently regress an edge case.
6. **Metafield definitions as code** (`shopify.app.toml` / CLI) rather than a documented
   checklist, so a second store can be provisioned without hand-clicking.
