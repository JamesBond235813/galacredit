#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-internal}"
case "$CHANNEL" in
  internal) EXPECTED_ID="com.galacredit.app.internal"; EXPECTED_ARTIFACT="APK" ;;
  play) EXPECTED_ID="com.galacredit.app"; EXPECTED_ARTIFACT="AAB" ;;
  *) echo "用法: $0 internal|play" >&2; exit 2 ;;
esac

ACTUAL_ID="${GALA_APPLICATION_ID:-$EXPECTED_ID}"
if [[ "$ACTUAL_ID" != "$EXPECTED_ID" ]]; then
  echo "错误：${CHANNEL} 渠道必须使用包名 ${EXPECTED_ID}，当前为 ${ACTUAL_ID}。" >&2
  exit 4
fi

if [[ "$CHANNEL" == "play" && "${GALA_SMS_COLLECTION_ENABLED:-false}" == "true" ]]; then
  echo "错误：Google Play 构建禁止启用 READ_SMS 采集能力。" >&2
  exit 3
fi

echo "渠道: $CHANNEL"
echo "期望包名: $EXPECTED_ID"
echo "期望产物: $EXPECTED_ARTIFACT"
if [[ "$CHANNEL" == "play" ]]; then
  : "${GALA_RELEASE_KEYSTORE:?Google Play 发布前必须配置 GALA_RELEASE_KEYSTORE}"
  : "${GALA_RELEASE_KEY_ALIAS:?Google Play 发布前必须配置 GALA_RELEASE_KEY_ALIAS}"
  echo "签名材料已配置；请使用 HBuilderX/Gradle 生成 AAB 后上传 Play Console。"
else
  echo "内部 APK 可使用 GALA_SMS_COLLECTION_ENABLED=true GALA_APPLICATION_ID=$EXPECTED_ID ./build_apk.sh debug 生成。"
fi
