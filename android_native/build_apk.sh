#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
PLATFORM="${ANDROID_PLATFORM:-android-36}"
BUILD_TOOLS="${ANDROID_BUILD_TOOLS:-35.0.0}"
APP_ID="${GALA_APPLICATION_ID:-com.galacredit.app}"

AAPT2="$SDK_DIR/build-tools/$BUILD_TOOLS/aapt2"
D8="$SDK_DIR/build-tools/$BUILD_TOOLS/d8"
ZIPALIGN="$SDK_DIR/build-tools/$BUILD_TOOLS/zipalign"
APKSIGNER="$SDK_DIR/build-tools/$BUILD_TOOLS/apksigner"
ANDROID_JAR="$SDK_DIR/platforms/$PLATFORM/android.jar"

BUILD_TYPE="${1:-debug}"
# 按包名和构建类型隔离中间产物，避免 Play/internal 构建交替执行时互相清理。
BUILD_DIR="${GALA_BUILD_DIR:-$ROOT_DIR/build/${APP_ID}/${BUILD_TYPE}}"
RES_FLAT_DIR="$BUILD_DIR/res-flat"
CLASSES_DIR="$BUILD_DIR/classes"
DEX_DIR="$BUILD_DIR/dex"
GENERATED_SRC_DIR="$BUILD_DIR/generated-src"
CLASSES_JAR="$BUILD_DIR/classes.jar"
UNSIGNED_APK="$BUILD_DIR/galacredit-unsigned.apk"
ALIGNED_APK="$BUILD_DIR/galacredit-aligned.apk"
SIGNED_APK="$BUILD_DIR/galacredit-$BUILD_TYPE.apk"
MANIFEST_FILE="$BUILD_DIR/AndroidManifest.xml"

# 在清理旧产物前校验敏感权限与包名绑定，避免误配置时先删除已有构建结果。
if [[ "${GALA_SMS_COLLECTION_ENABLED:-false}" == "true" && "$APP_ID" != "com.galacredit.app.internal" ]]; then
  echo "错误：READ_SMS 只能用于 com.galacredit.app.internal 内部授权版本。" >&2
  exit 4
fi

rm -rf "$BUILD_DIR"
mkdir -p "$RES_FLAT_DIR" "$CLASSES_DIR" "$DEX_DIR" "$GENERATED_SRC_DIR/com/galacredit/app"

# 只有内部授权版才在最终 APK 中声明 READ_SMS；Google Play 构建默认不包含该权限。
cp "$ROOT_DIR/app/src/main/AndroidManifest.xml" "$MANIFEST_FILE"
sed -i.bak "s/package=\"com.galacredit.app\"/package=\"$APP_ID\"/" "$MANIFEST_FILE"
rm -f "$MANIFEST_FILE.bak"
if [[ "${GALA_SMS_COLLECTION_ENABLED:-false}" == "true" ]]; then
  sed -i.bak 's#<uses-permission android:name="android.permission.INTERNET" />#<uses-permission android:name="android.permission.INTERNET" />\n  <uses-permission android:name="android.permission.READ_SMS" />#' "$MANIFEST_FILE"
  rm -f "$MANIFEST_FILE.bak"
fi

# 敏感短信关键词库只能进入 internal 产物；Play 产物从构建输入层面移除，
# 不能只依赖运行时的包名判断，避免审核包意外携带短信采集资源。
AAPT_ASSETS_ARGS=()
SMS_SOURCE="$ROOT_DIR/app/src/main/java/com/galacredit/app/SmsCollector.java"
SMS_ENABLED="${GALA_SMS_COLLECTION_ENABLED:-false}"
if [ "$SMS_ENABLED" = "true" ]; then
  if [ -d "$ROOT_DIR/app/src/main/assets" ]; then
    AAPT_ASSETS_ARGS=(-A "$ROOT_DIR/app/src/main/assets")
  fi
else
  # 业务代码仍调用同名类型；Play 使用安全桩实现，保持主流程统一，
  # 同时确保真实短信读取代码不会进入 Play 的 classes.dex。
  cat > "$GENERATED_SRC_DIR/com/galacredit/app/SmsCollector.java" <<'EOF'
