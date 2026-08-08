#!/usr/bin/env python3
"""
Create the hero's "Any 2 products" bundle on a store that was already seeded.

WHY THIS EXISTS
The prototype's hero is a bundle ladder: 1 bottle at 200/299, any 2 at 349/598 (save
249), any 3 at 499/897 (save 398). The first seed run had no product at 349/598, so the
middle rung borrowed the Laundry care set at 599 — which made two products cost more than
three and inverted the ladder.

`seed.py` now creates this product, but re-running the whole seeder against a live store
would duplicate everything. This adds just the missing product, and it is idempotent:
run it twice and the second run reports the product already exists and changes nothing.

    python3 scripts/add_hero_bundle.py <admin-api-token>

Then point the hero's middle slide at it in the theme editor:
Customize -> Purelane hero -> the "Any 2 products" slide -> Price product.
That is a merchant-editable setting, so no code change is needed.
"""
import json
import subprocess
import sys

STORE = "purelane-assignment-5nfz1uad"
API = "2025-01"
RAW = "https://raw.githubusercontent.com/gabana-dev/purelane-shopify/main/seed-images/png"

TITLE = "Any 2 products"
PRICE = "349"
COMPARE = "598"
BLURB = "Pick any two Purelane products at one flat price."
# The two bottles the prototype's 2-up slide shows.
ITEM_HANDLES = ["tap-cleaner-limescale-remover", "kitchen-cleaner-foaming"]


def gql(token, query, variables=None):
    payload = {"query": query, "variables": variables or {}}
    out = subprocess.run(
        ["curl", "-s",
         f"https://{STORE}.myshopify.com/admin/api/{API}/graphql.json",
         "-H", f"X-Shopify-Access-Token: {token}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True).stdout
    body = json.loads(out)
    if "errors" in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]


FIND = """query($q:String!){ products(first:1, query:$q){ nodes{ id title } } }"""

BY_HANDLE = """query($h:String!){ productByHandle(handle:$h){ id } }"""

CREATE = """
mutation($input: ProductSetInput!) {
  productSet(synchronous: true, input: $input) {
    product { id handle variants(first:1){ nodes{ id } } }
    userErrors { field message }
  }
}"""

MEDIA = """
mutation($id: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $id, media: $media) { mediaUserErrors { message } }
}"""

METAFIELDS = """
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) { userErrors { message } }
}"""

VARIANTS = """
mutation($pid: ID!, $vars: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $pid, variants: $vars) { userErrors { message } }
}"""

PUBLICATIONS = """query{ publications(first:10){ nodes{ id name } } }"""

PUBLISH = """
mutation($id: ID!, $pubs: [PublicationInput!]!) {
  publishablePublish(id: $id, input: $pubs) { userErrors { message } }
}"""


def main(token):
    existing = gql(token, FIND, {"q": f'title:"{TITLE}"'})["products"]["nodes"]
    if existing:
        print(f"= already exists: {existing[0]['title']} — nothing to do")
        return

    res = gql(token, CREATE, {"input": {
        "title": TITLE,
        "status": "ACTIVE",
        "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
        "variants": [{
            "price": PRICE,
            "compareAtPrice": COMPARE,
            "inventoryItem": {"tracked": True},
            "inventoryPolicy": "DENY",
            "optionValues": [{"optionName": "Title", "name": "Default Title"}],
        }],
    }})["productSet"]
    if res["userErrors"]:
        sys.exit(f"! create failed: {res['userErrors']}")

    pid = res["product"]["id"]
    vid = res["product"]["variants"]["nodes"][0]["id"]
    print(f"+ created {TITLE} at {PRICE}/{COMPARE} (handle: {res['product']['handle']})")

    gql(token, MEDIA, {"id": pid, "media": [{
        "originalSource": f"{RAW}/p-combo2.png",
        "mediaContentType": "IMAGE",
        "alt": TITLE,
    }]})

    item_ids = []
    for h in ITEM_HANDLES:
        node = gql(token, BY_HANDLE, {"h": h})["productByHandle"]
        if node:
            item_ids.append(node["id"])
    mf = [{"ownerId": pid, "namespace": "custom", "key": "combo_blurb",
           "type": "multi_line_text_field", "value": BLURB}]
    if item_ids:
        mf.append({"ownerId": pid, "namespace": "custom", "key": "combo_items",
                   "type": "list.product_reference", "value": json.dumps(item_ids)})
    gql(token, METAFIELDS, {"mf": mf})
    print(f"  + metafields ({len(item_ids)} combo items)")

    # productSet turns inventory tracking ON at zero stock, which reads as sold out on
    # the storefront while the Admin API still reports the variant as sellable. Same trap
    # as step 8 of seed.py.
    gql(token, VARIANTS, {"pid": pid, "vars": [
        {"id": vid, "inventoryItem": {"tracked": False}}
    ]})
    print("  + untracked inventory (otherwise it reads as sold out)")

    pubs = [{"publicationId": p["id"]}
            for p in gql(token, PUBLICATIONS)["publications"]["nodes"]
            if p["name"] in ("Online Store", "Headless")]
    if pubs:
        gql(token, PUBLISH, {"id": pid, "pubs": pubs})
        print(f"  + published to {len(pubs)} channel(s)")

    print("\nDone. Now set it as the hero middle slide's Price product in the theme "
          "editor:\n  Customize -> Purelane hero -> 'Any 2 products' slide -> Price product")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 scripts/add_hero_bundle.py <admin-api-token>")
    main(sys.argv[1])
