#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HX_CLI="${GALA_HX_CLI:-/Applications/HBuilderX.app/Contents/MacOS/cli}"
# 复用已安装测试包的证书，保证覆盖安装时不因签名不一致丢失应用数据。
KEYSTORE="${GALA_KEYSTORE:-$ROOT_DIR/.local/app-plus-compatible.jks}"
test -x "$HX_CLI"
test -f "$KEYSTORE"
cd "$ROOT_DIR"
bash scripts/build-app-plus.sh
"$HX_CLI" pack --project "$ROOT_DIR" --platform android --safemode true \
  --android.packagename com.galacredit.app \
  --android.androidpacktype 0 \
  --android.certfile "$KEYSTORE" \
  --android.certalias "${GALA_KEY_ALIAS:-androiddebugkey}" \
  --android.certpassword "${GALA_KEY_PASSWORD:-android}" \
  --android.storepassword "${GALA_STORE_PASSWORD:-android}"
# CLI 的退出码并不总能反映云端失败；需查询任务状态后再认定成功。
"$HX_CLI" pack status --project "$ROOT_DIR"
