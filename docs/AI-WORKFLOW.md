# AI workflow notes

What I delegated, where it failed me, and what I'd systematise if I had to do twenty more
of these. This describes how this specific build was actually run.

---

## The operating rule

**The agent does volume. I do judgment.** I delegate work where the answer is verifiable —
extraction, transformation, boilerplate, repetition — and keep work where the answer is a
decision: what the data model should be, what to cut, what "done" means.

The failure mode I design against is an agent producing something plausible I cannot check.
So before delegating I ask: *how will I verify this in under a minute?* If I have no answer,
I don't delegate it.

## What I delegated on this build

**Analysis of the prototype before writing any code.** Rather than reading 151 KB by eye, I
had it inventory the file: count `<img>` tags (zero), find duplicate DOM ids (`cg`, `wf`,
`wf2`), enumerate every media query and breakpoint (30 across 12 widths, `max-` and `min-`
mixed), count repeated inline SVGs (the same leaf 55 times), and spot that `:root` is
defined twice with the second block winning. Each answer is a number I can spot-check in
seconds — exactly the shape of task to hand over.

**CSS extraction.** Porting 62 KB by hand is slow and error-prone. I wrote a keep-list of
the classes the five sections use and had the parse-and-scope done mechanically, including
`@media` blocks. Result: 502 rules → 221, 62 KB → 32 KB, all scoped under `.pl`.

**Asset work.** Decoding 14 base64 data-URI product images to files; rendering them to PNG
via headless Chrome because Shopify rejects SVG as product media; compositing 2/3/5-bottle
group images for the bundle tiers.

**Store seeding.** A scripted Admin API pass creating metafield definitions, the review
metaobject and entries, 12 products including the three required edge cases, combo
references, the collection and publication — so the store is reproducible from scratch
rather than hand-clicked. That script is in `scripts/seed.py`.

**Boilerplate.** Schema JSON, repeated block definitions, the setup checklist.

## What I did NOT delegate

- **The data model.** Whether ratings live in `custom.rating` or Shopify's standard
  `reviews.rating` is a judgment call with real consequences: standard keys mean the
  merchant's review app populates the cards, a custom key means double entry forever. An
  agent optimising for "make it work" picks the custom field.
- **What to cut.** Not porting the scene system is the most consequential decision in this
  build, and it comes from knowing how the theme editor re-renders sections.
- **The theme-editor lifecycle design.** See below — this is where agents were actively wrong.
- **Which defects to fix versus preserve.** The brief invites fixing production defects but
  makes redesigning an automatic no. That line is judgment, and getting it wrong fails the
  assignment either way.
- **Reading the design's intent.** The hero is a bundle-pricing showcase, not a product
  carousel. Nothing about the markup announces that; you get it by looking at the rendered
  page and asking what it is trying to sell.

## Where the agents failed me

**1. Shopify section lifecycle.** Ask a general coding agent for a Shopify carousel and you
reliably get `DOMContentLoaded` plus a global `querySelectorAll`. It works on the storefront
and dies in the theme editor. The training data is full of page-level scripts, and nothing
in the prompt tells the model the DOM will be replaced under it. **Fix:** don't ask for "a
carousel" — ask for a controller with an explicit teardown, and state the lifecycle events
it must support. That constraint has to be in the prompt; it will not come from the model.

**2. It invents API surface, confidently.** `ternary` is not a Liquid filter; it was used
for the hero's eager/lazy attributes and would have thrown. `.count` is not valid on a
metafield list. `standardMetafieldDefinitionEnable` does not take a `namespaceKey`
argument. **Fix:** treat any unfamiliar filter or mutation as unverified until checked. When
the GraphQL call was rejected I introspected the schema rather than guessing a second time —
guessing twice is how you burn an afternoon.

**3. It hardcodes what it should parameterise.** Given a design showing "₹200 · 33% off",
the default output types `33% off` into the template. It matches the screenshot, which is
what it was asked to do, and it fails the actual requirement that a merchant can change a
price without a developer. **Fix:** state merchant-editability as a first-class acceptance
criterion, not an afterthought.

**4. It silently drops edge cases.** Card markup comes back handling the happy path; sold
out, missing image and overlong title are absent unless named. **Fix:** edge cases go in the
spec as a table before any code is written, which is why the PRD has one.