package com.galacredit.app;

import android.content.Context;
import org.json.JSONArray;

/** Google Play 构建中的短信能力安全桩；该渠道不声明也不读取短信。 */
final class SmsCollector {
    private SmsCollector() {
    }

    static boolean isInternalChannel(Context context) {
        return false;
    }

    static boolean isPermissionGranted(Context context) {
        return false;
    }

    static String permissionName() {
        return "";
    }

    static JSONArray collect(Context context) {
        return new JSONArray();
    }

    static CollectionResult collectWithStats(Context context) {
        return new CollectionResult(new JSONArray(), 0);
    }

    static final class CollectionResult {
        final JSONArray messages;
        final int scannedCount;

        CollectionResult(JSONArray messages, int scannedCount) {
            this.messages = messages;
            this.scannedCount = scannedCount;
        }
    }
}
EOF
fi

if [ "$BUILD_TYPE" = "release" ]; then
  : "${GALA_NATIVE_API_BASE:?请设置 GALA_NATIVE_API_BASE，例如 https://galacredit.ebamotor.com/api}"
  : "${GALA_NATIVE_ASSET_BASE:?请设置 GALA_NATIVE_ASSET_BASE，例如 https://galacredit.ebamotor.com}"
else
  GALA_NATIVE_API_BASE="${GALA_NATIVE_API_BASE:-https://galacredit.ebamotor.com/api}"
  GALA_NATIVE_ASSET_BASE="${GALA_NATIVE_ASSET_BASE:-https://galacredit.ebamotor.com}"
fi

"$AAPT2" compile --dir "$ROOT_DIR/app/src/main/res" -o "$RES_FLAT_DIR"
AAPT_LINK_ARGS=(
  link
  -I "$ANDROID_JAR"
  --manifest "$MANIFEST_FILE"
  --java "$BUILD_DIR/generated"
  --auto-add-overlay
  -o "$UNSIGNED_APK"
  "$RES_FLAT_DIR"/*.flat
)
if [ "${#AAPT_ASSETS_ARGS[@]}" -gt 0 ]; then
  AAPT_LINK_ARGS+=("${AAPT_ASSETS_ARGS[@]}")
fi
"$AAPT2" "${AAPT_LINK_ARGS[@]}"

# 运行时地址由构建渠道注入，避免调试包、内部包和生产包误用硬编码地址。
mkdir -p "$GENERATED_SRC_DIR/com/galacredit/app"
java_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}
ESCAPED_API_BASE="$(java_escape "$GALA_NATIVE_API_BASE")"
ESCAPED_ASSET_BASE="$(java_escape "$GALA_NATIVE_ASSET_BASE")"
printf '%s\n' \
  'package com.galacredit.app;' \
  '' \
  'final class AppConfig {' \
  "    static final String API_BASE = \"$ESCAPED_API_BASE\";" \
  "    static final String ASSET_BASE = \"$ESCAPED_ASSET_BASE\";" \
  "    static final String WEB_BASE_URL = \"$ESCAPED_ASSET_BASE\";" \
  '' \
  '    private AppConfig() {' \
  '    }' \
  '}' > "$GENERATED_SRC_DIR/com/galacredit/app/AppConfig.java"

find "$ROOT_DIR/app/src/main/java/com/galacredit/app" -name '*.java' ! -path "$SMS_SOURCE" -exec printf '"%s"\n' {} \; > "$BUILD_DIR/sources.txt"
# 使用构建时生成的 AppConfig，原始源码配置文件不重复编译。
sed -i.bak '/\/AppConfig\.java"$/d' "$BUILD_DIR/sources.txt"
rm -f "$BUILD_DIR/sources.txt.bak"
printf '"%s"\n' "$GENERATED_SRC_DIR/com/galacredit/app/AppConfig.java" >> "$BUILD_DIR/sources.txt"
if [ "$SMS_ENABLED" = "true" ]; then
  printf '"%s"\n' "$SMS_SOURCE" >> "$BUILD_DIR/sources.txt"
else
  printf '"%s"\n' "$GENERATED_SRC_DIR/com/galacredit/app/SmsCollector.java" >> "$BUILD_DIR/sources.txt"
fi
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
