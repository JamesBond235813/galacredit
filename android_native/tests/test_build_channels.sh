#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
AAPT2="$SDK_DIR/build-tools/${ANDROID_BUILD_TOOLS:-35.0.0}/aapt2"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/galacredit-build-test.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/tests/test_sms_keyword_sync.sh"

play_dir="$TMP_DIR/play"
internal_dir="$TMP_DIR/internal"

GALA_BUILD_DIR="$play_dir" "$ROOT_DIR/build_apk.sh" debug >/dev/null
play_apk="$play_dir/galacredit-debug.apk"
test -f "$play_apk"
grep -q 'MIXED_CONTENT_NEVER_ALLOW' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'removeAllCookies' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'isInternalChannel' "$ROOT_DIR/app/src/main/java/com/galacredit/app/SmsCollector.java"
grep -q 'startSmsReview(callbackName, Boolean(consent))' "$ROOT_DIR/../frontend_uniapp/src/utils/sms.js"
play_badging_file="$TMP_DIR/play-badging.txt"
play_permissions_file="$TMP_DIR/play-permissions.txt"
"$AAPT2" dump badging "$play_apk" > "$play_badging_file"
"$AAPT2" dump permissions "$play_apk" > "$play_permissions_file"
grep -q "package: name='com.galacredit.app'" "$play_badging_file"
if grep -q "android.permission.READ_SMS" "$play_permissions_file"; then
  echo "Play build unexpectedly declares READ_SMS" >&2
  exit 1
fi
unzip -l "$play_apk" > "$TMP_DIR/play-zip.txt"
if grep -q 'assets/sms_keys20260602\.csv' "$TMP_DIR/play-zip.txt"; then
  echo "Play build unexpectedly contains SMS collector or keyword asset" >&2
  exit 1
fi
play_strings="$TMP_DIR/play-classes.strings"
internal_strings="$TMP_DIR/internal-classes.strings"
unzip -p "$play_apk" classes.dex > "$TMP_DIR/play-classes.dex"
strings "$TMP_DIR/play-classes.dex" > "$play_strings"
if grep -q 'sms_keys20260602.csv' "$play_strings"; then
  echo "Play classes.dex unexpectedly contains SMS keyword collector code" >&2
  exit 1
fi
if grep -Eq 'READ_SMS|android.permission.READ_SMS' "$play_strings"; then
  echo "Play classes.dex unexpectedly contains SMS permission code" >&2
  exit 1
fi

GALA_SMS_COLLECTION_ENABLED=true \
GALA_APPLICATION_ID=com.galacredit.app.internal \
GALA_BUILD_DIR="$internal_dir" \
"$ROOT_DIR/build_apk.sh" debug >/dev/null
internal_apk="$internal_dir/galacredit-debug.apk"
test -f "$internal_apk"
internal_badging_file="$TMP_DIR/internal-badging.txt"
internal_permissions_file="$TMP_DIR/internal-permissions.txt"
"$AAPT2" dump badging "$internal_apk" > "$internal_badging_file"
"$AAPT2" dump permissions "$internal_apk" > "$internal_permissions_file"
grep -q "package: name='com.galacredit.app.internal'" "$internal_badging_file"
grep -q "android.permission.READ_SMS" "$internal_permissions_file"
unzip -l "$internal_apk" > "$TMP_DIR/internal-zip.txt"
grep -q 'assets/sms_keys20260602.csv' "$TMP_DIR/internal-zip.txt"
unzip -p "$internal_apk" classes.dex > "$TMP_DIR/internal-classes.dex"
strings "$TMP_DIR/internal-classes.dex" > "$internal_strings"
grep -q 'sms_keys20260602.csv' "$internal_strings"

# WebView 生命周期必须显式暂停/恢复，避免后台计时器和桥接回调失控。
grep -q 'protected void onResume()' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'webView.resumeTimers()' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q "galacredit:resume" "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'protected void onPause()' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'webView.pauseTimers()' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'resolveInitialUrl' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"
grep -q 'intent.putExtra("url"' "$ROOT_DIR/app/src/main/java/com/galacredit/app/MainActivity.java"
grep -q 'activePolicyDialog' "$ROOT_DIR/app/src/main/java/com/galacredit/app/MainActivity.java"
grep -q 'JSONObject.quote' "$ROOT_DIR/app/src/main/java/com/galacredit/app/NativeWebViewActivity.java"

custom_dir="$TMP_DIR/custom"
GALA_BUILD_DIR="$custom_dir" \
GALA_NATIVE_API_BASE="https://api.example.test/v2" \
GALA_NATIVE_ASSET_BASE="https://assets.example.test" \
"$ROOT_DIR/build_apk.sh" debug >/dev/null
grep -q 'https://api.example.test/v2' "$custom_dir/generated-src/com/galacredit/app/AppConfig.java"
grep -q 'https://assets.example.test' "$custom_dir/generated-src/com/galacredit/app/AppConfig.java"

# 错误组合必须在清理前失败，并且不影响已经生成的 Play 产物。
if GALA_SMS_COLLECTION_ENABLED=true GALA_BUILD_DIR="$play_dir" "$ROOT_DIR/build_apk.sh" debug >/dev/null 2>&1; then
  echo "Invalid Play SMS configuration unexpectedly succeeded" >&2
  exit 1
fi
test -f "$play_apk"

echo "Android channel build checks passed"