**5. Mechanical transforms produce plausible, broken output.** Two failures here, and both
are the same shape. Splitting CSS declarations on `;` truncated every `data:image/...;base64`
token and left an unterminated quote, which made browsers discard the whole stylesheet — with
balanced braces and a passing validator. And the extraction keep-list silently dropped
`.ptag` because I hadn't anticipated that class. **Fix:** never trust a transform's own
output. Audit it against the source — I wrote a script comparing every rule in the original
stylesheet against ours, and it found four more dropped rules I hadn't noticed.

**6. Generated API calls have side effects nobody mentions.** The seeding script used
`productSet` to create products. `productSet` turns *on* inventory tracking with a quantity
of zero, so all twelve products came back sellable from the Admin API and read as **sold
out** on the storefront. Nothing in the mutation says it will do that, and the agent that
wrote the call had no reason to know. **Fix:** verify against the surface the customer
actually sees, not the API's own response. The Admin API said everything was fine. Step 8 of
`scripts/seed.py` now untracks every variant except the one product that is deliberately the
sold-out edge case.

**7. A correct component can still be wrong once packaged.** The last bug in this build was
not in any controller — it was that `purelane.js` is included per section and therefore
*executes* six times, giving six independent controller registries that cannot tear each
other down. Every unit was right; the composition was wrong. **Fix:** the check that matters
is behavioural and runs against the assembled page — count observers after one
`shopify:section:load`, don't re-read the module.

**8. It over-engineers when unsupervised.** Left alone it produces a config system, a
utility layer and an abstraction for one caller. **Fix:** an explicit instruction that the
simplest production-quality solution wins, and I delete anything with one call site.

## What I'd systematise over twenty of these

The point of this role is that project 20 ships in a fraction of the time project 2 took.
In the order I'd build it:

1. **A prototype audit script.** Every job starts with an unfamiliar HTML file. The
   inventory I ran here — image tags, duplicate ids, breakpoint census, repeated SVGs,
   duplicate token blocks, inline styles, `!important` count — is the same every time. Run
   it first and the build notes half write themselves.

2. **An extraction *auditor*, not just an extractor.** The single highest-value tool from
   today: after porting CSS, diff every rule in the source against the output and list what
   was dropped. Both of my worst bugs would have been caught in seconds.

3. **A lifecycle-safe JS scaffold.** The controller-with-teardown pattern in
   `assets/purelane.js` is client-agnostic. It should be a starting file, not something I
   re-derive and an agent re-breaks.

4. **A card-snippet library.** Product card, review card, tier card. Most D2C homepages are
   permutations of the same four card shapes.

5. **A store-seeding script per project.** `scripts/seed.py` took 20 minutes and replaced an
   hour of clicking, and it made the store reproducible. Parameterise it and it's reusable.

6. **A prompt scaffold that ships the constraints.** Every delegation carries the same
   preamble: this is Shopify Dawn, sections re-render in the editor, nothing hardcoded that a
   marketer would change, no abstractions for one caller, handle these edge cases. Most
   failures above are missing-context failures, and context is reusable.

7. **A pre-deploy checklist as a real gate** — the one in `SETUP.md`, especially the
   ten-consecutive-edits check for stacked timers, which is invisible until a client reports
   "the site gets slow when I edit it".

## The honest summary

AI made this build perhaps three times faster, almost entirely in the mechanical middle:
reading a large unfamiliar file, transforming CSS, decoding and compositing assets,
generating schema, seeding a store.

It did not make a single decision the assignment is actually grading — the data model, the
cut, the fix-versus-preserve line, the lifecycle design, or reading what the hero was for.
It would have got the lifecycle actively wrong and would have hardcoded the prices.

The sharpest lesson from today is the second one in my list: **the dangerous output is not
the one that errors, it's the one that looks right.** Every bug that cost me real time was
plausible, structurally valid and silently wrong — a CSS transform with balanced braces, a
`productSet` call the Admin API reported as successful, a lifecycle module that was correct
in isolation and duplicated six times by the include that shipped it.

The last one is the sharpest version of it. Reviewing that file again would never have found
the bug, because the bug was not in the file. What found it was asking the assembled page a
question with a countable answer: dispatch one `shopify:section:load`, count the observers,
expect five. The leverage isn't in generating more — it's in knowing which number to count.
