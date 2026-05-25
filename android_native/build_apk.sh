#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
PLATFORM="${ANDROID_PLATFORM:-android-34}"
BUILD_TOOLS="${ANDROID_BUILD_TOOLS:-35.0.0}"
APP_ID="com.juxin.xiaohebao.admin"

AAPT2="$SDK_DIR/build-tools/$BUILD_TOOLS/aapt2"
D8="$SDK_DIR/build-tools/$BUILD_TOOLS/d8"
ZIPALIGN="$SDK_DIR/build-tools/$BUILD_TOOLS/zipalign"
APKSIGNER="$SDK_DIR/build-tools/$BUILD_TOOLS/apksigner"
ANDROID_JAR="$SDK_DIR/platforms/$PLATFORM/android.jar"

BUILD_TYPE="${1:-debug}"
BUILD_DIR="$ROOT_DIR/build"
RES_FLAT_DIR="$BUILD_DIR/res-flat"
CLASSES_DIR="$BUILD_DIR/classes"
DEX_DIR="$BUILD_DIR/dex"
CLASSES_JAR="$BUILD_DIR/classes.jar"
UNSIGNED_APK="$BUILD_DIR/xiaohebao-unsigned.apk"
ALIGNED_APK="$BUILD_DIR/xiaohebao-aligned.apk"
SIGNED_APK="$BUILD_DIR/xiaohebao-$BUILD_TYPE.apk"

rm -rf "$BUILD_DIR"
mkdir -p "$RES_FLAT_DIR" "$CLASSES_DIR" "$DEX_DIR"

if [ "$BUILD_TYPE" = "release" ]; then
  : "${XHB_NATIVE_API_BASE:?请设置 XHB_NATIVE_API_BASE，例如 https://xhbadmin.juxin.pro/api}"
  : "${XHB_NATIVE_ASSET_BASE:?请设置 XHB_NATIVE_ASSET_BASE，例如 https://xhbadmin.juxin.pro}"
else
  XHB_NATIVE_API_BASE="${XHB_NATIVE_API_BASE:-http://10.0.2.2:8001/api}"
  XHB_NATIVE_ASSET_BASE="${XHB_NATIVE_ASSET_BASE:-http://10.0.2.2:8001}"
fi

java_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

CONFIG_DIR="$BUILD_DIR/generated/com/juxin/xiaohebao/admin"
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_DIR/AppConfig.java" <<EOF
package com.juxin.xiaohebao.admin;

final class AppConfig {
    static final String API_BASE = "$(java_escape "$XHB_NATIVE_API_BASE")";
    static final String ASSET_BASE = "$(java_escape "$XHB_NATIVE_ASSET_BASE")";

    private AppConfig() {
    }
}
EOF

"$AAPT2" compile --dir "$ROOT_DIR/app/src/main/res" -o "$RES_FLAT_DIR"
"$AAPT2" link \
  -I "$ANDROID_JAR" \
  --manifest "$ROOT_DIR/app/src/main/AndroidManifest.xml" \
  --java "$BUILD_DIR/generated" \
  --auto-add-overlay \
  -o "$UNSIGNED_APK" \
  "$RES_FLAT_DIR"/*.flat

find "$ROOT_DIR/app/src/main/java" "$BUILD_DIR/generated" -name '*.java' -exec printf '"%s"\n' {} \; > "$BUILD_DIR/sources.txt"
javac -encoding UTF-8 -source 1.8 -target 1.8 \
  -classpath "$ANDROID_JAR" \
  -d "$CLASSES_DIR" \
  @"$BUILD_DIR/sources.txt"

jar cf "$CLASSES_JAR" -C "$CLASSES_DIR" .
"$D8" --min-api 23 --lib "$ANDROID_JAR" --output "$DEX_DIR" "$CLASSES_JAR"
cd "$DEX_DIR"
zip -q -u "$UNSIGNED_APK" classes.dex
cd "$ROOT_DIR"

"$ZIPALIGN" -f 4 "$UNSIGNED_APK" "$ALIGNED_APK"

if [ "$BUILD_TYPE" = "release" ]; then
  : "${XHB_RELEASE_KEYSTORE:?请设置 XHB_RELEASE_KEYSTORE}"
  : "${XHB_RELEASE_STORE_PASS:?请设置 XHB_RELEASE_STORE_PASS}"
  : "${XHB_RELEASE_KEY_ALIAS:?请设置 XHB_RELEASE_KEY_ALIAS}"
  : "${XHB_RELEASE_KEY_PASS:?请设置 XHB_RELEASE_KEY_PASS}"
  KEYSTORE="$XHB_RELEASE_KEYSTORE"
  STORE_PASS="$XHB_RELEASE_STORE_PASS"
  KEY_ALIAS="$XHB_RELEASE_KEY_ALIAS"
  KEY_PASS="$XHB_RELEASE_KEY_PASS"
else
  KEYSTORE="$BUILD_DIR/debug.keystore"
  STORE_PASS="android"
  KEY_ALIAS="androiddebugkey"
  KEY_PASS="android"
  if [ ! -f "$KEYSTORE" ]; then
    keytool -genkeypair \
      -keystore "$KEYSTORE" \
      -storepass "$STORE_PASS" \
      -keypass "$KEY_PASS" \
      -alias "$KEY_ALIAS" \
      -keyalg RSA \
      -keysize 2048 \
      -validity 10000 \
      -dname "CN=Android Debug,O=Xiaohebao,C=CN" >/dev/null 2>&1
  fi
fi

"$APKSIGNER" sign \
  --ks "$KEYSTORE" \
  --ks-key-alias "$KEY_ALIAS" \
  --ks-pass "pass:$STORE_PASS" \
  --key-pass "pass:$KEY_PASS" \
  --out "$SIGNED_APK" \
  "$ALIGNED_APK"

"$APKSIGNER" verify "$SIGNED_APK"
echo "$SIGNED_APK"
