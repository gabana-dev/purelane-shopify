#!/usr/bin/env python3
"""
Bring an already-seeded Purelane store in line with the prototype.

WHY THIS EXISTS
Three things were wrong on the first seed and all three are fixed in `seed.py`, but that
script creates products and cannot be re-run against a live store without duplicating
everything. This repairs a store in place instead.

  1. Every seed image was rendered onto one shared 600x920 canvas regardless of its
     source viewBox, so the art was distorted — worst on the hero bottles (0.322 drawn
     at 0.652) and the combo art (1.125 drawn at 0.652). seed-images/png is now rendered
     per asset; this re-uploads it.
  2. The hero needs the prototype's tall bottle art, which is a different drawing from
     the product-card art. It goes on `custom.hero_image` so the card keeps its own shot.
  3. The combos rail should carry the prototype's five bundles at its prices. Three
     existed under different names and prices; two were missing.

Idempotent: it matches products by title, replaces media only when the media it would
upload is not already there, and creates a combo only when no product of that title
exists. Run it twice and the second run reports no changes.

    python3 scripts/resync.py <admin-api-token>
"""
import json
import subprocess
import sys

STORE = "purelane-assignment-5nfz1uad"
API = "2025-01"
RAW = "https://raw.githubusercontent.com/gabana-dev/purelane-shopify/main/seed-images/png"

# product title -> (card art, hero art or None)
ART = {
    "Tap cleaner & limescale remover": ("p-tap", "p-tbtl"),
    "Kitchen cleaner, foaming": ("p-kitchen", "p-kbtl"),
    "Copper, bronze & brass cleaner": ("p-metal", "p-mbtl"),
    "Washing machine cleaner & descaler": ("p-wm", None),
    "Organic dishwash liquid gel": ("p-dish", None),
    "Liquid handwash, aloe & neem": ("p-handwash", None),
    # "Floor cleaner concentrate" is the no-image edge case — deliberately skipped.
    "Plant-powered laundry detergent concentrate for sensitive skin, tough stains "
    "and everyday family washing": ("p-laundry", None),
}

# Rendered aspect of each asset, used to tell already-correct art from the distorted
# 0.652 everything shipped at on the first pass.
ASPECT = {
    "p-tap": 703 / 1100, "p-kitchen": 703 / 1100, "p-metal": 769 / 1100,
    "p-wm": 676 / 1100, "p-dish": 686 / 1100, "p-handwash": 820 / 1100,
    "p-laundry": 693 / 1100, "p-combo2": 1100 / 978, "p-eraser": 1100 / 834,
}

# The prototype's five combos, in its order, with its prices.
COMBOS = [
    ("Kitchen essentials", "499", "897", "p-combo2",
     "Includes: Foaming Kitchen Cleaner, Dishwash Gel & Tap Cleaner. Everything for a "
     "sparkling kitchen, no need to pick separately."),
    ("Laundry care bundle", "499", "947", "p-laundry",
     "Includes: Laundry Detergent, Fabric Conditioner & Machine Cleaner Powder. Softer, "
     "fresher wash, all in one box."),
    ("Complete home bundle", "799", "1495", "p-combo2",
     "Includes: Kitchen Cleaner, Laundry Detergent, Floor Cleaner, Toilet Cleaner & "
     "Handwash. Our biggest saving."),
    ("Bathroom deep clean", "499", "897", "p-eraser",
     "Includes: Toilet Cleaner, Tap Cleaner & Magic Eraser. A complete bathroom refresh "
     "in one box."),
    ("Hard water solution kit", "349", "598", "p-combo2",
     "Includes: Tap Cleaner & Toilet Cleaner. A quick, focused fix for hard water stains "
     "across the home."),
]

# Renames from the first seed, so existing products are updated rather than duplicated.
RENAMES = {"Laundry care set": "Laundry care bundle", "Whole home box": "Complete home bundle"}


def gql(token, query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}})
    out = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         f"https://{STORE}.myshopify.com/admin/api/{API}/graphql.json",
         "-H", f"X-Shopify-Access-Token: {token}",
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {json.dumps(data['errors'])[:500]}")
    return data["data"]


ALL_PRODUCTS = """
{ products(first: 60) {
    nodes { id title handle
      media(first: 10) { nodes { id alt ... on MediaImage { image { url width height } } } }
      variants(first: 1) { nodes { id price compareAtPrice } } } } }"""

DELETE_MEDIA = """
mutation($pid: ID!, $ids: [ID!]!) {
  productDeleteMedia(productId: $pid, mediaIds: $ids) { mediaUserErrors { message } } }"""

CREATE_MEDIA = """
mutation($id: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $id, media: $media) { mediaUserErrors { message } } }"""

FILE_CREATE = """
mutation($files: [FileCreateInput!]!) {
  fileCreate(files: $files) { files { id fileStatus } userErrors { message } } }"""

METAFIELDS = """
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) { userErrors { message } } }"""

DEF_CREATE = """
mutation($d: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $d) { userErrors { message code } } }"""

PRODUCT_SET = """
mutation($input: ProductSetInput!) {
  productSet(synchronous: true, input: $input) {
    product { id handle variants(first:1){ nodes{ id } } }
    userErrors { message } } }"""

UPDATE = """
mutation($input: ProductInput!) {
  productUpdate(input: $input) { product { id } userErrors { message } } }"""

VARIANTS = """
mutation($pid: ID!, $vars: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $pid, variants: $vars) { userErrors { message } } }"""

