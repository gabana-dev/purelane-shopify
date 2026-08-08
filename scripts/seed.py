"""
Purelane dev-store seeder.

Populates the store in one pass so it is reproducible from scratch rather than
hand-clicked: metafield definitions, the review metaobject definition and entries,
eight products (including the three edge cases the brief requires), three combo
products, a Bestsellers collection, and Online Store publication.

Not part of the deliverable — this is scaffolding. Delete the custom app afterwards.

Usage:  python3 seed.py shpat_xxx
"""

import json
import subprocess
import sys
import time

STORE = "purelane-assignment-5nfz1uad"
API = "2025-01"
RAW = "https://raw.githubusercontent.com/gabana-dev/purelane-shopify/main/seed-images/png"


def gql(token, query, variables=None):
    """POST a GraphQL request via curl (the system Python's trust store rejects Shopify's chain)."""
    payload = json.dumps({"query": query, "variables": variables or {}})
    out = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         f"https://{STORE}.myshopify.com/admin/api/{API}/graphql.json",
         "-H", f"X-Shopify-Access-Token: {token}",
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True, check=True,
    )
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"Non-JSON response: {out.stdout[:400]}")
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {json.dumps(data['errors'])[:600]}")
    return data["data"]


# --------------------------------------------------------------------------- definitions

# Custom definitions we own.
METAFIELDS = [
    ("Card badge", "custom", "badge", "single_line_text_field"),
    ("Combo items", "custom", "combo_items", "list.product_reference"),
    ("Combo blurb", "custom", "combo_blurb", "multi_line_text_field"),
]

# reviews.rating and reviews.rating_count are RESERVED by Shopify for its standard
# definitions -- creating them fails with RESERVED_NAMESPACE_KEY. They must be enabled
# instead. That reservation is the whole reason we use these keys: they are the ones
# review apps write to.
STANDARD = [("reviews", "rating"), ("reviews", "rating_count")]

STD_ENABLE = """
mutation($ns: String!, $k: String!) {
  standardMetafieldDefinitionEnable(ownerType: PRODUCT, namespace: $ns, key: $k, pin: true) {
    createdDefinition { id namespace key }
    userErrors { field message code }
  }
}"""

DEF_CREATE = """
mutation($d: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $d) {
    createdDefinition { id key namespace }
    userErrors { field message code }
  }
}"""

MO_DEF_CREATE = """
mutation($d: MetaobjectDefinitionCreateInput!) {
  metaobjectDefinitionCreate(definition: $d) {
    metaobjectDefinition { id type }
    userErrors { field message code }
  }
}"""

MO_CREATE = """
mutation($m: MetaobjectCreateInput!) {
  metaobjectCreate(metaobject: $m) {
    metaobject { id handle }
    userErrors { field message code }
  }
}"""

PRODUCT_SET = """
mutation($input: ProductSetInput!) {
  productSet(synchronous: true, input: $input) {
    product { id title handle variants(first: 1) { nodes { id } } }
    userErrors { field message }
  }
}"""

VARIANTS_UPDATE = """
mutation($pid: ID!, $vars: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $pid, variants: $vars) {
    productVariants { id availableForSale }
    userErrors { field message }
  }
}"""

PUBLICATIONS = """
{ publications(first: 10) { nodes { id name } } }
"""

PUBLISH = """
mutation($id: ID!, $pubs: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $pubs) { userErrors { field message } }
}"""

COLLECTION_CREATE = """
mutation($input: CollectionInput!) {
  collectionCreate(input: $input) {
    collection { id title handle }
    userErrors { field message }
  }
}"""

MEDIA_CREATE = """
mutation($id: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $id, media: $media) {
    media { alt status }
    mediaUserErrors { field message }
  }
}"""

METAFIELDS_SET = """
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) { userErrors { field message } }
}"""


# --------------------------------------------------------------------------- seed data
# price / compare are in store currency units (INR). The three edge cases the brief
# names are marked; they are the point of the seed, not filler.

PRODUCTS = [
    dict(title="Tap cleaner & limescale remover", price="200", compare="299",
         img="p-tap", badge="Best seller", rating="4.8", count=237),
    dict(title="Kitchen cleaner, foaming", price="200", compare="299",
         img="p-kitchen", badge="Best seller", rating="4.8", count=254),
    dict(title="Copper, bronze & brass cleaner", price="200", compare="299",
         img="p-metal", badge="Top rated", rating="4.8", count=231),
    dict(title="Washing machine cleaner & descaler", price="200", compare="299",
         img="p-wm", badge="New", rating="4.8", count=183),
    dict(title="Organic dishwash liquid gel", price="249", compare="349",
         img="p-dish", badge="", rating="4.7", count=402),
    # EDGE CASE 1 — sold out
    dict(title="Liquid handwash, aloe & neem", price="179", compare="249",
         img="p-handwash", badge="", rating="4.9", count=118, sold_out=True),
    # EDGE CASE 2 — no image
    dict(title="Floor cleaner concentrate", price="299", compare="399",
         img=None, badge="", rating="4.6", count=95),
    # EDGE CASE 3 — very long title (90+ chars)
    dict(title="Plant-powered laundry detergent concentrate for sensitive skin, "
               "tough stains and everyday family washing",
         price="349", compare="499", img="p-laundry", badge="Best seller",
         rating="4.8", count=512),
]

