#!/usr/bin/env bash
# Rebuild the derived assets under resources/html-templates.
#
# Only files that actually changed are rebuilt. ui.css is left untouched and its
# already-shipped minified form is reused, so the diff stays minimal.
#
# Derived-file contract (mirrors crates/http/src/request.rs):
#   ui.hash            sha256(<ui.css.min> + <ui.js.min>)[:12]
#   *.html.min         same HTML with ui-HASH replaced by ui-<hash>
#   *.min.gz           gzip -9 -n of the corresponding .min file
set -euo pipefail

ROOT="${1:?usage: rebuild-assets.sh <repo-root> <node_modules/.bin>}"
TOOLS="${2:?usage: rebuild-assets.sh <repo-root> <node_modules/.bin>}"
TPL="$ROOT/resources/html-templates"

HTML_MIN="$TOOLS/html-minifier-terser"
TERSER="$TOOLS/terser"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# 1. Reuse the shipped CSS artifact: decompress the .gz, which is the source of truth.
gzip -dc "$TPL/ui.css.min.gz" > "$work/ui.css.min"

# 2. Minify ui.js from its readable source.
"$TERSER" "$TPL/ui.js" -c -m -o "$work/ui.js.min"

# 3. Content hash, exactly as the server assembles the asset prefix.
HASH="$(cat "$work/ui.css.min" "$work/ui.js.min" | sha256sum | cut -c1-12)"
echo "ui.hash = $HASH"

# 4. Point the HTML pages at the new asset names before minifying them.
sed "s|ui-HASH|ui-$HASH|g" "$TPL/login.html" > "$work/login.html"
sed "s|ui-HASH|ui-$HASH|g" "$TPL/calendar-rsvp.html" > "$work/calendar-rsvp.html"

for page in login calendar-rsvp; do
    "$HTML_MIN" --collapse-whitespace --conservative-collapse --minify-css true \
        "$work/$page.html" -o "$TPL/$page.html.min"
    gzip -9 -n -c "$TPL/$page.html.min" > "$TPL/$page.html.min.gz"
done

# 5. Install the JS artifacts.
gzip -9 -n -c "$work/ui.js.min" > "$TPL/ui.js.min.gz"

# No trailing newline: request.rs asserts UI_ASSET_PREFIX.len() == "ui-".len() + 12,
# so a stray "\n" in this file would fail the build.
printf '%s' "$HASH" > "$TPL/ui.hash"

echo "done"
