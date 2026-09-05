#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-play}"
if [[ "$CHANNEL" != "play" && "$CHANNEL" != "internal" ]]; then
  echo "用法: $0 play|internal" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST_FILE="$ROOT_DIR/manifest.json"
BACKUP_FILE="$(mktemp)"
cp "$MANIFEST_FILE" "$BACKUP_FILE"
restore_manifest() {
  cp "$BACKUP_FILE" "$MANIFEST_FILE"
  rm -f "$BACKUP_FILE"
}
trap restore_manifest EXIT
if [[ "$CHANNEL" == "internal" ]]; then
  cp "$ROOT_DIR/manifest.internal.json" "$MANIFEST_FILE"
  export VITE_APP_CHANNEL=internal
  export VITE_SMS_COLLECTION_ENABLED=true
else
  export VITE_APP_CHANNEL=play
  export VITE_SMS_COLLECTION_ENABLED=false
fi

if command -v uni >/dev/null 2>&1; then
  uni build -p app-plus
  exit $?
fi
if command -v cli >/dev/null 2>&1 && cli --help 2>/dev/null | grep -qi 'uni'; then
  cli build -p app-plus
  exit $?
fi
cat >&2 <<'EOF'
未检测到 HBuilderX/uni-app CLI。
请安装 HBuilderX CLI 或使用 HBuilderX 打开 frontend_uniapp 后执行 app-plus 构建。
调用方式：./scripts/build-app.sh internal（内部 APK，含短信权限）或 ./scripts/build-app.sh play（Google Play AAB，不含短信权限）。iOS 需在 Xcode 中 Archive。
EOF
exit 2