COMBOS = [
    # The hero's middle rung. The prototype's bundle ladder is 1 bottle at 200/299,
    # "Any 2 products" at 349/598 (save 249) and "Any 3 products" at 499/897 (save 398).
    # Without a product at 349/598 the hero tier had to borrow the Laundry care set at
    # 599 — which made two products cost more than three and inverted the whole ladder.
    # It is seeded as a real product so the hero price still comes from platform data.
    dict(title="Any 2 products", price="349", compare="598", img="p-combo2",
         blurb="Pick any two Purelane products at one flat price.",
         items=[0, 1]),
    dict(title="Kitchen essentials", price="499", compare="897", img="p-combo2",
         blurb="Includes: Foaming Kitchen Cleaner, Dishwash Gel & Tap Cleaner. "
               "Everything for a sparkling kitchen, no need to pick separately.",
         items=[1, 4, 0]),
    dict(title="Laundry care set", price="599", compare="998", img="p-laundry",
         blurb="Includes: Laundry Detergent & Liquid Handwash. Gentle on skin, "
               "tough on everyday stains.",
         items=[7, 5]),
    dict(title="Whole home box", price="999", compare="1796", img="p-combo2",
         blurb="Includes: Tap Cleaner, Kitchen Cleaner, Dishwash Gel & Floor Cleaner. "
               "One box for every room.",
         items=[0, 1, 4, 6]),
]

REVIEWS = [
    dict(rating=5, title="Works like a charm", author="Anita", context="Laundry detergent",
         body="Finally an eco option that cleans as well as the chemical detergent I used "
              "for years, and it smells better."),
    dict(rating=5, title="Best dishwash ever", author="Priya", context="Dishwash gel",
         body="Our old dishwash left my help with dry, cracked skin. That stopped "
              "completely after we switched."),
    dict(rating=5, title="Great product, great packaging", author="Sunita", context="Liquid handwash",
         body="Very soft on hands with a lovely fragrance, and it feels good to be using "
              "far less plastic."),
    dict(rating=5, title="Dog friendly", author="Rahul", context="Floor cleaner",
         body="No harsh fumes, so I can mop with the dog in the room. That alone was "
              "worth the switch."),
    dict(rating=4, title="Solid everyday cleaner", author="Meera", context="Kitchen cleaner",
         body="Cuts grease on the hob without the eye-watering smell. Takes one extra "
              "wipe on baked-on stains."),
]


