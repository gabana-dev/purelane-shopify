# AI workflow notes

What I delegated, where it failed me, and what I'd systematise if I had to do twenty more
of these. This describes how this specific build was actually run, not a general opinion
about AI.

---

## The operating rule

**The agent does volume. I do judgment.** Concretely, I delegate work where the answer is
verifiable — extraction, transformation, boilerplate, repetition — and keep work where the
answer is a decision: what the data model should be, what to cut, what "done" means.

The failure mode I design against is an agent producing something plausible that I cannot
check. So before delegating I ask: *how will I verify this in under a minute?* If I have no
answer, I don't delegate it.

## What I delegated on this build

**Analysis of the prototype before writing any code.** Rather than reading 151 KB by eye, I
had the agent inventory it: count `<img>` tags (zero), find duplicate DOM ids (`cg`, `wf`,
`wf2`), enumerate every media query and breakpoint (30 across 12 widths, `max-` and `min-`
mixed), count repeated inline SVGs (the same leaf 55 times). Each answer is a number I can
spot-check in seconds, which is exactly the shape of task to hand over.

**CSS extraction.** Porting 62 KB of CSS by hand is error-prone and slow. I wrote a keep-list
of the classes the five sections actually use and had the agent parse the stylesheet,
including `@media` blocks, keeping only matching rules and scoping every selector under
`.pl`. Result: 502 rules → 221, 62 KB → 24 KB. Verifiable by diffing the dropped selector
list against the sections I'm not building.

**Asset extraction.** The 14 product images were base64 data-URIs inside CSS custom
properties. Decoded to SVG files for store seeding — a mechanical task with an obvious
correctness check (the files open and look like bottles).

**Boilerplate.** Schema JSON, repeated block definitions, the setup checklist.

## What I did NOT delegate

- **The data model.** Whether ratings belong in `custom.rating` or Shopify's standard
  `reviews.rating` is a judgment call with real consequences: the standard keys mean the
  merchant's review app populates the cards on day one, a custom key means double entry
  forever. An agent optimising for "make it work" picks the custom field.
- **What to cut.** Not porting the scene system is the most consequential decision in this
  build, and it comes from knowing how the theme editor re-renders sections — context an
  agent does not have unless I supply it.
- **The theme-editor lifecycle design.** See below; this is where agents were actively wrong.
- **Which defects to fix versus preserve.** The brief invites fixing production defects but
  makes redesigning an automatic no. That line is judgment, and getting it wrong fails the
  assignment either way.

## Where the agents failed me

**1. Shopify section lifecycle is the big one.** Ask a general coding agent for a Shopify
carousel and you reliably get `document.addEventListener('DOMContentLoaded', ...)` with a
global `querySelectorAll`. It works on the storefront and dies in the theme editor. The
training data is full of jQuery-era page-level scripts, and nothing in the prompt tells the
model the DOM will be replaced under it. **Fix:** I don't ask for "a carousel" — I ask for a
controller with an explicit teardown function, and I state the lifecycle events it must
support. The constraint has to be in the prompt because it will not come from the model.

**2. It invents Liquid filters that don't exist.** Confidently. `ternary`, aggressive
`where` chaining, metafield access patterns that changed between API versions. **Fix:**
treat any unfamiliar filter as unverified until checked against the Shopify docs, and
prefer the boring construct I already know renders.

**3. It hardcodes what it should parameterise.** Given a design showing "₹200 · 33% off",
the default output types `33% off` into the template. It matches the screenshot, which is
what it was asked to do, and it fails the actual requirement that a merchant can change a
price without a developer. **Fix:** I state the merchant-editability requirement as a
first-class acceptance criterion, not as an afterthought.

**4. It silently drops edge cases.** Card markup comes back handling the happy path; sold
out, missing image and overlong title are absent unless named. **Fix:** edge cases go in the
spec as a table before any code is written — which is why the PRD has one.

**5. It over-engineers when unsupervised.** Left alone it will produce a configuration
system, a utility layer and an abstraction for one caller. **Fix:** an explicit instruction
that the simplest production-quality solution wins, and I delete anything with one call site.

## What I'd systematise over twenty of these

The point of this role is that project 20 ships in a fraction of the time project 2 took.
What I'd build, in the order I'd build it:

1. **A prototype audit script.** Every one of these jobs starts with an unfamiliar HTML
   file. The inventory I ran here — image tags, duplicate ids, breakpoint census, repeated
   SVGs, token blocks, inline styles, `!important` count — is the same every time. Run it
   first, and the build notes half write themselves.

2. **A PRD template with the non-obvious requirements pre-loaded.** Theme-editor survival,
   the edge-case table, merchant-editability, the metafield decision. These are exactly what
   agents omit, so the template carries them and every project inherits them.

3. **A card-snippet library.** Product card, review card, tier card. Most D2C homepages are
   permutations of the same four card shapes; the parameterised versions should be assets,
   not rewritten per client.

4. **A lifecycle-safe JS scaffold.** The controller-with-teardown pattern in
   `assets/purelane.js` is client-agnostic. It should be a starting file, not a thing I
   re-derive and an agent re-breaks.

5. **A prompt scaffold that ships the constraints.** Every delegation carries the same
   preamble: this is Shopify Dawn, sections re-render in the editor, nothing hardcoded that
   a marketer would change, no new abstractions for one caller, handle these edge cases.
   Most agent failures above are missing-context failures, and context is reusable.

6. **A pre-deploy checklist as a real gate.** The one in `SETUP.md`, run every time — the
   ten-consecutive-edits check for stacked timers especially, because it is invisible until
   a client reports "the site gets slow when I edit it".

## The honest summary

AI made this build maybe three times faster, almost entirely in the mechanical middle:
reading a large unfamiliar file, transforming CSS, extracting assets, generating schema.

It did not make a single one of the decisions the assignment is actually grading — the data
model, the cut, the fix-versus-preserve line, the lifecycle design. It would have got the
lifecycle actively wrong, and it would have hardcoded the prices.

That is the split I'd expect to hold at twenty projects: agents compress the volume,
judgment stays with the engineer, and the leverage comes from systematising the context so
the agent's failure modes get designed out rather than caught by hand every time.
