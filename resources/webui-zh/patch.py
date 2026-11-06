"""Add a Simplified Chinese resource to a Stalwart WebUI bundle.

The shipped bundle registers exactly one i18next resource (`en`) inside a
module-scoped instance, so a script outside the bundle cannot reach it. This
rewrites the bundle in place instead:

  * injects `ZH={...}` immediately before the English table,
  * registers it as the `zh` resource next to `en`,
  * selects `zh` when the browser language is Chinese.

`zh` is the key the WebUI actually asks i18next for: it derives the language
with `navigator.language.split("-")[0]`, so `zh-CN` becomes `zh`.

Everything else is left byte-identical.

Usage:
    python -I patch.py <bundle-dir> [zh.json]

Idempotent: running it twice is a no-op.
"""
import glob
import json
import os
import sys

EN_TABLE_ANCHOR = "fe={accounts:`Accounts`"
INIT_ANCHOR = "init({resources:{en:{translation:fe}},lng:navigator.language?.split(`-`)[0]||`en`"
INIT_PATCHED = (
    "init({resources:{en:{translation:fe},zh:{translation:ZH}},"
    "lng:navigator.language?.split(`-`)[0]===`zh`?`zh`:(navigator.language?.split(`-`)[0]||`en`)"
)


def find_chunk(bundle):
    """Locate the chunk holding the i18n table, without pinning its hashed name."""
    matches = []
    for path in glob.glob(os.path.join(bundle, "assets", "*.js")):
        with open(path, encoding="utf-8") as handle:
            if EN_TABLE_ANCHOR in handle.read():
                matches.append(path)
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one chunk with the i18n table, found {len(matches)}: {matches}"
        )
    return matches[0]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    bundle = sys.argv[1]
    zh_json = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(os.path.dirname(os.path.abspath(__file__)), "zh.json")
    )

    chunk = find_chunk(bundle)
    with open(chunk, encoding="utf-8") as handle:
        src = handle.read()

    if "zh:{translation:ZH}" in src:
        print(f"already patched: {chunk}")
        return

    for anchor, what in ((EN_TABLE_ANCHOR, "English table"), (INIT_ANCHOR, "i18n init")):
        if anchor not in src:
            raise SystemExit(f"{what} anchor not found; the WebUI bundle layout changed")

    nested = json.load(open(zh_json, encoding="utf-8"))["zh"]["translation"]
    zh_literal = "ZH=" + json.dumps(nested, ensure_ascii=False, separators=(",", ":")) + ";"

    src = src.replace(EN_TABLE_ANCHOR, zh_literal + EN_TABLE_ANCHOR, 1)
    src = src.replace(INIT_ANCHOR, INIT_PATCHED, 1)

    with open(chunk, "w", encoding="utf-8", newline="") as handle:
        handle.write(src)

    leaves = sum(1 for _ in _walk(nested))
    print(f"patched: {chunk}")
    print(f"zh entries: {leaves}")


def _walk(node):
    for value in node.values():
        if isinstance(value, dict):
            yield from _walk(value)
        else:
            yield value


if __name__ == "__main__":
    main()