def main(token):
    log = lambda m: print(m, flush=True)

    # 1. metafield definitions -------------------------------------------------
    log("\n== metafield definitions ==")
    for name, ns, key, typ in METAFIELDS:
        d = gql(token, DEF_CREATE, {"d": {
            "name": name, "namespace": ns, "key": key, "type": typ,
            "ownerType": "PRODUCT",
        }})["metafieldDefinitionCreate"]
        errs = d["userErrors"]
        if errs and errs[0].get("code") == "TAKEN":
            log(f"  = {ns}.{key} already exists")
        elif errs:
            log(f"  ! {ns}.{key}: {errs}")
        else:
            log(f"  + {ns}.{key}")

    log("\n== standard review definitions ==")
    for ns, k in STANDARD:
        d = gql(token, STD_ENABLE, {"ns": ns, "k": k})["standardMetafieldDefinitionEnable"]
        log(f"  {'+ ' + ns + '.' + k if d['createdDefinition'] else '= ' + ns + '.' + k + ' already enabled'}")

    # 2. review metaobject definition ------------------------------------------
    log("\n== metaobject definition: review ==")
    mo = gql(token, MO_DEF_CREATE, {"d": {
        "name": "Review", "type": "review",
        "access": {"storefront": "PUBLIC_READ"},
        "fieldDefinitions": [
            {"key": "rating", "name": "Rating", "type": "number_integer"},
            {"key": "title", "name": "Title", "type": "single_line_text_field"},
            {"key": "body", "name": "Body", "type": "multi_line_text_field"},
            {"key": "author", "name": "Author", "type": "single_line_text_field"},
            {"key": "context", "name": "Context", "type": "single_line_text_field"},
        ],
    }})["metaobjectDefinitionCreate"]
    log(f"  {'+ created' if mo['metaobjectDefinition'] else mo['userErrors']}")

    # 3. review entries ---------------------------------------------------------
    log("\n== reviews ==")
    for r in REVIEWS:
        res = gql(token, MO_CREATE, {"m": {
            "type": "review",
            "fields": [{"key": k, "value": str(v)} for k, v in r.items()],
        }})["metaobjectCreate"]
        log(f"  {'+ ' + r['title'] if res['metaobject'] else res['userErrors']}")

    # 4. products ---------------------------------------------------------------
    log("\n== products ==")
    ids = []
    variant_ids = {}
    for p in PRODUCTS + COMBOS:
        is_combo = "items" in p
        variant = {
            "price": p["price"],
            "compareAtPrice": p["compare"],
            "inventoryItem": {"tracked": True},
            "inventoryPolicy": "DENY",
            "optionValues": [{"optionName": "Title", "name": "Default Title"}],
        }
        res = gql(token, PRODUCT_SET, {"input": {
            "title": p["title"],
            "status": "ACTIVE",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [variant],
        }})["productSet"]
        if res["userErrors"]:
            log(f"  ! {p['title'][:40]}: {res['userErrors']}")
            continue
        pid = res["product"]["id"]
        ids.append((pid, p))
        variant_ids[pid] = res["product"]["variants"]["nodes"][0]["id"]
        log(f"  + {p['title'][:52]}")

        if p.get("img"):
            gql(token, MEDIA_CREATE, {"id": pid, "media": [{
                "originalSource": f"{RAW}/{p['img']}.png",
                "mediaContentType": "IMAGE",
                "alt": p["title"],
            }]})

        mf = []
        if not is_combo:
            mf.append({"ownerId": pid, "namespace": "reviews", "key": "rating",
                       "type": "rating",
                       "value": json.dumps({"value": p["rating"], "scale_min": "1.0",
                                            "scale_max": "5.0"})})
            mf.append({"ownerId": pid, "namespace": "reviews", "key": "rating_count",
                       "type": "number_integer", "value": str(p["count"])})
            if p.get("badge"):
                mf.append({"ownerId": pid, "namespace": "custom", "key": "badge",
                           "type": "single_line_text_field", "value": p["badge"]})
        else:
            mf.append({"ownerId": pid, "namespace": "custom", "key": "combo_blurb",
                       "type": "multi_line_text_field", "value": p["blurb"]})
        if mf:
            gql(token, METAFIELDS_SET, {"mf": mf})

    # 5. combo item references (needs product ids, so it runs after creation) ----
    log("\n== combo contents ==")
    product_ids = [i for i, p in ids if "items" not in p]
    for pid, p in ids:
        if "items" not in p:
            continue
        refs = [product_ids[i] for i in p["items"] if i < len(product_ids)]
        gql(token, METAFIELDS_SET, {"mf": [{
            "ownerId": pid, "namespace": "custom", "key": "combo_items",
            "type": "list.product_reference", "value": json.dumps(refs),
        }]})
        log(f"  + {p['title']} -> {len(refs)} items")

    # 6. collection --------------------------------------------------------------
    log("\n== collection ==")
    col = gql(token, COLLECTION_CREATE, {"input": {
        "title": "Bestsellers",
        "products": [i for i, p in ids if "items" not in p],
    }})["collectionCreate"]
    log(f"  {'+ Bestsellers' if col['collection'] else col['userErrors']}")

    # 7. publish everything to the Online Store ---------------------------------
    log("\n== publish ==")
    pubs = gql(token, PUBLICATIONS)["publications"]["nodes"]
    online = [p for p in pubs if "Online Store" in p["name"]]
    if not online:
        log("  ! no Online Store publication found")
    else:
        target = [{"publicationId": online[0]["id"]}]
        for pid, _ in ids:
            gql(token, PUBLISH, {"id": pid, "pubs": target})
        if col["collection"]:
            gql(token, PUBLISH, {"id": col["collection"]["id"], "pubs": target})
        log(f"  + published {len(ids)} products + collection")

    # 8. availability ------------------------------------------------------------
    # productSet turns on inventory tracking with zero stock, which makes EVERY product
    # read as sold out. Untrack all of them except the one product that is deliberately
    # the sold-out edge case.
    log("\n== availability ==")
    for pid, p in ids:
        if p.get("sold_out"):
            log(f"  = kept sold out: {p['title'][:44]}")
            continue
        gql(token, VARIANTS_UPDATE, {"pid": pid, "vars": [
            {"id": variant_ids[pid], "inventoryItem": {"tracked": False}}
        ]})
    log(f"  + {len(ids) - 1} products available")

    log("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python3 seed.py shpat_...")
    main(sys.argv[1])
