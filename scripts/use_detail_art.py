#!/usr/bin/env python3
"""
Swap four products onto the prototype's detailed card art.

The bestsellers grid in the prototype renders eight cards from four products: four with
the simple CSS-background bottle (`--p-tap` and friends) and four with a detailed inline
SVG — a white spray bottle with a printed PURELANE label, product name and 500 ML. The
detailed drawing is the finished art; next to it the simple one reads as placeholder.

Only these four have a detailed version in the file, so the other four products keep the
art they have. Hero art is untouched: the hero reads `custom.hero_image` and only falls
back to the featured image, so replacing the card shot cannot disturb the bundle stage.

Idempotent — Shopify keeps the filename in the CDN URL, so a product already on
`*-detail.png` is skipped.

    python3 scripts/use_detail_art.py <admin-api-token>
"""
import json
import subprocess
import sys

STORE = "purelane-assignment-5nfz1uad"
API = "2025-01"
RAW = "https://raw.githubusercontent.com/gabana-dev/purelane-shopify/main/seed-images/png"

DETAIL = {
    "Tap cleaner & limescale remover": "p-tap-detail",
    "Kitchen cleaner, foaming": "p-kitchen-detail",
    "Copper, bronze & brass cleaner": "p-metal-detail",
    "Washing machine cleaner & descaler": "p-wm-detail",
}

PRODUCTS = """
{ products(first: 60) {
    nodes { id title
      media(first: 10) { nodes { id ... on MediaImage { image { url } } } } } } }"""

CREATE_MEDIA = """
mutation($id: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $id, media: $media) { mediaUserErrors { message } } }"""

DELETE_MEDIA = """
mutation($pid: ID!, $ids: [ID!]!) {
  productDeleteMedia(productId: $pid, mediaIds: $ids) { mediaUserErrors { message } } }"""


def gql(token, query, variables=None):
    out = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         f"https://{STORE}.myshopify.com/admin/api/{API}/graphql.json",
         "-H", f"X-Shopify-Access-Token: {token}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"query": query, "variables": variables or {}})],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {json.dumps(data['errors'])[:400]}")
    return data["data"]


def main(token):
    products = {p["title"]: p for p in gql(token, PRODUCTS)["products"]["nodes"]}
    changed = 0
    for title, asset in DETAIL.items():
        p = products.get(title)
        if not p:
            print(f"  ? not found: {title[:44]}")
            continue
        have = [m for m in p["media"]["nodes"] if m.get("image")]
        if any(asset in (m["image"]["url"] or "") for m in have):
            print(f"  = already detailed: {title[:44]}")
            continue
        # Upload before deleting, so a failure leaves the old image in place rather than
        # leaving a live product with no image at all.
        res = gql(token, CREATE_MEDIA, {"id": p["id"], "media": [{
            "originalSource": f"{RAW}/{asset}.png",
            "mediaContentType": "IMAGE", "alt": title}]})["productCreateMedia"]
        if res["mediaUserErrors"]:
            print(f"  ! {title[:40]}: {res['mediaUserErrors']}")
            continue
        if have:
            gql(token, DELETE_MEDIA, {"pid": p["id"], "ids": [m["id"] for m in have]})
        print(f"  + {title[:44]} -> {asset}")
        changed += 1
    print(f"\nDone — {changed} change(s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 scripts/use_detail_art.py <admin-api-token>")
    main(sys.argv[1])