PUBLICATIONS = "{ publications(first: 10) { nodes { id name } } }"

PUBLISH = """
mutation($id: ID!, $pubs: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $pubs) { userErrors { message } } }"""


def log(m):
    print(m, flush=True)


def main(token):
    changed = 0

    log("== hero_image definition ==")
    res = gql(token, DEF_CREATE, {"d": {
        "name": "Hero image", "namespace": "custom", "key": "hero_image",
        "type": "file_reference", "ownerType": "PRODUCT", "pin": True,
    }})["metafieldDefinitionCreate"]
    errs = res["userErrors"]
    log("  = already defined" if errs and errs[0].get("code") == "TAKEN"
        else f"  + created" if not errs else f"  ! {errs}")

    products = gql(token, ALL_PRODUCTS)["products"]["nodes"]
    by_title = {p["title"]: p for p in products}

    log("\n== renames ==")
    for old, new in RENAMES.items():
        if old in by_title and new not in by_title:
            gql(token, UPDATE, {"input": {"id": by_title[old]["id"], "title": new}})
            by_title[new] = by_title.pop(old)
            by_title[new]["title"] = new
            log(f"  + {old} -> {new}")
            changed += 1
    if not changed:
        log("  = nothing to rename")

    log("\n== product art (re-rendered at true aspect) ==")
    for title, (card, hero) in ART.items():
        p = by_title.get(title)
        if not p:
            log(f"  ? not found: {title[:44]}")
            continue

        want_aspect = ASPECT[card]
        have = [m for m in p["media"]["nodes"] if m.get("image")]
        # Idempotency reads the image's own shape rather than a marker written into alt
        # text: alt belongs to the customer using a screen reader, not to this script.
        current_ok = any(
            m["image"].get("height") and
            abs(m["image"]["width"] / m["image"]["height"] - want_aspect) < 0.02
            for m in have)
        if current_ok:
            log(f"  = current: {title[:44]}")
        else:
            # Upload first, delete second. Reversed, a failed upload leaves the product
            # with no image at all on a live storefront.
            res = gql(token, CREATE_MEDIA, {"id": p["id"], "media": [{
                "originalSource": f"{RAW}/{card}.png",
                "mediaContentType": "IMAGE", "alt": title}]})["productCreateMedia"]
            if res["mediaUserErrors"]:
                log(f"  ! {title[:40]}: {res['mediaUserErrors']} — old art left in place")
                continue
            if have:
                gql(token, DELETE_MEDIA, {"pid": p["id"], "ids": [m["id"] for m in have]})
            log(f"  + card art: {title[:44]}")
            changed += 1

        if hero:
            f = gql(token, FILE_CREATE, {"files": [{
                "originalSource": f"{RAW}/{hero}.png",
                "contentType": "IMAGE", "alt": f"{title} hero"}]})["fileCreate"]
            if f["userErrors"]:
                log(f"    ! hero art: {f['userErrors']}")
            else:
                gql(token, METAFIELDS, {"mf": [{
                    "ownerId": p["id"], "namespace": "custom", "key": "hero_image",
                    "type": "file_reference", "value": f["files"][0]["id"]}]})
                log(f"    + hero art: {hero}")
                changed += 1

    log("\n== combos ==")
    pubs = [{"publicationId": x["id"]}
            for x in gql(token, PUBLICATIONS)["publications"]["nodes"]
            if x["name"] in ("Online Store", "Headless")]
    for title, price, compare, img, blurb in COMBOS:
        p = by_title.get(title)
        if p:
            v = p["variants"]["nodes"][0]
            if v["price"] != price or (v["compareAtPrice"] or "") != compare:
                gql(token, VARIANTS, {"pid": p["id"], "vars": [
                    {"id": v["id"], "price": price, "compareAtPrice": compare}]})
                log(f"  + repriced {title} -> {price}/{compare}")
                changed += 1
            else:
                log(f"  = current: {title}")
            continue
        res = gql(token, PRODUCT_SET, {"input": {
            "title": title, "status": "ACTIVE",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [{"price": price, "compareAtPrice": compare,
                          "inventoryItem": {"tracked": True}, "inventoryPolicy": "DENY",
                          "optionValues": [{"optionName": "Title", "name": "Default Title"}]}],
        }})["productSet"]
        if res["userErrors"]:
            log(f"  ! {title}: {res['userErrors']}")
            continue
        pid = res["product"]["id"]
        vid = res["product"]["variants"]["nodes"][0]["id"]
        gql(token, CREATE_MEDIA, {"id": pid, "media": [{
            "originalSource": f"{RAW}/{img}.png", "mediaContentType": "IMAGE",
            "alt": title}]})
        gql(token, METAFIELDS, {"mf": [{
            "ownerId": pid, "namespace": "custom", "key": "combo_blurb",
            "type": "multi_line_text_field", "value": blurb}]})
        # productSet enables inventory tracking at zero, which reads as sold out.
        gql(token, VARIANTS, {"pid": pid, "vars": [
            {"id": vid, "inventoryItem": {"tracked": False}}]})
        if pubs:
            gql(token, PUBLISH, {"id": pid, "pubs": pubs})
        log(f"  + created {title} at {price}/{compare}")
        changed += 1

    log(f"\nDone — {changed} change(s).")
    if changed:
        log("\nIn the theme editor, point the combos rail at the five bundles and the "
            "hero's middle slide at 'Hard water solution kit' (349/598).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 scripts/resync.py <admin-api-token>")
    main(sys.argv[1])
