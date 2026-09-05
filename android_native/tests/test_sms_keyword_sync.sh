#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SOURCE_FILE="$ROOT_DIR/3rd_doc/sms_keys20260602.csv"
ASSET_FILE="$ROOT_DIR/android_native/app/src/main/assets/sms_keys20260602.csv"
JS_FILE="$ROOT_DIR/frontend_uniapp/src/data/smsKeywords.js"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/galacredit-sms-keywords.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

test -s "$SOURCE_FILE"
test -s "$ASSET_FILE"
test -s "$JS_FILE"

# 三端必须使用同一份关键词顺序，避免 Java、UniApp 和服务端命中结果漂移。
# CSV 可能由 Windows 工具生成，比较前统一去除 CR，避免换行格式造成假差异。
sed 's/\r$//' "$SOURCE_FILE" > "$TMP_DIR/source_keywords.txt"
sed 's/\r$//' "$ASSET_FILE" > "$TMP_DIR/asset_keywords.txt"
diff -u "$TMP_DIR/source_keywords.txt" "$TMP_DIR/asset_keywords.txt"
sed -n '/Object.freeze(\[/,/^\])/p' "$JS_FILE" \
  | sed -n 's/^[[:space:]]*"\(.*\)"[,]\{0,1\}$/\1/p' > "$TMP_DIR/js_keywords.txt"
sed -i.bak '/^[[:space:]]*$/d' "$TMP_DIR/source_keywords.txt"
rm -f "$TMP_DIR/source_keywords.txt.bak"
diff -u "$TMP_DIR/source_keywords.txt" "$TMP_DIR/js_keywords.txt"

keyword_count="$(wc -l < "$TMP_DIR/source_keywords.txt" | tr -d ' ')"
test "$keyword_count" -gt 0
echo "SMS keyword sources are synchronized ($keyword_count keywords)"
