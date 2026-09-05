#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"

cd "$ROOT_DIR"
VITE_SMS_COLLECTION_ENABLED=false npm run build:h5 >/dev/null

if rg -l '(^|[^A-Za-z])rpx([^A-Za-z]|$)' "$DIST_DIR"/assets/*.css >/dev/null 2>&1; then
  echo "H5 生产产物仍包含未转换的 rpx 单位" >&2
  exit 1
fi
if ! rg -l 'rem' "$DIST_DIR"/assets/*.css >/dev/null 2>&1; then
  echo "H5 生产产物未生成兼容的 rem 单位" >&2
  exit 1
fi

if rg -l 'android\.permission\.READ_SMS|content://sms|ifectivo|yumicash' "$DIST_DIR/assets" >/dev/null 2>&1; then
  echo "安全渠道构建产物意外包含短信权限或关键词库" >&2
  exit 1
fi

VITE_SMS_COLLECTION_ENABLED=true npm run build:h5 >/dev/null
if ! rg -l 'android\.permission\.READ_SMS|content://sms|ifectivo|yumicash' "$DIST_DIR/assets" >/dev/null 2>&1; then
  echo "Internal 构建未包含短信能力输入，无法提供短信风控" >&2
  exit 1
fi

# 测试脚本结束时必须留下可安全发布的 Play/H5 产物，避免开发者运行检查后
# 误把 Internal 关键词库和短信能力带入默认 dist 目录。
VITE_SMS_COLLECTION_ENABLED=false npm run build:h5 >/dev/null
if rg -l 'android\.permission\.READ_SMS|content://sms|ifectivo|yumicash' "$DIST_DIR/assets" >/dev/null 2>&1; then
  echo "最终 H5 产物仍包含短信权限、短信 Provider 或关键词库" >&2
  exit 1
fi

echo "UniApp SMS channel asset checks passed"
