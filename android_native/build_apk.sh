#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
PLATFORM="${ANDROID_PLATFORM:-android-36}"
BUILD_TOOLS="${ANDROID_BUILD_TOOLS:-35.0.0}"
APP_ID="com.galacredit.app"

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
UNSIGNED_APK="$BUILD_DIR/galacredit-unsigned.apk"
ALIGNED_APK="$BUILD_DIR/galacredit-aligned.apk"
SIGNED_APK="$BUILD_DIR/galacredit-$BUILD_TYPE.apk"

rm -rf "$BUILD_DIR"
mkdir -p "$RES_FLAT_DIR" "$CLASSES_DIR" "$DEX_DIR"

if [ "$BUILD_TYPE" = "release" ]; then
  : "${GALA_NATIVE_API_BASE:?请设置 GALA_NATIVE_API_BASE，例如 https://galacredit.ebamotor.com/api}"
  : "${GALA_NATIVE_ASSET_BASE:?请设置 GALA_NATIVE_ASSET_BASE，例如 https://galacredit.ebamotor.com}"
else
  GALA_NATIVE_API_BASE="${GALA_NATIVE_API_BASE:-https://galacredit.ebamotor.com/api}"
  GALA_NATIVE_ASSET_BASE="${GALA_NATIVE_ASSET_BASE:-https://galacredit.ebamotor.com}"
fi

java_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

"$AAPT2" compile --dir "$ROOT_DIR/app/src/main/res" -o "$RES_FLAT_DIR"
"$AAPT2" link \
  -I "$ANDROID_JAR" \
  --manifest "$ROOT_DIR/app/src/main/AndroidManifest.xml" \
  --java "$BUILD_DIR/generated" \
  --auto-add-overlay \
  -o "$UNSIGNED_APK" \
  "$RES_FLAT_DIR"/*.flat

find "$ROOT_DIR/app/src/main/java/com/galacredit/app" -name '*.java' -exec printf '"%s"\n' {} \; > "$BUILD_DIR/sources.txt"
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
  : "${GALA_RELEASE_KEYSTORE:?请设置 GALA_RELEASE_KEYSTORE}"
  : "${GALA_RELEASE_STORE_PASS:?请设置 GALA_RELEASE_STORE_PASS}"
  : "${GALA_RELEASE_KEY_ALIAS:?请设置 GALA_RELEASE_KEY_ALIAS}"
  : "${GALA_RELEASE_KEY_PASS:?请设置 GALA_RELEASE_KEY_PASS}"
  KEYSTORE="$GALA_RELEASE_KEYSTORE"
  STORE_PASS="$GALA_RELEASE_STORE_PASS"
  KEY_ALIAS="$GALA_RELEASE_KEY_ALIAS"
  KEY_PASS="$GALA_RELEASE_KEY_PASS"
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
      -dname "CN=Android Debug,O=GalaCredit,C=GH" >/dev/null 2>&1
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
