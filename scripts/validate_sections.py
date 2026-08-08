"""
Validates the Purelane sections before they can reach a store.

Checks two things a browser will not tell you about:
  1. Every {% schema %} block is valid JSON. A malformed schema does not error on the
     storefront -- the section simply never appears in the theme editor.
  2. Every Liquid block tag is closed. An unbalanced tag renders as raw text.

Run: python3 scripts/validate_sections.py
"""

import glob
import json
import re
import sys

BLOCK_TAGS = ("if", "for", "form", "unless", "case", "capture", "comment", "paginate")

failures = []

for path in sorted(glob.glob("sections/purelane-*.liquid")):
    source = open(path, encoding="utf-8").read()

    match = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}", source, re.S)
    if not match:
        failures.append(f"{path}: no schema block")
    else:
        try:
            schema = json.loads(match.group(1))
            if "name" not in schema:
                failures.append(f"{path}: schema has no name")
        except json.JSONDecodeError as err:
            failures.append(f"{path}: schema is not valid JSON — {err}")

    for tag in BLOCK_TAGS:
        opened = len(re.findall(r"\{%-?\s*" + tag + r"[\s%]", source))
        closed = len(re.findall(r"\{%-?\s*end" + tag + r"\s*-?%\}", source))
        if opened != closed:
            failures.append(f"{path}: {tag} unbalanced — {opened} open, {closed} closed")

    print(f"checked {path}")

for path in sorted(glob.glob("snippets/purelane-*.liquid")):
    source = open(path, encoding="utf-8").read()
    for tag in BLOCK_TAGS:
        opened = len(re.findall(r"\{%-?\s*" + tag + r"[\s%]", source))
        closed = len(re.findall(r"\{%-?\s*end" + tag + r"\s*-?%\}", source))
        if opened != closed:
            failures.append(f"{path}: {tag} unbalanced — {opened} open, {closed} closed")
    print(f"checked {path}")

if failures:
    print("\nFAILED:")
    for failure in failures:
        print(f"  {failure}")
    sys.exit(1)

print("\nAll sections valid.")
